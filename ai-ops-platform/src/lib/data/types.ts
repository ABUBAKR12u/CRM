import type { Role } from "@/lib/auth/roles";
import type { Priority, TaskStatus } from "@/lib/schemas/directory";

export type Person = {
  id: string;
  name: string;
  email: string;
  role: Role;
  dept: string;
  managerId: string | null;
  active: boolean;
};

/** Joriy foydalanuvchi: backend tokeni bilan (faqat serverda). */
export type Actor = Person & { token: string };

export type Task = {
  id: string;
  title: string;
  description: string;
  assigneeId: string;
  creatorId: string | null;
  status: TaskStatus;
  priority: Priority;
  /** YYYY-MM-DD */
  due: string;
  /** Rahbar vazifani qaytarganda yozgan izoh. */
  note: string | null;
  updatedAt: string;
};

export type TaskView = Task & {
  assigneeName: string;
  creatorName: string;
  /** Joriy foydalanuvchi bu vazifada nima qila oladi (UI tugmalari uchun). */
  can: { manage: boolean; advance: TaskStatus[] };
};

export type TeamRow = Person & { open: number; review: number; done: number };

export type Stats = {
  users: number;
  teamTasks: number;
  pending: number;
  late: number;
  myTasks: number;
  doneWeek: number;
};

export type NotificationKey =
  | "taskAssigned"
  | "approvalWaiting"
  | "approved"
  | "taskReturned"
  | "deadlineSoon"
  | "taskLate"
  | "newUser"
  | "roleChange"
  | "passwordReset";

export type NotificationItem = {
  id: string;
  key: NotificationKey;
  params: Record<string, string>;
  read: boolean;
  createdAt: string;
};

export type NotificationFeed = { items: NotificationItem[]; unread: number };
