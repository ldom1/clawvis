import { test, expect, type APIRequestContext } from "@playwright/test";
import { registerHubGate, enLocale } from "./hub-gate";

registerHubGate();

test.describe("Persona 3 — project lifecycle", () => {
  const createdProjectSlugs = new Set<string>();

  async function cleanupCreatedProject(request: APIRequestContext, slug: string) {
    const res = await request.delete(
      `/api/hub/kanban/hub/projects/${encodeURIComponent(slug)}`,
      { failOnStatusCode: false },
    );
    if (res.ok()) {
      console.log(`[projects.spec] deleted project: ${slug}`);
      createdProjectSlugs.delete(slug);
      return;
    }
    if (res.status() === 404) {
      createdProjectSlugs.delete(slug);
      return;
    }
    console.warn(
      `[projects.spec] failed to delete project: ${slug} (status=${res.status()})`,
    );
  }

  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test.afterAll(async ({ request }) => {
    const slugs = [...createdProjectSlugs];
    for (const slug of slugs) {
      await cleanupCreatedProject(request, slug);
    }
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
      const createRes = page.waitForResponse(
        (r) =>
          r.url().includes("/api/hub/kanban/hub/projects") &&
          r.request().method() === "POST",
      );
      await page.locator("#create-project").click();
      const created = await createRes;
      expect(created.ok(), await created.text()).toBeTruthy();
      await page.waitForLoadState("networkidle").catch(() => {});
      await page.goto("/");
      const card = page.locator("a.card-project", { hasText: name });
      await expect(card).toBeVisible({ timeout: 60000 });
      const href = await card.getAttribute("href");
      slug = (href || "").replace(/^\/project\//, "").split("/")[0] || "";
      expect(slug.length).toBeGreaterThan(0);
      createdProjectSlugs.add(slug);
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
      createdProjectSlugs.delete(slug);
      slug = null;
    } finally {
      if (slug) {
        await cleanupCreatedProject(request, slug);
      }
    }
  });

  test("frontend vite project shows Build & Launch before dist exists", async ({
    page,
    request,
  }) => {
    const suffix = Date.now();
    const name = `E2E Frontend ${suffix}`;
    let slug: string | null = null;

    try {
      await page.goto("/");
      await expect(page.locator(".section-label", { hasText: "Projects" })).toBeVisible();
      await page.locator("#new-project").click();
      await expect(page.locator("#modal.open")).toBeVisible();
      await page.locator("#project-name").fill(name);
      await page.locator("#project-description").fill("Frontend launch status test");
      await page.locator("#project-template").selectOption("frontend-vite");
      await page.locator("#create-project").click();
      await page.waitForLoadState("networkidle").catch(() => {});
      await page.goto("/");
      const card = page.locator("a.card-project", { hasText: name });
      await expect(card).toBeVisible({ timeout: 60000 });
      const href = await card.getAttribute("href");
      slug = (href || "").replace(/^\/project\//, "").split("/")[0] || "";
      expect(slug.length).toBeGreaterThan(0);
      createdProjectSlugs.add(slug);

      await page.goto(`/project/${encodeURIComponent(slug)}`);
      const launchBtn = page.locator("#project-launch-btn");
      await expect(launchBtn).toBeVisible({ timeout: 15000 });
      await expect(launchBtn).toContainText(/Build & Launch/i);
    } finally {
      if (slug) {
        await cleanupCreatedProject(request, slug);
      }
    }
  });

  test("bulk delete selected projects from home grid", async ({ page, request }) => {
    const suffix = Date.now();
    const names = [`E2E Bulk A ${suffix}`, `E2E Bulk B ${suffix}`];
    const slugs: string[] = [];

    try {
      for (const name of names) {
        const res = await request.post("/api/hub/kanban/hub/projects", {
          data: {
            name,
            description: "Bulk delete test",
            template: "python-fastapi",
            init_git: false,
          },
          failOnStatusCode: false,
        });
        expect(res.ok(), await res.text()).toBeTruthy();
        const body = (await res.json()) as { slug?: string };
        expect(body.slug).toBeTruthy();
        slugs.push(body.slug as string);
        createdProjectSlugs.add(body.slug as string);
      }

      await page.goto("/");
      const bulkBtn = page.locator("#projects-bulk-delete");
      await expect(bulkBtn).toBeHidden();

      for (const name of names) {
        const card = page.locator(".card-project-wrap", { hasText: name });
        await expect(card).toBeVisible({ timeout: 60000 });
        await card.locator("input.card-project-select").check();
      }

      await expect(bulkBtn).toBeVisible();
      await expect(bulkBtn).toContainText("(2)");

      let confirmMessage = "";
      page.once("dialog", async (dialog) => {
        confirmMessage = dialog.message();
        await dialog.accept();
      });
      await bulkBtn.click();

      expect(confirmMessage).toBe("Delete 2 project(s)? This cannot be undone.");
      for (const name of names) {
        await expect(page.locator("a.card-project", { hasText: name })).toHaveCount(0);
      }
      for (const slug of slugs) createdProjectSlugs.delete(slug);
    } finally {
      for (const slug of slugs) {
        await cleanupCreatedProject(request, slug);
      }
    }
  });
});
