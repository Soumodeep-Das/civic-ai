from copy import deepcopy
import json
from pathlib import Path

import pytest
from research.civicai_research import release as r
from research.civicai_research.manifest import _file_hash


def fixture():
    text = 'Blocked drain. Contact Example Person.'
    record = {'task_id': 'toy-1', 'text': text, 'text_sha256': r.text_hash(text),
              'group_id': 'toy-group', 'candidate_family': 'drainage_and_sewerage',
              'disposition': 'annotation_candidate', 'privacy_flags': [], 'proposed_spans': []}
    packet = {'schema': 'development-review-v1', 'development_only': True, 'records': [record]}
    ledger = {'schema': 'development-decisions-v1', 'packet_sha256': 'bound',
              'author_kind': 'human_reviewer', 'reviewer_id': 'synthetic-test-reviewer',
              'reviewed_at': '2026-11-19T00:00:00+00:00',
              'gates': {g: {'approved': True, 'evidence': 'Synthetic test evidence only, not real approval.'} for g in r.GATES},
              'records': [{'task_id': 'toy-1', 'text_sha256': r.text_hash(text), 'decision': 'include',
                           'family': 'drainage_and_sewerage', 'spans': [{'start': 23, 'end': len(text)-1, 'kinds': ['person']}],
                           'rationale': 'Synthetic test decision, not real human review.'}]}
    return packet, ledger


def test_minimal_export_and_no_person():
    packet, ledger = fixture()
    out = r.validate(packet, ledger, 'bound')
    assert out[0]['text'] == 'Blocked drain. Contact [REDACTED].'
    assert set(out[0]) == {'record_id', 'group_id', 'text', 'label', 'label_origin'}
    assert 'Example Person' in packet['records'][0]['text']


@pytest.mark.parametrize('mutation', [
    lambda p,l: l.update(author_kind='ai_assistant'),
    lambda p,l: l.update(packet_sha256='stale'),
    lambda p,l: l.update(reviewed_at='2026-11-19'),
    lambda p,l: l.update(reviewer_id=''),
    lambda p,l: l['gates']['privacy'].update(approved=False),
    lambda p,l: l['gates']['labels'].update(evidence=''),
    lambda p,l: l['gates'].pop('research_rights'),
    lambda p,l: l.update(training_approved=True),
    lambda p,l: l['records'][0].update(decision='pending'),
    lambda p,l: l['records'][0].update(family='unknown'),
    lambda p,l: l['records'][0].update(text_sha256='stale'),
    lambda p,l: l['records'].append(deepcopy(l['records'][0])),
    lambda p,l: l.update(records=[]),
    lambda p,l: p['records'][0].update(text='changed'),
    lambda p,l: p.update(development_only=False),
])
def test_fail_closed(mutation):
    packet, ledger = fixture(); mutation(packet, ledger)
    with pytest.raises((ValueError, KeyError)): r.validate(packet, ledger, 'bound')


@pytest.mark.parametrize('spans', [
    [{'start': True, 'end': 2, 'kinds': ['person']}],
    [{'start': -1, 'end': 2, 'kinds': ['person']}],
    [{'start': 1, 'end': 50, 'kinds': ['person']}],
    [{'start': 1, 'end': 5, 'kinds': ['person']}, {'start': 4, 'end': 6, 'kinds': ['person']}],
    [{'start': 0, 'end': 6, 'kinds': ['person']}],
])
def test_bad_redactions(spans):
    with pytest.raises(ValueError): r.redact('abcdef', spans)


def test_unicode_offsets():
    assert r.redact('নাম: অমল, drain', [{'start': 5, 'end': 8, 'kinds': ['person']}]) == 'নাম: [REDACTED], drain'


def test_duplicate_after_redaction_and_group_conflict():
    packet, ledger = fixture()
    second = deepcopy(packet['records'][0]); second.update(task_id='toy-2', group_id='other')
    packet['records'].append(second)
    decision = deepcopy(ledger['records'][0]); decision['task_id']='toy-2'; ledger['records'].append(decision)
    with pytest.raises(ValueError, match='duplicate'): r.validate(packet, ledger, 'bound')
    second['group_id'] = 'toy-group'; decision['family'] = 'solid_waste'
    with pytest.raises(ValueError, match='Conflicting'): r.validate(packet, ledger, 'bound')


def test_real_export_artifacts_and_immutable_input(tmp_path, monkeypatch):
    monkeypatch.setattr(r, 'ROOT', tmp_path)
    packet, ledger = fixture()
    source = tmp_path/'data/review/source'
    r.save(source, {'packet.json': packet}, ledger)
    before = (source/'packet.json').read_bytes()
    output = tmp_path/'data/review/export'
    result = r.export(source, source/'decisions.json', output)
    assert result['training_approved'] is False and result['evaluation_holdout'] is False
    assert (output/'COMPLETE').exists() and not (output/'INCOMPLETE').exists()
    assert (source/'packet.json').read_bytes() == before
    for name, sha in json.loads((output/'artifacts.json').read_text()).items(): assert _file_hash(output/name)==sha
    with pytest.raises(ValueError): r.export(source, source/'decisions.json', output)
    with pytest.raises(ValueError): r.export(source, source/'decisions.json', tmp_path/'public')
    (source/'packet.json').write_text('{}')
    with pytest.raises(ValueError): r.export(source, source/'decisions.json', tmp_path/'data/review/other')


def test_write_failure_stays_incomplete(tmp_path, monkeypatch):
    def fail(*args): raise OSError('synthetic failure')
    monkeypatch.setattr(r, 'write_json', fail)
    with pytest.raises(OSError): r.save(tmp_path/'out', {'data.json': []})
    assert (tmp_path/'out/INCOMPLETE').exists()
    assert not (tmp_path/'out/COMPLETE').exists()


def test_prepare_pending_packet_and_stale_source(tmp_path, monkeypatch):
    monkeypatch.setattr(r, 'ROOT', tmp_path)
    root = tmp_path/'data/review'
    pilot, ready, context = root/'pilot', root/'ready', root/'context'
    pilot.mkdir(parents=True); (pilot/'reviewer').mkdir()
    r.write_json(pilot/'reviewer/tasks.json', [{'task_id': 'toy', 'text': 'Blocked drain'}])
    r.write_json(pilot/'artifacts.json', {'reviewer/tasks.json': _file_hash(pilot/'reviewer/tasks.json')})
    (pilot/'COMPLETE').touch()
    r.save(context, {'privacy-spans.json': [{'task_id': 'toy', 'text_sha256': r.text_hash('Blocked drain'), 'proposed_spans': []}]})
    r.save(ready, {'inventory.json': [{'task_id': 'toy', 'component': 'group', 'candidate_family': 'drainage_and_sewerage', 'disposition': 'annotation_candidate', 'privacy_flags': ['context_not_reviewed']}],
                   'summary.json': {'training_approved': False, 'input_sha256': {'tasks': _file_hash(pilot/'reviewer/tasks.json'), 'privacy': _file_hash(context/'privacy-spans.json')}}})
    out = root/'packet'
    assert r.prepare(pilot, ready, context, out)['records']==1
    ledger = r.read(out/'decisions.json')
    assert ledger['author_kind']=='pending' and ledger['records'][0]['decision']=='pending'
    assert ledger['packet_sha256']==_file_hash(out/'packet.json')
    with pytest.raises(ValueError): r.export(out, out/'decisions.json', root/'refused')
    assert not (root/'refused').exists()
    (pilot/'reviewer/tasks.json').write_text('[]')
    with pytest.raises(ValueError): r.prepare(pilot, ready, context, root/'stale')
