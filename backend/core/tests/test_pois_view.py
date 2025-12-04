from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import POI

User = get_user_model()


class POIsListViewTest(TestCase):
    """Tests for the POIs list API endpoint."""

    def setUp(self):
        """Set up test client and create test data."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            role=User.Role.DISPATCHER
        )
        
        # Create test POIs
        self.reception = POI.objects.create(code="RECEPTION", name="Reception")
        self.beach_bar = POI.objects.create(code="BEACH_BAR", name="Beach Bar")
        self.bel_air = POI.objects.create(code="BEL_AIR", name="Bel Air")
        self.spa = POI.objects.create(code="SPA", name="Club Med Spa")

    def test_list_pois_requires_authentication(self):
        """Test that POIs endpoint requires authentication."""
        response = self.client.get('/api/pois/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_pois_success(self):
        """Test successfully listing all POIs."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/pois/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        
        # Verify POI structure
        poi = response.data[0]
        self.assertIn('id', poi)
        self.assertIn('code', poi)
        self.assertIn('name', poi)

    def test_list_pois_ordered_by_name(self):
        """Test that POIs are returned in alphabetical order by name."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/pois/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check alphabetical order
        names = [poi['name'] for poi in response.data]
        self.assertEqual(names, sorted(names))
        
        # Verify specific order
        self.assertEqual(names[0], "Beach Bar")  # First alphabetically
        self.assertEqual(names[1], "Bel Air")
        self.assertEqual(names[2], "Club Med Spa")
        self.assertEqual(names[3], "Reception")

    def test_list_pois_contains_correct_data(self):
        """Test that POI data contains correct fields and values."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/pois/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find the reception POI
        reception_data = next(poi for poi in response.data if poi['code'] == 'RECEPTION')
        
        self.assertEqual(reception_data['code'], 'RECEPTION')
        self.assertEqual(reception_data['name'], 'Reception')
        self.assertEqual(reception_data['id'], self.reception.id)

    def test_list_pois_empty_database(self):
        """Test listing POIs when none exist."""
        # Delete all POIs
        POI.objects.all().delete()
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/pois/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        self.assertEqual(response.data, [])

    def test_list_pois_works_for_all_roles(self):
        """Test that POIs endpoint works for all user roles."""
        roles = [User.Role.DISPATCHER, User.Role.DRIVER, User.Role.MANAGER]
        
        for role in roles:
            user = User.objects.create_user(
                username=f"user_{role}",
                password="testpass123",
                role=role
            )
            
            self.client.force_authenticate(user=user)
            response = self.client.get('/api/pois/')
            
            self.assertEqual(
                response.status_code, 
                status.HTTP_200_OK,
                f"POIs endpoint should work for {role} role"
            )
            self.assertEqual(len(response.data), 4)

