import React, { useState, useEffect, useCallback } from "react";
import Layout from "../components/Layout";
import { fetchBuggies, Buggy } from "../api/buggies";
import { fetchRides, createRideAndAssign, RideRequest, CreateRidePayload } from "../api/rides";
import { fetchPOIs, POI } from "../api/pois";

const DispatcherDashboard: React.FC = () => {
  const [buggies, setBuggies] = useState<Buggy[]>([]);
  const [rides, setRides] = useState<RideRequest[]>([]);
  const [pois, setPois] = useState<POI[]>([]);
  const [hasActiveBuggy, setHasActiveBuggy] = useState(false);
  const [loading, setLoading] = useState(true);

  const [pickupPoi, setPickupPoi] = useState("");
  const [dropoffPoi, setDropoffPoi] = useState("");
  const [numGuests, setNumGuests] = useState(2);
  const [roomNumber, setRoomNumber] = useState("");
  const [guestName, setGuestName] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadInitial = useCallback(async () => {
    try {
      const [buggiesData, poisData] = await Promise.all([
        fetchBuggies(),
        fetchPOIs(),
      ]);
      setBuggies(buggiesData);
      setHasActiveBuggy(buggiesData.some(b => b.status === "ACTIVE"));
      setPois(poisData);
      if (poisData.length >= 2) {
        setPickupPoi(poisData[0].code);
        setDropoffPoi(poisData[1].code);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load data");
    }
  }, []);

  const loadRides = useCallback(async () => {
    try {
      const ridesData = await fetchRides();
      setRides(ridesData);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load data");
    }
  }, []);

  useEffect(() => {
    const bootstrap = async () => {
      await loadInitial();
      await loadRides();
      setLoading(false);
    };
    bootstrap();
    const interval = window.setInterval(loadRides, 10000);
    return () => window.clearInterval(interval);
  }, [loadInitial, loadRides]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    const payload: CreateRidePayload = {
      pickup_poi_code: pickupPoi,
      dropoff_poi_code: dropoffPoi,
      num_guests: numGuests,
      room_number: roomNumber,
      guest_name: guestName,
    };

    try {
      const result = await createRideAndAssign(payload);
      setSuccessMessage(
        `Ride ${result.ride.public_code} assigned to ${result.assigned_buggy.display_name}`
      );
      // Reset form
      setRoomNumber("");
      setGuestName("");
      // Reload data
      await loadRides();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to create ride");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <Layout><div className="page">Loading...</div></Layout>;
  }

  return (
    <Layout>
      <div className="page">
        <div className="page-header">
          <div>
            <div className="page-title">Dispatcher dashboard</div>
            <div className="page-subtitle">
              Club Med Seychelles · Buggy service optimization
            </div>
          </div>
        </div>

        <div className="grid-2">
          {/* Left: New Ride Form */}
          <div className="card">
            <h2 className="card-title">New ride request</h2>
            <div className="card-subtitle">Create and assign a new guest ride</div>

            {!hasActiveBuggy && (
              <div className="banner-error">
                No active buggies available. Cannot create rides.
              </div>
            )}

            {successMessage && (
              <div className="banner-success">{successMessage}</div>
            )}

            {errorMessage && (
              <div className="banner-error">{errorMessage}</div>
            )}

            <form onSubmit={handleSubmit}>
              <fieldset disabled={!hasActiveBuggy || submitting} style={{ border: "none", padding: 0, margin: 0 }}>
                <div className="form-field">
                  <label className="form-label">Pickup POI</label>
                  <select
                    value={pickupPoi}
                    onChange={(e) => setPickupPoi(e.target.value)}
                    className="form-select"
                  >
                    {pois.map(poi => (
                      <option key={poi.id} value={poi.code}>
                        {poi.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-field">
                  <label className="form-label">Dropoff POI</label>
                  <select
                    value={dropoffPoi}
                    onChange={(e) => setDropoffPoi(e.target.value)}
                    className="form-select"
                  >
                    {pois.map(poi => (
                      <option key={poi.id} value={poi.code}>
                        {poi.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-field">
                  <label className="form-label">Number of Guests</label>
                  <input
                    type="number"
                    value={numGuests}
                    onChange={(e) => setNumGuests(Number(e.target.value))}
                    min={1}
                    className="form-number"
                  />
                </div>

                <div className="form-field">
                  <label className="form-label">Room Number</label>
                  <input
                    type="text"
                    value={roomNumber}
                    onChange={(e) => setRoomNumber(e.target.value)}
                    className="form-input"
                  />
                </div>

                <div className="form-field">
                  <label className="form-label">Guest Name</label>
                  <input
                    type="text"
                    value={guestName}
                    onChange={(e) => setGuestName(e.target.value)}
                    className="form-input"
                  />
                </div>

                <button
                  type="submit"
                  className="primary-button"
                  style={{ width: "100%", marginTop: "0.5rem" }}
                >
                  {submitting ? "Creating..." : "Create & Assign Ride"}
                </button>
              </fieldset>
            </form>
          </div>

          {/* Right: Data Cards */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            {/* Active Buggies */}
            <div className="card">
              <h2 className="card-title">Active buggies</h2>
              <div className="card-subtitle">Live status of all buggies on the island</div>
              
              {buggies.length === 0 ? (
                <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                  No buggies found
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {buggies.map(buggy => (
                    <div 
                      key={buggy.id}
                      style={{ 
                        borderBottom: "1px solid var(--border-subtle)", 
                        paddingBottom: "0.75rem" 
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                        <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>
                          {buggy.display_name}
                        </div>
                        <span className={`pill ${buggy.status === "ACTIVE" ? "pill--active" : "pill--inactive"}`}>
                          {buggy.status}
                        </span>
                      </div>
                      <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        Location: {buggy.current_poi ? buggy.current_poi.name : "—"} · Onboard: {buggy.current_onboard_guests} guest{buggy.current_onboard_guests !== 1 ? "s" : ""}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Rides */}
            <div className="card">
              <h2 className="card-title">Recent rides</h2>
              <div className="card-subtitle">Last 10 ride requests</div>
              
              {rides.length === 0 ? (
                <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                  No rides yet
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {rides.slice(0, 10).map(ride => (
                    <div 
                      key={ride.id}
                      style={{ 
                        borderBottom: "1px solid var(--border-subtle)", 
                        paddingBottom: "0.75rem" 
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                        <div style={{ fontFamily: "monospace", fontWeight: 600, fontSize: "1rem" }}>
                          {ride.public_code}
                        </div>
                        <span className="pill pill--status">
                          {ride.status}
                        </span>
                      </div>
                      <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        {ride.pickup_poi.name} → {ride.dropoff_poi.name} · {ride.num_guests} guest{ride.num_guests !== 1 ? "s" : ""}
                      </div>
                      {ride.assigned_buggy && (
                        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                          {ride.assigned_buggy.display_name}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default DispatcherDashboard;
