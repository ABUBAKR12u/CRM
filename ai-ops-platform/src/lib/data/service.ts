import "server-only";
import { backend, type BackendResult } from "@/lib/backend";
import type { Role } from "@/lib/auth/roles";
import type {
  TaskCreateInput,
  TaskStatus,
  UserCreateOutput,
  UserUpdateInput,
} from "@/lib/schemas/directory";
import type {
  Actor,
  NotificationFeed,
  NotificationItem,
  Person,
  Stats,
  TaskView,
  TeamRow,
} from "./types";

/**
 * Biznes qoidalari va ruxsatlar backendda (FastAPI). Bu fayl faqat adapter: so'rov yuboradi va
 * backend javobini (son ID'lar, null) UI turlariga (satr ID'lar) aylantiradi.
 */
export type Result<T> =
  { ok: true; value: T } | { ok: false; error: string; status: number };

type Id = number | string;
type BackendUser = Omit<Person, "id" | "managerId"> & { id: Id; managerId: Id | null };
type BackendTask = Omit<TaskView, "id" | "assigneeId" | "creatorId" | "creatorName"> & {
  id: Id;
  assigneeId: Id;
  creatorId: Id | null;
  creatorName: string | null;
};
type BackendNotification = Omit<NotificationItem, "id"> & { id: Id };

const str = (value: Id | null) => (value === null ? null : String(value));

function toPerson(user: BackendUser): Person {
  return { ...user, id: String(user.id), managerId: str(user.managerId) };
}

function toTask(task: BackendTask): TaskView {
  return {
    ...task,
    id: String(task.id),
    assigneeId: String(task.assigneeId),
    creatorId: str(task.creatorId),
    creatorName: task.creatorName ?? "-",
  };
}

function map<T, U>(result: BackendResult<T>, convert: (value: T) => U): Result<U> {
  return result.ok ? { ok: true, value: convert(result.value) } : result;
}

/** Sahifalar uchun: xato bo'lsa error.tsx chegarasi ko'rsatiladi. */
export function orThrow<T>(result: Result<T>): T {
  if (!result.ok) throw new Error(`backend: ${result.error} (${result.status})`);
  return result.value;
}

// ---------------------------------------------------------------- sessiya

/** Token egasini oladi. Token yaroqsiz yoki hisob bloklangan bo'lsa null. */
export async function findActor(token: string | undefined): Promise<Actor | null> {
  if (!token) return null;
  const result = await backend<BackendUser>("/auth/me", { token });
  if (result.ok) return { ...toPerson(result.value), token };
  if (result.status === 401 || result.status === 403) return null;
  throw new Error(`backend: ${result.error} (${result.status})`);
}

// ---------------------------------------------------------------- foydalanuvchilar

export async function listPeople(actor: Actor): Promise<Result<Person[]>> {
  const result = await backend<BackendUser[]>("/users/", { token: actor.token });
  return map(result, (users) => users.map(toPerson));
}

export async function createUser(
  actor: Actor,
  input: UserCreateOutput,
): Promise<Result<Person>> {
  const result = await backend<BackendUser>("/users/", {
    method: "POST",
    token: actor.token,
    json: input,
  });
  return map(result, toPerson);
}

export async function updateUser(
  actor: Actor,
  id: string,
  patch: UserUpdateInput,
): Promise<Result<Person>> {
  const result = await backend<BackendUser>(`/users/${encodeURIComponent(id)}`, {
    method: "PATCH",
    token: actor.token,
    json: patch,
  });
  return map(result, toPerson);
}

export async function deleteUser(actor: Actor, id: string): Promise<Result<null>> {
  const result = await backend(`/users/${encodeURIComponent(id)}`, {
    method: "DELETE",
    token: actor.token,
  });
  return map(result, () => null);
}

// ---------------------------------------------------------------- vazifalar

export async function listTasks(actor: Actor): Promise<Result<TaskView[]>> {
  const result = await backend<BackendTask[]>("/tasks/", { token: actor.token });
  return map(result, (tasks) => tasks.map(toTask));
}

/** Vazifa tayinlash mumkin bo'lgan odamlar. */
export async function assignablePeople(
  actor: Actor,
): Promise<Result<{ id: string; name: string }[]>> {
  const result = await backend<{ id: Id; name: string }[]>("/tasks/assignees", {
    token: actor.token,
  });
  return map(result, (people) =>
    people.map(({ id, name }) => ({ id: String(id), name })),
  );
}

export async function createTask(
  actor: Actor,
  input: TaskCreateInput,
): Promise<Result<TaskView>> {
  const result = await backend<BackendTask>("/tasks/", {
    method: "POST",
    token: actor.token,
    json: input,
  });
  return map(result, toTask);
}

type TaskPatch =
  Partial<TaskCreateInput> | { status: TaskStatus; note?: string | undefined };

export async function updateTask(
  actor: Actor,
  id: string,
  patch: TaskPatch,
): Promise<Result<TaskView>> {
  const path = `/tasks/${encodeURIComponent(id)}${"status" in patch ? "/status" : ""}`;
  const result = await backend<BackendTask>(path, {
    method: "PATCH",
    token: actor.token,
    json: patch,
  });
  return map(result, toTask);
}

export async function deleteTask(actor: Actor, id: string): Promise<Result<null>> {
  const result = await backend(`/tasks/${encodeURIComponent(id)}`, {
    method: "DELETE",
    token: actor.token,
  });
  return map(result, () => null);
}

// ---------------------------------------------------------------- jamoa, statistika, bildirishnomalar

export async function teamRows(actor: Actor): Promise<Result<TeamRow[]>> {
  const result = await backend<(BackendUser & Omit<TeamRow, keyof Person>)[]>("/team/", {
    token: actor.token,
  });
  return map(result, (rows) => rows.map((row) => ({ ...row, ...toPerson(row) })));
}

export async function statsFor(actor: Actor): Promise<Result<Stats>> {
  return backend<Stats>("/dashboard/stats", { token: actor.token });
}

export async function notificationsFor(actor: Actor): Promise<Result<NotificationFeed>> {
  const result = await backend<{ items: BackendNotification[]; unread: number }>(
    "/notifications/",
    { token: actor.token },
  );
  return map(result, ({ items, unread }) => ({
    unread,
    items: items.map((item) => ({ ...item, id: String(item.id) })),
  }));
}

export async function readNotifications(
  actor: Actor,
  id: string | null,
): Promise<Result<null>> {
  const result = id
    ? await backend(`/notifications/${encodeURIComponent(id)}/read`, {
        method: "PATCH",
        token: actor.token,
      })
    : await backend("/notifications/read", { method: "POST", token: actor.token });
  return map(result, () => null);
}

export function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export type { Role, TaskView, TeamRow };
