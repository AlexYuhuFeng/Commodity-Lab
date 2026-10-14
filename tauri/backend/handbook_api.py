"""Additive handbook API; reuse local storage, learner profile and AI providers."""
from typing import Literal
from fastapi import APIRouter, HTTPException, Depends
from core.handbook import StartConversation, Turn, Answer, HandbookStore, chapter_for, generate
from core.handbook_content import CHAPTERS

router=APIRouter(prefix="/api/v1/handbook",tags=["handbook"])


def learner_profile():
    return {"profile_available":False}


def failure(exc):
    return HTTPException(404 if isinstance(exc,KeyError) else 409,detail=str(exc).strip("'"))


@router.get("/chapters")
def chapters(commodity: Literal["european_gas","crude_oil"]="european_gas"):
    return {"chapters":[{"id":c.id,"version":c.version,"title":c.title.model_dump(),"summary":c.summary.model_dump(),"content_status":c.content_status} for c in CHAPTERS.values() if c.commodity==commodity]}


@router.get("/chapters/{chapter_id}")
def chapter(chapter_id:str):
    try:return chapter_for(chapter_id).model_dump(mode="json")
    except ValueError as exc:raise HTTPException(404,detail="unsupported_chapter") from exc


@router.post("/conversations")
def start(request:StartConversation):
    try:return HandbookStore().start(request)
    except (KeyError,ValueError) as exc:raise failure(exc) from exc


@router.get("/conversations/{id}")
def read(id:str):
    try:
        store=HandbookStore()
        return {**store.conversation(id),"attempts":store.question_attempts(id)}
    except (KeyError,ValueError) as exc:raise failure(exc) from exc


@router.post("/conversations/{id}/messages")
def message(id:str,turn:Turn,profile:dict=Depends(learner_profile)):
    from core.haineng_client import HainengClient
    try:
        store=HandbookStore()
        state=store.conversation(id)
        if state["revision"]!=turn.revision or turn.revision>=100:raise ValueError("stale_or_exhausted_conversation")
        context=store.context(id,profile)
        response=generate(context,turn,HainengClient())
        return {**store.append(id,turn,response),"attempts":store.question_attempts(id)}
    except (KeyError,ValueError) as exc:raise failure(exc) from exc


@router.post("/conversations/{id}/questions/{question_id}/answer")
def answer(id:str,question_id:str,request:Answer):
    try:return HandbookStore().answer(id,question_id,request)
    except (KeyError,ValueError) as exc:raise failure(exc) from exc
