from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Buggy, User, POI


class ManagerDriverCRUDTests(APITestCase):
    def setUp(self):
        # Create users
        self.manager = User.objects.create_user(username="manager", password="manager", role=User.Role.MANAGER)
        self.dispatcher = User.objects.create_user(username="dispatcher", password="dispatcher", role=User.Role.DISPATCHER)
        self.driver1 = User.objects.create_user(
            username="driver1",
            password="driver1",
            role=User.Role.DRIVER,
            first_name="John",
            last_name="Doe"
        )
        
        self.list_url = reverse("manager-driver-list")
        
    def _authenticate_as(self, user):
        self.client.force_authenticate(user=user)
    
    def test_list_drivers_unauthenticated(self):
        """Unauthenticated users cannot list drivers."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_drivers_non_manager(self):
        """Non-manager users cannot list drivers."""
        self._authenticate_as(self.dispatcher)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_drivers_success(self):
        """Manager can list all drivers."""
        self._authenticate_as(self.manager)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], "driver1")
        self.assertEqual(response.data[0]["first_name"], "John")
        self.assertEqual(response.data[0]["last_name"], "Doe")
    
    def test_create_driver_unauthenticated(self):
        """Unauthenticated users cannot create drivers."""
        response = self.client.post(self.list_url, {
            "username": "driver2",
            "password": "password123",
            "first_name": "Jane",
            "last_name": "Smith"
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_driver_non_manager(self):
        """Non-manager users cannot create drivers."""
        self._authenticate_as(self.dispatcher)
        response = self.client.post(self.list_url, {
            "username": "driver2",
            "password": "password123",
            "first_name": "Jane",
            "last_name": "Smith"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_driver_success(self):
        """Manager can create a driver."""
        self._authenticate_as(self.manager)
        response = self.client.post(self.list_url, {
            "username": "driver2",
            "password": "password123",
            "first_name": "Jane",
            "last_name": "Smith"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "driver2")
        self.assertEqual(response.data["first_name"], "Jane")
        self.assertEqual(response.data["last_name"], "Smith")
        self.assertNotIn("password", response.data)
        
        # Verify in database
        driver = User.objects.get(username="driver2")
        self.assertEqual(driver.role, User.Role.DRIVER)
        self.assertTrue(driver.check_password("password123"))
    
    def test_create_driver_missing_password(self):
        """Creating driver without password fails."""
        self._authenticate_as(self.manager)
        response = self.client.post(self.list_url, {
            "username": "driver2",
            "first_name": "Jane",
            "last_name": "Smith"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_driver_success(self):
        """Manager can update a driver."""
        self._authenticate_as(self.manager)
        url = reverse("manager-driver-detail", kwargs={"driver_id": self.driver1.id})
        response = self.client.put(url, {
            "first_name": "Jonathan",
            "last_name": "Doe-Smith"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.driver1.refresh_from_db()
        self.assertEqual(self.driver1.first_name, "Jonathan")
        self.assertEqual(self.driver1.last_name, "Doe-Smith")
    
    def test_update_driver_password(self):
        """Manager can update driver password."""
        self._authenticate_as(self.manager)
        url = reverse("manager-driver-detail", kwargs={"driver_id": self.driver1.id})
        response = self.client.put(url, {
            "password": "newpassword123"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.driver1.refresh_from_db()
        self.assertTrue(self.driver1.check_password("newpassword123"))
    
    def test_delete_driver_success(self):
        """Manager can delete a driver."""
        self._authenticate_as(self.manager)
        url = reverse("manager-driver-detail", kwargs={"driver_id": self.driver1.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deletion
        self.assertFalse(User.objects.filter(id=self.driver1.id).exists())
    
    def test_delete_driver_with_assigned_buggy(self):
        """Cannot delete driver with assigned buggies."""
        self._authenticate_as(self.manager)
        
        # Create buggy assigned to driver
        poi = POI.objects.create(code="RECEPTION", name="Reception")
        Buggy.objects.create(
            code="BUGGY_1",
            display_name="Buggy #1",
            capacity=4,
            status=Buggy.Status.ACTIVE,
            current_poi=poi,
            driver=self.driver1
        )
        
        url = reverse("manager-driver-detail", kwargs={"driver_id": self.driver1.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assigned buggies", response.data["error"])
        
        # Verify not deleted
        self.assertTrue(User.objects.filter(id=self.driver1.id).exists())
    
    def test_delete_non_driver_user(self):
        """Attempting to delete non-driver user returns 404."""
        self._authenticate_as(self.manager)
        url = reverse("manager-driver-detail", kwargs={"driver_id": self.manager.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

