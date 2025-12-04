from django.db.models import Q
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Buggy, POI, PoiEdge, RideRequest, User


class RideCreationPlaceholderTests(APITestCase):
    def setUp(self):
        self.dispatcher = User.objects.create_user(
            username="dispatcher",
            password="dispatcher",
            role=User.Role.DISPATCHER,
        )
        self.client.force_authenticate(user=self.dispatcher)

        self.reception = POI.objects.create(code="RECEPTION", name="Reception")
        self.beach_bar = POI.objects.create(code="BEACH_BAR", name="Beach Bar")
        PoiEdge.objects.create(from_poi=self.reception, to_poi=self.beach_bar, travel_time_s=120)

        self.buggy = Buggy.objects.create(
            code="BUGGY_1",
            display_name="Buggy #1",
            capacity=4,
            status=Buggy.Status.ACTIVE,
            current_poi=self.reception,
            current_onboard_guests=0,
        )

        self.create_url = reverse("rides-create-and-assign")

    def test_missing_codes_use_placeholder_pois(self):
        payload = {
            "pickup_poi_code": "",
            "dropoff_poi_code": "",
            "num_guests": 2,
            "room_number": "101",
            "guest_name": "Placeholder Ride",
        }

        response = self.client.post(self.create_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ride_id = response.data["ride"]["id"]
        ride = RideRequest.objects.get(id=ride_id)

        self.assertEqual(ride.pickup_poi.code, "N/A-PICKUP")
        self.assertEqual(ride.dropoff_poi.code, "N/A-DROPOFF")

        na_pickup = ride.pickup_poi
        na_dropoff = ride.dropoff_poi

        # Placeholder POIs should be connected to all other POIs with the default travel time.
        for poi in [self.reception, self.beach_bar, na_dropoff]:
            self.assertTrue(
                PoiEdge.objects.filter(
                    Q(from_poi=na_pickup, to_poi=poi) | Q(from_poi=poi, to_poi=na_pickup)
                ).exists()
            )
        for poi in [self.reception, self.beach_bar, na_pickup]:
            self.assertTrue(
                PoiEdge.objects.filter(
                    Q(from_poi=na_dropoff, to_poi=poi) | Q(from_poi=poi, to_poi=na_dropoff)
                ).exists()
            )

    def test_unknown_poi_code_returns_400(self):
        payload = {
            "pickup_poi_code": "UNKNOWN",
            "dropoff_poi_code": self.beach_bar.code,
            "num_guests": 2,
        }

        response = self.client.post(self.create_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pickup_poi_code", response.data)
