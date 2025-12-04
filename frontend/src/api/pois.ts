import { apiFetch } from "./client";

export interface POI {
  id: number;
  code: string;
  name: string;
}

export async function fetchPOIs(): Promise<POI[]> {
  return apiFetch("/pois/");
}

