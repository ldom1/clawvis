import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale } from "./hub-gate";

registerHubGate();

test.describe("Persona 5 — Settings", () => {
  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test("workspace save, instances UI, runtime link, back to hub", async ({ page }) => {
    await page.goto("/settings/");
    await expect(page.locator(".settings-page-header h1")).toContainText(/Settings/i);
    await page.locator("#projects-root").fill("/tmp/clawvis-e2e-projects");
    await page.locator("#save-settings").click();
    await expect(page.locator("#settings-save-feedback.test-result.ok")).toContainText(/Workspace saved/i, {
      timeout: 15000,
    });

    await expect(page.locator("#instances-multi")).toBeVisible();
    await page.locator("#refresh-instances").click();
    await expect(page.locator("#instances-multi option:not([disabled])").first()).toBeVisible({
      timeout: 15000,
    });
    const firstPath = await page.locator("#instances-multi option:not([disabled])").first().getAttribute("value");
    if (firstPath) {
      await page.locator("#instances-multi").selectOption([firstPath]);
      await page.locator("#instances-link-selected").click();
    }

    const runtimeLink = page.locator('a[href="/setup/runtime/"]');
    await expect(
      runtimeLink.filter({ hasText: /Configure|configurer/i }).first(),
    ).toBeVisible();
    await expect(page.locator("#ai-wizard-overlay")).toHaveCount(0);

    await page.locator(".back-btn").click();
    await expect.poll(() => new URL(page.url()).pathname).toBe("/");
  });
});
