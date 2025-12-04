import { apiFetch, setAuthToken } from "./client";

export interface User {
  username: string;
  role: "DRIVER" | "DISPATCHER" | "MANAGER";
}

export async function login(username: string, password: string): Promise<User> {
  const tokens = await apiFetch("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

  const access = tokens.access;
  setAuthToken(access);

  const user = await apiFetch("/auth/me/");
  return user as User;
}

export async function getCurrentUser(): Promise<User> {
  return apiFetch("/auth/me/");
}

export function logout() {
  setAuthToken(null);
}

