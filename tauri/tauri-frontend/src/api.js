import { invoke } from "@tauri-apps/api/tauri";

const DEFAULT_BACKEND_BASE_URL = "http://127.0.0.1:8000";

function normalizePath(path) {
  return path.startsWith("/") ? path : `/${path}`;
}

async function requestViaTauri(method, path, body) {
  return invoke("backend_request", {
    method,
    path: normalizePath(path),
    body: body ?? null
  });
}

async function requestViaHttp(method, path, body) {
  const baseUrl = import.meta.env.VITE_COMMODITY_LAB_BACKEND ?? DEFAULT_BACKEND_BASE_URL;
  const response = await fetch(`${baseUrl}${normalizePath(path)}`, {
    method,
    headers: body === undefined ? undefined : { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail ?? payload.message ?? response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload;
}

export async function backendRequest(method, path, body) {
  const normalizedMethod = method.toUpperCase();

  if (typeof window !== "undefined" && typeof window.__COMMODITY_LAB_BACKEND__ === "function") {
    return window.__COMMODITY_LAB_BACKEND__(normalizedMethod, normalizePath(path), body);
  }

  if (
    typeof window !== "undefined" &&
    (window.__TAURI__ || window.__TAURI_IPC__ || window.__TAURI_INTERNALS__)
  ) {
    try {
      return await requestViaTauri(normalizedMethod, path, body);
    } catch (error) {
      if (import.meta.env.PROD) {
        throw error;
      }
    }
  }

  return requestViaHttp(normalizedMethod, path, body);
}
