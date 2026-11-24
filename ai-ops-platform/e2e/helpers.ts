import {
  expect,
  type Browser,
  type Page,
  type PlaywrightWorkerArgs,
} from "@playwright/test";

export const ACCOUNTS = {
  admin: { email: "admin@aiops.uz", password: "Admin#2026" },
  manager: { email: "manager@aiops.uz", password: "Manager#2026" },
  employee: { email: "employee@aiops.uz", password: "Employee#2026" },
} as const;

export type RoleName = keyof typeof ACCOUNTS;

/** Login formasini to'ldirib, bosh sahifa ochilishini kutadi. */
export async function loginAs(page: Page, role: RoleName, locale = "uz") {
  const { email, password } = ACCOUNTS[role];
  await page.goto(`/${locale}/login`);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Parol", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Kirish", exact: true }).click();
  // Haqiqiy backend: parol argon2 bilan tekshiriladi, sovuq startda bir necha soniya ketishi mumkin.
  await expect(page).toHaveURL(new RegExp(`/${locale}/dashboard`), { timeout: 15_000 });
}

export const BASE_URL = "http://localhost:3100";

/** Alohida brauzer konteksti (alohida cookie'lar) ochib, shu rol bilan kiradi. */
export async function newSession(browser: Browser, role: RoleName, locale = "uz") {
  const context = await browser.newContext({ baseURL: BASE_URL });
  const page = await context.newPage();
  await loginAs(page, role, locale);
  return { context, page };
}

/** API so'rovlari uchun rol sessiyasi (cookie saqlanadi). */
export async function apiAs(
  playwright: PlaywrightWorkerArgs["playwright"],
  role: RoleName,
) {
  const ctx = await playwright.request.newContext({
    baseURL: BASE_URL,
    extraHTTPHeaders: { Origin: BASE_URL },
  });
  const response = await ctx.post("/api/auth/login", {
    data: { ...ACCOUNTS[role], locale: "uz" },
  });
  expect(response.status()).toBe(200);
  return ctx;
}

/**
 * Seed'dagi odam va vazifalarning ID'larini nom bo'yicha topadi: ID'larni backend beradi,
 * shuning uchun testlar ularni qattiq yozmaydi.
 */
export async function seedIds(playwright: PlaywrightWorkerArgs["playwright"]) {
  const admin = await apiAs(playwright, "admin");
  const { users } = (await (await admin.get("/api/users")).json()) as {
    users: { id: string; name: string }[];
  };
  const { tasks } = (await (await admin.get("/api/tasks")).json()) as {
    tasks: { id: string; title: string }[];
  };
  await admin.dispose();
  const find = <T extends { id: string }>(
    items: T[],
    matches: (item: T) => boolean,
    label: string,
  ) => {
    const found = items.find(matches);
    if (!found) throw new Error(`seed'da topilmadi: ${label}`);
    return found.id;
  };
  return {
    userId: (name: string) => find(users, (u) => u.name === name, name),
    taskId: (title: string) => find(tasks, (t) => t.title === title, title),
  };
}

export async function apiAnonymous(playwright: PlaywrightWorkerArgs["playwright"]) {
  return playwright.request.newContext({
    baseURL: BASE_URL,
    extraHTTPHeaders: { Origin: BASE_URL },
  });
}
