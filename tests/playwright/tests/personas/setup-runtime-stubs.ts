import type { Page, Route } from "@playwright/test";

/** Stub GET /api/hub/agent/config (other methods pass through). */
export async function stubAgentConfigGet(
  page: Page,
  body: Record<string, unknown>,
): Promise<void> {
  await page.route("**/api/hub/agent/config", async (route: Route) => {
    if (route.request().method() !== "GET") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
}

/** Stub POST /api/hub/setup/provider with 200 and echo PRIMARY_AI_PROVIDER from body. */
export async function stubSetupProviderSuccess(
  page: Page,
  onPost?: (raw: string) => void,
): Promise<void> {
  await page.route("**/api/hub/setup/provider", async (route: Route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    const raw = route.request().postData() || "";
    onPost?.(raw);
    let prov = "claude";
    try {
      prov = JSON.parse(raw).provider ?? prov;
    } catch {
      /* noop */
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, PRIMARY_AI_PROVIDER: prov }),
    });
  });
}

/** Stub POST /api/hub/setup/provider with an error payload. */
export async function stubSetupProviderError(
  page: Page,
  status: number,
  body: Record<string, unknown>,
): Promise<void> {
  await page.route("**/api/hub/setup/provider", async (route: Route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
}
