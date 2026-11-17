import hashlib
import json
import pytest
from research.civicai_research.curation_qa import privacy_spans,near_pairs,source_coverage,run
from research.civicai_research.manifest import _file_hash
from research.tests.test_ai_labels import batch,save


def test_privacy_offsets_overlap_and_no_matched_values():
    text='বাংলা\nName: Alice Example\nAddress: #42 Example Road\nComplaint ID 20201234\nRegards,\nAlice Example\n'
    spans=privacy_spans(text)
    assert {k for s in spans for k in s['kinds']} >= {'self_named_person','address_cue','complaint_identifier','signature'}
    assert all(0<=s['start']<s['end']<=len(text) for s in spans)
    assert all(a['end']<=b['start'] for a,b in zip(spans,spans[1:]))
    assert all(set(s)=={'start','end','kinds'} for s in spans)
    assert any(text[s['start']:s['end']]=='Alice Example' for s in spans)
    assert privacy_spans('The public road has a pothole and no sewage overflow.')==[]


def test_pairs_symmetric_negation_numbers_and_short_text():
    tasks=[{'task_id':'b','text':'The public road near point 20 is not blocked today'},
           {'task_id':'a','text':'The public road near point 10 is blocked today'},
           {'task_id':'c','text':'Streetlight not working'}, {'task_id':'d','text':'streetlight not working'}]
    pairs=near_pairs(tasks,0.7)
    assert pairs==near_pairs(list(reversed(tasks)),0.7)
    p=next(p for p in pairs if p['left']=='a' and p['right']=='b')
    assert p['negation_difference'] and p['numeric_difference'] and not p['same_incident_verified']
    assert next(p for p in pairs if p['left']=='c')['short_generic_text']


@pytest.mark.parametrize('tasks,threshold', [([{'task_id':'a','text':'x'*20001}],0.82),([],1.2),
                                          ([{'task_id':'a','text':'x'}]*2,0.82)])
def test_comparison_bounds_fail_without_truncation(tasks,threshold):
    with pytest.raises(ValueError):near_pairs(tasks,threshold)


def groups_config():
    groups=[{'source_category':'Fixture','source_subcategory':'Unmapped','records':1,'record_ids':['a']}]
    config={'status':'proposed_not_training_labels','families':['roads'],'rules':[]}
    return groups,config


def test_unmapped_source_retained_without_label():
    groups,config=groups_config();rows,summary=source_coverage(groups,config)
    assert rows[0]['disposition']=='unresolved' and rows[0]['proposed_families']==[]
    assert summary['records']==1 and summary['unmatched_pairs']==1
    assert not rows[0]['training_approved']


@pytest.mark.parametrize('case',['overlap','duplicate_rule','invalid_family','count'])
def test_crosswalk_rejects_invalid_membership_and_rules(case):
    groups,config=groups_config()
    rule={'source_category':'Fixture','source_subcategory':'Unmapped','proposed_families':['roads'],
          'disposition':'family_proposal','rationale':'Synthetic fixture.'}
    config['rules']=[rule]
    if case=='overlap':groups.append(dict(groups[0],source_subcategory='Second'))
    if case=='duplicate_rule':config['rules'].append(dict(rule))
    if case=='invalid_family':rule['proposed_families']=['unsupported']
    if case=='count':groups[0]['records']=2
    with pytest.raises(ValueError):source_coverage(groups,config)


def setup(tmp_path):
    pilot,data=batch(tmp_path)
    tasks=json.loads((pilot/'reviewer/tasks.json').read_text())
    row=dict(data['responses'][0]);row.update(task_id=tasks[1]['task_id'],text_sha256=hashlib.sha256(tasks[1]['text'].encode()).hexdigest())
    data['responses'].append(row)
    responses=save(tmp_path,data);proposal=tmp_path/'proposal'
    _,config=groups_config();config['basis_mapping_groups_sha256']=_file_hash(proposal/'mapping-groups.json')
    path=tmp_path/'crosswalk.json';path.write_text(json.dumps(config))
    return proposal,pilot,responses,path


def test_run_is_reproducible_and_preserves_inputs(tmp_path):
    proposal,pilot,responses,crosswalk=setup(tmp_path)
    before=(pilot/'reviewer/tasks.json').read_bytes()
    a,b=tmp_path/'qa-a',tmp_path/'qa-b'
    report=run(proposal,pilot,responses,a,crosswalk)
    assert run(proposal,pilot,responses,b,crosswalk)==report
    assert report['coverage']['records']==3 and report['pilot_records']==2
    assert not report['privacy_approved'] and not report['training_approved']
    assert before==(pilot/'reviewer/tasks.json').read_bytes()
    assert {p.name:p.read_bytes() for p in a.iterdir()}=={p.name:p.read_bytes() for p in b.iterdir()}
    with pytest.raises(ValueError):run(proposal,pilot,responses,a,crosswalk)
    with pytest.raises(ValueError):run(proposal,pilot,responses,pilot/'nested',crosswalk)


def test_partial_pilot_refused(tmp_path):
    proposal,pilot,responses,crosswalk=setup(tmp_path)
    data=json.loads(responses.read_text());data['responses'].pop();responses.write_text(json.dumps(data))
    with pytest.raises(ValueError):run(proposal,pilot,responses,tmp_path/'qa',crosswalk)
    assert not (tmp_path/'qa').exists()


@pytest.mark.parametrize('relative',['mapping-groups.json','readiness.json'])
def test_changed_source_artifact_refused(tmp_path,relative):
    proposal,pilot,responses,crosswalk=setup(tmp_path)
    path=proposal/relative;path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError):run(proposal,pilot,responses,tmp_path/'qa',crosswalk)
    assert not (tmp_path/'qa').exists()


def test_interrupted_output_retains_incomplete_marker(tmp_path,monkeypatch):
    proposal,pilot,responses,crosswalk=setup(tmp_path)
    from research.civicai_research import curation_qa
    def fail(*args):raise OSError('Synthetic write interruption')
    monkeypatch.setattr(curation_qa,'write_json',fail)
    with pytest.raises(OSError):run(proposal,pilot,responses,tmp_path/'qa',crosswalk)
    assert (tmp_path/'qa/INCOMPLETE').exists() and not (tmp_path/'qa/COMPLETE').exists()
