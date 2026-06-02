Tauri desktop app for Commodity-Lab

Quick start (dev):

Requirements: Rust toolchain, Node.js, Python

1. Start the Python backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r tauri/backend/requirements.txt
python tauri/backend/main.py
```

2. From `tauri/` run (requires Node + Rust):

```bash
npm install
npx tauri dev
```

Packaging notes: See `tauri/scripts/` for helper scripts.
