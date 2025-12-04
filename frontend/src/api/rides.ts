import { apiFetch } from "./client";
import type { Buggy, POI } from "./buggies";

export interface RideRequest {
  id: number;
  public_code: string;
  pickup_poi: POI;
  dropoff_poi: POI;
  num_guests: number;
  room_number: string;
  guest_name: string;
  status: string;
  assigned_buggy: Buggy | null;
  requested_at: string;
  assigned_at: string | null;
}

export interface CreateRidePayload {
  pickup_poi_code: string;
  dropoff_poi_code: string;
  num_guests: number;
  room_number: string;
  guest_name: string;
}

export interface RideWithAssignmentResponse {
  ride: RideRequest;
  assigned_buggy: Buggy;
}

export async function fetchRides(): Promise<RideRequest[]> {
  return apiFetch("/rides/");
}

export async function createRideAndAssign(payload: CreateRidePayload): Promise<RideWithAssignmentResponse> {
  return apiFetch("/rides/create-and-assign/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

