#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
out_dir="$repo_root/tauri/bundled/backend"
work_dir="$repo_root/build/pyinstaller-linux"
main_path="$repo_root/tauri/backend/main.py"

rm -rf "$out_dir" "$work_dir"
mkdir -p "$out_dir" "$work_dir"

hidden_imports=(
  core.db
  core.energy_models
  core.gas_scenarios
  core.haineng_client
  core.hedge
  core.learner_profile
  core.learning_journey
  core.learning_session
  core.market_learning
  core.platts_market
  core.scenario_registry
  core.training_templates
)

pyinstaller_args=(
  -m PyInstaller
  --noconfirm
  --clean
  --onefile
  --noconsole
  --name commodity_lab_backend
  --paths "$repo_root"
)

for module_name in "${hidden_imports[@]}"; do
  pyinstaller_args+=(--hidden-import "$module_name")
done

pyinstaller_args+=(
  --distpath "$out_dir"
  --workpath "$work_dir"
  --specpath "$work_dir"
  "$main_path"
)

PYTHONPATH="" python "${pyinstaller_args[@]}"
test -x "$out_dir/commodity_lab_backend"
