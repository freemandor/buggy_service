const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

let authToken: string | null = localStorage.getItem("authToken");

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem("authToken", token);
  } else {
    localStorage.removeItem("authToken");
  }
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (authToken) {
    (headers as any)["Authorization"] = `Bearer ${authToken}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  let data: any = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const message = (data && (data.detail || data.error || data.message)) || res.statusText;
    const err: any = new Error(message);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}

