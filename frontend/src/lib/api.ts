const API_BASE = "http://localhost:8000";
const TOKEN_KEY = "omni_copilot_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function extractError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) return data.detail.map((d: { msg?: string }) => d.msg).join(", ");
    if (typeof data?.message === "string") return data.message;
    return res.statusText || `Request failed (${res.status})`;
  } catch {
    return res.statusText || `Request failed (${res.status})`;
  }
}

export async function signup(username: string, password: string): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/api/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error(await extractError(res));
  return res.json();
}

export async function login(username: string, password: string): Promise<{ access_token: string; token_type: string }> {
  const body = new URLSearchParams();
  body.append("username", username);
  body.append("password", password);

  const res = await fetch(`${API_BASE}/api/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });
  if (!res.ok) throw new Error(await extractError(res));
  const data = await res.json();
  setToken(data.access_token);
  return data;
}

export async function chat(message: string): Promise<{ response: string }> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated");
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error(await extractError(res));
  return res.json();
}

export async function ingest(directoryPath: string): Promise<{ status: string }> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated");
  const res = await fetch(`${API_BASE}/api/ingest`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ directory_path: directoryPath }),
  });
  if (!res.ok) throw new Error(await extractError(res));
  return res.json();
}
