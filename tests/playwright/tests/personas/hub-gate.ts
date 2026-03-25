import { test } from "@playwright/test";

let hubUp = false;

/** Call once per spec file: skips all tests when the Hub is not reachable. */
export function registerHubGate() {
  test.beforeAll(async ({ request }) => {
    try {
      const r = await request.get("/", { timeout: 20000 });
      hubUp = r.ok();
    } catch {
      hubUp = false;
    }
  });
  test.beforeEach(() => {
    test.skip(!hubUp, "Start the Hub (e.g. clawvis start). Set PLAYWRIGHT_BASE_URL if not using the default.");
  });
}

export async function enLocale(page: import("@playwright/test").Page) {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "language", { get: () => "en-US" });
    Object.defineProperty(navigator, "languages", { get: () => ["en-US", "en"] });
  });
}

export async function frLocale(page: import("@playwright/test").Page) {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "language", { get: () => "fr-FR" });
    Object.defineProperty(navigator, "languages", { get: () => ["fr-FR", "fr"] });
  });
}
