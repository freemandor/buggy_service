from django.test import TestCase
from core.models import POI, PoiEdge
from core.services.graph import get_travel_time_and_route


class PoiGraphTests(TestCase):
    def setUp(self):
        self.reception = POI.objects.create(code="RECEPTION", name="Reception")
        self.bel_air = POI.objects.create(code="BEL_AIR", name="Bel Air")
        self.beach_bar = POI.objects.create(code="BEACH_BAR", name="Beach Bar")

        PoiEdge.objects.create(from_poi=self.bel_air, to_poi=self.beach_bar, travel_time_s=120)
        PoiEdge.objects.create(from_poi=self.reception, to_poi=self.bel_air, travel_time_s=60)
        PoiEdge.objects.create(from_poi=self.reception, to_poi=self.beach_bar, travel_time_s=300)

    def test_shortest_path_prefers_bel_air(self):
        res = get_travel_time_and_route(self.reception, self.beach_bar)
        self.assertEqual(res.travel_time_s, 180)
        self.assertEqual(res.poi_ids, [self.reception.id, self.bel_air.id, self.beach_bar.id])

