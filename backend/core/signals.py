from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from core.models import POI, PoiEdge
from core.services import graph


@receiver(post_save, sender=POI)
@receiver(post_delete, sender=POI)
@receiver(post_save, sender=PoiEdge)
@receiver(post_delete, sender=PoiEdge)
def invalidate_poi_graph_cache(**kwargs):
    graph._graph_cache = None

