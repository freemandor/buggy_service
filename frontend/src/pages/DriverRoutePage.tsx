import React, { useState, useEffect, useCallback, useRef } from "react";
import Layout from "../components/Layout";
import { fetchDriverRoute, driverStartStop, driverCompleteStop, DriverRouteStop } from "../api/driver";

const DriverRoutePage: React.FC = () => {
  const [stops, setStops] = useState<DriverRouteStop[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const latestRequestId = useRef(0);
  const bootstrapped = useRef(false);

  const loadRoute = useCallback(async () => {
    const requestId = ++latestRequestId.current;
    try {
      const data = await fetchDriverRoute();
      // Only apply the latest response to avoid clobbering newer state.
      if (requestId === latestRequestId.current) {
        setStops(data);
        setError(null);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load route");
    } finally {
      if (!bootstrapped.current) {
        bootstrapped.current = true;
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    loadRoute();
    const interval = window.setInterval(loadRoute, 10000);
    return () => window.clearInterval(interval);
  }, [loadRoute]);

  const handleStart = async (stopId: number) => {
    try {
      await driverStartStop(stopId);
      await loadRoute();
    } catch (err: any) {
      setError(err.message || "Failed to start stop");
    }
  };

  const handleComplete = async (stopId: number) => {
    try {
      await driverCompleteStop(stopId);
      await loadRoute();
    } catch (err: any) {
      setError(err.message || "Failed to complete stop");
    }
  };

  if (loading) {
    return <Layout><div className="page">Loading...</div></Layout>;
  }

  return (
    <Layout>
      <div className="page">
        <div className="card">
          <h2 className="card-title">My route</h2>
          <div className="card-subtitle">Today's pickups and dropoffs in order</div>

          {error && <div className="banner-error">{error}</div>}

          {stops.length === 0 ? (
            <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)" }}>
              No upcoming stops.
            </div>
          ) : (
            <div className="stop-list">
              {stops.map((stop, index) => {
                const isNext = index === 0;
                return (
                  <div
                    key={stop.id}
                    className={`stop-card ${isNext ? 'stop-card--next' : ''}`}
                  >
                    <div className="stop-main">
                      {isNext && (
                        <div style={{ fontSize: "0.7rem", color: "var(--brand-teal)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.15rem" }}>
                          Next Stop
                        </div>
                      )}
                      <div className="stop-title">
                        {stop.stop_type === "PICKUP" ? "Pickup" : "Dropoff"} – {stop.poi.name}
                      </div>
                      <div className="stop-subtitle">
                        Ride {stop.ride_request_code} · {stop.num_guests} guest{stop.num_guests !== 1 ? "s" : ""}
                      </div>
                    </div>
                    <div className="stop-actions">
                      <span className="pill pill--status">{stop.status}</span>
                      {isNext && stop.status === "PLANNED" && (
                        <button
                          className="primary-button"
                          onClick={() => handleStart(stop.id)}
                        >
                          Start
                        </button>
                      )}
                      {isNext && stop.status === "ON_ROUTE" && (
                        <button
                          className="primary-button"
                          onClick={() => handleComplete(stop.id)}
                          style={{ background: "#059669" }}
                        >
                          Complete
                        </button>
                      )}
                      {!isNext && (
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                          Waiting
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default DriverRoutePage;
