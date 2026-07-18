from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_windows_release_script_enforces_local_build_and_tag_guardrails() -> None:
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
        'CurrentBranch -ne "main"',
        'git" @("tag", "-a"',
        'git" @("push", "origin"',
        "cross-platform CI",
    ]
    for fragment in required_fragments:
        assert fragment in script


def test_tag_workflow_publishes_all_supported_desktop_architectures() -> None:
    workflow_path = REPO_ROOT / ".github" / "workflows" / "tauri-build.yml"
    workflow = workflow_path.read_text(encoding="utf-8")

    required_fragments = [
        "commodity-lab-windows-x86_64",
        "commodity-lab-linux-x86_64",
        "commodity-lab-linux-arm64",
        "ubuntu-22.04-arm",
        "--bundles deb,appimage",
        "gh release create",
    ]
    for fragment in required_fragments:
        assert fragment in workflow
