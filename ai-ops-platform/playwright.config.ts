import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

const PORT = 3100;
const BACKEND_PORT = 8100;
// Backend venv'idagi python (masalan, ../backend/.venv/Scripts/python.exe) yoki PATH'dagisi.
const PYTHON = process.env.E2E_PYTHON ?? "python";
const BACKEND_DIR = process.env.E2E_BACKEND_DIR ?? path.join(__dirname, "..", "backend");

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        // Ixtiyoriy: tayyor Chromium bo'lsa, shu yo'l ishlatiladi (CI/sandbox uchun).
        launchOptions: process.env.PW_CHROMIUM_PATH
          ? { executablePath: process.env.PW_CHROMIUM_PATH }
          : {},
      },
    },
  ],
  webServer: [
    {
      // Har ishga tushishda alohida e2e bazasi seed holatiga qaytariladi.
      command: [
        `${PYTHON} -m alembic upgrade head`,
        `${PYTHON} -m app.utils.seed --reset`,
        `${PYTHON} -m uvicorn app.main:app --port ${BACKEND_PORT}`,
      ].join(" && "),
      cwd: BACKEND_DIR,
      url: `http://127.0.0.1:${BACKEND_PORT}/health/ready`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        ENVIRONMENT: "development",
        DB_NAME: process.env.E2E_DB_NAME ?? "erpcrm_e2e",
      },
    },
    {
      command: `npx next start -p ${PORT}`,
      url: `http://localhost:${PORT}/uz/login`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        SESSION_SECRET: "e2e-test-secret-with-more-than-thirty-two-characters",
        BACKEND_URL: `http://127.0.0.1:${BACKEND_PORT}`,
        SHOW_DEMO_ACCOUNTS: "true",
      },
    },
  ],
});
