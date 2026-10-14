"""Smoke an already-running local backend, including packaged builds.

Example: python scripts/smoke_handbook.py --base-url http://127.0.0.1:18765
Use an isolated COMMODITY_LAB_TRAINING_DB and disabled AI credentials on the server.
"""
import argparse
import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-url',default='http://127.0.0.1:18765')
    args=parser.parse_args()
    target=urlparse(args.base_url)
    if target.scheme!='http' or target.hostname not in ('127.0.0.1','localhost'):
        parser.error('Smoke target must be a local HTTP training backend')
    base=args.base_url.rstrip('/')+'/api/v1/handbook'
    def call(path,body=None):
        request=Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
        with urlopen(request,timeout=20) as response:return json.load(response)
    assert len(call('/chapters')['chapters'])==3
    assert len(call('/chapters?commodity=crude_oil')['chapters'])==2
    references={'gas-hub-supply':'20500.00','gas-beach-hub':'2000.00','gas-lng-regas':'72000.00','crude-refinery-supply':'130000.00','crude-inventory':'56000.00'}
    for chapter,answer in references.items():
        assert call('/chapters/'+chapter)['content_status']=='editorial_training_draft'
        state=call('/conversations',{'chapter_id':chapter})
        url='/conversations/'+state['id']
        state=call(url+'/messages',{'revision':0,'message':'New numerical practice','intent':'practice','locale':'en','practice_seed':0})
        question=next(c['question'] for c in state['messages'][-1]['cards'] if c['type']=='practice')
        assert 'expected_answer' not in json.dumps(state) and 'answer' not in question
        result=call(url+'/questions/'+question['id']+'/answer',{'answer':answer})
        assert result['correct'] and result['expected_answer']==answer
        assert call(url)['attempts'][question['id']][-1]['assessment']==result
        print(chapter,answer,'PASS')


if __name__=='__main__':main()
