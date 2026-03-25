import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale } from "./hub-gate";

registerHubGate();

test.describe("Persona 4 — Brain", () => {
  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test("memory page, edit page list and save", async ({ page }) => {
    await page.goto("/memory/");
    await expect(page.locator(".settings-page-header h1")).toContainText(/Brain/i);
    await expect(page.locator("#quartz-frame")).toBeVisible();
    await expect(page.locator("#brain-memory-select")).toBeVisible();

    await page.goto("/memory/edit");
    await expect(page.locator(".settings-page-header h1")).toContainText(/Edit Brain/i);
    await expect(page.locator(".settings-page-header h1")).toContainText(/Clawvis/);
    await expect(page.locator("#memory-file-select")).toBeVisible();
    const optCount = await page.locator("#memory-file-select option").count();
    test.skip(optCount === 0, "No memory/project .md files — seed instance memory first.");
    await page.locator("#memory-file-select").selectOption({ index: 0 });
    const before = await page.locator("#memory-content").inputValue();
    await page.locator("#memory-content").fill(`${before}\n\n<!-- e2e-playwright -->\n`);
    const dialogDone = page.waitForEvent("dialog").then((d) => d.accept());
    await page.locator("#memory-save").click();
    await dialogDone;
  });

  test("kanban filter smoke after brain routes", async ({ page }) => {
    await page.goto("/kanban/");
    await expect(page.locator("#kanban-board")).toBeVisible();
  });

  test("dependency graph view on Kanban", async ({ page }) => {
    await page.goto("/kanban/");
    await page.locator("#view-graph").click();
    await expect(page.locator("#kanban-graph-wrap")).toBeVisible();
    await expect(page.locator("#kanban-graph")).toBeVisible();
  });
});
