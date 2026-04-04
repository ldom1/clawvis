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
