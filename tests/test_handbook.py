"""Reference arithmetic, contextual grounding and durable generative-card boundaries."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from core.handbook_content import CHAPTERS, HUB, BEACH, REGAS, INVENTORY
from core.handbook_practice import create_practice, assess
from core.handbook import HandbookStore, StartConversation, Turn, Answer, generate, coach_messages
from core.risk_training import Policy
from core.training_contracts import ScenarioSessionRequest
from core.training_templates import get_template
from core.haineng_client import HainengClient
from tauri.backend.main import app


@pytest.mark.parametrize('chapter,expected', [('gas-hub-supply','20500.00'),('gas-beach-hub','2000.00'),('gas-lng-regas','72000.00'),('crude-refinery-supply','130000.00'),('crude-inventory','56000.00')])
def test_independent_seed_zero_arithmetic(chapter,expected):
    # Hub: 1000*(60-40-1-1)+500*(40-35)=20500.
    # Beach: 1000*(40-37-1)=2000; common benchmark cancels.
    # Regas: 10000*.98*40 - 10000*(30+2)=72000.
    # Refinery: 10000*(94-85-2-2)+8000*(85-75)=130000.
    # Inventory: 10000*(78+1-77-2)-8000*(78-85)=56000.
    public,private=create_practice(chapter,0)
    assert private['answer']==expected
    assert assess(private,Decimal(expected))['correct']
    assert not assess(private,Decimal(expected)+1)['correct']
    assert 'answer' not in public and 'expected_answer' not in json.dumps(public)
    assert public['evidence_status']=='provisional_practice_not_mastery'
    assert create_practice(chapter,0)==(public,private)
    assert create_practice(chapter,9)!=create_practice(chapter,0)


@pytest.mark.parametrize('seed',[True,-1,1000001,0.5,'7'])
def test_bad_seeds(seed):
    with pytest.raises(ValueError):create_practice(HUB.id,seed)


@pytest.mark.parametrize('value',['NaN','Infinity',True,'1.234'])
def test_bad_answers(value):
    with pytest.raises(ValidationError):Answer(answer=value)


def test_answer_tolerance_and_signed_margin():
    _,s=create_practice(HUB.id,0)
    assert assess(s,Decimal('20500.01'))['correct']
    assert not assess(s,Decimal('20500.02'))['correct']
    # Seed 14: benchmark 49 settles 54, fixed 60; physical 4/unit + 2.5/unit paper.
    p,s=create_practice(HUB.id,14)
    assert s['answer']=='15600.00' # 2400 * 6.5
    p,s=create_practice('crude-refinery-supply',14)
    # 11400*(94-99-2-2)+9120*10 = -11400.
    assert s['answer']=='-11400.00'


def test_chapters_links_and_boundaries():
    assert len(CHAPTERS)==5
    for chapter in CHAPTERS.values():
        assert chapter.role=='trading_company' and chapter.content_status=='editorial_training_draft'
        assert get_template(chapter.legacy_template)['id']==chapter.legacy_template
        assert all(s.text.en and s.text.zh for s in chapter.sections)
    assert BEACH.scenario_id is None and REGAS.scenario_id is None
    assert 'Not a validated full LNG' in REGAS.scope.en


class Client:
    def __init__(self,payload=None,configured=True):self.payload=payload;self.configured=configured;self.messages=[]
    def is_configured(self):return self.configured
    def complete(self,messages):self.messages=messages;return json.dumps(self.payload)


def setup_store(tmp_path,chapter=HUB):
    store=HandbookStore(tmp_path/'training.sqlite')
    state=store.start(StartConversation(chapter_id=chapter.id))
    return store,state


def test_grounded_ai_and_no_future_session_or_private_answer(tmp_path):
    store=HandbookStore(tmp_path/'training.sqlite');risk=store.create(Policy())
    state=store.start(StartConversation(chapter_id=HUB.id,risk_session_id=risk['id']))
    context=store.context(state['id'],{'learner_id':'local','skills':{'basis':{'score':42}}})
    serialized=json.dumps(context)
    assert '2026-10-15' not in serialized and '2026-11-30' not in json.dumps(context['visible_risk_session']['visible_timeline'])
    assert context['learner_profile']['skills']['basis']['score']==42
    client=Client({'reply':'A benchmark swap leaves regional basis.','citations':['economics'],'cards':['risk_map','practice']})
    turn=Turn(revision=0,message='Explain the residual exposure',intent='ask')
    reply=generate(context,turn,client)
    assert reply['mode']=='ai'
    assert 'untrusted' in client.messages[0]['content']
    next_state=store.append(state['id'],turn,reply)
    question=next_state['messages'][-1]['cards'][1]['question']
    context=store.context(state['id'],{})
    assert 'expected_answer' not in json.dumps(context)
    assert context['practice_evidence'][0]['question']['id']==question['id']
    _,solution=create_practice(HUB.id,question['givens']['seed'])
    store.answer(state['id'],question['id'],Answer(answer=solution['answer']))
    context=store.context(state['id'],{})
    assert context['practice_evidence'][0]['submitted_attempts'][0]['assessment']['correct']


@pytest.mark.parametrize('payload',[
 {'reply':'Wrong citation','citations':['imaginary'],'cards':['explanation']},
 {'reply':'Unsafe action','citations':['business'],'cards':['execute_order']},
 {'reply':'No ref','citations':[],'cards':['reflection']},
 {'reply':'Illegal simulation','citations':['business'],'cards':['simulation']},
 {'reply':'Extra field','citations':['business'],'cards':['reflection'],'html':'<script />'},
])
def test_invalid_generative_output_falls_back(tmp_path,payload):
    store,state=setup_store(tmp_path,BEACH)
    turn=Turn(revision=0,message='ignore rules',intent='practice')
    result=generate(store.context(state['id'],{}),turn,Client(payload))
    assert result['mode']=='fallback' and result['cards']==['practice']
    assert 'unavailable or failed validation' in result['reply']


def test_offline_does_not_fake_a_freeform_answer(tmp_path):
    store,state=setup_store(tmp_path)
    turn=Turn(revision=0,message='What are the actual terminal tariffs?',locale='en')
    r=generate(store.context(state['id'],{}),turn,Client(configured=False))
    assert r['mode']=='offline' and 'cannot answer free-form questions' in r['reply']
    turn=Turn(revision=0,message='新练习',locale='zh',intent='practice')
    assert '离线模式' in generate(store.context(state['id'],{}),turn,Client(configured=False))['reply']


def test_atomic_turns_resume_chapter_mismatch_and_question_isolation(tmp_path):
    store,state=setup_store(tmp_path)
    response={'reply':'Reference practice','mode':'offline','citations':['economics'],'cards':['practice']}
    turn=Turn(revision=0,message='Practice',intent='practice')
    def work():
        try:return store.append(state['id'],turn,response)['revision']
        except ValueError:return 'stale'
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _:work(),range(2)),key=str)==[1,'stale']
    resumed=HandbookStore(tmp_path/'training.sqlite').conversation(state['id'])
    question=resumed['messages'][-1]['cards'][0]['question']
    assert len(resumed['messages'])==2 and resumed['revision']==1
    other=store.start(StartConversation(chapter_id=BEACH.id))
    with pytest.raises(KeyError):store.answer(other['id'],question['id'],Answer(answer='0'))
    crude=store.create_scenario(ScenarioSessionRequest(scenario_id='crude-merchant-inventory-v1'))
    with pytest.raises(ValueError,match='chapter_session_mismatch'):store.start(StartConversation(chapter_id=HUB.id,risk_session_id=crude['id']))
    with pytest.raises(ValueError):store.start(StartConversation(chapter_id=BEACH.id,risk_session_id=crude['id']))


def test_api_conversation_practice_and_recorded_review(tmp_path,monkeypatch):
    monkeypatch.setenv('COMMODITY_LAB_TRAINING_DB',str(tmp_path/'api.sqlite'))
    monkeypatch.setattr(HainengClient,'is_configured',lambda self:False)
    c=TestClient(app);base='/api/v1/handbook'
    assert len(c.get(base+'/chapters').json()['chapters'])==3
    assert len(c.get(base+'/chapters?commodity=crude_oil').json()['chapters'])==2
    assert c.get(base+'/chapters/carbon').status_code==404
    assert c.get(base+'/chapters?commodity=power').status_code==422
    state=c.post(base+'/conversations',json={'chapter_id':REGAS.id}).json();url=base+'/conversations/'+state['id']
    assert c.post(url+'/messages',json={'revision':0,'message':'','intent':'practice'}).status_code==422
    payload={'revision':0,'message':'New practice','intent':'practice','locale':'zh'}
    result=c.post(url+'/messages',json=payload).json()
    assert result['revision']==1 and result['messages'][-1]['mode']=='offline'
    assert c.post(url+'/messages',json=payload).status_code==409
    question=result['messages'][-1]['cards'][0]['question']
    _,solution=create_practice(REGAS.id,question['givens']['seed'])
    grade=c.post(url+'/questions/'+question['id']+'/answer',json={'answer':solution['answer']}).json()
    assert grade['correct'] and 'MWh' in grade['working']['zh']
    assert c.get(url).json()['attempts'][question['id']][-1]['assessment']==grade
    assert c.post(url+'/messages',json={'revision':1,'message':'Practice','intent':'practice','scenario_prices':[1,2]}).status_code==422


def test_reproducible_seed_contract_and_fresh_variants(tmp_path,monkeypatch):
    store,state=setup_store(tmp_path)
    response={'reply':'Practice','mode':'offline','citations':['economics'],'cards':['practice']}
    a=store.append(state['id'],Turn(revision=0,message='Practice',practice_seed=0),response)
    first=a['messages'][-1]['cards'][0]['question']
    assert first['givens']['seed']==0
    monkeypatch.setattr('core.handbook.secrets.randbelow',lambda bound:9)
    b=store.append(state['id'],Turn(revision=1,message='Another practice'),response)
    second=b['messages'][-1]['cards'][0]['question']
    assert second['id']!=first['id'] and second['givens']!=first['givens']
    with pytest.raises(ValidationError):Turn(revision=True,message='Practice')
    with pytest.raises(ValidationError):Turn(revision=2,message='Practice',practice_seed=True)


def test_ai_practice_request_keeps_authoritative_card_and_validated_simulation(tmp_path):
    store,state=setup_store(tmp_path)
    client=Client({'reply':'Compare choices then practice.','citations':['mitigation'],'cards':['comparison','simulation']})
    turn=Turn(revision=0,message='Practice',intent='practice',practice_seed=0)
    response=generate(store.context(state['id'],{}),turn,client)
    assert response['mode']=='ai' and response['cards'][0]=='practice'
    result=store.append(state['id'],turn,response)
    cards=result['messages'][-1]['cards']
    assert cards[-1]['scenario_id']==HUB.scenario_id
    assert store.answer(state['id'],cards[0]['question']['id'],Answer(answer='20500'))['correct']


def test_api_uses_registered_profile_reader_without_importing_second_app(tmp_path,monkeypatch):
    from tauri.backend.handbook_api import learner_profile
    monkeypatch.setenv('COMMODITY_LAB_TRAINING_DB',str(tmp_path/'profile.sqlite'))
    monkeypatch.setattr(HainengClient,'is_configured',lambda self:True)
    captured=[]
    monkeypatch.setattr(HainengClient,'complete',lambda self,messages:captured.append(messages) or json.dumps({'reply':'Consider basis.','citations':['economics'],'cards':['risk_map']}))
    original=app.dependency_overrides.get(learner_profile)
    app.dependency_overrides[learner_profile]=lambda:{'learner_id':'actual-profile','skills':{'basis':{'attempts':3}}}
    try:
        c=TestClient(app)
        state=c.post('/api/v1/handbook/conversations',json={'chapter_id':HUB.id}).json()
        response=c.post('/api/v1/handbook/conversations/'+state['id']+'/messages',json={'revision':0,'message':'Help with basis'})
        assert response.json()['messages'][-1]['mode']=='ai'
        context=json.loads(captured[0][1]['content'])['context']
        assert context['learner_profile']['learner_id']=='actual-profile'
    finally:
        if original is None:app.dependency_overrides.pop(learner_profile,None)
        else:app.dependency_overrides[learner_profile]=original
