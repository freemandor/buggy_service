from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models

from core.models import Buggy, BuggyRouteStop, RideRequest, User
from core.serializers import (
    UserSerializer,
    BuggySummarySerializer,
    BuggyRouteStopSerializer,
    RideRequestSerializer,
    RideRequestCreateSerializer,
    RideWithAssignmentSerializer,
)
from core.services.routing import assign_ride_to_best_buggy, NoActiveBuggiesError


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class BuggiesListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BuggySummarySerializer

    def get_queryset(self):
        return Buggy.objects.select_related("current_poi")


class RidesListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RideRequestSerializer

    def get_queryset(self):
        return (
            RideRequest.objects
            .select_related("pickup_poi", "dropoff_poi", "assigned_buggy", "assigned_buggy__current_poi")
            .order_by("-requested_at")[:100]
        )


class RideCreateAndAssignView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RideRequestCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        ride = serializer.save()

        try:
            buggy = assign_ride_to_best_buggy(ride)
        except NoActiveBuggiesError:
            ride.delete()
            return Response(
                {"detail": "Cannot create ride: no active buggies.", "code": "NO_ACTIVE_BUGGIES"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        out = RideWithAssignmentSerializer({"ride": ride, "assigned_buggy": buggy}).data
        return Response(out, status=status.HTTP_201_CREATED)


class DriverMyRouteView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BuggyRouteStopSerializer

    def get_queryset(self):
        user = self.request.user
        buggy = getattr(user, "assigned_buggy", None)
        if not buggy:
            return BuggyRouteStop.objects.none()
        return (
            BuggyRouteStop.objects
            .filter(buggy=buggy)
            .exclude(status=BuggyRouteStop.StopStatus.COMPLETED)
            .select_related("poi", "ride_request")
            .order_by("sequence_index")
        )


class DriverStopStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, stop_id):
        user = request.user
        buggy = getattr(user, "assigned_buggy", None)
        if not buggy:
            return Response({"detail": "No buggy assigned"}, status=status.HTTP_403_FORBIDDEN)

        stop = get_object_or_404(BuggyRouteStop, id=stop_id, buggy=buggy)

        first = (
            BuggyRouteStop.objects
            .filter(buggy=buggy)
            .exclude(status=BuggyRouteStop.StopStatus.COMPLETED)
            .order_by("sequence_index")
            .first()
        )
        if not first or first.id != stop.id:
            return Response({"detail": "Can only start the next stop in sequence"}, status=status.HTTP_400_BAD_REQUEST)

        if stop.status != BuggyRouteStop.StopStatus.PLANNED:
            return Response({"detail": "Stop is not in PLANNED status"}, status=status.HTTP_400_BAD_REQUEST)

        stop.status = BuggyRouteStop.StopStatus.ON_ROUTE
        stop.save(update_fields=["status"])

        ride = stop.ride_request
        if stop.stop_type == BuggyRouteStop.StopType.PICKUP:
            ride.status = RideRequest.Status.PICKING_UP
            ride.save(update_fields=["status"])

        return Response({"detail": "Stop started."})


class DriverStopCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, stop_id):
        user = request.user
        buggy = getattr(user, "assigned_buggy", None)
        if not buggy:
            return Response({"detail": "No buggy assigned"}, status=status.HTTP_403_FORBIDDEN)

        stop = get_object_or_404(BuggyRouteStop, id=stop_id, buggy=buggy)
        if stop.status != BuggyRouteStop.StopStatus.ON_ROUTE:
            return Response({"detail": "Stop is not ON_ROUTE"}, status=status.HTTP_400_BAD_REQUEST)

        ride = stop.ride_request

        buggy.current_poi = stop.poi

        if stop.stop_type == BuggyRouteStop.StopType.PICKUP:
            buggy.current_onboard_guests += ride.num_guests
            ride.status = RideRequest.Status.IN_PROGRESS
            ride.pickup_completed_at = timezone.now()
            ride.save(update_fields=["status", "pickup_completed_at"])
        else:
            buggy.current_onboard_guests -= ride.num_guests
            remaining = ride.route_stops.exclude(status=BuggyRouteStop.StopStatus.COMPLETED)
            if not remaining.exists():
                ride.status = RideRequest.Status.COMPLETED
                ride.dropoff_completed_at = timezone.now()
                ride.save(update_fields=["status", "dropoff_completed_at"])

        buggy.save(update_fields=["current_poi", "current_onboard_guests"])

        stop.status = BuggyRouteStop.StopStatus.COMPLETED
        stop.completed_at = timezone.now()
        stop.save(update_fields=["status", "completed_at"])

        return Response({"detail": "Stop completed."})


class MetricsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        qs = RideRequest.objects.filter(requested_at__date=today)

        total_rides = qs.count()
        avg_wait = (
            qs.filter(assigned_at__isnull=False)
            .annotate(wait_s=models.ExpressionWrapper(
                models.F("assigned_at") - models.F("requested_at"),
                output_field=models.DurationField(),
            ))
            .aggregate(avg=models.Avg("wait_s"))["avg"]
        )
        avg_wait_s = int(avg_wait.total_seconds()) if avg_wait else None

        return Response(
            {
                "date": today.isoformat(),
                "total_rides": total_rides,
                "avg_wait_time_s": avg_wait_s,
            }
        )
