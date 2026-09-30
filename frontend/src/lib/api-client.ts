const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";
const cleanUrl = rawUrl.trim().replace(/\/+$/, "");
export const API_BASE_URL = cleanUrl.endsWith("/api")
  ? cleanUrl
  : `${cleanUrl}/api`;

function getAuthHeaders(isFormData = false): HeadersInit {
  const headers: Record<string, string> = {};
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  if (typeof window !== "undefined") {
    const token = localStorage.getItem("karmayogi_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  return headers;
}

export async function apiGet<T>(endpoint: string): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
  const response = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `GET request to ${endpoint} failed (${response.status})`);
  }

  return response.json();
}

export async function apiPost<T>(endpoint: string, body?: any): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
  const response = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `POST request to ${endpoint} failed (${response.status})`);
  }

  return response.json();
}

export async function apiPut<T>(endpoint: string, body?: any): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
  const response = await fetch(url, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `PUT request to ${endpoint} failed (${response.status})`);
  }

  return response.json();
}

export async function apiUpload<T>(endpoint: string, formData: FormData): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
  const response = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(true),
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload request to ${endpoint} failed (${response.status})`);
  }

  return response.json();
}
