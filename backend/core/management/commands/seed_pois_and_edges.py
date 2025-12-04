from django.core.management.base import BaseCommand
from core.models import POI, PoiEdge, Buggy, User


class Command(BaseCommand):
    help = "Seed POIs, POI edges, demo buggies and drivers for Club Med Seychelles"

    def handle(self, *args, **options):
        # Create all POIs
        self.stdout.write("Creating POIs...")
        
        # Existing POIs
        reception, _ = POI.objects.get_or_create(code="RECEPTION", defaults={"name": "Reception"})
        beach_bar, _ = POI.objects.get_or_create(code="BEACH_BAR", defaults={"name": "Beach Bar"})
        bel_air, _ = POI.objects.get_or_create(code="BEL_AIR", defaults={"name": "Bel Air"})
        
        # Main Guest Destinations
        villa_seychelles, _ = POI.objects.get_or_create(code="VILLA_DES_SEYCHELLES", defaults={"name": "Villa des Seychelles"})
        the_reef, _ = POI.objects.get_or_create(code="THE_REEF", defaults={"name": "The Reef"})
        beach_lounge, _ = POI.objects.get_or_create(code="BEACH_LOUNGE", defaults={"name": "Beach Lounge"})
        au_cap, _ = POI.objects.get_or_create(code="AU_CAP", defaults={"name": "Au Cap"})
        robinson, _ = POI.objects.get_or_create(code="ROBINSON", defaults={"name": "Robinson"})
        monkey_tales, _ = POI.objects.get_or_create(code="MONKEY_TALES", defaults={"name": "Monkey Tales"})
        turtle_cove, _ = POI.objects.get_or_create(code="TURTLE_COVE", defaults={"name": "Turtle Cove"})
        mont_fleuri, _ = POI.objects.get_or_create(code="MONT_FLEURI", defaults={"name": "Mont Fleuri"})
        
        # Central Facilities
        main_restaurant, _ = POI.objects.get_or_create(code="MAIN_RESTAURANT", defaults={"name": "Main Restaurant"})
        main_bar, _ = POI.objects.get_or_create(code="MAIN_BAR", defaults={"name": "Main Bar"})
        main_pool, _ = POI.objects.get_or_create(code="MAIN_POOL", defaults={"name": "Main Pool"})
        kids_club, _ = POI.objects.get_or_create(code="KIDS_CLUB", defaults={"name": "Kids Club"})
        
        # Sports & Wellness
        spa, _ = POI.objects.get_or_create(code="SPA", defaults={"name": "Club Med Spa"})
        tennis_courts, _ = POI.objects.get_or_create(code="TENNIS_COURTS", defaults={"name": "Tennis Courts"})
        beach_sports, _ = POI.objects.get_or_create(code="BEACH_SPORTS", defaults={"name": "Beach Sports"})
        watersports, _ = POI.objects.get_or_create(code="WATERSPORTS", defaults={"name": "Watersports"})
        fitness_center, _ = POI.objects.get_or_create(code="FITNESS_CENTER", defaults={"name": "Fitness Center"})
        
        # Services
        boutique, _ = POI.objects.get_or_create(code="BOUTIQUE", defaults={"name": "La Boutique"})
        theatre, _ = POI.objects.get_or_create(code="THEATRE", defaults={"name": "Theatre"})
        
        self.stdout.write(self.style.SUCCESS(f"  Created {POI.objects.count()} POIs"))

        # Create edges helper function
        def edge(a, b, seconds):
            PoiEdge.objects.update_or_create(
                from_poi=min(a, b, key=lambda p: p.id),
                to_poi=max(a, b, key=lambda p: p.id),
                defaults={"travel_time_s": seconds},
            )

        self.stdout.write("Creating POI edges...")
        
        # From Reception
        edge(reception, bel_air, 90)
        edge(reception, beach_bar, 120)
        edge(reception, main_restaurant, 60)
        edge(reception, main_pool, 45)
        edge(reception, kids_club, 75)
        edge(reception, spa, 90)
        edge(reception, robinson, 180)
        edge(reception, boutique, 75)
        edge(reception, fitness_center, 105)
        
        # From Beach Bar
        edge(beach_bar, bel_air, 120)
        edge(beach_bar, beach_lounge, 90)
        edge(beach_bar, beach_sports, 105)
        edge(beach_bar, watersports, 120)
        
        # From Bel Air
        edge(bel_air, au_cap, 105)
        edge(bel_air, villa_seychelles, 135)
        edge(bel_air, the_reef, 120)
        
        # From Villa des Seychelles
        edge(villa_seychelles, the_reef, 45)
        edge(villa_seychelles, beach_lounge, 75)
        
        # From The Reef
        edge(the_reef, beach_lounge, 60)
        
        # From Beach Lounge
        edge(beach_lounge, main_restaurant, 150)
        
        # From Au Cap
        edge(au_cap, monkey_tales, 90)
        
        # From Monkey Tales
        edge(monkey_tales, turtle_cove, 75)
        edge(monkey_tales, main_bar, 120)
        
        # From Turtle Cove
        edge(turtle_cove, mont_fleuri, 60)
        
        # From Mont Fleuri
        edge(mont_fleuri, main_restaurant, 165)
        
        # From Robinson
        edge(robinson, tennis_courts, 90)
        edge(robinson, beach_sports, 75)
        
        # From Main Restaurant
        edge(main_restaurant, main_pool, 30)
        edge(main_restaurant, main_bar, 45)
        edge(main_restaurant, kids_club, 60)
        
        # From Main Pool
        edge(main_pool, kids_club, 45)
        
        # From Main Bar
        edge(main_bar, theatre, 60)
        
        # From Spa
        edge(spa, fitness_center, 45)
        edge(spa, tennis_courts, 75)
        
        # From Tennis Courts
        edge(tennis_courts, beach_sports, 60)
        
        # From Beach Sports
        edge(beach_sports, watersports, 45)
        
        # From Boutique
        edge(boutique, main_restaurant, 90)
        
        self.stdout.write(self.style.SUCCESS(f"  Created {PoiEdge.objects.count()} edges"))

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

