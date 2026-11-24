import { SignJWT, jwtVerify } from "jose";
import { isRole, type Role } from "./roles";

/**
 * JWT imzolash/tekshirish. Proxy (edge) va server ikkalasida ishlaydi.
 * Cookie bilan ishlash lib/auth/session.ts da (server-only).
 * `token` — backend (FastAPI) access tokeni; u faqat httpOnly cookie ichida yuradi.
 */
export const SESSION_COOKIE = "aiops_session";
export const SESSION_TTL_SECONDS = 60 * 60 * 8; // 8 soat, backend ACCESS_TOKEN_MINUTES bilan bir xil

export type SessionPayload = {
  sub: string;
  role: Role;
  name: string;
  email: string;
  dept: string;
  token: string;
};

const ISSUER = "ai-ops-platform";
const DEV_FALLBACK_SECRET =
  "dev-only-insecure-secret-do-not-use-in-production-0123456789";

function getSecret(): Uint8Array {
  const secret = process.env.SESSION_SECRET;
  if (secret && secret.length >= 32) return new TextEncoder().encode(secret);
  if (process.env.NODE_ENV === "production") {
    throw new Error("SESSION_SECRET kamida 32 belgidan iborat bo'lishi shart.");
  }
  return new TextEncoder().encode(DEV_FALLBACK_SECRET);
}

export async function signSession(payload: SessionPayload): Promise<string> {
  return new SignJWT({
    role: payload.role,
    name: payload.name,
    email: payload.email,
    dept: payload.dept,
    token: payload.token,
    typ: "session",
  })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(payload.sub)
    .setIssuer(ISSUER)
    .setIssuedAt()
    .setExpirationTime(`${SESSION_TTL_SECONDS}s`)
    .sign(getSecret());
}

export async function verifySession(
  token: string | undefined,
): Promise<SessionPayload | null> {
  if (!token) return null;
  try {
    const { payload } = await jwtVerify(token, getSecret(), {
      issuer: ISSUER,
      algorithms: ["HS256"],
    });
    if (payload.typ !== "session") return null;
    const {
      sub,
      role,
      name,
      email,
      dept,
      token: backendToken,
    } = payload as Record<string, unknown>;
    if (
      typeof sub !== "string" ||
      !isRole(role) ||
      typeof name !== "string" ||
      typeof email !== "string" ||
      typeof dept !== "string" ||
      typeof backendToken !== "string"
    ) {
      return null;
    }
    return { sub, role, name, email, dept, token: backendToken };
  } catch {
    return null;
  }
}
