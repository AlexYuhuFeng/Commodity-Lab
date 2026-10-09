import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e", workers: 1, timeout: 30000,
  use: { baseURL: "http://127.0.0.1:5173", viewport: { width: 1440, height: 1000 },
    launchOptions: process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
    trace: "retain-on-failure" },
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.01 } },
  webServer: [
    { command: `${process.env.COMMODITY_TEST_PYTHON || "python"} -m uvicorn tauri.backend.main:app --host 127.0.0.1 --port 8000`, cwd: "../..", url: "http://127.0.0.1:8000/api/health", reuseExistingServer: !process.env.CI,
      env: { COMMODITY_LAB_TRAINING_DB: "/tmp/commodity-lab-e2e.sqlite", COMMODITY_LAB_DISABLE_LOCAL_AI_SETTINGS: "1", HAINENG_API_KEY: "", DEEPSEEK_API_KEY: "" } },
    { command: "npm run dev -- --host 127.0.0.1", url: "http://127.0.0.1:5173", reuseExistingServer: !process.env.CI }
  ]
});
