import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale } from "./hub-gate";

registerHubGate();

/** UI copy on failed fetch + streamed error prefixes from hub_core.chat_runtime */
function assertAssistantNotApiError(text: string) {
  const t = text.trim();
  expect(t.length, "assistant reply empty").toBeGreaterThan(2);
  const patterns: RegExp[] = [
    /^Error communicating with API\.?$/im,
    /^Network error\.?$/im,
    /^Erreur de communication avec l'API\.?$/im,
    /^Erreur réseau\.?$/im,
    /\[API error\s/i,
    /\[No AI provider configured/i,
    /\[Connection error/i,
    /\[Error:/i,
  ];
  for (const p of patterns) {
    expect(t, `assistant must not be an API/backend error, got: ${t.slice(0, 280)}`).not.toMatch(p);
  }
}

test.describe("Persona 6 — Chat", () => {
  test.beforeEach(async ({ page }) => {
    await enLocale(page);
  });

  test("header and status bar when runtime not configured", async ({ page }) => {
    await page.goto("/chat/");
    await expect(page.locator(".settings-page-header h1")).toContainText(/Chat/i);
    await expect(page.locator(".settings-page-header h1")).toContainText(/Clawvis/);
    await expect(page.locator("#chat-status-bar")).toBeVisible();
    const configured = await page.locator("#chat-status-bar .chat-status-dot.ok").count();
    if (configured) {
      await expect(page.locator("#chat-status-bar")).toContainText(/Server key set|Clé serveur prête/i);
    } else {
      const link = page.locator('#chat-status-bar a.chat-setup-link[href="/setup/runtime/"]');
      await expect(link).toBeVisible();
      await expect(link).toContainText(/Setup runtime|Configurer le runtime/i);
    }
  });

  test("when agent connected, send message and fail on API error reply", async ({ page, request }) => {
    await page.goto("/chat/");
    const connected = await page.locator("#chat-status-bar .chat-status-dot.ok").count();
    test.skip(connected === 0, "Backend AI runtime not configured (no server key in .env)");
    await expect(page.locator("#chat-status-bar")).toContainText(/Server key set|Clé serveur prête/i);

    const probe = await request.post("/api/hub/chat", {
      data: JSON.stringify({ message: "ping", history: [] }),
      headers: { "Content-Type": "application/json" },
    });
    expect(probe.ok()).toBeTruthy();
    const probeText = await probe.text();
    test.skip(
      /\[API error\s/i.test(probeText) ||
        /\[No AI provider/i.test(probeText) ||
        /\[Connection error/i.test(probeText) ||
        /\[Error:/i.test(probeText),
      "Provider returns an error for /api/hub/chat — fix API keys or network (E2E skipped).",
    );

    await page.locator("#chat-input").fill("Say OK in one word.");
    await page.locator("#chat-send").click();
    await expect(page.locator(".chat-bubble-user")).toContainText("Say OK");

    const assistantInner = page.locator(".chat-bubble-assistant .chat-bubble-inner").last();
    await expect(assistantInner).toBeVisible({ timeout: 45000 });
    await expect(assistantInner).not.toHaveText(/^[…]+$/, { timeout: 45000 });

    const text = (await assistantInner.innerText()).trim();
    assertAssistantNotApiError(text);
  });

  test("send message shows assistant bubble", async ({ page }) => {
    await page.goto("/chat/");
    await page.locator("#chat-input").fill("hello");
    await page.locator("#chat-send").click();
    await expect(page.locator(".chat-bubble-user")).toContainText("hello");
    await expect(page.locator(".chat-bubble-assistant")).toBeVisible({ timeout: 25000 });
    const assistantText = await page.locator(".chat-bubble-assistant .chat-bubble-inner").last().innerText();
    expect(assistantText.length).toBeGreaterThan(0);
  });

  test("Shift+Enter inserts newline in input", async ({ page }) => {
    await page.goto("/chat/");
    const input = page.locator("#chat-input");
    await input.click();
    await page.keyboard.type("line1");
    await page.keyboard.press("Shift+Enter");
    await page.keyboard.type("line2");
    const val = await input.inputValue();
    expect(val).toContain("line1");
    expect(val).toContain("line2");
    expect(val.includes("\n")).toBeTruthy();
  });
});
