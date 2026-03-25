import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale } from "./hub-gate";

registerHubGate();

test.describe("Persona 3 — project lifecycle", () => {
  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test("create from home, open project, kanban filter, delete", async ({ page, request }) => {
    const suffix = Date.now();
    const name = `E2E Project ${suffix}`;
    let slug: string | null = null;

    try {
      await page.goto("/");
      await expect(page.locator(".section-label", { hasText: "Projects" })).toBeVisible();
      await page.locator("#new-project").click();
      await expect(page.locator("#modal.open")).toBeVisible();
      await page.locator("#project-name").fill(name);
      await page.locator("#project-description").fill("Testing via Playwright");
      await page.locator("#project-tags").fill("e2e");
      await page.locator("#project-tags").press("Enter");
      await page.locator("#project-template").selectOption("python-fastapi");
      await page.locator("#create-project").click();
      await page.waitForLoadState("networkidle").catch(() => {});
      await page.goto("/");
      const card = page.locator("a.card-project", { hasText: name });
      await expect(card).toBeVisible({ timeout: 60000 });
      const href = await card.getAttribute("href");
      slug = (href || "").replace(/^\/project\//, "").split("/")[0] || "";
      expect(slug.length).toBeGreaterThan(0);
      await card.click();

      expect(page.url()).toContain(`/project/${slug}`);
      await expect(page.locator("#project-subtitle")).toContainText(name);
      await expect(page.locator("#project-kanban")).toBeVisible();
      await expect(page.locator("#project-avatar-fallback")).toHaveText("EP");

      const memMark = `E2E memory sync ${suffix}`;
      await page.locator("#pm-description").fill(memMark);
      await page.locator("#project-memory-save").click();
      await expect(page.locator("#project-memory-save-status")).toContainText(/memory updated|mémoire/i, {
        timeout: 15000,
      });
      const mdRes = await request.get(
        `/api/hub/memory/projects/${encodeURIComponent(`${slug}.md`)}`,
      );
      expect(mdRes.ok()).toBeTruthy();
      const mdBody = (await mdRes.json()) as { content?: string };
      expect(mdBody.content || "").toContain(memMark);

      await page.goto("/kanban/");
      await expect(page.locator("#codir-grid")).toContainText(slug, { timeout: 15000 });
      await page.locator("#kanban-project-filter").selectOption(slug);
      const cards = page.locator("#kanban-board .kanban-card");
      await expect(cards.first()).toBeVisible();
      await expect(cards).toHaveCount(3);

      await page.goto(`/project/${slug}`);
      await page.locator("#delete-project-btn").click();
      await expect(page.locator("#global-confirm-overlay.open")).toBeVisible();
      await expect(page.locator("#confirm-modal-title")).toHaveText(/Are you sure/i);
      await expect(page.locator("#confirm-modal-message")).toBeVisible();
      await page.locator("#confirm-modal-cancel").click();
      await expect(page.locator("#global-confirm-overlay.open")).toHaveCount(0);

      await page.locator("#delete-project-btn").click();
      await expect(page.locator("#global-confirm-overlay.open")).toBeVisible();
      await page.locator("#confirm-modal-ok").click();
      await expect(page).toHaveURL("/", { timeout: 30000 });
      await expect(page.locator(`a.card-project`, { hasText: name })).toHaveCount(0);
      slug = null;
    } finally {
      if (slug) {
        await request.delete(`/api/hub/kanban/hub/projects/${encodeURIComponent(slug)}`, {
          failOnStatusCode: false,
        });
      }
    }
  });
});
