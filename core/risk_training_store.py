"""Local durable sessions. Atomic revision checks; no enterprise identity claim."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
from uuid import uuid4
from core.risk_training import Decision, Policy, initial_state
from core.training_contracts import CommodityDecision, ScenarioSessionRequest
from core.training_engine import create_state, submit_state, view_state


class SessionStore:
    def __init__(self, path: Path | None = None):
        self.path = path or Path(os.getenv("COMMODITY_LAB_TRAINING_DB", str(Path.home() / ".commodity-lab" / "training.sqlite")))

    @contextmanager
    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=10)
        con.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, state TEXT NOT NULL)")
        try:
            with con:
                yield con
        finally:
            con.close()

    def create(self, policy: Policy) -> dict:
        return self._create(initial_state(policy))

    def create_scenario(self, request: ScenarioSessionRequest) -> dict:
        return self._create(create_state(request))

    def _create(self, state: dict) -> dict:
        session_id = uuid4().hex
        with self.connect() as con:
            con.execute("INSERT INTO sessions VALUES (?, ?)", (session_id, json.dumps(state)))
        return {"id": session_id, **view_state(state)}

    def read(self, session_id: str) -> dict:
        with self.connect() as con:
            row = con.execute("SELECT state FROM sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            raise KeyError("session_not_found")
        return json.loads(row[0])

    def view(self, session_id: str) -> dict:
        return {"id": session_id, **view_state(self.read(session_id))}

    def decide(self, session_id: str, decision: Decision | CommodityDecision) -> dict:
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT state FROM sessions WHERE id=?", (session_id,)).fetchone()
            if not row:
                raise KeyError("session_not_found")
            state, assessment = submit_state(json.loads(row[0]), decision)
            con.execute("UPDATE sessions SET state=? WHERE id=?", (json.dumps(state), session_id))
        return {"id": session_id, **view_state(state), "latest_assessment": assessment}
