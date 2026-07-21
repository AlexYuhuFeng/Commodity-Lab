const DEEPSEEK_KEY_PATTERN = /\bDEEPSEEK[_-]?API[_-]?KEY\b/i;
const PROVIDER_PATTERN = /\b(?:AI[_-]?PROVIDER|PROVIDER)\b/i;

function normalizedKey(key) {
  return String(key ?? "").trim().toLowerCase().replace(/[-_\s]/g, "");
}

export function normalizeAiKeyFileText(value) {
  const source = String(value ?? "");
  const trimmed = source.trim();
  if (!trimmed || !DEEPSEEK_KEY_PATTERN.test(trimmed) || PROVIDER_PATTERN.test(trimmed)) {
    return source;
  }

  if (trimmed.startsWith("{")) {
    try {
      const parsed = JSON.parse(trimmed);
      if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") return source;
      const entries = Object.entries(parsed);
      const hasProvider = entries.some(([key]) => ["provider", "aiprovider"].includes(normalizedKey(key)));
      const hasDeepSeekKey = entries.some(([key, item]) => normalizedKey(key) === "deepseekapikey" && String(item ?? "").trim());
      if (!hasProvider && hasDeepSeekKey) {
        return JSON.stringify({ ...parsed, provider: "deepseek" });
      }
    } catch {
      return source;
    }
    return source;
  }

  return `provider=deepseek\n${source}`;
}

export function installAiKeyFileCompatibility() {
  if (typeof File === "undefined" || !File.prototype?.text || File.prototype.__commodityLabAiKeyCompat) return;
  const originalText = File.prototype.text;
  Object.defineProperty(File.prototype, "__commodityLabAiKeyCompat", {
    configurable: false,
    enumerable: false,
    value: true,
    writable: false
  });
  File.prototype.text = async function commodityLabAiKeyText() {
    const source = await originalText.call(this);
    return normalizeAiKeyFileText(source);
  };
}
