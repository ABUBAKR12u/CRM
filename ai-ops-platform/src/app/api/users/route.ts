import type { NextRequest } from "next/server";
import { readJson } from "@/lib/api/guard";
import { respond, withActor } from "@/lib/api/respond";
import { createUser, listPeople } from "@/lib/data/service";
import { userCreateSchema } from "@/lib/schemas/directory";

export async function GET(request: NextRequest) {
  return withActor(request, async (actor) =>
    respond(await listPeople(actor), (users) => ({ users })),
  );
}

export async function POST(request: NextRequest) {
  return withActor(
    request,
    async (actor) => {
      const body = await readJson(request, userCreateSchema);
      if (!body.ok) return body.response;
      return respond(await createUser(actor, body.data), (user) => ({ user }));
    },
    { write: true },
  );
}
