import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import { fetchPOIs, POI } from "../api/pois";
import {
  fetchPOIEdges,
  createPOIEdge,
  updatePOIEdge,
  deletePOIEdge,
  POIEdge,
  POIEdgeCreatePayload,
  POIEdgeUpdatePayload
} from "../api/poiEdges";

const POIDetailPage: React.FC = () => {
  const { poiId } = useParams<{ poiId: string }>();
  const navigate = useNavigate();
  
  const [poi, setPoi] = useState<POI | null>(null);
  const [allPois, setAllPois] = useState<POI[]>([]);
  const [edges, setEdges] = useState<POIEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Edge form state
  const [showEdgeForm, setShowEdgeForm] = useState(false);
  const [editingEdge, setEditingEdge] = useState<POIEdge | null>(null);
  const [edgeFormData, setEdgeFormData] = useState<POIEdgeCreatePayload>({
    from_poi_id: 0,
    to_poi_id: 0,
    travel_time_s: 60
  });
  const [edgeSubmitting, setEdgeSubmitting] = useState(false);

  const showSuccess = (message: string) => {
    setSuccessMessage(message);
    setErrorMessage(null);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const showError = (message: string) => {
    setErrorMessage(message);
    setSuccessMessage(null);
  };

  const loadData = async () => {
    try {
      const [poisData, edgesData] = await Promise.all([
        fetchPOIs(),
        fetchPOIEdges(parseInt(poiId!))
      ]);
      
      setAllPois(poisData);
      setEdges(edgesData);
      
      const currentPoi = poisData.find(p => p.id === parseInt(poiId!));
      if (!currentPoi) {
        showError("POI not found");
        navigate("/manager");
        return;
      }
      setPoi(currentPoi);
    } catch (err: any) {
      showError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (poiId) {
      loadData();
    }
  }, [poiId]);

  const handleEdgeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEdgeSubmitting(true);
    try {
      if (editingEdge) {
        await updatePOIEdge(editingEdge.id, edgeFormData as POIEdgeUpdatePayload);
        showSuccess("Connection updated successfully");
      } else {
        await createPOIEdge(edgeFormData);
        showSuccess("Connection created successfully");
      }
      setShowEdgeForm(false);
      setEditingEdge(null);
      loadData();
    } catch (err: any) {
      showError(err.message || "Failed to save connection");
    } finally {
      setEdgeSubmitting(false);
    }
  };

  const handleEditEdge = (edge: POIEdge) => {
    setEditingEdge(edge);
    setEdgeFormData({
      from_poi_id: edge.from_poi.id,
      to_poi_id: edge.to_poi.id,
      travel_time_s: edge.travel_time_s
    });
    setShowEdgeForm(true);
  };

  const handleDeleteEdge = async (edge: POIEdge) => {
    const otherPoi = edge.from_poi.id === poi?.id ? edge.to_poi : edge.from_poi;
    if (!confirm(`Are you sure you want to delete the connection to ${otherPoi.name}?`)) return;
    
    try {
      await deletePOIEdge(edge.id);
      showSuccess("Connection deleted successfully");
      loadData();
    } catch (err: any) {
      showError(err.message || "Failed to delete connection");
    }
  };

  const handleCancelEdge = () => {
    setShowEdgeForm(false);
    setEditingEdge(null);
    setEdgeFormData({
      from_poi_id: poi?.id || 0,
      to_poi_id: 0,
      travel_time_s: 60
    });
  };

  const handleCreateNew = () => {
    if (allPois.length < 2) {
      showError("You need at least 2 POIs to create a connection");
      return;
    }
    
    // Set current POI as from_poi, and first other POI as to_poi
    const otherPoi = allPois.find(p => p.id !== poi?.id);
    setEdgeFormData({
      from_poi_id: poi?.id || 0,
      to_poi_id: otherPoi?.id || 0,
      travel_time_s: 60
    });
    setShowEdgeForm(true);
  };

  if (loading) {
    return <Layout><div className="page">Loading...</div></Layout>;
  }

  if (!poi) {
    return <Layout><div className="page">POI not found</div></Layout>;
  }

  // Get the other POI in each edge (since edges are bidirectional)
  const getOtherPoi = (edge: POIEdge) => {
    return edge.from_poi.id === poi.id ? edge.to_poi : edge.from_poi;
  };

  return (
    <Layout>
      <div className="page">
        {/* Header with back button */}
        <div style={{ marginBottom: "1.5rem" }}>
          <button 
            onClick={() => navigate("/manager")}
            className="secondary-button"
            style={{ marginBottom: "1rem" }}
          >
            ← Back to POIs
          </button>
          
          <div className="page-header">
            <div>
              <h1 className="page-title">{poi.name}</h1>
              <div className="page-subtitle">
                Code: {poi.code}
              </div>
            </div>
          </div>
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

        {/* Connections Card */}
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <div>
              <h2 className="card-title">Connections</h2>
              <div className="card-subtitle">
                Manage travel times to other locations
              </div>
            </div>
            {!showEdgeForm && (
              <button 
                onClick={handleCreateNew} 
                className="primary-button"
              >
                Create New Connection
              </button>
            )}
          </div>

          {showEdgeForm && (
            <div style={{ 
              background: "var(--bg-subtle)", 
              padding: "1.5rem", 
              borderRadius: "8px", 
              marginBottom: "1.5rem" 
            }}>
              <h3 style={{ marginBottom: "1rem", fontSize: "1.1rem" }}>
                {editingEdge ? "Edit Connection" : "Create New Connection"}
              </h3>
              <form onSubmit={handleEdgeSubmit}>
                <div className="form-field">
                  <label className="form-label">From POI</label>
                  <select
                    value={edgeFormData.from_poi_id}
                    onChange={(e) => setEdgeFormData({ ...edgeFormData, from_poi_id: parseInt(e.target.value) })}
                    className="form-select"
                    required
                  >
                    {allPois.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-field">
                  <label className="form-label">To POI</label>
                  <select
                    value={edgeFormData.to_poi_id}
                    onChange={(e) => setEdgeFormData({ ...edgeFormData, to_poi_id: parseInt(e.target.value) })}
                    className="form-select"
                    required
                  >
                    {allPois.filter(p => p.id !== edgeFormData.from_poi_id).map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-field">
                  <label className="form-label">Travel Time (seconds)</label>
                  <input
                    type="number"
                    value={edgeFormData.travel_time_s}
                    onChange={(e) => setEdgeFormData({ ...edgeFormData, travel_time_s: parseInt(e.target.value) })}
                    className="form-number"
                    required
                    min="1"
                  />
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                    ≈ {Math.round(edgeFormData.travel_time_s / 60)} minutes
                  </div>
                </div>
                <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
                  <button type="submit" disabled={edgeSubmitting} className="primary-button">
                    {edgeSubmitting ? "Saving..." : (editingEdge ? "Update" : "Create")}
                  </button>
                  <button type="button" onClick={handleCancelEdge} className="secondary-button">
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {edges.length === 0 ? (
            <div style={{ 
              textAlign: "center", 
              padding: "2rem", 
              color: "var(--text-muted)" 
            }}>
              No connections yet. Create one to connect this location to others.
            </div>
          ) : (
            <table className="table-lite">
              <thead>
                <tr>
                  <th>Connected To</th>
                  <th>Travel Time</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {edges.map(edge => {
                  const otherPoi = getOtherPoi(edge);
                  return (
                    <tr key={edge.id}>
                      <td>
                        <strong>{otherPoi.name}</strong>
                        <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                          {otherPoi.code}
                        </div>
                      </td>
                      <td>
                        {edge.travel_time_s}s
                        <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                          ≈ {Math.round(edge.travel_time_s / 60)} minutes
                        </div>
                      </td>
                      <td>
                        <button 
                          onClick={() => handleEditEdge(edge)} 
                          className="secondary-button"
                          style={{ marginRight: "0.5rem", padding: "0.25rem 0.75rem", fontSize: "0.85rem" }}
                        >
                          Edit
                        </button>
                        <button 
                          onClick={() => handleDeleteEdge(edge)} 
                          className="secondary-button"
                          style={{ padding: "0.25rem 0.75rem", fontSize: "0.85rem" }}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default POIDetailPage;

