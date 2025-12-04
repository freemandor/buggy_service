import React, { useState, useEffect } from "react";
import Layout from "../components/Layout";
import { fetchMetricsSummary, MetricsSummary } from "../api/metrics";
import { fetchBuggies, Buggy } from "../api/buggies";
import { fetchRides, RideRequest } from "../api/rides";

const ManagerDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [buggies, setBuggies] = useState<Buggy[]>([]);
  const [rides, setRides] = useState<RideRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [metricsData, buggiesData, ridesData] = await Promise.all([
          fetchMetricsSummary(),
          fetchBuggies(),
          fetchRides(),
        ]);
        setMetrics(metricsData);
        setBuggies(buggiesData);
        setRides(ridesData);
      } catch (err) {
        console.error("Failed to load data", err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) {
    return <Layout><div className="page">Loading...</div></Layout>;
  }

  return (
    <Layout>
      <div className="page">
        <div className="page-header">
          <div>
            <div className="page-title">Manager dashboard</div>
            <div className="page-subtitle">
              Live operations overview for Club Med Seychelles
            </div>
          </div>
        </div>

        {/* KPI Cards Row */}
        <div style={{ display: "flex", gap: "1.25rem", marginBottom: "1.25rem" }}>
          <div className="card" style={{ flex: 1 }}>
            <div className="card-subtitle" style={{ marginBottom: "0.5rem" }}>
              Total Rides
            </div>
            <div style={{ fontSize: "2.25rem", fontWeight: "bold", color: "var(--brand-teal)" }}>
              {metrics?.total_rides || 0}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
              Today · {metrics?.date}
            </div>
          </div>

          <div className="card" style={{ flex: 1 }}>
            <div className="card-subtitle" style={{ marginBottom: "0.5rem" }}>
              Avg Wait Time
            </div>
            <div style={{ fontSize: "2.25rem", fontWeight: "bold", color: "var(--brand-teal)" }}>
              {metrics?.avg_wait_time_s !== null && metrics?.avg_wait_time_s !== undefined
                ? `${metrics.avg_wait_time_s}s`
                : "—"}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
              From request to assignment
            </div>
          </div>
        </div>

        {/* Data Row */}
        <div className="grid-2">
          {/* Buggies Overview */}
          <div className="card">
            <h2 className="card-title">Buggies</h2>
            <div className="card-subtitle">Fleet status overview</div>
            
            {buggies.map(buggy => (
              <div 
                key={buggy.id}
                style={{ 
                  borderBottom: "1px solid var(--border-subtle)", 
                  paddingBottom: "0.75rem",
                  marginBottom: "0.75rem"
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

          {/* Today's Rides */}
          <div className="card">
            <h2 className="card-title">Today's rides</h2>
            <div className="card-subtitle">Recent ride requests</div>
            
            {rides.slice(0, 10).map(ride => (
              <div 
                key={ride.id}
                style={{ 
                  borderBottom: "1px solid var(--border-subtle)", 
                  paddingBottom: "0.75rem",
                  marginBottom: "0.75rem"
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
        </div>
      </div>
    </Layout>
  );
};

export default ManagerDashboard;
