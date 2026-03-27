import { test, expect } from "@playwright/test";
import { registerHubGate, enLocale, frLocale } from "./hub-gate";

registerHubGate();

test.describe("Persona 9 — Language switching", () => {
  test.beforeEach(async ({ page }) => {
    // Clear any persisted locale so each test starts from navigator.language
    await page.addInitScript(() => {
      localStorage.removeItem("clawvis-locale");
    });
  });

  test("Settings page renders in French when navigator.language is fr-FR", async ({ page }) => {
    await frLocale(page);
    await page.goto("/settings/");
    await expect(page.locator(".settings-page-header h1")).toContainText(/Paramètres/i);
    await expect(page.locator(".back-btn")).toContainText(/Retour au hub/i);
    // Language card shows Français as selected
    const frRadio = page.locator("#lang-fr");
    await expect(frRadio).toBeChecked();
  });

  test("Settings page renders in English when navigator.language is en-US", async ({ page }) => {
    await enLocale(page);
    await page.goto("/settings/");
    await expect(page.locator(".settings-page-header h1")).toContainText(/Settings/i);
    await expect(page.locator(".back-btn")).toContainText(/Back to hub/i);
    // Language card shows English as selected
    const enRadio = page.locator("#lang-en");
    await expect(enRadio).toBeChecked();
  });

  test("Switching to French persists in localStorage and re-renders", async ({ page }) => {
    await enLocale(page);
    await page.goto("/settings/");
    // Start in English
    await expect(page.locator(".settings-page-header h1")).toContainText(/Settings/i);
    // Click the French language card (label wraps the radio — click the label)
    await page.locator("label[data-value='fr']").click();
    // Page re-renders in French
    await expect(page.locator(".settings-page-header h1")).toContainText(/Paramètres/i);
    await expect(page.locator(".back-btn")).toContainText(/Retour au hub/i);
    // Preference is saved to localStorage
    const locale = await page.evaluate(() => localStorage.getItem("clawvis-locale"));
    expect(locale).toBe("fr");
  });

  test("Switching to English persists in localStorage and re-renders", async ({ page }) => {
    await frLocale(page);
    await page.goto("/settings/");
    // Start in French
    await expect(page.locator(".settings-page-header h1")).toContainText(/Paramètres/i);
    // Click the English language card (label wraps the radio — click the label)
    await page.locator("label[data-value='en']").click();
    // Page re-renders in English
    await expect(page.locator(".settings-page-header h1")).toContainText(/Settings/i);
    await expect(page.locator(".back-btn")).toContainText(/Back to hub/i);
    // Preference is saved to localStorage
    const locale = await page.evaluate(() => localStorage.getItem("clawvis-locale"));
    expect(locale).toBe("en");
  });

  test("localStorage locale overrides navigator.language", async ({ page }) => {
    // navigator says French but localStorage says English
    await frLocale(page);
    await page.addInitScript(() => {
      localStorage.setItem("clawvis-locale", "en");
    });
    await page.goto("/settings/");
    await expect(page.locator(".settings-page-header h1")).toContainText(/Settings/i);
    const enRadio = page.locator("#lang-en");
    await expect(enRadio).toBeChecked();
  });
});
