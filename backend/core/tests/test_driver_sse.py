from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import User, POI, PoiEdge, Buggy, RideRequest
from core.services.events import send_event_to_driver, broadcaster
import json


class DriverSSETests(APITestCase):
    def setUp(self):
        # Create users
        self.driver1 = User.objects.create_user(
            username="driver1",
            password="driver1",
            role=User.Role.DRIVER
        )
        self.driver2 = User.objects.create_user(
            username="driver2",
            password="driver2",
            role=User.Role.DRIVER
        )
        self.dispatcher = User.objects.create_user(
            username="dispatcher",
            password="dispatcher",
            role=User.Role.DISPATCHER
        )
        
        # Create POIs
        self.reception = POI.objects.create(code="RECEPTION", name="Reception")
        self.beach_bar = POI.objects.create(code="BEACH_BAR", name="Beach Bar")
        
        # Create edge between POIs for routing
        PoiEdge.objects.create(
            from_poi=self.reception,
            to_poi=self.beach_bar,
            travel_time_s=240
        )
        
        # Create buggy for driver1
        self.buggy1 = Buggy.objects.create(
            code="BUGGY_1",
            display_name="Buggy #1",
            capacity=4,
            status=Buggy.Status.ACTIVE,
            current_poi=self.reception,
            driver=self.driver1
        )
        
        self.sse_url = reverse("driver-ride-notifications")
        
    def _authenticate_as(self, user):
        self.client.force_authenticate(user=user)
    
    def test_sse_endpoint_requires_authentication(self):
        """Unauthenticated users cannot access SSE endpoint."""
        response = self.client.get(self.sse_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_sse_endpoint_requires_driver_role(self):
        """Non-driver users cannot access SSE endpoint."""
        self._authenticate_as(self.dispatcher)
        response = self.client.get(self.sse_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_sse_endpoint_returns_streaming_response(self):
        """Driver can access SSE endpoint and get streaming response."""
        self._authenticate_as(self.driver1)
        response = self.client.get(self.sse_url)
        
        # SSE returns 200 with text/event-stream content type
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
        self.assertEqual(response['Cache-Control'], 'no-cache')
    
    def test_event_broadcasting_to_specific_driver(self):
        """Events are sent only to the targeted driver."""
        # Register both drivers
        queue1 = broadcaster.register_driver(self.driver1.id)
        queue2 = broadcaster.register_driver(self.driver2.id)
        
        # Send event to driver1 only
        send_event_to_driver(
            driver_id=self.driver1.id,
            event_type="new_ride",
            data={"ride_id": 123, "ride_code": "ABC123"}
        )
        
        # Driver1 should receive event
        self.assertFalse(queue1.empty())
        event1 = queue1.get_nowait()
        self.assertEqual(event1["type"], "new_ride")
        self.assertEqual(event1["data"]["ride_id"], 123)
        
        # Driver2 should NOT receive event
        self.assertTrue(queue2.empty())
        
        # Cleanup
        broadcaster.unregister_driver(self.driver1.id)
        broadcaster.unregister_driver(self.driver2.id)
    
    def test_ride_assignment_triggers_sse_event(self):
        """Creating and assigning a ride triggers SSE event to driver."""
        # Register driver to receive events
        event_queue = broadcaster.register_driver(self.driver1.id)
        
        # Create and assign ride via API
        self._authenticate_as(self.dispatcher)
        create_url = reverse("rides-create-and-assign")
        
        response = self.client.post(create_url, {
            "pickup_poi_code": self.reception.code,
            "dropoff_poi_code": self.beach_bar.code,
            "num_guests": 2,
            "room_number": "101",
            "guest_name": "Test Guest"
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if event was sent to driver
        self.assertFalse(event_queue.empty())
        event = event_queue.get_nowait()
        
        self.assertEqual(event["type"], "new_ride")
        self.assertIn("ride_id", event["data"])
        self.assertIn("ride_code", event["data"])
        self.assertEqual(event["data"]["buggy_id"], self.buggy1.id)
        
        # Cleanup
        broadcaster.unregister_driver(self.driver1.id)
    
    def test_event_queue_cleanup_on_disconnect(self):
        """Driver queue is removed when they disconnect."""
        # Register driver
        broadcaster.register_driver(self.driver1.id)
        self.assertIn(self.driver1.id, broadcaster._driver_queues)
        
        # Unregister driver
        broadcaster.unregister_driver(self.driver1.id)
        self.assertNotIn(self.driver1.id, broadcaster._driver_queues)

