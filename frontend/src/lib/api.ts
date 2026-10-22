import type { AppConfig, ScanResult, TrackedMessage } from "../types";

const BASE = (import.meta.env.VITE_API_URL as string | undefined) || "/api/v1";

export class ApiError extends Error {
  status: number;
  code?: string;
  reasons?: string[];
  constructor(message: string, status: number, code?: string, reasons?: string[]) {
    super(message);
    this.status = status;
    this.code = code;
    this.reasons = reasons;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(BASE + path, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection and try again.", 0);
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const fieldError = data && typeof data === "object" ? Object.values(data).flat()[0] : undefined;
    const message =
      (data as { detail?: string }).detail ||
      (typeof fieldError === "string" ? fieldError : "") ||
      (res.status === 429 ? "Too many requests. Please wait a bit." : "Something went wrong.");
    throw new ApiError(message, res.status, (data as { code?: string }).code, (data as { reasons?: string[] }).reasons);
  }
  return data as T;
}

const post = <T,>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  config: () => request<AppConfig>("/config/"),
  waitlist: (email: string, turnstile_token: string) => post<{ ok: boolean }>("/waitlist/", { email, turnstile_token }),
  scan: (text: string, turnstile_token: string) => post<ScanResult>("/scan/", { text, turnstile_token }),
  createMessage: (to: string, body: string, turnstile_token: string) =>
    post<TrackedMessage>("/messages/", { to, body, turnstile_token }),
  track: (id: string) => request<TrackedMessage>(`/messages/${encodeURIComponent(id)}/`),
  mockPay: (id: string) => post<TrackedMessage>(`/messages/${encodeURIComponent(id)}/mock-pay/`),
  recipient: (token: string) =>
    request<{ to: string; blocked: boolean }>(`/recipient/${encodeURIComponent(token)}/`),
  block: (token: string) => post<{ blocked: boolean }>(`/recipient/${encodeURIComponent(token)}/block/`),
  report: (token: string, category: string, details: string, turnstile_token: string) =>
    post<{ reported: boolean }>(`/recipient/${encodeURIComponent(token)}/report/`, { category, details, turnstile_token }),
};
