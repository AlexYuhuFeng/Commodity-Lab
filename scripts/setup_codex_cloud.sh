#!/usr/bin/env bash
# Run in a Codex Cloud checkout with package-registry network access.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python -m venv "$repo_dir/.venv"
"$repo_dir/.venv/bin/python" -m pip install -r "$repo_dir/requirements.txt" pytest httpx pyinstaller
cd "$repo_dir/tauri/tauri-frontend"
npm ci
npx playwright install --with-deps chromium
