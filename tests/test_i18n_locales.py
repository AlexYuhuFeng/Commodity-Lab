import json
from pathlib import Path


def flatten_keys(data: dict, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for k, v in data.items():
        full = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys |= flatten_keys(v, full)
        else:
            keys.add(full)
    return keys


def test_locale_key_parity_between_en_and_zh():
    locales_dir = Path("app/locales")
    en = json.loads((locales_dir / "en.json").read_text(encoding="utf-8"))
    zh = json.loads((locales_dir / "zh.json").read_text(encoding="utf-8"))

    en_keys = flatten_keys(en)
    zh_keys = flatten_keys(zh)

    missing_in_zh = sorted(en_keys - zh_keys)
    missing_in_en = sorted(zh_keys - en_keys)

    assert not missing_in_zh, f"Missing in zh locale: {missing_in_zh}"
    assert not missing_in_en, f"Missing in en locale: {missing_in_en}"
