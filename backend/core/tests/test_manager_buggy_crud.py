from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Buggy, User, POI, BuggyRouteStop, RideRequest


class ManagerBuggyCRUDTests(APITestCase):
    def setUp(self):
        # Create users
        self.manager = User.objects.create_user(username="manager", password="manager", role=User.Role.MANAGER)
        self.dispatcher = User.objects.create_user(username="dispatcher", password="dispatcher", role=User.Role.DISPATCHER)
        self.driver1 = User.objects.create_user(username="driver1", password="driver1", role=User.Role.DRIVER)
        
        # Create POI
        self.reception = POI.objects.create(code="RECEPTION", name="Reception")
        
        # Create test buggy
        self.buggy1 = Buggy.objects.create(
            code="BUGGY_1",
            display_name="Buggy #1",
            capacity=4,
            status=Buggy.Status.ACTIVE,
            current_poi=self.reception,
            driver=self.driver1
        )
        
        self.create_url = reverse("manager-buggy-list")
        
    def _authenticate_as(self, user):
        self.client.force_authenticate(user=user)
    
    def test_create_buggy_unauthenticated(self):
        """Unauthenticated users cannot create buggies."""
        response = self.client.post(self.create_url, {
            "code": "BUGGY_2",
            "display_name": "Buggy #2",
            "capacity": 4,
            "status": "ACTIVE"
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_buggy_non_manager(self):
        """Non-manager users cannot create buggies."""
        self._authenticate_as(self.dispatcher)
        response = self.client.post(self.create_url, {
            "code": "BUGGY_2",
            "display_name": "Buggy #2",
            "capacity": 4,
            "status": "ACTIVE"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_buggy_success(self):
        """Manager can create a buggy."""
        self._authenticate_as(self.manager)
        response = self.client.post(self.create_url, {
            "code": "BUGGY_2",
            "display_name": "Buggy #2",
            "capacity": 6,
            "status": "ACTIVE",
            "current_poi_id": self.reception.id,
            "current_onboard_guests": 0
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["code"], "BUGGY_2")
        self.assertEqual(response.data["display_name"], "Buggy #2")
        self.assertEqual(response.data["capacity"], 6)
        
        # Verify in database
        self.assertTrue(Buggy.objects.filter(code="BUGGY_2").exists())
    
    def test_create_buggy_with_driver(self):
        """Manager can create a buggy with a driver assigned."""
        self._authenticate_as(self.manager)
        driver2 = User.objects.create_user(username="driver2", password="driver2", role=User.Role.DRIVER)
        response = self.client.post(self.create_url, {
            "code": "BUGGY_3",
            "display_name": "Buggy #3",
            "capacity": 4,
            "status": "ACTIVE",
            "driver_id": driver2.id,
            "current_onboard_guests": 0
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        buggy = Buggy.objects.get(code="BUGGY_3")
        self.assertEqual(buggy.driver, driver2)
    
    def test_create_buggy_invalid_driver(self):
        """Creating buggy with non-existent driver fails."""
        self._authenticate_as(self.manager)
        response = self.client.post(self.create_url, {
            "code": "BUGGY_3",
            "display_name": "Buggy #3",
            "capacity": 4,
            "status": "ACTIVE",
            "driver_id": 99999,
            "current_onboard_guests": 0
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_buggy_success(self):
        """Manager can update a buggy."""
        self._authenticate_as(self.manager)
        url = reverse("manager-buggy-detail", kwargs={"buggy_id": self.buggy1.id})
        response = self.client.put(url, {
            "display_name": "Updated Buggy #1",
            "capacity": 6
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.buggy1.refresh_from_db()
        self.assertEqual(self.buggy1.display_name, "Updated Buggy #1")
        self.assertEqual(self.buggy1.capacity, 6)
    
    def test_update_buggy_status(self):
        """Manager can update buggy status."""
        self._authenticate_as(self.manager)
        url = reverse("manager-buggy-detail", kwargs={"buggy_id": self.buggy1.id})
        response = self.client.put(url, {
            "status": "INACTIVE"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.buggy1.refresh_from_db()
        self.assertEqual(self.buggy1.status, Buggy.Status.INACTIVE)
    
    def test_delete_buggy_success(self):
        """Manager can delete a buggy."""
        self._authenticate_as(self.manager)
        url = reverse("manager-buggy-detail", kwargs={"buggy_id": self.buggy1.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deletion
        self.assertFalse(Buggy.objects.filter(id=self.buggy1.id).exists())
    
    def test_delete_buggy_with_active_stops(self):
        """Cannot delete buggy with active route stops."""
        self._authenticate_as(self.manager)
        
        # Create active ride and route stop
        ride = RideRequest.objects.create(
            pickup_poi=self.reception,
            dropoff_poi=self.reception,
            num_guests=2,
            room_number="101",
            guest_name="Test Guest",
            status=RideRequest.Status.IN_PROGRESS,
            assigned_buggy=self.buggy1
        )
        BuggyRouteStop.objects.create(
            buggy=self.buggy1,
            ride_request=ride,
            stop_type=BuggyRouteStop.StopType.DROPOFF,
            poi=self.reception,
            sequence_index=0,
            status=BuggyRouteStop.StopStatus.PLANNED
        )
        
        url = reverse("manager-buggy-detail", kwargs={"buggy_id": self.buggy1.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("active route stops", response.data["error"])
        
        # Verify not deleted
        self.assertTrue(Buggy.objects.filter(id=self.buggy1.id).exists())

