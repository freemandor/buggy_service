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
  current_onboard_guests: number;
}

export async function fetchBuggies(): Promise<Buggy[]> {
  return apiFetch("/buggies/");
}

