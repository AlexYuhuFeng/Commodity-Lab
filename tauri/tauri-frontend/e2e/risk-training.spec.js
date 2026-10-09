import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
// Normalize test typography with a pinned OFL font, independent of system fonts.
const fontCss = readFileSync("node_modules/@fontsource/noto-sans-sc/400.css", "utf8")
  .replaceAll("./files/", "/node_modules/@fontsource/noto-sans-sc/files/");
async function openLab(page, locale = "en", theme = "dark") {
  await page.addInitScript(({ locale, theme }) => {
    localStorage.setItem("commodity-lab-locale", locale);
    localStorage.setItem("commodity-lab-theme", theme);
    localStorage.setItem("commodity-lab-guide-complete", "1");
    localStorage.removeItem("commodity-lab-risk-session-v1");
  }, { locale, theme });
  await page.goto("/");
  await page.getByRole("button", { name: locale === "zh" ? "风险实验室" : "Risk Lab", exact: true }).click();
  await expect(page.locator(".risk-lab")).toBeVisible();
  await page.addStyleTag({ content: fontCss + '\n.cl-app-shell, .cl-app-shell * { font-family: "Noto Sans SC", sans-serif !important; }' });
  await page.evaluate(async () => { await document.fonts.ready; });
}
async function fill(page, target) {
  await page.getByLabel("Target total long swap position (MWh)").fill(target);
  await page.getByLabel("Which commercial risk are you managing?").selectOption("rising_purchase_cost");
  await page.getByLabel("What remains after a TTF hedge?").selectOption("basis_remains");
  await page.getByLabel("What must the risk manager plan for?").selectOption("collateral_needed");
  await page.getByLabel("Commercial rationale").fill("Hedge rising procurement cost while retaining basis exposure and a collateral reserve.");
}
async function noOverflow(page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
}

test("real backend gas journey, blocked proposal, resize, settlement and resume", async ({ page }) => {
  await openLab(page);
  await page.locator(".cl-content-shell").evaluate(el => { el.scrollTop = 0; });
  await expect(page).toHaveScreenshot("gas-setup-en-dark.png");
  await page.getByRole("button", { name: "Start scenario", exact: true }).click();
  await expect(page.getByText("Decision checkpoint 1 / 2")).toBeVisible();
  await page.locator(".cl-content-shell").evaluate(el => { el.scrollTop = 0; });
  await expect(page).toHaveScreenshot("gas-decision-en-dark.png");
  await fill(page, "9000");
  await page.getByRole("button", { name: "Submit decision and reveal next checkpoint" }).click();
  await expect(page.getByText("Proposal blocked — revise and resubmit")).toBeVisible();
  await expect(page.getByText("Decision checkpoint 1 / 2")).toBeVisible();
  await fill(page, "8000");
  await page.getByRole("button", { name: "Submit decision and reveal next checkpoint" }).click();
  await expect(page.getByText("Decision checkpoint 2 / 2")).toBeVisible();
  await expect(page.getByText(/Existing position breaches/)).toBeVisible();
  await expect(page.locator(".risk-lab")).not.toContainText("2026-11-30");
  await fill(page, "6400");
  await page.getByRole("button", { name: "Submit decision and reveal next checkpoint" }).click();
  await expect(page.getByText("Settlement review", { exact: true })).toBeVisible();
  await expect(page.getByText("€368,000.00", { exact: true })).toBeVisible();
  await expect(page.getByText("Trading margin before other costs", { exact: true })).toBeVisible();
  await expect(page.locator(".risk-lab")).toContainText("€112,000.00");
  await page.getByRole("button", { name: "Ask the coach" }).click();
  await expect(page.getByRole("heading", { name: "Offline coaching" })).toBeVisible();
  await page.locator(".cl-content-shell").evaluate(el => { el.scrollTop = 0; });
  await page.getByRole("heading", { name: "Financial outcome", exact: true }).scrollIntoViewIfNeeded();
  await expect(page).toHaveScreenshot("gas-settlement-en-dark.png");
  await noOverflow(page);
  // Reload without initialization script removing the saved id.
  const id = await page.evaluate(() => localStorage.getItem("commodity-lab-risk-session-v1"));
  await page.reload();
  await page.evaluate(id => localStorage.setItem("commodity-lab-risk-session-v1", id), id);
  await page.getByRole("button", { name: "Risk Lab", exact: true }).click();
  await expect(page.getByText("Settlement review", { exact: true })).toBeVisible();
});

test("Chinese mobile setup and decision are readable and keyboard accessible", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await openLab(page, "zh", "light");
  await expect(page.getByRole("heading", { name: "欧洲天然气风险实验室" })).toBeVisible();
  await noOverflow(page);
  await page.locator(".cl-content-shell").evaluate(el => { el.scrollTop = 0; });
  await expect(page).toHaveScreenshot("gas-setup-zh-mobile-light.png");
  await page.getByRole("button", { name: "开始情景", exact: true }).click();
  await expect(page.getByText("决策时点 1 / 2")).toBeVisible();
  await noOverflow(page);
  await page.locator(".cl-content-shell").evaluate(el => { el.scrollTop = 0; });
  await expect(page).toHaveScreenshot("gas-decision-zh-mobile-light.png");
  await page.getByLabel("目标掉期多头总量（MWh）").focus();
  await expect(page.getByLabel("目标掉期多头总量（MWh）")).toBeFocused();
  await expect(page).toHaveScreenshot("gas-form-zh-mobile-light.png");
  for (const [target, checkpoint] of [["8000", 2], ["6400", null]]) {
    await page.getByLabel("目标掉期多头总量（MWh）").fill(target);
    await page.getByLabel("你在管理哪类商业风险？").selectOption("rising_purchase_cost");
    await page.getByLabel("TTF套保后仍有哪些风险？").selectOption("basis_remains");
    await page.getByLabel("风险经理需要规划什么？").selectOption("collateral_needed");
    await page.getByLabel("商业理由", { exact: true }).fill("通过多头掉期管理采购成本上涨风险，同时保留基差敞口并准备足够的抵押资金。");
    await page.getByRole("button", { name: "提交决策并揭示下一时点" }).click();
    await expect(page.getByText(checkpoint ? "决策时点 2 / 2" : "结算复盘", { exact: true })).toBeVisible();
  }
  await noOverflow(page);
});
