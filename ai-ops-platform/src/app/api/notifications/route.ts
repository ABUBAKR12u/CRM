import type { NextRequest } from "next/server";
import { respond, withActor } from "@/lib/api/respond";
import { notificationsFor } from "@/lib/data/service";

export async function GET(request: NextRequest) {
  return withActor(request, async (actor) =>
    respond(await notificationsFor(actor), (feed) => feed),
  );
}
