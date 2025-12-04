import { apiFetch } from "./client";

export interface POI {
  id: number;
  code: string;
  name: string;
}

export interface Buggy {
  id: number;
  code: string;
  display_name: string;
  capacity: number;
  status: "ACTIVE" | "INACTIVE";
  current_poi: POI | null;
  driver_id: number | null;
  current_onboard_guests: number;
}

export async function fetchBuggies(): Promise<Buggy[]> {
  return apiFetch("/buggies/");
}

// Manager CRUD Operations

export interface BuggyCreatePayload {
  code: string;
  display_name: string;
  capacity: number;
  status: "ACTIVE" | "INACTIVE";
  driver_id?: number | null;
  current_poi_id?: number | null;
  current_onboard_guests?: number;
}

export interface BuggyUpdatePayload {
  code?: string;
  display_name?: string;
  capacity?: number;
  status?: "ACTIVE" | "INACTIVE";
  driver_id?: number | null;
  current_poi_id?: number | null;
  current_onboard_guests?: number;
}

export async function createBuggy(payload: BuggyCreatePayload): Promise<Buggy> {
  return apiFetch("/manager/buggies/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateBuggy(id: number, payload: BuggyUpdatePayload): Promise<Buggy> {
  return apiFetch(`/manager/buggies/${id}/`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteBuggy(id: number): Promise<void> {
  await apiFetch(`/manager/buggies/${id}/`, {
    method: "DELETE",
  });
}

