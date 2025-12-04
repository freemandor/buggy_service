from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Buggy, BuggyRouteStop, POI, RideRequest, User


class DriverStopCompletionTests(APITestCase):
    def setUp(self):
        self.driver = User.objects.create_user(
            username="driver1",
            password="driver1",
            role=User.Role.DRIVER,
        )
        self.reception = POI.objects.create(code="RECEPTION", name="Reception")
        self.beach_bar = POI.objects.create(code="BEACH_BAR", name="Beach Bar")

        self.buggy = Buggy.objects.create(
            code="BUGGY_1",
            display_name="Buggy #1",
            capacity=4,
            status=Buggy.Status.ACTIVE,
            current_poi=self.reception,
            current_onboard_guests=2,
            driver=self.driver,
        )

        self.ride = RideRequest.objects.create(
            pickup_poi=self.reception,
            dropoff_poi=self.beach_bar,
            num_guests=2,
            status=RideRequest.Status.IN_PROGRESS,
            assigned_buggy=self.buggy,
            pickup_completed_at=timezone.now(),
        )

        self.stop = BuggyRouteStop.objects.create(
            buggy=self.buggy,
            ride_request=self.ride,
            stop_type=BuggyRouteStop.StopType.DROPOFF,
            poi=self.beach_bar,
            sequence_index=0,
            status=BuggyRouteStop.StopStatus.ON_ROUTE,
        )

    def test_final_dropoff_marks_ride_completed(self):
        self.client.force_authenticate(user=self.driver)

        url = reverse("driver-stop-complete", kwargs={"stop_id": self.stop.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.ride.refresh_from_db()
        self.stop.refresh_from_db()
        self.buggy.refresh_from_db()

        self.assertEqual(self.ride.status, RideRequest.Status.COMPLETED)
        self.assertIsNotNone(self.ride.dropoff_completed_at)
        self.assertEqual(self.stop.status, BuggyRouteStop.StopStatus.COMPLETED)
        self.assertEqual(self.buggy.current_poi, self.beach_bar)
        self.assertEqual(self.buggy.current_onboard_guests, 0)
