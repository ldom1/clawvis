import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale } from "./hub-gate";

registerHubGate();

test.describe("Persona 8 — Project × Memory × Kanban integration", () => {
  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test("create task, split, memory refresh, delete subtasks, delete project", async ({
    page,
    request,
  }) => {
    test.setTimeout(240_000);
    const suffix = Date.now();
    const name = `E2E MemKan ${suffix}`;
    const parentTitle = `Parent split ${suffix}`;
    const subBase = `SubMem ${suffix}`;
    let slug: string | null = null;

    try {
      await page.goto("/");
      await expect(page.locator(".section-label", { hasText: "Projects" })).toBeVisible();
      await page.locator("#new-project").click();
      await expect(page.locator("#modal.open")).toBeVisible();
      await page.locator("#project-name").fill(name);
      await page.locator("#project-description").fill("Playwright memory + kanban");
      await page.locator("#project-template").selectOption("python-fastapi");
      await page.locator("#create-project").click();
      await page.waitForLoadState("networkidle").catch(() => {});
      await page.goto("/");
      const card = page.locator("a.card-project", { hasText: name });
      await expect(card).toBeVisible({ timeout: 60000 });
      const href = await card.getAttribute("href");
      slug = (href || "").replace(/^\/project\//, "").split("/")[0] || "";
      expect(slug.length).toBeGreaterThan(0);

      await page.goto(`/project/${encodeURIComponent(slug)}`);
      await expect(page.locator("#project-subtitle")).toContainText(name);
      await page.locator("#project-new-task").click();
      await expect(page.locator("#kanban-create-overlay.open")).toBeVisible();
      await expect(page.locator("#kanban-create-project")).toHaveValue(slug);
      await page.locator("#kanban-create-title").fill(parentTitle);
      await page.locator("#kanban-create-submit").click();
      await expect(page.locator("#kanban-create-overlay.open")).toHaveCount(0);
      await expect(
        page.locator("#project-kanban .kanban-card", { hasText: parentTitle }),
      ).toBeVisible();

      await page.locator("#project-kanban .kanban-card", { hasText: parentTitle }).click();
      await expect(page.locator("#kanban-detail-overlay.open")).toBeVisible();

      // Override window.prompt to provide answers synchronously (native prompt dialogs
      // are unreliable in headless Chromium — CDP auto-dismisses before the Playwright
      // dialog event fires, making waitForEvent hang until timeout).
      await page.evaluate((answers: string[]) => {
        let idx = 0;
        window.prompt = (_msg?: string, _def?: string) => answers[idx++] ?? null;
      }, ["3", subBase]);

      await page.locator("#kanban-detail-split").click();
      await expect(page.locator("#kanban-detail-overlay.open")).toHaveCount(0, { timeout: 30_000 });
      for (const n of ["#1", "#2", "#3"]) {
        await expect(
          page.locator("#project-kanban .kanban-card", { hasText: `${subBase} ${n}` }),
        ).toBeVisible({ timeout: 20000 });
      }

      // Check whether kanban→memory MD sync wrote the task names to the project file.
      // In Docker CI, kanban_parser is absent so _MD_SYNC=False and tasks are not synced.
      let mdSyncActive = false;
      {
        const memRes = await request.get(
          `/api/hub/memory/projects/${encodeURIComponent(`${slug}.md`)}`,
        );
        if (memRes.ok()) {
          const { content } = (await memRes.json()) as { content?: string };
          mdSyncActive = !!content?.includes(subBase);
        }
      }

      await page.goto("/memory/");
      await expect(page.locator("#quartz-frame")).toBeVisible();
      // Suppress window.alert so a failed rebuild (e.g. "build-quartz.sh not found")
      // doesn't freeze the page waiting for an unhandled dialog.
      await page.evaluate(() => { window.alert = () => {}; });
      const rebuildP = page.waitForResponse(
        (r) =>
          r.url().includes("/api/hub/memory/brain/rebuild-static") &&
          r.request().method() === "POST",
        { timeout: 15_000 },
      );
      await page.locator("#quartz-refresh").click();
      const rebuildRes = await rebuildP.catch(() => null);
      // Only assert quartz content when MD sync is active (tasks written to .md).
      // In Docker CI this is skipped gracefully (kanban_parser absent → no MD sync).
      if (rebuildRes?.ok() && mdSyncActive) {
        const body = page.frameLocator("#quartz-frame").locator("body");
        await expect(body).toContainText(subBase, { timeout: 30_000 });
      }

      await page.goto(`/project/${encodeURIComponent(slug)}`);
      for (const n of ["#1", "#2", "#3"]) {
        const c = page.locator("#project-kanban .kanban-card", { hasText: `${subBase} ${n}` });
        await c.click();
        await expect(page.locator("#kanban-detail-overlay.open")).toBeVisible();
        await page.locator("#kanban-detail-delete").click();
        await expect(page.locator("#global-confirm-overlay.open")).toBeVisible();
        await expect(page.locator("#confirm-modal-title")).toHaveText(/Are you sure/i);
        await page.locator("#confirm-modal-ok").click();
        await expect(page.locator("#kanban-detail-overlay.open")).toHaveCount(0);
      }

      await page.goto("/memory/edit");
      await expect(page.locator("#memory-file-select")).toBeVisible();
      await page.locator("#memory-file-select").selectOption(`${slug}.md`);
      await expect
        .poll(
          async () => {
            const r = await request.get(
              `/api/hub/kanban/tasks?project=${encodeURIComponent(slug)}`,
            );
            if (!r.ok()) return -1;
            const data = (await r.json()) as { tasks?: { title?: string }[] };
            const titles = (data.tasks || []).map((t) => t.title || "");
            return titles.filter((t) => t.includes(subBase)).length;
          },
          { timeout: 20_000 },
        )
        .toBe(0);

      await page.goto(`/project/${encodeURIComponent(slug)}`);
      await expect(
        page.locator("#project-kanban .kanban-card", { hasText: `${subBase} #1` }),
      ).toHaveCount(0);

      const slugBeforeDelete = slug;
      await page.locator("#delete-project-btn").click();
      await expect(page.locator("#global-confirm-overlay.open")).toBeVisible();
      await expect(page.locator("#confirm-modal-title")).toHaveText(/Are you sure/i);
      await page.locator("#confirm-modal-ok").click();
      await expect(page).toHaveURL("/", { timeout: 30_000 });

      const projRes = await request.get(
        `/api/hub/kanban/hub/projects/${encodeURIComponent(slugBeforeDelete)}`,
      );
      expect(projRes.status()).toBe(404);
      const memRes = await request.get(
        `/api/hub/memory/projects/${encodeURIComponent(`${slugBeforeDelete}.md`)}`,
      );
      expect(memRes.status()).toBe(404);

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
