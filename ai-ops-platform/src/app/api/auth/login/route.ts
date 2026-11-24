import type { NextRequest } from "next/server";
import { HOME_SECTION } from "@/lib/auth/roles";
import { loginSchema } from "@/lib/auth/schemas";
import { createSession } from "@/lib/auth/session";
import { backendError, clientIp, jsonOk, readJson } from "@/lib/api/guard";
import { backend } from "@/lib/backend";
import type { Person } from "@/lib/data/types";

type LoginResponse = { access_token: string; user: Omit<Person, "id"> & { id: number } };

/** Parol va limit backendda tekshiriladi: 401 invalid, 403 blocked, 429 rate_limited. */
export async function POST(request: NextRequest) {
  const body = await readJson(request, loginSchema);
  if (!body.ok) return body.response;
  const { email, password, locale } = body.data;

  const result = await backend<LoginResponse>("/auth/login", {
    method: "POST",
    form: { username: email, password },
    ip: clientIp(request),
  });
  if (!result.ok) return backendError(result);

  const { access_token: token, user } = result.value;
  await createSession({
    sub: String(user.id),
    role: user.role,
    name: user.name,
    email: user.email,
    dept: user.dept,
    token,
  });

  return jsonOk({ role: user.role, redirectTo: `/${locale}/${HOME_SECTION}` });
}
