import csv
import io
import json
from pathlib import Path

import pytest

from research.civicai_research.opencity import ingest
from research.civicai_research.text_proposal import propose, screen
from research.civicai_research import text_proposal


def snapshot(tmp_path, records=None):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["title", "description", "category_title", "sub_category_title", "created_at"])
    for text, label in records or [("Large pothole\nblocks the school entrance", "Fixing/Reparing Potholes")]:
        writer.writerow(["Synthetic fixture", text, "Fixture", label, "2020-01-01"])
    root = tmp_path / "raw"
    ingest(stream.getvalue().encode(), root, b"{}")
    return root


def rows(output):
    return [json.loads(line) for line in (output / "proposals.jsonl").read_text(encoding="utf-8").splitlines()]


def test_proposal_reproducible_preserves_multiline_and_never_grants_training(tmp_path):
    root = snapshot(tmp_path)
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    a, b = tmp_path / 'a', tmp_path / 'b'
    report = propose(root, a)
    assert propose(root, b) == report
    for p in a.rglob('*'):
        if p.is_file(): assert p.read_bytes() == (b/p.relative_to(a)).read_bytes()
    r = rows(a)[0]
    assert '\n' in (a/r['derived_text_ref']).read_text()
    assert r['category_label'] is None and r['annotation_status']=='pending' and r['split']=='unassigned'
    assert r['privacy_status'].startswith('pending')
    assert r['proposed_category']=='road_damage' and r['review_route']=='candidate_review'
    assert not report['training_approved'] and report['class_support']['road_damage']['approved_records']==0
    assert before == {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_redaction_merges_overlapping_url_email_phone_and_preserves_negation():
    value = 'Not blocked. https://example.invalid/a?email=a@example.invalid&phone=9876543210 call 98765 43210'
    derived, spans = screen(value)
    assert derived == 'Not blocked. [REDACTED] call [REDACTED]'
    assert len(spans)==2 and spans[0]['kinds']==['email','phone','url']
    assert all(a['end'] <= b['start'] for a,b in zip(spans,spans[1:]))


def test_groups_include_every_duplicate_and_hold_category_conflicts(tmp_path):
    entries = [('Large public passage blocked at point 10', 'Fixing/Reparing Potholes')]*25
    entries.append(('Large public passage blocked at point 20', 'Stop Water Leakage'))
    root = snapshot(tmp_path, entries)
    out = tmp_path/'out'; report = propose(root,out)
    groups = json.loads((out/'groups.json').read_text())
    assert len(groups)==1 and len(groups[0]['members'])==26
    assert report['category_conflict_groups']==1
    assert {r['review_route'] for r in rows(out)}=={'targeted_review'}
    assert all('group_category_conflict' in r['review_reasons'] for r in rows(out))


def test_redaction_collision_and_unmapped_member_block_candidate_pool(tmp_path):
    root = snapshot(tmp_path, [('Large pothole reported by alice@example.invalid', 'Fixing/Reparing Potholes'),
                              ('Large pothole reported by bob@example.invalid', 'Others')])
    out=tmp_path/'out'; report=propose(root,out)
    assert report['group_count']==1 and report['privacy_flagged_records']==2
    assert report['class_support']['road_damage']['screened_candidate_records']==0
    assert all('group_unresolved_mapping' in r['review_reasons'] for r in rows(out))


def test_empty_import_omissions_do_not_shift_source_identity(tmp_path):
    root=snapshot(tmp_path,[('', 'Others'),('Damaged pavement blocks public access','Report A Broken Footpath')])
    report=propose(root,tmp_path/'out')
    assert report['records']==1
    assert rows(tmp_path/'out')[0]['source_record_id'].endswith('row-2')


@pytest.mark.parametrize('target',['source.csv','publisher-metadata.json','source-labels.json','text'])
def test_tampered_input_rejected_before_output(tmp_path,target):
    root=snapshot(tmp_path)
    if target=='source-labels.json':
        path=root/target; data=json.loads(path.read_text());data[0]['source_subcategory']='Others';path.write_text(json.dumps(data))
    else:
        path=next((root/'texts').iterdir()) if target=='text' else root/target
        path.write_bytes(path.read_bytes()+b'altered')
    with pytest.raises(ValueError): propose(root,tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_incomplete_and_overwrite_refused(tmp_path):
    root=snapshot(tmp_path);out=tmp_path/'out'
    propose(root,out)
    with pytest.raises(ValueError,match='Output exists'):propose(root,out)
    (root/'INCOMPLETE').write_text('interrupted')
    with pytest.raises(ValueError,match='not complete'):propose(root,tmp_path/'b')


def test_output_cannot_mutate_snapshot(tmp_path):
    root = snapshot(tmp_path)
    with pytest.raises(ValueError, match='outside the immutable snapshot'):
        propose(root, root/'derived')
    assert not (root/'derived').exists()


def test_annotated_input_cannot_be_recast_as_unreviewed_proposal(tmp_path):
    root=snapshot(tmp_path)
    p=root/'manifest.jsonl'; r=json.loads(p.read_text());r.update(annotation_status='annotated',category_label='road_damage',annotator_id='fixture')
    p.write_text(json.dumps(r)+'\n')
    with pytest.raises(ValueError):propose(root,tmp_path/'out')


def test_interrupted_write_retains_incomplete_marker(tmp_path, monkeypatch):
    root=snapshot(tmp_path)
    def interrupted(*args): raise OSError('fixture interruption')
    monkeypatch.setattr(text_proposal, 'write_json', interrupted)
    with pytest.raises(OSError):propose(root,tmp_path/'out')
    assert (tmp_path/'out/INCOMPLETE').exists()
    assert not (tmp_path/'out/COMPLETE').exists()


def test_unknown_mapping_category_rejected(tmp_path):
    root=snapshot(tmp_path)
    m=json.loads(text_proposal.DEFAULT_MAPPING.read_text())
    m['rules'][0]['proposed_category']='unsupported'
    p=tmp_path/'mapping.json';p.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='mapping rule'):propose(root,tmp_path/'out',p)


def test_non_latin_text_preserved_and_explicitly_queued(tmp_path):
    root=snapshot(tmp_path,[('রাস্তায় জল জমে আছে এবং চলাচল বন্ধ', 'Flooding/Waterlogging Of Roads And Footpaths')])
    out=tmp_path/'out';report=propose(root,out)
    r=rows(out)[0]
    assert r['script_bucket_not_language']=='bengali_script'
    assert 'script_review' in r['review_reasons']
    assert (out/r['derived_text_ref']).read_text(encoding='utf-8').startswith('রাস্তায়')
    assert report['class_support']['waterlogging']['screened_candidate_records']==0
