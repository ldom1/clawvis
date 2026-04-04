import { escapeHtml } from "../src/utils.js";

describe("Runtime tile text", () => {
  it("escapeHtml does not escape plain strings", () => {
    expect(escapeHtml("Runtime IA")).toBe("Runtime IA");
  });
});
