import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale, frLocale } from "./hub-gate";

registerHubGate();

test.describe("Persona 1 — onboarding (EN)", () => {
  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test("home, setup runtime wizard through failed connection test", async ({ page, request }) => {
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
    await expect(page.locator("#setup-stepper .setup-step-circle")).toHaveCount(4);

    await expect(page.locator("[data-provider]")).toHaveCount(3);
    await expect(page.getByRole("button", { name: /Claude/i }).first()).toBeVisible();
    const next1 = page.locator("#setup-next-1");
    await expect(next1).toBeDisabled();
    await page.locator('[data-provider="claude"]').click();
    await expect(next1).toBeEnabled();
    await next1.click();

    await expect(page.locator("#step-circle-2.active")).toBeVisible();
    const keyInput = page.locator("#setup-cred-key");
    await expect(keyInput).toBeVisible();
    await expect(keyInput).toHaveAttribute("type", "password");
    const next2 = page.locator("#setup-next-2");
    await expect(next2).toBeDisabled();
    await keyInput.fill("sk-ant-test-key-00000000");
    await expect(next2).toBeEnabled();
    await next2.click();

    await expect(page.locator("#step-circle-3.active")).toBeVisible();
    const next3 = page.locator("#setup-next-3");
    await expect(next3).toBeDisabled();
    await page.locator("#setup-test-btn").click();
    const result = page.locator("#setup-test-result");
    await expect(result).not.toBeEmpty({ timeout: 30000 });
    if (await page.locator("#setup-test-result.err").isVisible()) {
      await expect(next3).toBeDisabled();
    } else {
      await expect(page.locator("#setup-test-result.ok")).toBeVisible();
      await expect(next3).toBeEnabled();
    }
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
