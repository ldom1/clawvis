import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale } from "./hub-gate";

registerHubGate();

test.describe("Persona 2 — Kanban lifecycle", () => {
  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test("create task, move columns, effort, archive", async ({ page }) => {
    await page.goto("/kanban/");
    await expect(page.locator(".settings-page-header h1")).toContainText(/Kanban/i);
    await expect(page.locator(".settings-page-header h1")).toContainText(/Clawvis/);
    await expect(page.locator("#kanban-stats-bar")).toBeVisible();
    for (const status of ["To Start", "In Progress", "Done"]) {
      await expect(page.locator(`.kanban-column[data-status="${status}"]`)).toBeVisible();
    }

    await page.locator("#kanban-new-task").click();
    await expect(page.locator("#kanban-create-overlay.open")).toBeVisible();

    const title = `E2E task ${Date.now()}`;
    await page.locator("#kanban-create-title").fill(title);
    const projectInput = page.locator("#kanban-create-project");
    const firstProject = await page
      .locator("#kanban-project-filter option")
      .nth(1)
      .textContent()
      .catch(() => null);
    if (firstProject?.trim()) {
      await projectInput.fill(firstProject.trim());
    }
    await page.locator("#kanban-create-priority").selectOption("High");
    await page.locator("#kanban-create-submit").click();
    await expect(page.locator("#kanban-create-overlay.open")).toHaveCount(0);

    const taskCard = () => page.locator(".kanban-card", { hasText: title });
    await expect(taskCard()).toBeVisible();
    await expect(
      page.locator(`.kanban-column[data-status="To Start"] .kanban-card`, { hasText: title }),
    ).toHaveCount(1);

    const totalBefore = await page.locator("#kanban-stats-bar .stat-item").first().textContent();
    await expect(totalBefore).toMatch(/Total/);

    await taskCard().click();
    await expect(page.locator("#kanban-detail-overlay.open")).toBeVisible();
    await expect(page.locator("#kanban-detail-modal")).toContainText(title);
    await page.locator('#kanban-detail-modal button[data-next-status="In Progress"]').click();
    await expect(page.locator("#kanban-detail-overlay.open")).toHaveCount(0);
    await expect(
      page.locator(`.kanban-column[data-status="In Progress"] .kanban-card`, { hasText: title }),
    ).toBeVisible();

    await taskCard().click();
    await page.locator("#detail-effort").fill("2");
    await page.locator("#kanban-detail-save").click();
    await expect(page.locator("#kanban-detail-overlay.open")).toHaveCount(0);
    await expect(taskCard().locator(".card-effort")).toContainText("2");

    await taskCard().click();
    await page.locator('#kanban-detail-modal button[data-next-status="Done"]').click();
    await expect(page.locator("#kanban-detail-overlay.open")).toHaveCount(0);
    await expect(
      page.locator(`.kanban-column[data-status="Done"] .kanban-card`, { hasText: title }),
    ).toBeVisible();

    await taskCard().click();
    page.once("dialog", (d) => d.accept().catch(() => {}));
    await page.locator("#kanban-detail-archive").click();
    await expect(page.locator("#kanban-detail-overlay.open")).toHaveCount(0);
    await expect(page.locator(`.kanban-column .kanban-card`, { hasText: title })).toHaveCount(0);

    await page.locator("#kanban-open-archive").click();
    await expect(page.locator("#kanban-archive-overlay.open")).toBeVisible();
    await expect(page.locator("#kanban-archive-content")).toContainText(title);
    await page.locator("#kanban-archive-close").click();
  });

  test("delete task shows confirmation modal", async ({ page }) => {
    await page.goto("/kanban/");
    await page.locator("#kanban-new-task").click();
    await expect(page.locator("#kanban-create-overlay.open")).toBeVisible();
    const delTitle = `E2E delete modal ${Date.now()}`;
    await page.locator("#kanban-create-title").fill(delTitle);
    const firstProject = await page
      .locator("#kanban-project-filter option")
      .nth(1)
      .textContent()
      .catch(() => null);
    if (firstProject?.trim()) {
      await page.locator("#kanban-create-project").fill(firstProject.trim());
    }
    await page.locator("#kanban-create-submit").click();
    await expect(page.locator("#kanban-create-overlay.open")).toHaveCount(0);

    const delCard = page.locator(".kanban-card", { hasText: delTitle });
    await expect(delCard.first()).toBeVisible({ timeout: 30000 });
    await delCard.first().click();
    await expect(page.locator("#kanban-detail-overlay.open")).toBeVisible();

    await page.locator("#kanban-detail-delete").click();
    await expect(page.locator("#global-confirm-overlay.open")).toBeVisible();
    await expect(page.locator("#confirm-modal-title")).toHaveText(/Are you sure/i);
    await expect(page.locator("#confirm-modal-cancel")).toBeVisible();
    await page.locator("#confirm-modal-cancel").click();
    await expect(page.locator("#global-confirm-overlay.open")).toHaveCount(0);
    await expect(delCard.first()).toBeVisible();

    await delCard.first().click();
    await page.locator("#kanban-detail-delete").click();
    await expect(page.locator("#global-confirm-overlay.open")).toBeVisible();
    await page.locator("#confirm-modal-ok").click();
    await expect(page.locator("#kanban-detail-overlay.open")).toHaveCount(0);
    await expect(page.locator(".kanban-card", { hasText: delTitle })).toHaveCount(0);
  });
});
