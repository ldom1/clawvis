import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale, frLocale } from "./hub-gate";
import {
  stubAgentConfigGet,
  stubSetupProviderError,
  stubSetupProviderSuccess,
} from "./setup-runtime-stubs";

registerHubGate();

test.describe("Persona 1 — onboarding (EN)", () => {
  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test("home, setup runtime wizard — choose Claude and confirm", async ({ page, request }) => {
    let posted: string | null = null;
    await stubAgentConfigGet(page, { primary_provider: null });
    await stubSetupProviderSuccess(page, (raw) => {
      posted = raw;
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
    await expect(page.getByRole("heading", { name: "Choose your agent" })).toBeVisible();

    await expect(page.locator(".setup-provider-cards [data-provider]")).toHaveCount(2);
    await expect(page.getByRole("button", { name: /Claude Code/i }).first()).toBeVisible();
    const confirm = page.locator("#setup-confirm");
    await expect(confirm).toBeDisabled();
    await page.locator('[data-provider="claude"]').click();
    await expect(confirm).toBeEnabled();
    await expect(page.locator('[data-provider="claude"]')).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await confirm.click();
    await expect(page).toHaveURL(/\//);
    expect(posted).toContain('"provider":"claude"');
  });

  test("setup runtime — choose OpenClaw and confirm", async ({ page }) => {
    let posted: string | null = null;
    await stubAgentConfigGet(page, { primary_provider: null });
    await stubSetupProviderSuccess(page, (raw) => {
      posted = raw;
    });
    await page.goto("/setup/runtime/");
    await expect(page.getByRole("button", { name: /OpenClaw/i }).first()).toBeVisible();
    await page.locator('[data-provider="openclaw"]').click();
    await expect(page.locator("#setup-confirm")).toBeEnabled();
    await expect(page.locator('[data-provider="openclaw"]')).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await page.locator("#setup-confirm").click();
    await expect(page).toHaveURL(/\//);
    expect(posted).toContain('"provider":"openclaw"');
  });

  test("setup runtime — preselects OpenClaw from GET /agent/config", async ({ page }) => {
    let posted: string | null = null;
    await stubAgentConfigGet(page, { primary_provider: "openclaw" });
    await stubSetupProviderSuccess(page, (raw) => {
      posted = raw;
    });
    await page.goto("/setup/runtime/");
    await expect(page.locator('[data-provider="openclaw"]')).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.locator("#setup-confirm")).toBeEnabled();
    await page.locator("#setup-confirm").click();
    await expect(page).toHaveURL(/\//);
    expect(posted).toContain('"provider":"openclaw"');
  });

  test("setup runtime — preselects Claude from GET /agent/config", async ({ page }) => {
    let posted: string | null = null;
    await stubAgentConfigGet(page, { primary_provider: "claude" });
    await stubSetupProviderSuccess(page, (raw) => {
      posted = raw;
    });
    await page.goto("/setup/runtime/");
    await expect(page.locator('[data-provider="claude"]')).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.locator("#setup-confirm")).toBeEnabled();
    await page.locator("#setup-confirm").click();
    await expect(page).toHaveURL(/\//);
    expect(posted).toContain('"provider":"claude"');
  });

  test("setup runtime — user overrides API preselection (OpenClaw → Claude)", async ({
    page,
  }) => {
    let posted: string | null = null;
    await stubAgentConfigGet(page, { primary_provider: "openclaw" });
    await stubSetupProviderSuccess(page, (raw) => {
      posted = raw;
    });
    await page.goto("/setup/runtime/");
    await expect(page.locator('[data-provider="openclaw"]')).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await page.locator('[data-provider="claude"]').click();
    await expect(page.locator('[data-provider="claude"]')).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await page.locator("#setup-confirm").click();
    await expect(page).toHaveURL(/\//);
    expect(posted).toContain('"provider":"claude"');
  });

  test("setup runtime — POST error surfaces in feedback", async ({ page }) => {
    await stubAgentConfigGet(page, { primary_provider: null });
    await stubSetupProviderError(page, 400, { detail: "cannot write .env" });
    await page.goto("/setup/runtime/");
    await page.locator('[data-provider="claude"]').click();
    await page.locator("#setup-confirm").click();
    const fb = page.locator("#setup-provider-feedback");
    await expect(fb).toBeVisible();
    await expect(fb).toHaveAttribute("class", /\berr\b/);
    await expect(fb).toContainText(/cannot write/i);
  });

  test("setup runtime — Claude stays selected if config arrives late as openclaw", async ({
    page,
  }) => {
    let posted: string | null = null;
    await page.route("**/api/hub/agent/config", async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await new Promise((r) => setTimeout(r, 600));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ primary_provider: "openclaw" }),
      });
    });
    await stubSetupProviderSuccess(page, (raw) => {
      posted = raw;
    });

    const configDone = page.waitForResponse(
      (res) =>
        res.url().includes("/api/hub/agent/config") &&
        res.request().method() === "GET" &&
        res.status() === 200,
    );
    await page.goto("/setup/runtime/");
    await page.locator('[data-provider="claude"]').click();
    await expect(page.locator("#setup-confirm")).toBeEnabled();
    await expect(page.locator('[data-provider="claude"]')).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await configDone;
    // Allow the in-page fetch().then(…) to run after the response is received.
    await expect
      .poll(async () =>
        page.locator('[data-provider="claude"]').getAttribute("aria-pressed"),
      )
      .toBe("true");
    await page.locator("#setup-confirm").click();
    expect(posted).toContain('"provider":"claude"');
  });
});

test.describe("Persona 1 — setup runtime (FR)", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.removeItem("clawvis-locale");
    });
    await frLocale(page);
  });

  test("wizard copy and confirm Claude", async ({ page }) => {
    await stubAgentConfigGet(page, { primary_provider: null });
    await stubSetupProviderSuccess(page);
    await page.goto("/setup/runtime/");
    await expect(page.locator(".settings-page-header h1")).toContainText(/Setup/i);
    await expect(page.getByRole("heading", { name: /Choisir ton agent/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Claude Code/i }).first()).toBeVisible();
    await expect(page.locator("#setup-confirm")).toBeDisabled();
    await page.locator('[data-provider="claude"]').click();
    await page.locator("#setup-confirm").click();
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
