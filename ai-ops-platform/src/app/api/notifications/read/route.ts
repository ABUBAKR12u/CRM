import type { NextRequest } from "next/server";
import { z } from "zod";
import { readJson } from "@/lib/api/guard";
import { respond, withActor } from "@/lib/api/respond";
import { readNotifications } from "@/lib/data/service";

/** `id` berilsa bitta bildirishnoma, berilmasa hammasi o'qilgan deb belgilanadi. */
const readSchema = z.object({ id: z.string().max(40).nullable().optional() });

export async function POST(request: NextRequest) {
  return withActor(
    request,
    async (actor) => {
      const body = await readJson(request, readSchema);
      if (!body.ok) return body.response;
      return respond(await readNotifications(actor, body.data.id ?? null), () => ({}));
    },
    { write: true },
  );
}
