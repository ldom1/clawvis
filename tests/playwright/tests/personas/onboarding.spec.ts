import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale, frLocale } from "./hub-gate";

registerHubGate();

test.describe("Persona 1 — onboarding (EN)", () => {
  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test("home, setup runtime wizard — choose agent and confirm", async ({ page, request }) => {
    await page.route("**/api/hub/agent/config", async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ primary_provider: null }),
      });
    });
    await page.route("**/api/hub/setup/provider", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true, PRIMARY_AI_PROVIDER: "claude" }),
      });
    });

    const home = await request.get("/");
    expect(home.ok()).toBeTruthy();
    await page.goto("/");
    await expect(page.locator(".header-logo")).toBeVisible();
    await expect(page.getByRole("heading", { name: /Clawvis/i }).first()).toBeVisible();
    await expect(page.locator("#ai-runtime-status")).toContainText(/Not configured/i);
    await expect(page.locator("#system-card")).toBeVisible();
    await expect(page.locator("#cpu-percent")).toBeVisible();
    await expect(page.locator("#kpi-projects")).toBeVisible();
    await expect(page.getByText("Core tools", { exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: /Kanban/i }).first()).toBeVisible();

    await page.locator("#ai-runtime-cta").click();
    await expect(page).toHaveURL(/\/setup\/runtime\/?/);
    await expect(page.locator(".settings-page-header h1")).toContainText(/Setup/i);
    await expect(page.locator(".settings-page-header h1")).toContainText(/Clawvis/);

    await expect(page.locator("[data-provider]")).toHaveCount(2);
    await expect(page.getByRole("button", { name: /Claude Code/i }).first()).toBeVisible();
    const confirm = page.locator("#setup-confirm");
    await expect(confirm).toBeDisabled();
    await page.locator('[data-provider="claude"]').click();
    await expect(confirm).toBeEnabled();
    await confirm.click();
    await expect(page).toHaveURL(/\//);
  });
});

test.describe("Persona 1 — home banner (FR)", () => {
  test.beforeEach(async ({ page }) => {
    await frLocale(page);
  });

  test("AI runtime badge in French", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("#ai-runtime-status")).toContainText(/Non configuré/i);
  });
});
