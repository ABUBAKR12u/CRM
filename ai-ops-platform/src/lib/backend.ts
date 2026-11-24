import "server-only";

/**
 * Python backend (FastAPI) bilan yagona aloqa nuqtasi. Faqat serverda ishlaydi: token brauzerga
 * chiqmaydi, u Next.js sessiya cookie'si ichida saqlanadi. Xato kodlari backenddan o'zgarishsiz
 * keladi va klientda `apiErrors.<kod>` orqali tarjima qilinadi.
 */
const BACKEND_URL = (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(
  /\/+$/,
  "",
);

export type BackendResult<T> =
  | { ok: true; value: T }
  | { ok: false; error: string; status: number; retryAfter?: string };

type Options = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  token?: string;
  json?: unknown;
  form?: Record<string, string>;
  /** Asl foydalanuvchi IP'si: backend login limitini shu bo'yicha hisoblaydi. */
  ip?: string | null;
};

export async function backend<T>(
  path: string,
  { method = "GET", token, json, form, ip }: Options = {},
): Promise<BackendResult<T>> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (ip) headers["X-Forwarded-For"] = ip;

  let body: string | undefined;
  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  } else if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    body = new URLSearchParams(form).toString();
  }

  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}${path}`, {
      method,
      headers,
      body,
      cache: "no-store",
    });
  } catch {
    return { ok: false, error: "unavailable", status: 503 };
  }

  const data = (await response.json().catch(() => null)) as unknown;
  if (response.ok) return { ok: true, value: data as T };

  // FastAPI validatsiya xatosi (422) klient uchun bitta "validation" kodi.
  const detail = (data as { detail?: unknown } | null)?.detail;
  return {
    ok: false,
    error: response.status === 422 || typeof detail !== "string" ? "validation" : detail,
    status: response.status === 422 ? 400 : response.status,
    retryAfter: response.headers.get("retry-after") ?? undefined,
  };
}
