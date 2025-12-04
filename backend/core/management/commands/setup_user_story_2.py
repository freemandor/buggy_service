from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import POI, Buggy, User, RideRequest, BuggyRouteStop


class Command(BaseCommand):
    help = "Set up User Story #2 test scenario: Buggy 1 busy, Buggy 2 idle"

    def handle(self, *args, **options):
        # Get POIs
        bel_air = POI.objects.get(code="BEL_AIR")
        beach_bar = POI.objects.get(code="BEACH_BAR")
        reception = POI.objects.get(code="RECEPTION")
        
        # Get or create driver2
        driver2, created = User.objects.get_or_create(
            username="driver2",
            defaults={"role": User.Role.DRIVER}
        )
        if created:
            driver2.set_password("driver2")
            driver2.save()
            self.stdout.write(self.style.SUCCESS(f"Created driver2"))
        
        # Get Buggy 1 (should already exist from seed)
        buggy1 = Buggy.objects.get(code="BUGGY_1")
        
        # Create or update Buggy 2 (idle at Reception)
        buggy2, created = Buggy.objects.update_or_create(
            code="BUGGY_2",
            defaults={
                "display_name": "Buggy #2",
                "capacity": 4,
                "status": Buggy.Status.ACTIVE,
                "current_poi": reception,
                "current_onboard_guests": 0,
                "driver": driver2,
            },
        )
        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} Buggy #2 at Reception (idle)"))
        
        # Clean up any existing incomplete rides for Buggy 1
        BuggyRouteStop.objects.filter(
            buggy=buggy1,
            status__in=[BuggyRouteStop.StopStatus.PLANNED, BuggyRouteStop.StopStatus.ON_ROUTE]
        ).delete()
        
        # Delete any pending/in-progress rides
        RideRequest.objects.filter(
            status__in=[
                RideRequest.Status.PENDING,
                RideRequest.Status.ASSIGNED,
                RideRequest.Status.PICKING_UP,
                RideRequest.Status.IN_PROGRESS,
            ]
        ).delete()
        
        # Create existing Ride A: Bel Air → Beach Bar (3 guests, assigned to Buggy 1)
        ride_a = RideRequest.objects.create(
            pickup_poi=bel_air,
            dropoff_poi=beach_bar,
            num_guests=3,
            room_number="301",
            guest_name="Mrs. Johnson",
            status=RideRequest.Status.IN_PROGRESS,  # Already picked up
            assigned_buggy=buggy1,
            assigned_at=timezone.now(),
            pickup_completed_at=timezone.now(),
        )
        
        # Update Buggy 1: Currently at Bel Air, 3 guests onboard
        buggy1.current_poi = bel_air
        buggy1.current_onboard_guests = 3
        buggy1.save()
        
        # Create route stop for Buggy 1: Dropoff at Beach Bar (PLANNED)
        BuggyRouteStop.objects.create(
            buggy=buggy1,
            ride_request=ride_a,
            stop_type=BuggyRouteStop.StopType.DROPOFF,
            poi=beach_bar,
            sequence_index=0,
            status=BuggyRouteStop.StopStatus.PLANNED,
        )
        
        self.stdout.write(self.style.SUCCESS(f"Created Ride A ({ride_a.public_code}): Bel Air -> Beach Bar"))
        self.stdout.write(self.style.SUCCESS(f"Buggy #1: At Bel Air, 3 guests onboard, heading to Beach Bar"))
        
        self.stdout.write(self.style.SUCCESS("\n=== User Story #2 Scenario Ready ==="))
        self.stdout.write(self.style.SUCCESS("Buggy #1: At Bel Air, has Ride A (dropoff at Beach Bar)"))
        self.stdout.write(self.style.SUCCESS("Buggy #2: At Reception, idle (0 guests)"))
        self.stdout.write(self.style.SUCCESS("\nNext: Create new ride Beach Bar -> Reception"))
        self.stdout.write(self.style.SUCCESS("Expected: System assigns to Buggy #1 (arrives in 145s vs Buggy #2's 210s)"))

