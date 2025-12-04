import { apiFetch } from "./client";
import type { POI } from "./buggies";

export interface DriverRouteStop {
  id: number;
  stop_type: "PICKUP" | "DROPOFF";
  status: "PLANNED" | "ON_ROUTE" | "COMPLETED";
  sequence_index: number;
  poi: POI;
  ride_request_code: string;
  num_guests: number;
}

export async function fetchDriverRoute(): Promise<DriverRouteStop[]> {
  return apiFetch("/driver/my-route/");
}

export async function driverStartStop(stopId: number): Promise<void> {
  await apiFetch(`/driver/stops/${stopId}/start/`, { method: "POST" });
}

export async function driverCompleteStop(stopId: number): Promise<void> {
  await apiFetch(`/driver/stops/${stopId}/complete/`, { method: "POST" });
}

