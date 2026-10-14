"""Evidence qualification is derived from immutable first attempts, never profit or AI."""
from concurrent.futures import ThreadPoolExecutor
import json
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from core.competency import (EvidenceStore, LearnerRequest, ReasoningRequest, Reflection,
                             ReviewRequest, Ratings, fingerprint, EVIDENCE_VERSION, RUBRIC_VERSION)
from core.handbook import HandbookStore, StartConversation, Turn, Answer
from core.handbook_content import HUB, BEACH
from core.handbook_practice import create_practice
from tauri.backend.main import app

RESPONSE = {"reply":"Practice","mode":"offline","citations":["economics"],"cards":["practice"]}
REFLECTION = dict(exposure="Floating procurement funds a fixed-price customer delivery in EUR/MWh.",
                  hedge="A long matching swap hedges rising purchase prices; partial or no hedge needs a rationale.",
                  residual="Regional basis and physical delivery remain; align contracts and reserve transport capacity.",
                  controls="Fund margin calls before receipts, check credit and the illustrative 80% training cap.")


def fixture(tmp_path):
    path = tmp_path / 'evidence.sqlite'
    return HandbookStore(path), EvidenceStore(path)


def practice(store, chapter=HUB.id, seed=0, learner='local', correct=True, grade=True):
    state = store.start(StartConversation(chapter_id=chapter,learner_id=learner))
    state = store.append(state['id'], Turn(revision=0,message='Practice',practice_seed=seed), RESPONSE)
    q = state['messages'][-1]['cards'][0]['question']
    if grade:
        _, solution = create_practice(chapter, seed)
        store.answer(state['id'],q['id'],Answer(answer=solution['answer'] if correct else '-999999'))
    return state, q


def chapter(store, id=HUB.id, learner='local'):
    return next(c for c in store.portfolio(learner)['chapters'] if c['chapter_id']==id)


def submit(store, q, learner='local'):
    return store.submit_reasoning(learner,ReasoningRequest(question_id=q['id'],reflection=Reflection(**REFLECTION)))


def reviewer(store):
    return store.create_learner(LearnerRequest(display_name='Independent reviewer'))['id']


def review(store, record, actor, ratings=None, revision=0):
    return store.review(record['id'],ReviewRequest(reviewer_id=actor,expected_revision=revision,
                        ratings=Ratings(**(ratings or dict(exposure=2,hedge=2,residual=1,controls=1))),
                        notes='Commercial rationale is defensible; add more detail about funding timing.'))


def test_legacy_records_default_local_and_persisted_profile_isolation(tmp_path):
    hb, ev = fixture(tmp_path)
    state,q=practice(hb)
    # Legacy state predates explicit owner.
    with hb.handbook_connect() as con:
        old=json.loads(con.execute('SELECT state FROM handbook_conversations WHERE id=?',(state['id'],)).fetchone()[0]);old.pop('learner_id')
        con.execute('UPDATE handbook_conversations SET state=? WHERE id=?',(json.dumps(old),state['id']))
    other=ev.create_learner(LearnerRequest(display_name='Second learner'))['id']
    assert chapter(ev)['distinct_first_pass_variants']==1
    assert chapter(ev,learner=other)['question_count']==0
    with pytest.raises(KeyError):submit(ev,q,other)
    _, second=practice(hb,seed=1,learner=other)
    resumed=EvidenceStore(ev.path)
    assert len(resumed.portfolio('local')['questions'])==len(resumed.portfolio(other)['questions'])==1
    with pytest.raises(KeyError):hb.start(StartConversation(chapter_id=HUB.id,learner_id='unknown'))
    assert {l['id'] for l in resumed.learners()}=={'local',other}


def test_retries_and_seed_wrap_cannot_inflate_first_pass_diagnostics(tmp_path):
    hb,ev=fixture(tmp_path)
    state,q=practice(hb,correct=False)
    hb.answer(state['id'],q['id'],Answer(answer='20500'))
    practice(hb,seed=300) # 300 has exactly seed-zero economics.
    practice(hb,seed=1);practice(hb,seed=2)
    c=chapter(ev)
    assert c['distinct_first_pass_variants']==2 and c['retry_count']==1
    assert not c['numerical_ready']
    practice(hb,seed=3)
    assert chapter(ev)['numerical_ready']
    assert chapter(ev)['status']=='reasoning_review_needed'


def test_reasoning_review_separate_from_arithmetic_and_multiple_solutions(tmp_path):
    hb,ev=fixture(tmp_path); actor=reviewer(ev)
    questions=[practice(hb,seed=n)[1] for n in range(3)]
    assert chapter(ev)['status']=='reasoning_review_needed'
    first=submit(ev,questions[0]);second=submit(ev,questions[1])
    # Low-dimensional minimum cannot be compensated by total or profitable outcome.
    review(ev,first,actor,dict(exposure=2,hedge=2,residual=2,controls=0))
    review(ev,second,actor)
    assert chapter(ev)['reviewed_reasoning_variants']==1
    review(ev,first,actor,revision=1)
    assert chapter(ev)['status']=='ready_for_guided_assessment'
    exported=ev.export('local')
    assert exported['portfolio']['authority']=='local_training_evidence_not_mastery'
    assert exported['rubric']['version']==RUBRIC_VERSION
    record=exported['portfolio']['reasoning'][0]
    assert len(record['reviews'])==2 and record['market_data']=='synthetic'
    assert record['policy_authority']=='illustrative_training_only'
    assert 'pnl' not in record
    assert record['first_attempt_snapshot']['submitted']=='20500.00'


def test_duplicate_review_economics_count_once(tmp_path):
    hb,ev=fixture(tmp_path);actor=reviewer(ev)
    for seed in (0,1,2,300):
        _,q=practice(hb,seed=seed)
        if seed in (0,300):review(ev,submit(ev,q),actor)
    assert chapter(ev)['reviewed_reasoning_variants']==1
    assert chapter(ev)['status']=='reasoning_review_needed'


def test_assessed_reasoning_prerequisite_enforced_without_blocking_reading(tmp_path):
    hb,ev=fixture(tmp_path)
    _,q=practice(hb,chapter=BEACH.id)
    assert chapter(ev,BEACH.id)['blocked_by']==[HUB.id]
    with pytest.raises(ValueError,match='prerequisite_diagnostic_needed'):submit(ev,q)
    for seed in (0,1,2):practice(hb,seed=seed)
    assert not chapter(ev,BEACH.id)['blocked_by']
    assert submit(ev,q)['chapter_id']==BEACH.id


def test_atomic_review_revision_and_self_review_rejected(tmp_path):
    hb,ev=fixture(tmp_path);_,q=practice(hb);record=submit(ev,q);actor=reviewer(ev)
    with pytest.raises(ValueError,match='separate_reviewer_required'):review(ev,record,'local')
    def work(_):
        try:return review(ev,record,actor)['revision']
        except ValueError as exc:return str(exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(work,range(2)),key=str)==[1,'stale_review_revision']
    assert len(ev.portfolio('local')['reasoning'][0]['reviews'])==1
    with pytest.raises(ValueError,match='reasoning_already_submitted'):submit(ev,q)


def test_ungraded_solutions_not_exported_and_version_drift_not_counted(tmp_path):
    hb,ev=fixture(tmp_path);_,q=practice(hb,grade=False)
    assert ev.portfolio('local')['questions']==[]
    assert 'expected_answer' not in json.dumps(ev.export('local'))
    with pytest.raises(ValueError,match='graded_practice_required'):submit(ev,q)
    state,q=practice(hb)
    with hb.handbook_connect() as con:
        con.execute('UPDATE handbook_conversations SET version=? WHERE id=?',('old',state['id']))
    assert chapter(ev)['distinct_first_pass_variants']==0
    with pytest.raises(ValueError,match='chapter_version_mismatch'):submit(ev,q)
    assert ev.portfolio('local')['questions'][0]['current_version'] is False


def test_unknown_units_and_legacy_profile_not_shared_between_learners(tmp_path):
    hb,ev=fixture(tmp_path);other=ev.create_learner(LearnerRequest(display_name='Other'))['id']
    state,_=practice(hb,learner=other,grade=False)
    context=hb.context(state['id'],{'learner_id':'local','skills':{'basis':{'score':100}}})
    assert context['learner_profile']=={'learner_id':other,'profile_available':False}
    assert context['chapter_evidence']['authority']=='local_training_evidence_not_mastery'
    assert 'expected_answer' not in json.dumps(context)


@pytest.mark.parametrize('bad',[True,1.0,'2',-1,3])
def test_strict_rubric_numbers(bad):
    with pytest.raises(ValidationError):Ratings(exposure=bad,hedge=2,residual=2,controls=2)


def test_api_contract_validation_and_export(tmp_path,monkeypatch):
    monkeypatch.setenv('COMMODITY_LAB_TRAINING_DB',str(tmp_path/'api.sqlite'))
    c=TestClient(app);base='/api/v1/competency'
    assert c.get(base+'/learners').json()['identity_scope']=='local_device_labels'
    assert c.get(base+'/learners/unknown/portfolio').status_code==404
    assert c.get(base+'/learners/local/portfolio?commodity=power').status_code==422
    assert c.post(base+'/learners',json={'display_name':'   '}).status_code==422
    assert c.post(base+'/learners',json={'display_name':'Person','role':'admin'}).status_code==422
    assert c.get(base+'/rubric').json()['version']==RUBRIC_VERSION
    actor=c.post(base+'/learners',json={'display_name':'Reviewer'}).json()['id']
    hb=HandbookStore();_,q=practice(hb)
    record=c.post(base+'/learners/local/reasoning',json={'question_id':q['id'],'reflection':REFLECTION}).json()
    body={'reviewer_id':actor,'expected_revision':0,'ratings':dict(exposure=2,hedge=2,residual=1,controls=1),'notes':'Reasonable explanation with matching periods and funded collateral.'}
    assert c.post(base+'/evidence/'+record['id']+'/reviews',json=body).status_code==200
    assert c.post(base+'/evidence/'+record['id']+'/reviews',json=body).status_code==409
    data=c.get(base+'/learners/local/export').json()
    assert data['portfolio']['version']==EVIDENCE_VERSION
    assert data['portfolio']['reasoning'][0]['revision']==1
    assert c.get(base+'/learners/local/portfolio?commodity=crude_oil').json()['questions']==[]


def test_nonlocal_learner_cannot_attach_unowned_legacy_risk_session(tmp_path):
    hb,ev=fixture(tmp_path)
    owner=ev.create_learner(LearnerRequest(display_name='New learner'))['id']
    with pytest.raises(ValueError,match='risk_session_owner_unverified'):
        hb.start(StartConversation(chapter_id=HUB.id,learner_id=owner,risk_session_id='legacy-shared-session'))
