from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Buggy, User, POI, RideRequest


class ManagerPOICRUDTests(APITestCase):
    def setUp(self):
        # Create users
        self.manager = User.objects.create_user(username="manager", password="manager", role=User.Role.MANAGER)
        self.dispatcher = User.objects.create_user(username="dispatcher", password="dispatcher", role=User.Role.DISPATCHER)
        
        # Create test POIs
        self.reception = POI.objects.create(code="RECEPTION", name="Reception")
        self.beach_bar = POI.objects.create(code="BEACH_BAR", name="Beach Bar")
        
        self.create_url = reverse("manager-poi-list")
        
    def _authenticate_as(self, user):
        self.client.force_authenticate(user=user)
    
    def test_create_poi_unauthenticated(self):
        """Unauthenticated users cannot create POIs."""
        response = self.client.post(self.create_url, {
            "code": "SPA",
            "name": "Club Med Spa"
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_poi_non_manager(self):
        """Non-manager users cannot create POIs."""
        self._authenticate_as(self.dispatcher)
        response = self.client.post(self.create_url, {
            "code": "SPA",
            "name": "Club Med Spa"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_poi_success(self):
        """Manager can create a POI."""
        self._authenticate_as(self.manager)
        response = self.client.post(self.create_url, {
            "code": "spa",
            "name": "Club Med Spa"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["code"], "SPA")  # Should be uppercased
        self.assertEqual(response.data["name"], "Club Med Spa")
        
        # Verify in database
        self.assertTrue(POI.objects.filter(code="SPA").exists())
    
    def test_create_poi_duplicate_code(self):
        """Creating POI with duplicate code fails."""
        self._authenticate_as(self.manager)
        response = self.client.post(self.create_url, {
            "code": "RECEPTION",
            "name": "Another Reception"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_poi_success(self):
        """Manager can update a POI."""
        self._authenticate_as(self.manager)
        url = reverse("manager-poi-detail", kwargs={"poi_id": self.reception.id})
        response = self.client.put(url, {
            "name": "Main Reception"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.reception.refresh_from_db()
        self.assertEqual(self.reception.name, "Main Reception")
    
    def test_update_poi_code(self):
        """Manager can update POI code."""
        self._authenticate_as(self.manager)
        url = reverse("manager-poi-detail", kwargs={"poi_id": self.reception.id})
        response = self.client.put(url, {
            "code": "main_reception"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.reception.refresh_from_db()
        self.assertEqual(self.reception.code, "MAIN_RECEPTION")  # Uppercased
    
    def test_delete_poi_success(self):
        """Manager can delete a POI."""
        self._authenticate_as(self.manager)
        url = reverse("manager-poi-detail", kwargs={"poi_id": self.beach_bar.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deletion
        self.assertFalse(POI.objects.filter(id=self.beach_bar.id).exists())
    
    def test_delete_poi_with_buggy_at_location(self):
        """Cannot delete POI if buggies are currently at that location."""
        self._authenticate_as(self.manager)
        
        # Create buggy at reception
        driver = User.objects.create_user(username="driver1", password="driver1", role=User.Role.DRIVER)
        Buggy.objects.create(
            code="BUGGY_1",
            display_name="Buggy #1",
            capacity=4,
            status=Buggy.Status.ACTIVE,
            current_poi=self.reception,
            driver=driver
        )
        
        url = reverse("manager-poi-detail", kwargs={"poi_id": self.reception.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("buggies are currently at this location", response.data["error"])
        
        # Verify not deleted
        self.assertTrue(POI.objects.filter(id=self.reception.id).exists())
    
    def test_delete_poi_with_active_ride(self):
        """Cannot delete POI if active rides are using it."""
        self._authenticate_as(self.manager)
        
        # Create active ride using beach_bar
        RideRequest.objects.create(
            pickup_poi=self.beach_bar,
            dropoff_poi=self.reception,
            num_guests=2,
            room_number="101",
            guest_name="Test Guest",
            status=RideRequest.Status.PENDING
        )
        
        url = reverse("manager-poi-detail", kwargs={"poi_id": self.beach_bar.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rides are using this location", response.data["error"])
        
        # Verify not deleted
        self.assertTrue(POI.objects.filter(id=self.beach_bar.id).exists())
    
    def test_delete_poi_with_completed_ride(self):
        """Cannot delete POI even if only completed rides used it (data integrity)."""
        self._authenticate_as(self.manager)
        
        # Create completed ride using beach_bar
        RideRequest.objects.create(
            pickup_poi=self.beach_bar,
            dropoff_poi=self.reception,
            num_guests=2,
            room_number="101",
            guest_name="Test Guest",
            status=RideRequest.Status.COMPLETED
        )
        
        url = reverse("manager-poi-detail", kwargs={"poi_id": self.beach_bar.id})
        response = self.client.delete(url)
        # POI deletion is blocked to preserve historical data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rides are using this location", response.data["error"])
        
        # Verify not deleted
        self.assertTrue(POI.objects.filter(id=self.beach_bar.id).exists())

