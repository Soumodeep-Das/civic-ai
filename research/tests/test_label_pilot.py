import json
import pytest
from research.civicai_research.label_pilot import build
from research.civicai_research.text_proposal import propose
from research.tests.test_text_proposal import snapshot


def fixture(tmp_path):
    root = snapshot(tmp_path, [('Large pothole blocks the public passage','Fixing/Reparing Potholes'),
                              ('Large pothole blocks the public passage','Fixing/Reparing Potholes'),
                              ('Unclear municipal service request','Others')])
    p=tmp_path/'proposal'; propose(root,p)
    return p


def test_pilot_blinded_deterministic_and_one_per_group(tmp_path):
    p=fixture(tmp_path); a=tmp_path/'a'; b=tmp_path/'b'
    result=build(p,a)
    assert build(p,b)==result
    assert result['selected_records']==result['selected_groups']==2
    assert not result['training_approved'] and not result['evaluation_holdout']
    for f in a.rglob('*'):
        if f.is_file(): assert f.read_bytes()==(b/f.relative_to(a)).read_bytes()
    tasks=json.loads((a/'reviewer/tasks.json').read_text())
    for t in tasks:
        assert not {'record_id','proposed_category','review_route','proposed_group_id'} & t.keys()
        assert t['category']==t['reviewer_id']==t['decision']==t['privacy_action']==''


@pytest.mark.parametrize('name',['readiness.json','proposals.jsonl','text'])
def test_pilot_rejects_changed_inputs(tmp_path,name):
    p=fixture(tmp_path)
    paths=list((p/'texts').iterdir()) if name=='text' else [p/name]
    for path in paths:
        path.write_bytes(path.read_bytes()+b'changed')
    with pytest.raises(ValueError):build(p,tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_refuses_incomplete_overwrite_nested_and_invalid_size(tmp_path):
    p=fixture(tmp_path)
    for size in [0,101]:
        with pytest.raises(ValueError):build(p,tmp_path/'out',size)
    with pytest.raises(ValueError):build(p,p/'nested')
    build(p,tmp_path/'out',1)
    with pytest.raises(ValueError):build(p,tmp_path/'out')
    (p/'INCOMPLETE').touch()
    with pytest.raises(ValueError):build(p,tmp_path/'other')


def test_path_escape_refused_even_with_matching_index(tmp_path):
    p=fixture(tmp_path)
    rows=[json.loads(x) for x in (p/'proposals.jsonl').read_text().splitlines()]
    for row in rows:
        row['derived_text_ref']='../outside.txt'
    (p/'proposals.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
    from research.civicai_research.manifest import _file_hash
    index=json.loads((p/'artifacts.json').read_text())
    index['proposals.jsonl']=_file_hash(p/'proposals.jsonl')
    (p/'artifacts.json').write_text(json.dumps(index))
    with pytest.raises(ValueError):build(p,tmp_path/'out')
