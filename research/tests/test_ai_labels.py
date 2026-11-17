import hashlib
import json
import pytest
from research.civicai_research.ai_labels import validate
from research.civicai_research.label_pilot import build
from research.civicai_research.manifest import _file_hash
from research.tests.test_label_pilot import fixture


def batch(tmp_path):
    proposal=fixture(tmp_path);p=tmp_path/'pilot';build(proposal,p)
    task=json.loads((p/'reviewer/tasks.json').read_text())[0]
    data={'kind':'ai_assisted_proposals','author':'synthetic test assistant',
          'limitations':['Not human reference'],'training_approved':False,
          'independent_human_review':False,'privacy_approved':False,
          'pilot_tasks_sha256':_file_hash(p/'reviewer/tasks.json'),
          'taxonomy_sha256':_file_hash(p/'reviewer/taxonomy.json'),
          'responses':[{'task_id':task['task_id'],'text_sha256':hashlib.sha256(task['text'].encode()).hexdigest(),
                        'decision':'unclear','proposed_categories':[],
                        'rationale':'Synthetic fixture, no annotation claim.','privacy_concerns':[]}]}
    return p,data


def save(tmp_path,data):
    f=tmp_path/'responses.json';f.write_text(json.dumps(data),encoding='utf-8');return f


def test_partial_ai_batch_never_grants_approval(tmp_path):
    p,data=batch(tmp_path);r=validate(p,save(tmp_path,data))
    assert r['reviewed_by_ai']==1 and r['remaining']==1
    assert not r['training_approved'] and not r['independent_human_review']


@pytest.mark.parametrize('key',['training_approved','independent_human_review','privacy_approved'])
def test_false_approval_claim_rejected(tmp_path,key):
    p,data=batch(tmp_path);data[key]=True
    with pytest.raises(ValueError):validate(p,save(tmp_path,data))


@pytest.mark.parametrize('case',['unknown','duplicate','text_hash','category','decision','empty','extra','missing_rationale'])
def test_invalid_response_rejected(tmp_path,case):
    p,data=batch(tmp_path);r=data['responses'][0]
    if case=='unknown':r['task_id']='missing'
    if case=='duplicate':data['responses'].append(dict(r))
    if case=='text_hash':r['text_sha256']='0'*64
    if case=='category':r.update(decision='supported',proposed_categories=['fake'])
    if case=='decision':r['decision']='supported'
    if case=='empty':data['responses']=[]
    if case=='extra':r['category_label']='road_damage'
    if case=='missing_rationale':r['rationale']=' '
    with pytest.raises(ValueError):validate(p,save(tmp_path,data))


def test_changed_pilot_rejected(tmp_path):
    p,data=batch(tmp_path);path=p/'reviewer/tasks.json';path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError):validate(p,save(tmp_path,data))
