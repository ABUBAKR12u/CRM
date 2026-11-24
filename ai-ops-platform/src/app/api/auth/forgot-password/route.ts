import type { NextRequest } from "next/server";
import { forgotSchema } from "@/lib/auth/schemas";
import { backendError, clientIp, jsonOk, readJson } from "@/lib/api/guard";
import { backend } from "@/lib/backend";

/**
 * Backend tiklash havolasini pochtaga yuboradi. Foydalanuvchi mavjudligi oshkor bo'lmaydi:
 * javob har doim bir xil. Production bo'lmagan muhitda backend tokenni ham qaytaradi,
 * shunda havola pochta o'rniga shu yerda ko'rsatiladi.
 */
export async function POST(request: NextRequest) {
  const body = await readJson(request, forgotSchema);
  if (!body.ok) return body.response;
  const { email, locale } = body.data;

  const result = await backend<{ resetToken: string | null }>("/auth/forgot-password", {
    method: "POST",
    json: { email, locale },
    ip: clientIp(request),
  });
  if (!result.ok) return backendError(result);

  const token = result.value.resetToken;
  return jsonOk(
    token
      ? { demoLink: `/${locale}/reset-password?token=${encodeURIComponent(token)}` }
      : {},
  );
}
