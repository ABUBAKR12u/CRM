import "server-only";
import type { Role } from "@/lib/auth/roles";

/**
 * Backend seed'i (`python -m app.utils.seed`) yaratadigan demo hisoblar. Login sahifasida
 * faqat dev'da yoki SHOW_DEMO_ACCOUNTS=true bo'lganda ko'rsatiladi.
 * Ochiq internetdagi muhitda buni yoqmang: backend seed production'da umuman ishlamaydi.
 */
export const DEMO_ACCOUNTS: ReadonlyArray<{
  role: Role;
  email: string;
  password: string;
}> = [
  { role: "admin", email: "admin@aiops.uz", password: "Admin#2026" },
  { role: "manager", email: "manager@aiops.uz", password: "Manager#2026" },
  { role: "employee", email: "employee@aiops.uz", password: "Employee#2026" },
];

export function showDemoAccounts(): boolean {
  return (
    process.env.NODE_ENV !== "production" || process.env.SHOW_DEMO_ACCOUNTS === "true"
  );
}
