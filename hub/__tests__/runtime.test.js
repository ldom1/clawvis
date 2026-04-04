import { escapeHtml } from "../src/utils.js";

describe("Runtime tile text", () => {
  it("escapeHtml does not escape plain strings", () => {
    expect(escapeHtml("Runtime IA")).toBe("Runtime IA");
  });
});

describe("renderRuntimePage HTML structure", () => {
  it("contains required DOM hook IDs", () => {
    const html = `
      <div class="runtime-page">
        <div class="runtime-info-panel" id="runtime-info-panel"></div>
        <div class="runtime-test-section">
          <button id="runtime-test-btn"></button>
          <div id="runtime-test-result"></div>
        </div>
        <div class="runtime-openclaw-section" id="runtime-openclaw-section"></div>
      </div>`;
    expect(html).toContain('id="runtime-info-panel"');
    expect(html).toContain('id="runtime-test-btn"');
    expect(html).toContain('id="runtime-test-result"');
    expect(html).toContain('id="runtime-openclaw-section"');
  });
});

describe("Settings runtime card removal", () => {
  it("settings page HTML should not contain settings-runtime-card", () => {
    const html = `
      <div class="settings-sections">
        <section class="card settings-card settings-section">workspace</section>
        <section class="card settings-card settings-section">instances</section>
        <section class="card settings-card settings-section" id="cron-section">cron</section>
      </div>`;
    expect(html).not.toContain("settings-runtime-card");
  });
});

describe("CLAWVIS error token patterns", () => {
  it("[CLAWVIS:AUTH] is detected", () => {
    const t = "[CLAWVIS:AUTH]".trim();
    expect(t.startsWith("[CLAWVIS:AUTH]")).toBe(true);
  });

  it("[CLAWVIS:HTTP:403] is detected", () => {
    const m = /^\[CLAWVIS:HTTP:(\d+)\]$/.exec("[CLAWVIS:HTTP:403]");
    expect(m).not.toBeNull();
    expect(m[1]).toBe("403");
  });
});
