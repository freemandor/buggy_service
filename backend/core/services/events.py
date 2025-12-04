"""
Event broadcasting system for Server-Sent Events (SSE).
Manages in-memory event queues for real-time notifications to drivers.
"""
import threading
import queue
import json
from typing import Dict, Any, Generator
from datetime import datetime


class EventBroadcaster:
    """Manages event queues for SSE connections."""
    
    def __init__(self):
        # Dictionary of driver_id -> queue
        self._driver_queues: Dict[int, queue.Queue] = {}
        # Dictionary of dispatcher_id -> queue
        self._dispatcher_queues: Dict[int, queue.Queue] = {}
        self._lock = threading.Lock()
    
    def register_driver(self, driver_id: int) -> queue.Queue:
        """Register a driver and return their event queue."""
        with self._lock:
            if driver_id not in self._driver_queues:
                self._driver_queues[driver_id] = queue.Queue()
            return self._driver_queues[driver_id]
    
    def unregister_driver(self, driver_id: int):
        """Remove driver's queue when they disconnect."""
        with self._lock:
            if driver_id in self._driver_queues:
                del self._driver_queues[driver_id]
    
    def register_dispatcher(self, dispatcher_id: int) -> queue.Queue:
        """Register a dispatcher and return their event queue."""
        with self._lock:
            if dispatcher_id not in self._dispatcher_queues:
                self._dispatcher_queues[dispatcher_id] = queue.Queue()
            return self._dispatcher_queues[dispatcher_id]
    
    def unregister_dispatcher(self, dispatcher_id: int):
        """Remove dispatcher's queue when they disconnect."""
        with self._lock:
            if dispatcher_id in self._dispatcher_queues:
                del self._dispatcher_queues[dispatcher_id]
    
    def send_event_to_driver(self, driver_id: int, event_type: str, data: Dict[str, Any]):
        """Send an event to a specific driver."""
        with self._lock:
            if driver_id in self._driver_queues:
                event = {
                    "type": event_type,
                    "timestamp": datetime.now().isoformat(),
                    "data": data
                }
                try:
                    # Non-blocking put with timeout to prevent blocking
                    self._driver_queues[driver_id].put_nowait(event)
                except queue.Full:
                    # Queue full, drop oldest event and add new one
                    try:
                        self._driver_queues[driver_id].get_nowait()
                        self._driver_queues[driver_id].put_nowait(event)
                    except queue.Empty:
                        pass
    
    def send_event_to_all_dispatchers(self, event_type: str, data: Dict[str, Any]):
        """Send an event to all connected dispatchers."""
        with self._lock:
            event = {
                "type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            for dispatcher_id, dispatcher_queue in self._dispatcher_queues.items():
                try:
                    dispatcher_queue.put_nowait(event)
                except queue.Full:
                    # Queue full, drop oldest event and add new one
                    try:
                        dispatcher_queue.get_nowait()
                        dispatcher_queue.put_nowait(event)
                    except queue.Empty:
                        pass
    
    def get_event_stream(self, driver_id: int) -> Generator[str, None, None]:
        """
        Generator that yields SSE-formatted events for a driver.
        Blocks until events are available.
        """
        event_queue = self.register_driver(driver_id)
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'driver_id': driver_id})}\n\n"
        
        try:
            while True:
                try:
                    # Wait for event with timeout to allow periodic heartbeats
                    event = event_queue.get(timeout=15)
                    # Format as SSE event
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
        finally:
            self.unregister_driver(driver_id)
    
    def get_dispatcher_event_stream(self, dispatcher_id: int) -> Generator[str, None, None]:
        """
        Generator that yields SSE-formatted events for a dispatcher.
        Blocks until events are available.
        """
        event_queue = self.register_dispatcher(dispatcher_id)
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'dispatcher_id': dispatcher_id})}\n\n"
        
        try:
            while True:
                try:
                    # Wait for event with timeout to allow periodic heartbeats
                    event = event_queue.get(timeout=15)
                    # Format as SSE event
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
        finally:
            self.unregister_dispatcher(dispatcher_id)


# Global broadcaster instance
broadcaster = EventBroadcaster()


# Convenience functions
def send_event_to_driver(driver_id: int, event_type: str, data: Dict[str, Any]):
    """Send an event to a specific driver."""
    broadcaster.send_event_to_driver(driver_id, event_type, data)


def send_event_to_all_dispatchers(event_type: str, data: Dict[str, Any]):
    """Send an event to all connected dispatchers."""
    broadcaster.send_event_to_all_dispatchers(event_type, data)


def get_driver_event_stream(driver_id: int) -> Generator[str, None, None]:
    """Get SSE event stream for a driver."""
    return broadcaster.get_event_stream(driver_id)


def get_dispatcher_event_stream(dispatcher_id: int) -> Generator[str, None, None]:
    """Get SSE event stream for a dispatcher."""
    return broadcaster.get_dispatcher_event_stream(dispatcher_id)

