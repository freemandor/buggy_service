import { apiFetch } from "./client";

export interface MetricsSummary {
  date: string;
  total_rides: number;
  avg_wait_time_s: number | null;
}

export async function fetchMetricsSummary(): Promise<MetricsSummary> {
  return apiFetch("/metrics/summary/");
}

