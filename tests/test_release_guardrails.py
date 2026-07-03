from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_windows_release_script_enforces_build_and_release_guardrails() -> None:
    script_path = REPO_ROOT / "tauri" / "scripts" / "release_windows.ps1"
    assert script_path.exists(), "release_windows.ps1 should codify the release checklist"

    script = script_path.read_text(encoding="utf-8")
    required_fragments = [
        "git status --porcelain",
        "npm.cmd",
        "test -- --run",
        "pytest",
        "npm.cmd audit",
        "package_tauri.ps1",
        "commodity_lab_backend.exe",
        "LastWriteTimeUtc",
        "gh release create",
        "Out-File -Encoding utf8",
        "Commodity Lab v$Version"
    ]
    for fragment in required_fragments:
        assert fragment in script
