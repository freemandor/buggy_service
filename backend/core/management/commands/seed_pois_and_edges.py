from django.core.management.base import BaseCommand
from core.models import POI, PoiEdge, Buggy, User


class Command(BaseCommand):
    help = "Seed POIs, POI edges, demo buggies and drivers for Club Med Seychelles"

    def handle(self, *args, **options):
        reception, _ = POI.objects.get_or_create(code="RECEPTION", defaults={"name": "Reception"})
        beach_bar, _ = POI.objects.get_or_create(code="BEACH_BAR", defaults={"name": "Beach Bar"})
        bel_air, _ = POI.objects.get_or_create(code="BEL_AIR", defaults={"name": "Bel Air"})

        def edge(a, b, seconds):
            PoiEdge.objects.update_or_create(
                from_poi=min(a, b, key=lambda p: p.id),
                to_poi=max(a, b, key=lambda p: p.id),
                defaults={"travel_time_s": seconds},
            )

        edge(bel_air, beach_bar, 120)
        edge(reception, beach_bar, 240)
        edge(reception, bel_air, 90)

        driver1, _ = User.objects.get_or_create(username="driver1", defaults={"role": User.Role.DRIVER})
        driver1.set_password("driver1")
        driver1.save()

        dispatcher, _ = User.objects.get_or_create(username="dispatcher", defaults={"role": User.Role.DISPATCHER})
        dispatcher.set_password("dispatcher")
        dispatcher.save()

        manager, _ = User.objects.get_or_create(username="manager", defaults={"role": User.Role.MANAGER})
        manager.set_password("manager")
        manager.save()

        buggy1, _ = Buggy.objects.get_or_create(
            code="BUGGY_1",
            defaults={
                "display_name": "Buggy #1",
                "capacity": 4,
                "status": Buggy.Status.ACTIVE,
                "current_poi": bel_air,
                "current_onboard_guests": 0,
                "driver": driver1,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seeded POIs, edges, users, and buggy."))

