import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale } from "./hub-gate";

registerHubGate();

test.describe("Home — Activate project (Brain status: active)", () => {
  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test.describe.configure({ timeout: 120_000 });

  test("shows Activate project on new project, moves to main grid after click", async ({
    page,
    request,
  }) => {
    const suffix = Date.now();
    const name = `E2E Activate ${suffix}`;
    let slug: string | null = null;

    try {
      await page.goto("/");
      await expect(page.locator(".section-label", { hasText: "Projects" })).toBeVisible();
      await page.locator("#new-project").click();
      await expect(page.locator("#modal.open")).toBeVisible();
      await page.locator("#project-name").fill(name);
      await page.locator("#project-description").fill("Playwright activate-project flow");
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

      const toggle = page.getByRole("button", { name: /Show all projects/i });
      if (await toggle.isVisible().catch(() => false)) {
        await toggle.click();
      }

      const wrap = page.locator(".card-project-wrap").filter({ hasText: name });
      await expect(wrap).toBeVisible({ timeout: 60000 });
      const activateBtn = wrap.getByRole("button", { name: /Activate project/i });
      await expect(activateBtn).toBeVisible();

      const href = await wrap.locator("a.card-project").first().getAttribute("href");
      slug = (href || "").replace(/^\/project\//, "").split("/")[0] || "";
      expect(slug.length).toBeGreaterThan(0);

      await activateBtn.click();
      await page.waitForLoadState("domcontentloaded");

      const mainGrid = page.locator("#projects-grid");
      const mainWrap = mainGrid.locator(".card-project-wrap").filter({ hasText: name });
      await expect(mainWrap).toBeVisible({ timeout: 30000 });
      await expect(mainWrap.getByRole("button", { name: /Activate project/i })).toHaveCount(0);

      const apiRes = await request.get(`/api/hub/kanban/hub/projects/${encodeURIComponent(slug!)}`);
      expect(apiRes.ok()).toBeTruthy();
      const detail = (await apiRes.json()) as { project?: { brain_status?: string } };
      expect((detail.project?.brain_status || "").toLowerCase()).toBe("active");
    } finally {
      if (slug) {
        await request.delete(`/api/hub/kanban/hub/projects/${encodeURIComponent(slug)}`, {
          failOnStatusCode: false,
        });
      }
    }
  });

  test("API POST brain-status sets active", async ({ request }) => {
    const suffix = Date.now();
    const name = `E2E BrainStatus ${suffix}`;
    const create = await request.post("/api/hub/kanban/hub/projects", {
      data: {
        name,
        description: "temp for brain-status API test",
        template: "python-fastapi",
        init_git: false,
      },
    });
    expect(create.ok(), await create.text()).toBeTruthy();
    const meta = (await create.json()) as { slug?: string };
    const slug = meta.slug;
    expect(slug).toBeTruthy();
    try {
      const post = await request.post(
        `/api/hub/kanban/hub/projects/${encodeURIComponent(slug!)}/brain-status`,
        { data: { status: "active" } },
      );
      expect(post.ok(), await post.text()).toBeTruthy();
      const body = (await post.json()) as { ok?: boolean; brain_status?: string };
      expect(body.ok).toBeTruthy();
      expect((body.brain_status || "").toLowerCase()).toBe("active");
    } finally {
      await request.delete(`/api/hub/kanban/hub/projects/${encodeURIComponent(slug!)}`, {
        failOnStatusCode: false,
      });
    }
  });
});
