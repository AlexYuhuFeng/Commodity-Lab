"""Local, additive evidence workflow; no enterprise reviewer authorization claim."""
from typing import Literal
from fastapi import APIRouter, HTTPException
from core.competency import EvidenceStore, LearnerRequest, ReasoningRequest, ReviewRequest, rubric

router = APIRouter(prefix="/api/v1/competency", tags=["competency"])


def failure(exc):
    return HTTPException(404 if isinstance(exc, KeyError) else 409, detail=str(exc).strip("'"))


@router.get("/rubric")
def read_rubric():
    return rubric()


@router.get("/learners")
def learners():
    return {"learners": EvidenceStore().learners(), "identity_scope": "local_device_labels"}


@router.post("/learners")
def create_learner(request: LearnerRequest):
    return EvidenceStore().create_learner(request)


@router.get("/learners/{learner_id}/portfolio")
def portfolio(learner_id: str, commodity: Literal["european_gas", "crude_oil"] | None = None):
    try: return EvidenceStore().portfolio(learner_id, commodity)
    except (KeyError, ValueError) as exc: raise failure(exc) from exc


@router.get("/learners/{learner_id}/export")
def export(learner_id: str):
    try: return EvidenceStore().export(learner_id)
    except (KeyError, ValueError) as exc: raise failure(exc) from exc


@router.post("/learners/{learner_id}/reasoning")
def submit_reasoning(learner_id: str, request: ReasoningRequest):
    try: return EvidenceStore().submit_reasoning(learner_id, request)
    except (KeyError, ValueError) as exc: raise failure(exc) from exc


@router.post("/evidence/{evidence_id}/reviews")
def review(evidence_id: str, request: ReviewRequest):
    try: return EvidenceStore().review(evidence_id, request)
    except (KeyError, ValueError) as exc: raise failure(exc) from exc
