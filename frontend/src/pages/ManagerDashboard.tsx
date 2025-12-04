import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import { fetchMetricsSummary, MetricsSummary } from "../api/metrics";
import { 
  fetchBuggies, 
  createBuggy, 
  updateBuggy, 
  deleteBuggy, 
  Buggy, 
  BuggyCreatePayload,
  BuggyUpdatePayload 
} from "../api/buggies";
import { fetchRides, RideRequest } from "../api/rides";
import { 
  fetchDrivers, 
  createDriver, 
  updateDriver, 
  deleteDriver, 
  Driver,
  DriverCreatePayload,
  DriverUpdatePayload 
} from "../api/drivers";
import { 
  fetchPOIs, 
  createPOI, 
  updatePOI, 
  deletePOI, 
  POI,
  POICreatePayload,
  POIUpdatePayload 
} from "../api/pois";

type Tab = "metrics" | "buggies" | "drivers" | "pois";

const ManagerDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>("metrics");
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [buggies, setBuggies] = useState<Buggy[]>([]);
  const [rides, setRides] = useState<RideRequest[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [pois, setPois] = useState<POI[]>([]);
  const [loading, setLoading] = useState(true);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const showSuccess = (message: string) => {
    setSuccessMessage(message);
    setErrorMessage(null);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const showError = (message: string) => {
    setErrorMessage(message);
    setSuccessMessage(null);
  };

  const loadInitialData = async () => {
    try {
      const [metricsData, buggiesData, ridesData] = await Promise.all([
        fetchMetricsSummary(),
        fetchBuggies(),
        fetchRides(),
      ]);
      setMetrics(metricsData);
      setBuggies(buggiesData);
      setRides(ridesData);
    } catch (err: any) {
      showError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const loadDrivers = async () => {
    try {
      const driversData = await fetchDrivers();
      setDrivers(driversData);
    } catch (err: any) {
      showError(err.message || "Failed to load drivers");
    }
  };

  const loadPOIs = async () => {
    try {
      const poisData = await fetchPOIs();
      setPois(poisData);
    } catch (err: any) {
      showError(err.message || "Failed to load POIs");
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (activeTab === "buggies") {
      if (drivers.length === 0) loadDrivers();
      if (pois.length === 0) loadPOIs();
    }
    if (activeTab === "drivers" && drivers.length === 0) {
      loadDrivers();
    }
    if (activeTab === "pois" && pois.length === 0) {
      loadPOIs();
    }
  }, [activeTab]);

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
              Operations management for Club Med Seychelles
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ 
          display: "flex", 
          gap: "0.5rem", 
          marginBottom: "1.5rem", 
          borderBottom: "2px solid var(--border-subtle)" 
        }}>
          <TabButton 
            active={activeTab === "metrics"} 
            onClick={() => setActiveTab("metrics")}
          >
            Metrics
          </TabButton>
          <TabButton 
            active={activeTab === "buggies"} 
            onClick={() => setActiveTab("buggies")}
          >
            Buggies
          </TabButton>
          <TabButton 
            active={activeTab === "drivers"} 
            onClick={() => setActiveTab("drivers")}
          >
            Drivers
          </TabButton>
          <TabButton 
            active={activeTab === "pois"} 
            onClick={() => setActiveTab("pois")}
          >
            POIs
          </TabButton>
        </div>

        {/* Messages */}
        {successMessage && (
          <div className="banner-success" style={{ marginBottom: "1rem" }}>
            {successMessage}
          </div>
        )}
        {errorMessage && (
          <div className="banner-error" style={{ marginBottom: "1rem" }}>
            {errorMessage}
          </div>
        )}

        {/* Tab Content */}
        {activeTab === "metrics" && (
          <MetricsTab metrics={metrics} buggies={buggies} rides={rides} />
        )}
        {activeTab === "buggies" && (
          <BuggiesTab 
            buggies={buggies} 
            drivers={drivers}
            pois={pois}
            onRefresh={loadInitialData} 
            onSuccess={showSuccess}
            onError={showError}
          />
        )}
        {activeTab === "drivers" && (
          <DriversTab 
            drivers={drivers} 
            onRefresh={loadDrivers} 
            onSuccess={showSuccess}
            onError={showError}
          />
        )}
        {activeTab === "pois" && (
          <POIsTab 
            pois={pois} 
            onRefresh={loadPOIs} 
            onSuccess={showSuccess}
            onError={showError}
          />
        )}
      </div>
    </Layout>
  );
};

// Tab Button Component
const TabButton: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode }> = ({ 
  active, 
  onClick, 
  children 
}) => (
  <button
    onClick={onClick}
    style={{
      padding: "0.75rem 1.5rem",
      background: "none",
      border: "none",
      borderBottom: active ? "3px solid var(--brand-blue)" : "3px solid transparent",
      fontWeight: active ? 600 : 400,
      color: active ? "var(--brand-blue)" : "var(--text-muted)",
      cursor: "pointer",
      fontSize: "1rem",
      transition: "all 0.2s ease"
    }}
  >
    {children}
  </button>
);

// Metrics Tab Component
const MetricsTab: React.FC<{ 
  metrics: MetricsSummary | null; 
  buggies: Buggy[]; 
  rides: RideRequest[] 
}> = ({ metrics, buggies, rides }) => (
  <>
    {/* KPI Cards Row */}
    <div style={{ display: "flex", gap: "1.25rem", marginBottom: "1.25rem" }}>
      <div className="card" style={{ flex: 1 }}>
        <div className="card-subtitle" style={{ marginBottom: "0.5rem" }}>
          Total Rides
        </div>
        <div style={{ fontSize: "2.25rem", fontWeight: "bold", color: "var(--brand-blue)" }}>
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
        <div style={{ fontSize: "2.25rem", fontWeight: "bold", color: "var(--brand-blue)" }}>
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
  </>
);

// Buggies Tab Component
const BuggiesTab: React.FC<{ 
  buggies: Buggy[];
  drivers: Driver[];
  pois: POI[];
  onRefresh: () => void; 
  onSuccess: (msg: string) => void;
  onError: (msg: string) => void;
}> = ({ buggies, drivers, pois, onRefresh, onSuccess, onError }) => {
  const [showForm, setShowForm] = useState(false);
  const [editingBuggy, setEditingBuggy] = useState<Buggy | null>(null);
  const [formData, setFormData] = useState<BuggyCreatePayload>({
    code: "",
    display_name: "",
    capacity: 4,
    status: "ACTIVE",
    current_onboard_guests: 0
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editingBuggy) {
        await updateBuggy(editingBuggy.id, formData as BuggyUpdatePayload);
        onSuccess("Buggy updated successfully");
      } else {
        await createBuggy(formData);
        onSuccess("Buggy created successfully");
      }
      setShowForm(false);
      setEditingBuggy(null);
      setFormData({
        code: "",
        display_name: "",
        capacity: 4,
        status: "ACTIVE",
        current_onboard_guests: 0
      });
      onRefresh();
    } catch (err: any) {
      onError(err.message || "Failed to save buggy");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (buggy: Buggy) => {
    setEditingBuggy(buggy);
    setFormData({
      code: buggy.code,
      display_name: buggy.display_name,
      capacity: buggy.capacity,
      status: buggy.status,
      driver_id: buggy.driver_id,
      current_poi_id: buggy.current_poi?.id,
      current_onboard_guests: buggy.current_onboard_guests
    });
    setShowForm(true);
  };

  const handleDelete = async (buggy: Buggy) => {
    if (!confirm(`Are you sure you want to delete ${buggy.display_name}?`)) return;
    try {
      await deleteBuggy(buggy.id);
      onSuccess("Buggy deleted successfully");
      onRefresh();
    } catch (err: any) {
      onError(err.message || "Failed to delete buggy");
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingBuggy(null);
    setFormData({
      code: "",
      display_name: "",
      capacity: 4,
      status: "ACTIVE",
      current_onboard_guests: 0
    });
  };

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <div>
          <h2 className="card-title">Buggies Management</h2>
          <div className="card-subtitle">Create, edit, and delete buggies</div>
        </div>
        {!showForm && (
          <button 
            onClick={() => setShowForm(true)} 
            className="primary-button"
          >
            Create New Buggy
          </button>
        )}
      </div>

      {showForm && (
        <div style={{ 
          background: "var(--bg-subtle)", 
          padding: "1.5rem", 
          borderRadius: "8px", 
          marginBottom: "1.5rem" 
        }}>
          <h3 style={{ marginBottom: "1rem", fontSize: "1.1rem" }}>
            {editingBuggy ? "Edit Buggy" : "Create New Buggy"}
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label className="form-label">Code</label>
              <input
                type="text"
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                className="form-input"
                required
              />
            </div>
            <div className="form-field">
              <label className="form-label">Display Name</label>
              <input
                type="text"
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                className="form-input"
                required
              />
            </div>
            <div className="form-field">
              <label className="form-label">Capacity</label>
              <input
                type="number"
                value={formData.capacity}
                onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value) })}
                className="form-number"
                required
                min="1"
              />
            </div>
            <div className="form-field">
              <label className="form-label">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as "ACTIVE" | "INACTIVE" })}
                className="form-select"
              >
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
              </select>
            </div>
            <div className="form-field">
              <label className="form-label">Driver (Optional)</label>
              <select
                value={formData.driver_id || ""}
                onChange={(e) => setFormData({ ...formData, driver_id: e.target.value ? parseInt(e.target.value) : null })}
                className="form-select"
              >
                <option value="">No Driver</option>
                {drivers.map(driver => (
                  <option key={driver.id} value={driver.id}>
                    {driver.username} - {driver.first_name} {driver.last_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-field">
              <label className="form-label">Current POI (Optional)</label>
              <select
                value={formData.current_poi_id || ""}
                onChange={(e) => setFormData({ ...formData, current_poi_id: e.target.value ? parseInt(e.target.value) : null })}
                className="form-select"
              >
                <option value="">No Location</option>
                {pois.map(poi => (
                  <option key={poi.id} value={poi.id}>
                    {poi.name}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
              <button type="submit" disabled={submitting} className="primary-button">
                {submitting ? "Saving..." : (editingBuggy ? "Update" : "Create")}
              </button>
              <button type="button" onClick={handleCancel} className="secondary-button">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <table className="table-lite">
        <thead>
          <tr>
            <th>Code</th>
            <th>Display Name</th>
            <th>Capacity</th>
            <th>Status</th>
            <th>Current Location</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {buggies.map(buggy => (
            <tr key={buggy.id}>
              <td>{buggy.code}</td>
              <td>{buggy.display_name}</td>
              <td>{buggy.capacity}</td>
              <td>
                <span className={`pill ${buggy.status === "ACTIVE" ? "pill--active" : "pill--inactive"}`}>
                  {buggy.status}
                </span>
              </td>
              <td>{buggy.current_poi ? buggy.current_poi.name : "—"}</td>
              <td>
                <button 
                  onClick={() => handleEdit(buggy)} 
                  className="secondary-button"
                  style={{ marginRight: "0.5rem", padding: "0.25rem 0.75rem", fontSize: "0.85rem" }}
                >
                  Edit
                </button>
                <button 
                  onClick={() => handleDelete(buggy)} 
                  className="secondary-button"
                  style={{ padding: "0.25rem 0.75rem", fontSize: "0.85rem" }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Drivers Tab Component
const DriversTab: React.FC<{ 
  drivers: Driver[]; 
  onRefresh: () => void; 
  onSuccess: (msg: string) => void;
  onError: (msg: string) => void;
}> = ({ drivers, onRefresh, onSuccess, onError }) => {
  const [showForm, setShowForm] = useState(false);
  const [editingDriver, setEditingDriver] = useState<Driver | null>(null);
  const [formData, setFormData] = useState<DriverCreatePayload>({
    username: "",
    password: "",
    first_name: "",
    last_name: ""
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editingDriver) {
        const updateData: DriverUpdatePayload = {
          username: formData.username,
          first_name: formData.first_name,
          last_name: formData.last_name
        };
        if (formData.password) {
          updateData.password = formData.password;
        }
        await updateDriver(editingDriver.id, updateData);
        onSuccess("Driver updated successfully");
      } else {
        await createDriver(formData);
        onSuccess("Driver created successfully");
      }
      setShowForm(false);
      setEditingDriver(null);
      setFormData({
        username: "",
        password: "",
        first_name: "",
        last_name: ""
      });
      onRefresh();
    } catch (err: any) {
      onError(err.message || "Failed to save driver");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (driver: Driver) => {
    setEditingDriver(driver);
    setFormData({
      username: driver.username,
      password: "",
      first_name: driver.first_name,
      last_name: driver.last_name
    });
    setShowForm(true);
  };

  const handleDelete = async (driver: Driver) => {
    if (!confirm(`Are you sure you want to delete driver ${driver.username}?`)) return;
    try {
      await deleteDriver(driver.id);
      onSuccess("Driver deleted successfully");
      onRefresh();
    } catch (err: any) {
      onError(err.message || "Failed to delete driver");
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingDriver(null);
    setFormData({
      username: "",
      password: "",
      first_name: "",
      last_name: ""
    });
  };

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <div>
          <h2 className="card-title">Drivers Management</h2>
          <div className="card-subtitle">Create, edit, and delete drivers</div>
        </div>
        {!showForm && (
          <button 
            onClick={() => setShowForm(true)} 
            className="primary-button"
          >
            Create New Driver
          </button>
        )}
      </div>

      {showForm && (
        <div style={{ 
          background: "var(--bg-subtle)", 
          padding: "1.5rem", 
          borderRadius: "8px", 
          marginBottom: "1.5rem" 
        }}>
          <h3 style={{ marginBottom: "1rem", fontSize: "1.1rem" }}>
            {editingDriver ? "Edit Driver" : "Create New Driver"}
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label className="form-label">Username</label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="form-input"
                required
              />
            </div>
            <div className="form-field">
              <label className="form-label">Password {editingDriver && "(leave blank to keep current)"}</label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="form-input"
                required={!editingDriver}
              />
            </div>
            <div className="form-field">
              <label className="form-label">First Name</label>
              <input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                className="form-input"
              />
            </div>
            <div className="form-field">
              <label className="form-label">Last Name</label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                className="form-input"
              />
            </div>
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
              <button type="submit" disabled={submitting} className="primary-button">
                {submitting ? "Saving..." : (editingDriver ? "Update" : "Create")}
              </button>
              <button type="button" onClick={handleCancel} className="secondary-button">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <table className="table-lite">
        <thead>
          <tr>
            <th>Username</th>
            <th>First Name</th>
            <th>Last Name</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {drivers.map(driver => (
            <tr key={driver.id}>
              <td>{driver.username}</td>
              <td>{driver.first_name || "—"}</td>
              <td>{driver.last_name || "—"}</td>
              <td>
                <button 
                  onClick={() => handleEdit(driver)} 
                  className="secondary-button"
                  style={{ marginRight: "0.5rem", padding: "0.25rem 0.75rem", fontSize: "0.85rem" }}
                >
                  Edit
                </button>
                <button 
                  onClick={() => handleDelete(driver)} 
                  className="secondary-button"
                  style={{ padding: "0.25rem 0.75rem", fontSize: "0.85rem" }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// POIs Tab Component
const POIsTab: React.FC<{ 
  pois: POI[];
  onRefresh: () => void;
  onSuccess: (msg: string) => void;
  onError: (msg: string) => void;
}> = ({ pois, onRefresh, onSuccess, onError }) => {
  const navigate = useNavigate();
  
  const [showForm, setShowForm] = useState(false);
  const [editingPOI, setEditingPOI] = useState<POI | null>(null);
  const [formData, setFormData] = useState<POICreatePayload>({
    code: "",
    name: ""
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editingPOI) {
        await updatePOI(editingPOI.id, formData as POIUpdatePayload);
        onSuccess("POI updated successfully");
      } else {
        await createPOI(formData);
        onSuccess("POI created successfully");
      }
      setShowForm(false);
      setEditingPOI(null);
      setFormData({
        code: "",
        name: ""
      });
      onRefresh();
    } catch (err: any) {
      onError(err.message || "Failed to save POI");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (poi: POI) => {
    setEditingPOI(poi);
    setFormData({
      code: poi.code,
      name: poi.name
    });
    setShowForm(true);
  };

  const handleDelete = async (poi: POI) => {
    if (!confirm(`Are you sure you want to delete ${poi.name}?`)) return;
    try {
      await deletePOI(poi.id);
      onSuccess("POI deleted successfully");
      onRefresh();
    } catch (err: any) {
      onError(err.message || "Failed to delete POI");
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingPOI(null);
    setFormData({
      code: "",
      name: ""
    });
  };

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <div>
          <h2 className="card-title">POIs Management</h2>
          <div className="card-subtitle">Create, edit, and delete points of interest</div>
        </div>
        {!showForm && (
          <button 
            onClick={() => setShowForm(true)} 
            className="primary-button"
          >
            Create New POI
          </button>
        )}
      </div>

      {showForm && (
        <div style={{ 
          background: "var(--bg-subtle)", 
          padding: "1.5rem", 
          borderRadius: "8px", 
          marginBottom: "1.5rem" 
        }}>
          <h3 style={{ marginBottom: "1rem", fontSize: "1.1rem" }}>
            {editingPOI ? "Edit POI" : "Create New POI"}
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label className="form-label">Code</label>
              <input
                type="text"
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                className="form-input"
                required
              />
            </div>
            <div className="form-field">
              <label className="form-label">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="form-input"
                required
              />
            </div>
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
              <button type="submit" disabled={submitting} className="primary-button">
                {submitting ? "Saving..." : (editingPOI ? "Update" : "Create")}
              </button>
              <button type="button" onClick={handleCancel} className="secondary-button">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <table className="table-lite">
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {pois.map(poi => (
            <tr key={poi.id}>
              <td>{poi.code}</td>
              <td>{poi.name}</td>
              <td>
                <button 
                  onClick={() => navigate(`/manager/pois/${poi.id}`)}
                  className="primary-button"
                  style={{ marginRight: "0.5rem", padding: "0.25rem 0.75rem", fontSize: "0.85rem" }}
                >
                  View Details
                </button>
                <button 
                  onClick={() => handleEdit(poi)} 
                  className="secondary-button"
                  style={{ marginRight: "0.5rem", padding: "0.25rem 0.75rem", fontSize: "0.85rem" }}
                >
                  Edit
                </button>
                <button 
                  onClick={() => handleDelete(poi)} 
                  className="secondary-button"
                  style={{ padding: "0.25rem 0.75rem", fontSize: "0.85rem" }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ManagerDashboard;
