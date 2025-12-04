from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from django.http import StreamingHttpResponse

from core.models import Buggy, BuggyRouteStop, RideRequest, User, POI
from core.serializers import (
    UserSerializer,
    BuggySummarySerializer,
    BuggyRouteStopSerializer,
    RideRequestSerializer,
    RideRequestCreateSerializer,
    RideWithAssignmentSerializer,
    POISerializer,
)
from core.services.routing import assign_ride_to_best_buggy, NoActiveBuggiesError
from core.services.events import (
    get_driver_event_stream,
    send_event_to_driver,
    get_dispatcher_event_stream,
    send_event_to_all_dispatchers,
)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class POIsListView(ListAPIView):
    """List all Points of Interest in the resort."""
    permission_classes = [IsAuthenticated]
    serializer_class = POISerializer
    queryset = POI.objects.all().order_by('name')


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

        # Send SSE notification to driver if buggy has a driver
        if buggy.driver:
            send_event_to_driver(
                driver_id=buggy.driver.id,
                event_type="new_ride",
                data={
                    "ride_id": ride.id,
                    "ride_code": ride.public_code,
                    "buggy_id": buggy.id,
                    "buggy_name": buggy.display_name,
                }
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

        # Notify all dispatchers of ride status update
        send_event_to_all_dispatchers(
            event_type="ride_status_update",
            data={
                "ride_id": ride.id,
                "ride_code": ride.public_code,
                "buggy_id": buggy.id,
                "buggy_name": buggy.display_name,
                "stop_type": stop.stop_type,
                "action": "started",
                "new_status": ride.status,
            }
        )

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

        buggy.save(update_fields=["current_poi", "current_onboard_guests"])

        stop.status = BuggyRouteStop.StopStatus.COMPLETED
        stop.completed_at = timezone.now()
        stop.save(update_fields=["status", "completed_at"])

        if stop.stop_type == BuggyRouteStop.StopType.DROPOFF:
            remaining = ride.route_stops.exclude(status=BuggyRouteStop.StopStatus.COMPLETED)
            if not remaining.exists():
                ride.status = RideRequest.Status.COMPLETED
                ride.dropoff_completed_at = timezone.now()
                ride.save(update_fields=["status", "dropoff_completed_at"])

        # Notify all dispatchers of ride status update
        send_event_to_all_dispatchers(
            event_type="ride_status_update",
            data={
                "ride_id": ride.id,
                "ride_code": ride.public_code,
                "buggy_id": buggy.id,
                "buggy_name": buggy.display_name,
                "stop_type": stop.stop_type,
                "action": "completed",
                "new_status": ride.status,
            }
        )

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


# ===== Manager CRUD Views =====

class ManagerPermission:
    """Helper to check if user is a manager."""
    @staticmethod
    def check(request):
        if not request.user.is_authenticated:
            return False
        return request.user.role == User.Role.MANAGER


class BuggyCRUDView(APIView):
    """CRUD operations for buggies (Manager only)."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create a new buggy."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        from core.serializers import BuggyCreateUpdateSerializer
        serializer = BuggyCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            buggy = serializer.save()
            return Response(BuggySummarySerializer(buggy).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, buggy_id):
        """Update an existing buggy."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        buggy = get_object_or_404(Buggy, id=buggy_id)
        from core.serializers import BuggyCreateUpdateSerializer
        serializer = BuggyCreateUpdateSerializer(buggy, data=request.data, partial=True)
        if serializer.is_valid():
            buggy = serializer.save()
            return Response(BuggySummarySerializer(buggy).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, buggy_id):
        """Delete a buggy."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        buggy = get_object_or_404(Buggy, id=buggy_id)
        
        # Prevent deletion if buggy has active/planned route stops
        active_stops = BuggyRouteStop.objects.filter(
            buggy=buggy,
            status__in=[BuggyRouteStop.StopStatus.PLANNED, BuggyRouteStop.StopStatus.ON_ROUTE]
        ).exists()
        
        if active_stops:
            return Response(
                {"error": "Cannot delete buggy with active route stops"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        buggy.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DriverCRUDView(APIView):
    """CRUD operations for drivers (Manager only)."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all drivers."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        drivers = User.objects.filter(role=User.Role.DRIVER).order_by('username')
        from core.serializers import DriverCreateUpdateSerializer
        serializer = DriverCreateUpdateSerializer(drivers, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new driver."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        from core.serializers import DriverCreateUpdateSerializer
        serializer = DriverCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            driver = serializer.save()
            return Response(DriverCreateUpdateSerializer(driver).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, driver_id):
        """Update an existing driver."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        driver = get_object_or_404(User, id=driver_id, role=User.Role.DRIVER)
        from core.serializers import DriverCreateUpdateSerializer
        serializer = DriverCreateUpdateSerializer(driver, data=request.data, partial=True)
        if serializer.is_valid():
            driver = serializer.save()
            return Response(DriverCreateUpdateSerializer(driver).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, driver_id):
        """Delete a driver."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        driver = get_object_or_404(User, id=driver_id, role=User.Role.DRIVER)
        
        # Prevent deletion if driver has assigned buggies
        if Buggy.objects.filter(driver=driver).exists():
            return Response(
                {"error": "Cannot delete driver with assigned buggies"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        driver.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class POICRUDView(APIView):
    """CRUD operations for POIs (Manager only)."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create a new POI."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        from core.serializers import POICreateUpdateSerializer
        serializer = POICreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            poi = serializer.save()
            return Response(POISerializer(poi).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, poi_id):
        """Update an existing POI."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        poi = get_object_or_404(POI, id=poi_id)
        from core.serializers import POICreateUpdateSerializer
        serializer = POICreateUpdateSerializer(poi, data=request.data, partial=True)
        if serializer.is_valid():
            poi = serializer.save()
            return Response(POISerializer(poi).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, poi_id):
        """Delete a POI."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        poi = get_object_or_404(POI, id=poi_id)
        
        # Prevent deletion if POI is currently used by buggies
        if Buggy.objects.filter(current_poi=poi).exists():
            return Response(
                {"error": "Cannot delete POI - buggies are currently at this location"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prevent deletion if POI is used by any rides (to preserve historical data)
        if RideRequest.objects.filter(
            models.Q(pickup_poi=poi) | models.Q(dropoff_poi=poi)
        ).exists():
            return Response(
                {"error": "Cannot delete POI - rides are using this location"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prevent deletion if POI is used in any route stops (to preserve historical data)
        if BuggyRouteStop.objects.filter(poi=poi).exists():
            return Response(
                {"error": "Cannot delete POI - route stops are using this location"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        poi.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class POIEdgeCRUDView(APIView):
    """CRUD operations for POI edges (Manager only)."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all POI edges, optionally filtered by POI."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        from core.models import PoiEdge
        from core.serializers import POIEdgeSerializer
        
        # Check if filtering by specific POI
        poi_id = request.query_params.get('poi_id')
        if poi_id:
            # Get edges where this POI is either from or to
            edges = PoiEdge.objects.filter(
                models.Q(from_poi_id=poi_id) | models.Q(to_poi_id=poi_id)
            ).select_related('from_poi', 'to_poi').order_by('from_poi__name', 'to_poi__name')
        else:
            # Get all edges
            edges = PoiEdge.objects.all().select_related('from_poi', 'to_poi').order_by('from_poi__name', 'to_poi__name')
        
        serializer = POIEdgeSerializer(edges, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new POI edge."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        from django.db import IntegrityError
        from core.serializers import POIEdgeCreateUpdateSerializer, POIEdgeSerializer
        serializer = POIEdgeCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                edge = serializer.save()
                return Response(POIEdgeSerializer(edge).data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {"error": "Edge between these POIs already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, edge_id):
        """Update an existing POI edge."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        from core.models import PoiEdge
        from core.serializers import POIEdgeCreateUpdateSerializer, POIEdgeSerializer
        edge = get_object_or_404(PoiEdge, id=edge_id)
        serializer = POIEdgeCreateUpdateSerializer(edge, data=request.data, partial=True)
        if serializer.is_valid():
            edge = serializer.save()
            return Response(POIEdgeSerializer(edge).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, edge_id):
        """Delete a POI edge."""
        if not ManagerPermission.check(request):
            return Response({"error": "Manager role required"}, status=status.HTTP_403_FORBIDDEN)
        
        from core.models import PoiEdge
        edge = get_object_or_404(PoiEdge, id=edge_id)
        edge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ===== Driver SSE Notifications =====

from django.views import View
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@method_decorator(csrf_exempt, name='dispatch')
class DriverRideNotificationsView(View):
    """Server-Sent Events endpoint for real-time driver notifications."""
    
    def options(self, request):
        """Handle CORS preflight."""
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    def get(self, request):
        """Stream SSE events to the driver."""
        # Authenticate via token query parameter (EventSource doesn't support headers)
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        token = request.GET.get('token')
        if not token:
            return JsonResponse({"error": "Token required"}, status=401)
        
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
        except (TokenError, User.DoesNotExist):
            return JsonResponse({"error": "Invalid token"}, status=401)
        
        # Verify user is a driver
        if user.role != User.Role.DRIVER:
            return JsonResponse({"error": "Driver role required"}, status=403)
        
        # Get driver's event stream
        event_stream = get_driver_event_stream(user.id)
        
        # Return streaming response
        response = StreamingHttpResponse(
            event_stream,
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
        # CORS headers for SSE
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response


@method_decorator(csrf_exempt, name='dispatch')
class DispatcherRideNotificationsView(View):
    """Server-Sent Events endpoint for real-time dispatcher notifications."""
    
    def options(self, request):
        """Handle CORS preflight."""
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    def get(self, request):
        """Stream SSE events to the dispatcher."""
        # Authenticate via token query parameter (EventSource doesn't support headers)
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        token = request.GET.get('token')
        if not token:
            return JsonResponse({"error": "Token required"}, status=401)
        
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
        except (TokenError, User.DoesNotExist):
            return JsonResponse({"error": "Invalid token"}, status=401)
        
        # Verify user is a dispatcher
        if user.role != User.Role.DISPATCHER:
            return JsonResponse({"error": "Dispatcher role required"}, status=403)
        
        # Get dispatcher's event stream
        event_stream = get_dispatcher_event_stream(user.id)
        
        # Return streaming response
        response = StreamingHttpResponse(
            event_stream,
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
        # CORS headers for SSE
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

