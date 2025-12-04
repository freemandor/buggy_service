import { apiFetch } from "./client";

export interface Driver {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  role: "DRIVER";
}

export interface DriverCreatePayload {
  username: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface DriverUpdatePayload {
  username?: string;
  password?: string;
  first_name?: string;
  last_name?: string;
}

export async function fetchDrivers(): Promise<Driver[]> {
  return apiFetch("/manager/drivers/");
}

export async function createDriver(payload: DriverCreatePayload): Promise<Driver> {
  return apiFetch("/manager/drivers/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateDriver(id: number, payload: DriverUpdatePayload): Promise<Driver> {
  return apiFetch(`/manager/drivers/${id}/`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteDriver(id: number): Promise<void> {
  await apiFetch(`/manager/drivers/${id}/`, {
    method: "DELETE",
  });
}

