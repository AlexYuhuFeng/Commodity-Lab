import { describe, expect, it } from "vitest";

import { normalizeAiKeyFileText } from "./aiKeyFileCompat";

describe("normalizeAiKeyFileText", () => {
  it("infers DeepSeek for env-style key files", () => {
    const normalized = normalizeAiKeyFileText("DEEPSEEK_API_KEY=sk-test\n");
    expect(normalized).toContain("provider=deepseek");
    expect(normalized).toContain("DEEPSEEK_API_KEY=sk-test");
  });

  it("infers DeepSeek for JSON key files", () => {
    const normalized = normalizeAiKeyFileText(JSON.stringify({ DEEPSEEK_API_KEY: "sk-test" }));
    expect(JSON.parse(normalized)).toEqual({ DEEPSEEK_API_KEY: "sk-test", provider: "deepseek" });
  });

  it("preserves an explicit provider", () => {
    const source = "provider=haineng\nDEEPSEEK_API_KEY=sk-test\n";
    expect(normalizeAiKeyFileText(source)).toBe(source);
  });

  it("does not alter unrelated files", () => {
    const source = "api_key=generic-key\n";
    expect(normalizeAiKeyFileText(source)).toBe(source);
  });
});
