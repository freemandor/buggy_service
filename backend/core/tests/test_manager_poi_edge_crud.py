from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import POI, PoiEdge, User


class ManagerPOIEdgeCRUDTests(APITestCase):
    def setUp(self):
        # Create users
        self.manager = User.objects.create_user(username="manager", password="manager", role=User.Role.MANAGER)
        self.dispatcher = User.objects.create_user(username="dispatcher", password="dispatcher", role=User.Role.DISPATCHER)
        
        # Create test POIs
        self.reception = POI.objects.create(code="RECEPTION", name="Reception")
        self.beach_bar = POI.objects.create(code="BEACH_BAR", name="Beach Bar")
        self.spa = POI.objects.create(code="SPA", name="Club Med Spa")
        
        # Create test edge
        self.edge1 = PoiEdge.objects.create(
            from_poi=self.reception,
            to_poi=self.beach_bar,
            travel_time_s=240
        )
        
        self.list_url = reverse("manager-poi-edge-list")
        
    def _authenticate_as(self, user):
        self.client.force_authenticate(user=user)
    
    def test_list_edges_unauthenticated(self):
        """Unauthenticated users cannot list edges."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_edges_non_manager(self):
        """Non-manager users cannot list edges."""
        self._authenticate_as(self.dispatcher)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_edges_success(self):
        """Manager can list all edges."""
        self._authenticate_as(self.manager)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        edge_data = response.data[0]
        self.assertEqual(edge_data["travel_time_s"], 240)
        self.assertIn("from_poi", edge_data)
        self.assertIn("to_poi", edge_data)
    
    def test_create_edge_unauthenticated(self):
        """Unauthenticated users cannot create edges."""
        response = self.client.post(self.list_url, {
            "from_poi_id": self.reception.id,
            "to_poi_id": self.spa.id,
            "travel_time_s": 90
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_edge_non_manager(self):
        """Non-manager users cannot create edges."""
        self._authenticate_as(self.dispatcher)
        response = self.client.post(self.list_url, {
            "from_poi_id": self.reception.id,
            "to_poi_id": self.spa.id,
            "travel_time_s": 90
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_edge_success(self):
        """Manager can create an edge."""
        self._authenticate_as(self.manager)
        response = self.client.post(self.list_url, {
            "from_poi_id": self.reception.id,
            "to_poi_id": self.spa.id,
            "travel_time_s": 90
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["travel_time_s"], 90)
        
        # Verify in database
        self.assertTrue(PoiEdge.objects.filter(
            from_poi=self.reception,
            to_poi=self.spa,
            travel_time_s=90
        ).exists() or PoiEdge.objects.filter(
            from_poi=self.spa,
            to_poi=self.reception,
            travel_time_s=90
        ).exists())
    
    def test_create_edge_canonical_ordering(self):
        """Edge is stored with canonical ordering (smaller ID first)."""
        self._authenticate_as(self.manager)
        # Create edge with larger ID first
        response = self.client.post(self.list_url, {
            "from_poi_id": self.spa.id,
            "to_poi_id": self.reception.id,
            "travel_time_s": 90
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Edge should be stored with smaller ID first
        edge = PoiEdge.objects.get(
            from_poi__in=[self.reception, self.spa],
            to_poi__in=[self.reception, self.spa],
            travel_time_s=90
        )
        self.assertTrue(edge.from_poi.id < edge.to_poi.id)
    
    def test_create_edge_self_loop(self):
        """Cannot create edge from POI to itself."""
        self._authenticate_as(self.manager)
        response = self.client.post(self.list_url, {
            "from_poi_id": self.reception.id,
            "to_poi_id": self.reception.id,
            "travel_time_s": 0
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_edge_duplicate(self):
        """Cannot create duplicate edge."""
        self._authenticate_as(self.manager)
        response = self.client.post(self.list_url, {
            "from_poi_id": self.reception.id,
            "to_poi_id": self.beach_bar.id,
            "travel_time_s": 120
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_edge_invalid_poi(self):
        """Cannot create edge with non-existent POI."""
        self._authenticate_as(self.manager)
        response = self.client.post(self.list_url, {
            "from_poi_id": 99999,
            "to_poi_id": self.beach_bar.id,
            "travel_time_s": 120
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_edge_success(self):
        """Manager can update edge travel time."""
        self._authenticate_as(self.manager)
        url = reverse("manager-poi-edge-detail", kwargs={"edge_id": self.edge1.id})
        response = self.client.put(url, {
            "travel_time_s": 300
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.edge1.refresh_from_db()
        self.assertEqual(self.edge1.travel_time_s, 300)
    
    def test_update_edge_pois(self):
        """Manager can update edge POIs."""
        self._authenticate_as(self.manager)
        url = reverse("manager-poi-edge-detail", kwargs={"edge_id": self.edge1.id})
        response = self.client.put(url, {
            "from_poi_id": self.beach_bar.id,
            "to_poi_id": self.spa.id,
            "travel_time_s": 150
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.edge1.refresh_from_db()
        self.assertEqual(self.edge1.travel_time_s, 150)
        # Check edge connects beach_bar and spa (in either direction due to canonical ordering)
        self.assertTrue(
            (self.edge1.from_poi == self.beach_bar and self.edge1.to_poi == self.spa) or
            (self.edge1.from_poi == self.spa and self.edge1.to_poi == self.beach_bar)
        )
    
    def test_delete_edge_success(self):
        """Manager can delete an edge."""
        self._authenticate_as(self.manager)
        url = reverse("manager-poi-edge-detail", kwargs={"edge_id": self.edge1.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deletion
        self.assertFalse(PoiEdge.objects.filter(id=self.edge1.id).exists())
    
    def test_delete_edge_non_manager(self):
        """Non-manager cannot delete edge."""
        self._authenticate_as(self.dispatcher)
        url = reverse("manager-poi-edge-detail", kwargs={"edge_id": self.edge1.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

