import "server-only";
import { cache } from "react";
import { getSession } from "@/lib/auth/session";
import { findActor } from "@/lib/data/service";
import type { Actor } from "@/lib/data/types";

/**
 * Sessiyadan joriy foydalanuvchini oladi. Rol va holat har safar backenddan olinadi:
 * hisob bloklansa yoki o'chirilsa, sessiya darhol yaroqsiz bo'ladi.
 * `cache` bitta so'rov ichida (layout + sahifa) backendga bir marta murojaat qiladi.
 */
export const currentActor = cache(async (): Promise<Actor | null> => {
  const session = await getSession();
  return findActor(session?.token);
});
