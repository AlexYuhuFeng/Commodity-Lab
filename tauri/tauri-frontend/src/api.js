import { invoke } from "@tauri-apps/api/tauri";
import { listen } from "@tauri-apps/api/event";

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

function decodeSseBlock(block) {
  let event = "message";
  const dataLines = [];
  block.split("\n").forEach((line) => {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
  });
  if (!dataLines.length) return null;
  const raw = dataLines.join("\n");
  try {
    return { event, data: JSON.parse(raw) };
  } catch {
    return { event, data: { text: raw } };
  }
}

async function streamViaHttp(path, body, onEvent) {
  const baseUrl = import.meta.env.VITE_COMMODITY_LAB_BACKEND ?? DEFAULT_BACKEND_BASE_URL;
  const response = await fetch(`${baseUrl}${normalizePath(path)}`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "text/event-stream" },
    body: JSON.stringify(body ?? {})
  });
  if (!response.ok || !response.body) {
    const detail = await response.text().catch(() => response.statusText);
    throw new Error(detail || response.statusText);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let streamError = null;
  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done }).replace(/\r\n/g, "\n");
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    blocks.forEach((block) => {
      const decoded = decodeSseBlock(block);
      if (!decoded) return;
      onEvent(decoded.event, decoded.data);
      if (decoded.event === "error") streamError = new Error(decoded.data?.message ?? "AI stream failed");
    });
    if (done) break;
  }
  const tail = decodeSseBlock(buffer);
  if (tail) {
    onEvent(tail.event, tail.data);
    if (tail.event === "error") streamError = new Error(tail.data?.message ?? "AI stream failed");
  }
  if (streamError) throw streamError;
}

export async function backendStreamRequest(path, body, onEvent) {
  if (typeof window !== "undefined" && typeof window.__COMMODITY_LAB_BACKEND_STREAM__ === "function") {
    return window.__COMMODITY_LAB_BACKEND_STREAM__(normalizePath(path), body, onEvent);
  }

  if (typeof window !== "undefined" && typeof window.__COMMODITY_LAB_BACKEND__ === "function") {
    const payload = await backendRequest("POST", normalizePath(path).replace(/\/stream$/, ""), body);
    onEvent("case", payload);
    onEvent("done", { ok: true });
    return;
  }

  if (
    typeof window !== "undefined" &&
    (window.__TAURI__ || window.__TAURI_IPC__ || window.__TAURI_INTERNALS__)
  ) {
    const requestId = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    let streamError = null;
    const unlisten = await listen("backend-stream-event", ({ payload }) => {
      if (payload?.request_id !== requestId) return;
      onEvent(payload.event, payload.data);
      if (payload.event === "error") streamError = new Error(payload.data?.message ?? "AI stream failed");
    });
    try {
      await invoke("backend_stream", { path: normalizePath(path), body: body ?? {}, requestId });
      if (streamError) throw streamError;
      return;
    } finally {
      unlisten();
    }
  }

  return streamViaHttp(path, body, onEvent);
}
