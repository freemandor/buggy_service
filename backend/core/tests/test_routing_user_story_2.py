from django.test import TestCase
from core.models import POI, PoiEdge, Buggy, RideRequest, BuggyRouteStop, User
from core.services.routing import assign_ride_to_best_buggy


class RoutingUserStory2Tests(TestCase):
    """
    User Story #2: Buggy 1 is busy on route BA→BB with existing ride A.
    Buggy 2 is idle at Reception.
    New ride request: Beach Bar → Reception (Ride C).
    Expected: System assigns Ride C to Buggy 1 (not Buggy 2) because Buggy 1
    will reach Beach Bar sooner than Buggy 2.
    """

    def setUp(self):
        # Create POIs
        self.bel_air = POI.objects.create(code="BEL_AIR", name="Bel Air")
        self.beach_bar = POI.objects.create(code="BEACH_BAR", name="Beach Bar")
        self.reception = POI.objects.create(code="RECEPTION", name="Reception")

        # Create edges (simplified: BA↔BB: 120s, BB↔R: 240s, BA↔R: 90s)
        PoiEdge.objects.create(from_poi=self.bel_air, to_poi=self.beach_bar, travel_time_s=120)
        PoiEdge.objects.create(from_poi=self.beach_bar, to_poi=self.reception, travel_time_s=240)
        PoiEdge.objects.create(from_poi=self.bel_air, to_poi=self.reception, travel_time_s=90)

        # Create drivers
        self.driver1 = User.objects.create_user(username="driver1", password="driver1", role=User.Role.DRIVER)
        self.driver2 = User.objects.create_user(username="driver2", password="driver2", role=User.Role.DRIVER)

        # Create Buggy 1: at Bel Air, ACTIVE, with 3 guests onboard (from existing Ride A)
        self.buggy1 = Buggy.objects.create(
            code="BUGGY_1",
            display_name="Buggy #1",
            capacity=4,
            status=Buggy.Status.ACTIVE,
            current_poi=self.bel_air,
            current_onboard_guests=3,
            driver=self.driver1,
        )

        # Create Buggy 2: at Reception, ACTIVE, idle (0 onboard)
        self.buggy2 = Buggy.objects.create(
            code="BUGGY_2",
            display_name="Buggy #2",
            capacity=4,
            status=Buggy.Status.ACTIVE,
            current_poi=self.reception,
            current_onboard_guests=0,
            driver=self.driver2,
        )

        # Create existing Ride A for Buggy 1: already picked up, heading to Beach Bar for dropoff
        self.ride_a = RideRequest.objects.create(
            pickup_poi=self.bel_air,
            dropoff_poi=self.beach_bar,
            num_guests=3,
            status=RideRequest.Status.IN_PROGRESS,
            assigned_buggy=self.buggy1,
        )

        # Buggy 1 has one pending stop: Dropoff Ride A at Beach Bar
        BuggyRouteStop.objects.create(
            buggy=self.buggy1,
            ride_request=self.ride_a,
            stop_type=BuggyRouteStop.StopType.DROPOFF,
            poi=self.beach_bar,
            sequence_index=0,
            status=BuggyRouteStop.StopStatus.PLANNED,
        )

    def test_new_ride_assigned_to_buggy1_not_buggy2(self):
        """
        Create new Ride C: Beach Bar → Reception, 2 guests.
        Expected: assigned to Buggy 1 because it arrives at Beach Bar sooner.
        
        Buggy 1 simulation:
          - Travel BA → BB: 120s
          - Dropoff service: 25s
          - Already at BB: 0s (total 145s to pickup)
          
        Buggy 2 simulation:
          - Travel Reception → BB: 240s (via direct edge or via BA)
          - Using shortest path R→BA→BB: 90+120=210s
          
        So Buggy 1 arrives in 145s, Buggy 2 in 210s → Buggy 1 wins.
        """
        # Create new Ride C
        ride_c = RideRequest.objects.create(
            pickup_poi=self.beach_bar,
            dropoff_poi=self.reception,
            num_guests=2,
            status=RideRequest.Status.PENDING,
        )

        # Assign the ride
        assigned_buggy = assign_ride_to_best_buggy(ride_c)

        # Verify it was assigned to Buggy 1
        self.assertEqual(assigned_buggy.id, self.buggy1.id)
        
        # Verify ride status updated
        ride_c.refresh_from_db()
        self.assertEqual(ride_c.status, RideRequest.Status.ASSIGNED)
        self.assertEqual(ride_c.assigned_buggy.id, self.buggy1.id)

        # Verify Buggy 1 now has 3 route stops (1 existing + 2 new)
        stops = BuggyRouteStop.objects.filter(buggy=self.buggy1).order_by("sequence_index")
        self.assertEqual(stops.count(), 3)
        
        # Check stop sequence:
        # Stop 0: Dropoff Ride A at Beach Bar
        # Stop 1: Pickup Ride C at Beach Bar
        # Stop 2: Dropoff Ride C at Reception
        self.assertEqual(stops[0].stop_type, BuggyRouteStop.StopType.DROPOFF)
        self.assertEqual(stops[0].poi.code, "BEACH_BAR")
        self.assertEqual(stops[0].ride_request.id, self.ride_a.id)
        
        self.assertEqual(stops[1].stop_type, BuggyRouteStop.StopType.PICKUP)
        self.assertEqual(stops[1].poi.code, "BEACH_BAR")
        self.assertEqual(stops[1].ride_request.id, ride_c.id)
        
        self.assertEqual(stops[2].stop_type, BuggyRouteStop.StopType.DROPOFF)
        self.assertEqual(stops[2].poi.code, "RECEPTION")
        self.assertEqual(stops[2].ride_request.id, ride_c.id)

        # Verify Buggy 2 has no stops
        self.assertEqual(BuggyRouteStop.objects.filter(buggy=self.buggy2).count(), 0)

