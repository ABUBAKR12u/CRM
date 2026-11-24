import "server-only";
import { NextResponse, type NextRequest } from "next/server";
import type { ZodType } from "zod";

/** Brauzerdan kelgan POST so'rov aynan shu saytdan ekanini tekshiradi (CSRF qo'shimcha qatlami). */
export function isSameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  const host = request.headers.get("host");
  if (origin) {
    try {
      return new URL(origin).host === host;
    } catch {
      return false;
    }
  }
  const site = request.headers.get("sec-fetch-site");
  return site === "same-origin" || site === "none";
}

export function jsonError(
  error: string,
  status: number,
  extra?: Record<string, unknown>,
) {
  return NextResponse.json(
    { ok: false, error, ...extra },
    { status, headers: { "Cache-Control": "no-store" } },
  );
}

export function jsonOk<T extends Record<string, unknown>>(data: T, status = 200) {
  return NextResponse.json(
    { ok: true, ...data },
    { status, headers: { "Cache-Control": "no-store" } },
  );
}

const MAX_BODY_BYTES = 8 * 1024;

export async function readJson<T>(
  request: NextRequest,
  schema: ZodType<T>,
): Promise<{ ok: true; data: T } | { ok: false; response: NextResponse }> {
  if (!isSameOrigin(request)) {
    return { ok: false, response: jsonError("forbidden", 403) };
  }
  if (!request.headers.get("content-type")?.includes("application/json")) {
    return { ok: false, response: jsonError("unsupported", 415) };
  }
  const text = await request.text();
  if (text.length > MAX_BODY_BYTES) {
    return { ok: false, response: jsonError("too_large", 413) };
  }
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch {
    return { ok: false, response: jsonError("validation", 400) };
  }
  const parsed = schema.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, response: jsonError("validation", 400) };
  }
  return { ok: true, data: parsed.data };
}

/** Brauzerning asl IP'si (reverse proxy qo'ygan). Backend login limitini shu bo'yicha sanaydi. */
export function clientIp(request: NextRequest): string | null {
  return request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || null;
}

/** Backend xatosini javobga aylantiradi, limit bo'lsa Retry-After sarlavhasi saqlanadi. */
export function backendError(result: {
  error: string;
  status: number;
  retryAfter?: string;
}) {
  const response = jsonError(result.error, result.status);
  if (result.retryAfter) response.headers.set("Retry-After", result.retryAfter);
  return response;
}
