import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale } from "./hub-gate";

registerHubGate();

async function skipIfNoQuartz(request: import("@playwright/test").APIRequestContext) {
  const list = await request.get("/api/hub/memory/quartz");
  if (!list.ok()) {
    test.skip(true, "Memory API not reachable at /api/hub/memory/quartz (start clawvis / memory service).");
  }
  const j = (await list.json()) as { files?: string[]; source?: string };
  test.skip(
    j.source !== "quartz" || !j.files?.length,
    "No Quartz build under quartz/public/*.html (run: bash scripts/build-quartz.sh or clawvis start after npm in quartz/).",
  );
  return j.files as string[];
}

test.describe("Brain — Quartz static (styles + install parity)", () => {
  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test("quartz-static HTML injects base; index.css is served", async ({ request }) => {
    const files = await skipIfNoQuartz(request);
    const htmlName = files[0];
    const pageRes = await request.get(
      `/api/hub/memory/quartz-static/${encodeURIComponent(htmlName)}`,
    );
    expect(pageRes.ok()).toBeTruthy();
    const html = await pageRes.text();
    expect(html).toMatch(/<base\s+href="[^"]*\/api\/hub\/memory\/quartz-static\/[^"]*"/i);

    const cssRes = await request.get("/api/hub/memory/quartz-static/index.css");
    expect(cssRes.ok(), "Quartz index.css must be reachable or the Brain iframe looks unstyled").toBeTruthy();
    expect(cssRes.headers()["content-type"] || "").toMatch(/text\/(css|plain)/);
    const css = await cssRes.text();
    expect(css.length).toBeGreaterThan(500);
    expect(css).toContain(".page");
  });

  test("quartz-static index.html falls back when Quartz has no root index", async ({ request }) => {
    const files = await skipIfNoQuartz(request);
    test.skip(!files.includes("README.html"), "Need README.html at Quartz root for this check.");
    const idx = await request.get("/api/hub/memory/quartz-static/index.html");
    expect(idx.ok(), "SPA clients request index.html; should not 404 when README is the home page").toBeTruthy();
    const body = await idx.text();
    expect(body).toMatch(/<base\s+href=/i);
  });

  test("nested Quartz page still reaches root index.css", async ({ request }) => {
    await skipIfNoQuartz(request);
    const pageRes = await request.get("/api/hub/memory/quartz-static/projects/example-project.html");
    test.skip(pageRes.status() === 404, "No projects/example-project.html in this Quartz build.");
    expect(pageRes.ok()).toBeTruthy();
    const html = await pageRes.text();
    expect(html).toContain("../index.css");

    const cssRes = await request.get("/api/hub/memory/quartz-static/index.css");
    expect(cssRes.ok()).toBeTruthy();
  });

  test("Brain iframe triggers successful Quartz stylesheet load", async ({ page, request }) => {
    await skipIfNoQuartz(request);

    const cssPromise = page.waitForResponse(
      (r) =>
        r.url().includes("/api/hub/memory/quartz-static/") &&
        r.url().includes("index.css") &&
        r.ok(),
      { timeout: 45_000 },
    );

    await page.goto("/memory/");
    await expect(page.locator("#quartz-frame")).toBeVisible();

    const cssResp = await cssPromise;
    expect(cssResp.status()).toBe(200);
    const frame = page.frameLocator("#quartz-frame");
    await expect(frame.locator("body")).toBeVisible({ timeout: 15_000 });
    const font = await frame.locator("body").evaluate((el) => getComputedStyle(el).fontFamily);
    expect(font.toLowerCase()).toMatch(/source sans|schibsted|system-ui|segoe/);
  });
});
