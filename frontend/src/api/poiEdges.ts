import { apiFetch } from "./client";
import { POI } from "./pois";

export interface POIEdge {
  id: number;
  from_poi: POI;
  to_poi: POI;
  travel_time_s: number;
}

export interface POIEdgeCreatePayload {
  from_poi_id: number;
  to_poi_id: number;
  travel_time_s: number;
}

export interface POIEdgeUpdatePayload {
  from_poi_id?: number;
  to_poi_id?: number;
  travel_time_s?: number;
}

export async function fetchPOIEdges(poiId?: number): Promise<POIEdge[]> {
  const url = poiId 
    ? `/manager/poi-edges/?poi_id=${poiId}` 
    : "/manager/poi-edges/";
  return apiFetch(url);
}

export async function createPOIEdge(payload: POIEdgeCreatePayload): Promise<POIEdge> {
  return apiFetch("/manager/poi-edges/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updatePOIEdge(id: number, payload: POIEdgeUpdatePayload): Promise<POIEdge> {
  return apiFetch(`/manager/poi-edges/${id}/`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deletePOIEdge(id: number): Promise<void> {
  await apiFetch(`/manager/poi-edges/${id}/`, {
    method: "DELETE",
  });
}

