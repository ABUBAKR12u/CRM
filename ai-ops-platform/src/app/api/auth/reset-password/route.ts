import type { NextRequest } from "next/server";
import { resetSchema } from "@/lib/auth/schemas";
import { backendError, clientIp, jsonOk, readJson } from "@/lib/api/guard";
import { backend } from "@/lib/backend";

/** Token bir martalik: parol yangilangach backend uni qayta qabul qilmaydi. */
export async function POST(request: NextRequest) {
  const body = await readJson(request, resetSchema);
  if (!body.ok) return body.response;

  const result = await backend("/auth/reset-password", {
    method: "POST",
    json: body.data,
    ip: clientIp(request),
  });
  return result.ok ? jsonOk({}) : backendError(result);
}
