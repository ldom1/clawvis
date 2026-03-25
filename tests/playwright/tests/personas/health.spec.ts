import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale } from "./hub-gate";

registerHubGate();

test.describe("Persona 7 — Health", () => {
  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test("active services count and API smoke", async ({ page, request }) => {
    await page.goto("/");
    await expect(page.locator("#active-services-count")).not.toHaveText("…", { timeout: 20000 });
    const countText = await page.locator("#active-services-count").innerText();
    expect(Number.parseInt(countText, 10)).toBeGreaterThanOrEqual(1);
    const hubTitle = await page.locator("#active-services-count").getAttribute("title");
    expect(hubTitle).toBeTruthy();

    const checks: [string, number][] = [
      ["/api/hub/kanban/tasks", 200],
      ["/api/hub/kanban/hub/projects", 200],
      ["/api/hub/kanban/stats", 200],
      ["/api/hub/chat/status", 200],
      ["/api/hub/memory/projects", 200],
      ["/api/hub/memory/settings", 200],
      ["/api/system.json", 200],
    ];
    for (const [path, code] of checks) {
      const res = await request.get(path);
      expect(res.status(), path).toBe(code);
    }
  });
});
