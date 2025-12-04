from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from core.models import User, POI, PoiEdge, Buggy, RideRequest, BuggyRouteStop
from core.services.events import send_event_to_all_dispatchers, broadcaster
import json


class DispatcherSSETests(APITestCase):
    def setUp(self):
        # Create users
        self.dispatcher1 = User.objects.create_user(
            username="dispatcher1",
            password="dispatcher1",
            role=User.Role.DISPATCHER
        )
        self.dispatcher2 = User.objects.create_user(
            username="dispatcher2",
            password="dispatcher2",
            role=User.Role.DISPATCHER
        )
        self.driver = User.objects.create_user(
            username="driver",
            password="driver",
            role=User.Role.DRIVER
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
        
        # Create buggy for driver
        self.buggy = Buggy.objects.create(
            code="BUGGY_1",
            display_name="Buggy #1",
            capacity=4,
            status=Buggy.Status.ACTIVE,
            current_poi=self.reception,
            driver=self.driver
        )
        
        self.sse_url = reverse("dispatcher-ride-notifications")
        
    def _authenticate_as(self, user):
        self.client.force_authenticate(user=user)
    
    def test_sse_endpoint_requires_authentication(self):
        """Unauthenticated users cannot access SSE endpoint."""
        response = self.client.get(self.sse_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_sse_endpoint_requires_dispatcher_role(self):
        """Non-dispatcher users cannot access SSE endpoint."""
        # Generate token for driver (non-dispatcher)
        token = str(AccessToken.for_user(self.driver))
        response = self.client.get(f"{self.sse_url}?token={token}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_sse_endpoint_returns_streaming_response(self):
        """Dispatcher can access SSE endpoint and get streaming response."""
        # Generate token for dispatcher
        token = str(AccessToken.for_user(self.dispatcher1))
        response = self.client.get(f"{self.sse_url}?token={token}")
        
        # SSE returns 200 with text/event-stream content type
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
        self.assertEqual(response['Cache-Control'], 'no-cache')
    
    def test_event_broadcasting_to_all_dispatchers(self):
        """Events are sent to all registered dispatchers."""
        # Register both dispatchers
        queue1 = broadcaster.register_dispatcher(self.dispatcher1.id)
        queue2 = broadcaster.register_dispatcher(self.dispatcher2.id)
        
        # Send event to all dispatchers
        send_event_to_all_dispatchers(
            event_type="ride_status_update",
            data={"ride_id": 123, "ride_code": "ABC123", "action": "started"}
        )
        
        # Both dispatchers should receive event
        self.assertFalse(queue1.empty())
        event1 = queue1.get_nowait()
        self.assertEqual(event1["type"], "ride_status_update")
        self.assertEqual(event1["data"]["ride_id"], 123)
        
        self.assertFalse(queue2.empty())
        event2 = queue2.get_nowait()
        self.assertEqual(event2["type"], "ride_status_update")
        self.assertEqual(event2["data"]["ride_id"], 123)
        
        # Cleanup
        broadcaster.unregister_dispatcher(self.dispatcher1.id)
        broadcaster.unregister_dispatcher(self.dispatcher2.id)
    
    def test_driver_stop_action_triggers_sse_event(self):
        """Starting/completing a stop triggers SSE event to dispatchers."""
        # Create a ride and route stop
        ride = RideRequest.objects.create(
            pickup_poi=self.reception,
            dropoff_poi=self.beach_bar,
            num_guests=2,
            room_number="101",
            guest_name="Test Guest",
            status=RideRequest.Status.ASSIGNED,
            assigned_buggy=self.buggy
        )
        
        stop = BuggyRouteStop.objects.create(
            buggy=self.buggy,
            ride_request=ride,
            stop_type=BuggyRouteStop.StopType.PICKUP,
            poi=self.reception,
            sequence_index=0,
            status=BuggyRouteStop.StopStatus.PLANNED
        )
        
        # Register dispatcher to receive events
        event_queue = broadcaster.register_dispatcher(self.dispatcher1.id)
        
        # Start the stop as driver
        self._authenticate_as(self.driver)
        start_url = reverse("driver-stop-start", kwargs={"stop_id": stop.id})
        response = self.client.post(start_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if event was sent to dispatcher
        self.assertFalse(event_queue.empty())
        event = event_queue.get_nowait()
        
        self.assertEqual(event["type"], "ride_status_update")
        self.assertIn("ride_id", event["data"])
        self.assertIn("ride_code", event["data"])
        self.assertEqual(event["data"]["action"], "started")
        self.assertEqual(event["data"]["buggy_id"], self.buggy.id)
        
        # Cleanup
        broadcaster.unregister_dispatcher(self.dispatcher1.id)
    
    def test_event_queue_cleanup_on_disconnect(self):
        """Dispatcher queue is removed when they disconnect."""
        # Register dispatcher
        broadcaster.register_dispatcher(self.dispatcher1.id)
        self.assertIn(self.dispatcher1.id, broadcaster._dispatcher_queues)
        
        # Unregister dispatcher
        broadcaster.unregister_dispatcher(self.dispatcher1.id)
        self.assertNotIn(self.dispatcher1.id, broadcaster._dispatcher_queues)

