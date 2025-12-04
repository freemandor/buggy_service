from django.core.management.base import BaseCommand
from core.models import User, POI, PoiEdge, Buggy, RideRequest, BuggyRouteStop


class Command(BaseCommand):
    help = "Reset database to clean state for E2E tests"

    def handle(self, *args, **options):
        # Clear route stops and rides first (due to foreign key constraints)
        BuggyRouteStop.objects.all().delete()
        RideRequest.objects.all().delete()
        
        # Delete ALL buggies (including test ones)
        Buggy.objects.all().delete()
        
        # Delete test users (keep only the default ones: driver1, driver2, dispatcher, manager)
        default_usernames = ['driver1', 'driver2', 'dispatcher', 'manager']
        test_users_deleted = User.objects.exclude(username__in=default_usernames).delete()[0]
        
        # Delete test POIs (those starting with TEST_)
        test_pois_deleted = POI.objects.filter(code__startswith='TEST_').delete()[0]
        
        # Keep core POIs and edges (they're essential for the system)
        
        self.stdout.write(self.style.SUCCESS("Database reset complete"))
        self.stdout.write(self.style.SUCCESS(f"Remaining POIs: {POI.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"Remaining Users: {User.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"Test users deleted: {test_users_deleted}"))
        self.stdout.write(self.style.SUCCESS(f"Test POIs deleted: {test_pois_deleted}"))
        self.stdout.write(self.style.SUCCESS("All rides, buggies, and route stops cleared"))

