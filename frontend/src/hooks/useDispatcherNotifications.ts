import { useEffect, useRef, useCallback } from "react";

interface NotificationEvent {
  type: string;
  timestamp: string;
  data: {
    ride_id?: number;
    ride_code?: string;
    buggy_id?: number;
    buggy_name?: string;
    stop_type?: string;
    action?: string;
    new_status?: string;
  };
}

interface UseDispatcherNotificationsOptions {
  onRideStatusUpdate?: (event: NotificationEvent) => void;
  onError?: (error: Error) => void;
}

/**
 * Custom hook for receiving real-time ride status updates via Server-Sent Events (SSE).
 * Automatically reconnects on connection loss.
 */
export function useDispatcherNotifications(options: UseDispatcherNotificationsOptions = {}) {
  const { onRideStatusUpdate, onError } = options;
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    // Get auth token (must match the key used in auth/client.ts)
    const token = localStorage.getItem("authToken");
    if (!token) {
      console.warn("No auth token found for SSE connection");
      return;
    }

    // Create EventSource with auth token in URL (EventSource doesn't support custom headers)
    const apiBase = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";
    const url = `${apiBase}/dispatcher/ride-notifications/?token=${encodeURIComponent(token)}`;

    const eventSource = new EventSource(url);

    eventSource.onopen = () => {
      console.log("✅ Dispatcher SSE connection established");
    };

    eventSource.onmessage = (event) => {
      try {
        const data: NotificationEvent = JSON.parse(event.data);

        if (data.type === "ride_status_update" && onRideStatusUpdate) {
          console.log("📨 Ride status update:", data.data.ride_code, data.data.action);
          onRideStatusUpdate(data);
        }
      } catch (err) {
        console.error("Failed to parse SSE event:", err);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE connection error:", error);
      eventSource.close();

      if (onError) {
        onError(new Error("SSE connection lost"));
      }

      // Attempt to reconnect after 5 seconds
      reconnectTimeoutRef.current = window.setTimeout(() => {
        console.log("Attempting to reconnect SSE...");
        connect();
      }, 5000);
    };

    eventSourceRef.current = eventSource;
  }, [onRideStatusUpdate, onError]);

  useEffect(() => {
    // Prevent duplicate connections
    if (eventSourceRef.current) {
      console.log("⚠️ SSE connection already exists, skipping duplicate");
      return;
    }

    connect();

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        console.log("Closing dispatcher SSE connection");
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, []); // Empty dependency array to run once

  return {
    isConnected: eventSourceRef.current?.readyState === EventSource.OPEN,
  };
}

