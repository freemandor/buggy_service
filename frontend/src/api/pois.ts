import { apiFetch } from "./client";

export interface POI {
  id: number;
  code: string;
  name: string;
}

export async function fetchPOIs(): Promise<POI[]> {
  return apiFetch("/pois/");
}

// Manager CRUD Operations

export interface POICreatePayload {
  code: string;
  name: string;
}

export interface POIUpdatePayload {
  code?: string;
  name?: string;
}

export async function createPOI(payload: POICreatePayload): Promise<POI> {
  return apiFetch("/manager/pois/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updatePOI(id: number, payload: POIUpdatePayload): Promise<POI> {
  return apiFetch(`/manager/pois/${id}/`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deletePOI(id: number): Promise<void> {
  await apiFetch(`/manager/pois/${id}/`, {
    method: "DELETE",
  });
}

