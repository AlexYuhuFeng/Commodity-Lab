"""Versioned local practice evidence. Readiness is never professional certification."""
from datetime import datetime, timezone
import hashlib
import json
from uuid import uuid4
from pydantic import Field, field_validator
from core.handbook_content import CHAPTERS, text
from core.handbook_practice import VERSION as PRACTICE_VERSION
from core.risk_training import Contract
from core.risk_training_store import SessionStore

EVIDENCE_VERSION = "chapter-evidence-v1"
RUBRIC_VERSION = "reasoning-rubric-v1"
REQUIRED_VARIANTS = 3
REQUIRED_REVIEWS = 2
PREREQUISITES = {
    "gas-hub-supply": (), "gas-beach-hub": ("gas-hub-supply",),
    "gas-lng-regas": ("gas-beach-hub",), "crude-refinery-supply": (),
    "crude-inventory": ("crude-refinery-supply",),
}
DIMENSIONS = {
    "exposure": text("Identify the commercial obligation, price direction and units.", "识别商业义务、价格方向与单位。"),
    "hedge": text("Explain instrument, direction, quantity and pricing-window fit; a defensible no-hedge choice is valid.", "解释工具、方向、数量及定价窗口匹配；有依据的不套保方案同样有效。"),
    "residual": text("Recognize remaining basis or operational risk and choose a suitable commercial response.", "识别剩余基差或运营风险并选择适当商业应对。"),
    "controls": text("Explain liquidity, credit and applicable illustrative policy constraints without claiming live authorization.", "解释流动性、信用及适用的示例政策约束，不声称获得实盘授权。"),
}
SKILLS = {
    "gas-hub-supply": ("price_risk", "basis", "controls"),
    "gas-beach-hub": ("spread", "capacity_route", "operations"),
    "gas-lng-regas": ("units_fx", "capacity_route", "operations"),
    "crude-refinery-supply": ("price_risk", "basis", "controls"),
    "crude-inventory": ("price_risk", "storage", "controls"),
}


def now():
    return datetime.now(timezone.utc).isoformat()


def initialize(con):
    con.execute("CREATE TABLE IF NOT EXISTS evidence_learners (id TEXT PRIMARY KEY, display_name TEXT NOT NULL, created_at TEXT NOT NULL)")
    con.execute("INSERT OR IGNORE INTO evidence_learners VALUES ('local','Local learner',?)", (now(),))
    con.execute("CREATE TABLE IF NOT EXISTS reasoning_evidence (id TEXT PRIMARY KEY, learner_id TEXT NOT NULL, question_id TEXT NOT NULL, revision INTEGER NOT NULL, record TEXT NOT NULL, UNIQUE(learner_id,question_id))")


def require_learner(con, learner_id):
    initialize(con)
    if not con.execute("SELECT 1 FROM evidence_learners WHERE id=?", (learner_id,)).fetchone():
        raise KeyError("learner_not_found")


def fingerprint(question, chapter_version):
    # Seeds may wrap to identical economics. Compare the actual public givens.
    givens = {k: v for k, v in question["givens"].items() if k != "seed"}
    raw = json.dumps([question["chapter_id"], chapter_version, question["version"], givens], sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def diagnostic_passes(questions):
    """Earliest graded record for the actual economics owns its diagnostic result."""
    seen=set(); passed={id:set() for id in CHAPTERS}
    for q in questions:
        if not q["current_version"] or not q["attempts"] or q["fingerprint"] in seen:continue
        seen.add(q["fingerprint"])
        if q["first_attempt_correct"]:passed[q["chapter_id"]].add(q["fingerprint"])
    return passed


class LearnerRequest(Contract):
    display_name: str = Field(min_length=1, max_length=80)

    @field_validator("display_name")
    @classmethod
    def nonempty(cls, v):
        if not v.strip(): raise ValueError("name_required")
        return v.strip()


class Reflection(Contract):
    exposure: str = Field(min_length=20, max_length=2000)
    hedge: str = Field(min_length=20, max_length=2000)
    residual: str = Field(min_length=20, max_length=2000)
    controls: str = Field(min_length=20, max_length=2000)

    @field_validator("*")
    @classmethod
    def meaningful_length(cls, v):
        if len(v.strip()) < 20: raise ValueError("reflection_too_short")
        return v.strip()


class ReasoningRequest(Contract):
    question_id: str = Field(min_length=1, max_length=64)
    reflection: Reflection


class Ratings(Contract):
    exposure: int = Field(ge=0, le=2, strict=True)
    hedge: int = Field(ge=0, le=2, strict=True)
    residual: int = Field(ge=0, le=2, strict=True)
    controls: int = Field(ge=0, le=2, strict=True)


class ReviewRequest(Contract):
    reviewer_id: str = Field(min_length=1, max_length=64)
    expected_revision: int = Field(ge=0, strict=True)
    ratings: Ratings
    notes: str = Field(min_length=20, max_length=3000)

    @field_validator("notes")
    @classmethod
    def meaningful_notes(cls, v):
        if len(v.strip()) < 20: raise ValueError("review_notes_too_short")
        return v.strip()


def rubric():
    return {"version": RUBRIC_VERSION, "dimensions": DIMENSIONS,
            "levels": {"0": text("Missing or materially incorrect", "缺失或存在重大错误"),
                       "1": text("Adequate but incomplete; explain remaining gaps", "基本充分但不完整；说明仍存在的缺口"),
                       "2": text("Specific, coherent and supported by visible evidence", "具体、连贯且有可见证据支持")},
            "readiness_rule": {"minimum_each": 1, "minimum_total": 6, "distinct_reviewed_variants": REQUIRED_REVIEWS},
            "authority": "local_unverified_reviewer_not_certification"}


class EvidenceStore(SessionStore):
    def learners(self):
        with self.connect() as con:
            initialize(con)
            return [{"id": id, "display_name": name} for id, name in con.execute("SELECT id,display_name FROM evidence_learners ORDER BY rowid")]

    def create_learner(self, request):
        id = uuid4().hex
        with self.connect() as con:
            initialize(con)
            con.execute("INSERT INTO evidence_learners VALUES (?,?,?)", (id, request.display_name, now()))
        return {"id": id, "display_name": request.display_name}

    def _questions(self, con, learner_id):
        require_learner(con, learner_id)
        # Existing installations have no handbook tables until their first conversation.
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='handbook_questions'").fetchone():
            return []
        rows = con.execute("SELECT q.id,q.conversation_id,q.public,q.attempts,c.chapter_id,c.version,c.state FROM handbook_questions q JOIN handbook_conversations c ON c.id=q.conversation_id ORDER BY q.rowid").fetchall()
        result = []
        for id, conversation_id, public, attempts, chapter_id, version, state in rows:
            if json.loads(state).get("learner_id", "local") != learner_id: continue
            question = json.loads(public); attempts = json.loads(attempts)
            current = chapter_id in CHAPTERS and CHAPTERS[chapter_id].version == version and question["version"] == PRACTICE_VERSION
            result.append({"id": id, "conversation_id": conversation_id, "chapter_id": chapter_id,
                           "chapter_version": version, "practice_version": question["version"],
                           "fingerprint": fingerprint(question, version), "question": question,
                           "attempts": attempts, "current_version": current,
                           "first_attempt_correct": bool(attempts and attempts[0]["assessment"]["correct"])})
        return result

    def _reasoning(self, con, learner_id):
        return [json.loads(row[0]) for row in con.execute("SELECT record FROM reasoning_evidence WHERE learner_id=? ORDER BY rowid", (learner_id,))]

    def portfolio(self, learner_id, commodity=None):
        with self.connect() as con:
            questions = self._questions(con, learner_id)
            reasoning = self._reasoning(con, learner_id)
        eligible = diagnostic_passes(questions)
        chapters = []
        for id, chapter in CHAPTERS.items():
            if commodity and chapter.commodity != commodity: continue
            evidence = [q for q in questions if q["chapter_id"] == id]
            numeric_ready = len(eligible[id]) >= REQUIRED_VARIANTS
            blockers = [p for p in PREREQUISITES[id] if len(eligible[p]) < REQUIRED_VARIANTS]
            reviewed = set()
            for r in reasoning:
                if r["chapter_id"] != id or r["chapter_version"] != chapter.version or r["practice_version"] != PRACTICE_VERSION or not r["first_attempt_snapshot"]["assessment"]["correct"] or not r["reviews"]: continue
                last = r["reviews"][-1]
                ratings = list(last["ratings"].values())
                if last["rubric_version"] == RUBRIC_VERSION and min(ratings) >= 1 and sum(ratings) >= 6 and r["fingerprint"] in eligible[id]:
                    reviewed.add(r["fingerprint"])
            ready = numeric_ready and not blockers and len(reviewed) >= REQUIRED_REVIEWS
            status = "ready_for_guided_assessment" if ready else "prerequisite_diagnostic_needed" if blockers else "reasoning_review_needed" if numeric_ready else "numerical_practice_needed"
            chapters.append({"chapter_id": id, "chapter_version": chapter.version, "title": chapter.title.model_dump(),
                             "skills": SKILLS[id], "status": status, "distinct_first_pass_variants": len(eligible[id]),
                             "required_variants": REQUIRED_VARIANTS, "numerical_ready": numeric_ready,
                             "reviewed_reasoning_variants": len(reviewed), "required_reviews": REQUIRED_REVIEWS,
                             "prerequisites": PREREQUISITES[id], "blocked_by": blockers,
                             "remediation_section": "economics" if not numeric_ready else "mitigation",
                             "question_count": len(evidence), "retry_count": sum(max(0, len(q["attempts"])-1) for q in evidence)})
        ids = {c["chapter_id"] for c in chapters}
        return {"version": EVIDENCE_VERSION, "rubric_version": RUBRIC_VERSION, "learner_id": learner_id,
                "authority": "local_training_evidence_not_mastery", "chapters": chapters,
                "questions": [q for q in questions if q["chapter_id"] in ids and q["attempts"]],
                "reasoning": [r for r in reasoning if r["chapter_id"] in ids]}

    def submit_reasoning(self, learner_id, request):
        # The prerequisite diagnostic is enforced on assessed reasoning, not reading/exploration.
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            questions = self._questions(con, learner_id)
            q = next((q for q in questions if q["id"] == request.question_id), None)
            if not q: raise KeyError("question_not_found_for_learner")
            if not q["current_version"]: raise ValueError("chapter_version_mismatch")
            if not q["attempts"]: raise ValueError("graded_practice_required")
            for prereq in PREREQUISITES[q["chapter_id"]]:
                passed = diagnostic_passes(questions)[prereq]
                if len(passed) < REQUIRED_VARIANTS: raise ValueError("prerequisite_diagnostic_needed")
            if con.execute("SELECT 1 FROM reasoning_evidence WHERE learner_id=? AND question_id=?", (learner_id, q["id"])).fetchone():
                raise ValueError("reasoning_already_submitted")
            record = {"id": uuid4().hex, "learner_id": learner_id, "question_id": q["id"], "chapter_id": q["chapter_id"],
                      "chapter_version": q["chapter_version"], "practice_version": q["practice_version"],
                      "evidence_version": EVIDENCE_VERSION, "rubric_version": RUBRIC_VERSION,
                      "fingerprint": q["fingerprint"], "created_at": now(), "revision": 0,
                      "reflection": request.reflection.model_dump(), "question_snapshot": q["question"],
                      "first_attempt_snapshot": q["attempts"][0], "reviews": [],
                      "policy_authority": "illustrative_training_only", "market_data": "synthetic"}
            con.execute("INSERT INTO reasoning_evidence VALUES (?,?,?,?,?)", (record["id"], learner_id, q["id"], 0, json.dumps(record)))
        return record

    def review(self, id, request):
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            require_learner(con, request.reviewer_id)
            row = con.execute("SELECT learner_id,revision,record FROM reasoning_evidence WHERE id=?", (id,)).fetchone()
            if not row: raise KeyError("evidence_not_found")
            if row[0] == request.reviewer_id: raise ValueError("separate_reviewer_required")
            if row[1] != request.expected_revision: raise ValueError("stale_review_revision")
            record = json.loads(row[2])
            if CHAPTERS[record["chapter_id"]].version != record["chapter_version"] or record["practice_version"] != PRACTICE_VERSION: raise ValueError("chapter_version_mismatch")
            reviewer = con.execute("SELECT display_name FROM evidence_learners WHERE id=?", (request.reviewer_id,)).fetchone()[0]
            record["reviews"].append({"reviewer_id": request.reviewer_id, "reviewer_name": reviewer, "created_at": now(),
                                      "rubric_version": RUBRIC_VERSION, "ratings": request.ratings.model_dump(),
                                      "notes": request.notes, "authority": "local_unverified_reviewer_not_certification"})
            record["revision"] += 1
            con.execute("UPDATE reasoning_evidence SET revision=?,record=? WHERE id=?", (record["revision"], json.dumps(record), id))
        return record

    def export(self, learner_id):
        return {"exported_at": now(), "source": "Commodity Lab local training evidence", "portfolio": self.portfolio(learner_id),
                "rubric": rubric(), "limitations": ["Local profile labels are not authenticated identities.",
                "Distinct arithmetic variants are not independent commercial cases or proof of mastery.",
                "No institutional certification or live trading authorization."]}
