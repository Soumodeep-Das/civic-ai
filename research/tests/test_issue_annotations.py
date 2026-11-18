"""Synthetic cases for strict text-evidence binding; not semantic accuracy tests."""
from copy import deepcopy
import hashlib
import pytest

from research.civicai_research import issue_annotations as module
from research.civicai_research.manifest import _file_hash
from research.civicai_research.text_proposal import write_json


def fixture(tmp_path):
    pilot, draft, authored = [tmp_path / p for p in ('pilot', 'draft', 'authored')]
    for path in (pilot / 'reviewer', draft, authored): path.mkdir(parents=True)
    tasks = [{'task_id': 'a', 'text': 'বাংলা broken footpath'}, {'task_id': 'b', 'text': 'Water leaking'}]
    write_json(pilot / 'reviewer/tasks.json', tasks)
    write_json(pilot / 'artifacts.json', {'reviewer/tasks.json': _file_hash(pilot / 'reviewer/tasks.json')})
    (pilot / 'COMPLETE').touch()
    prior = [{'task_id': t['task_id'], 'text_sha256': hashlib.sha256(t['text'].encode()).hexdigest(),
              'annotation_state': 'transferred_needs_text_review' if i == 0 else 'needs_richer_annotation',
              'issues': []} for i, t in enumerate(tasks)]
    write_json(draft / 'annotations.json', prior)
    write_json(draft / 'contract.json', {'status': 'synthetic_fixture'})
    write_json(draft / 'summary.json', {'input_sha256': {'pilot_tasks': _file_hash(pilot / 'reviewer/tasks.json')}})
    write_json(draft / 'artifacts.json', {p.name: _file_hash(p) for p in draft.iterdir()})
    (draft / 'COMPLETE').touch()
    bindings = {'pilot_tasks': _file_hash(pilot / 'reviewer/tasks.json'),
                'prior_annotations': _file_hash(draft / 'annotations.json'),
                'prior_contract': _file_hash(draft / 'contract.json')}
    rows = []
    for i, task in enumerate(tasks):
        rows.append({'task_id': task['task_id'], 'text_sha256': prior[i]['text_sha256'],
                     'outcome': 'described_issue' if i == 0 else 'clarification_needed',
                     'rationale': 'Synthetic text explicitly names a condition; source type may be unknown.',
                     'issues': [{'family': 'roads_and_pedestrian_access' if i == 0 else 'unknown',
                                 'asset': 'footpath' if i == 0 else 'unknown',
                                 'issue_kind': 'damage' if i == 0 else 'leakage',
                                 'evidence': [{'start': 6 if i == 0 else 0, 'end': len(task['text'])}],
                                 'basis': 'complainant_report_not_verified_event', 'setting': 'unknown',
                                 'time_state': 'unknown', 'setting_evidence': [], 'time_evidence': []}]})
    data = {'version': module.VERSION, 'author_kind': 'ai_assistant', 'input_sha256': bindings,
            **{f: False for f in module.FLAGS}, 'rows': rows}
    annotations = authored / 'annotations.json'; write_json(annotations, data)
    return pilot, draft, annotations, data, tasks, prior, bindings


def test_deterministic_complete_run_preserves_originals(tmp_path):
    pilot, draft, annotations, data, tasks, prior, bindings = fixture(tmp_path)
    before = {p: p.read_bytes() for folder in (pilot, draft, annotations.parent)
              for p in folder.rglob('*') if p.is_file()}
    outputs = [tmp_path / 'one', tmp_path / 'two']
    for output in outputs:
        summary = module.run(pilot, draft, annotations, output)
        assert summary['records_read_by_ai'] == 2 and summary['issue_descriptions'] == 2
        assert summary['previously_unresolved_reviewed'] == 1
        assert summary['previously_transferred_reviewed'] == 1
        assert summary['changed_transferred_records'] == 1
        assert all(summary[f] is False for f in module.FLAGS)
        assert (output / 'COMPLETE').exists() and not (output / 'INCOMPLETE').exists()
    assert {p.name: p.read_bytes() for p in outputs[0].iterdir()} == {p.name: p.read_bytes() for p in outputs[1].iterdir()}
    assert all(p.read_bytes() == value for p, value in before.items())
    assert tasks[0]['text'][6:] == 'broken footpath'
    with pytest.raises(ValueError): module.run(pilot, draft, annotations, outputs[0])
    with pytest.raises(ValueError): module.run(pilot, draft, annotations, pilot / 'nested')


@pytest.mark.parametrize('case', ['approval', 'human', 'version', 'bindings', 'missing', 'extra', 'duplicate',
    'hash', 'short_rationale', 'severity', 'unknown_family', 'asset', 'asset_family', 'kind',
    'duplicate_issue', 'empty_evidence', 'offset', 'bool_offset', 'overlap', 'whitespace',
    'event_verified', 'context_without_evidence', 'unknown_with_evidence', 'invalid_context',
    'unusable_with_issues', 'described_without_issues', 'unknown_source_described'])
def test_invalid_annotations_refused(tmp_path, case):
    pilot, draft, annotations, data, tasks, prior, bindings = fixture(tmp_path)
    row = data['rows'][0]; issue = row['issues'][0]
    if case == 'approval': data['training_approved'] = True
    if case == 'human': data['author_kind'] = 'independent_human'
    if case == 'version': data['version'] = 'unapproved-version'
    if case == 'bindings': data['input_sha256'] = {}
    if case == 'missing': data['rows'].pop()
    if case == 'extra': data['rows'].append(dict(row, task_id='extra'))
    if case == 'duplicate': data['rows'].append(deepcopy(row))
    if case == 'hash': row['text_sha256'] = 'f' * 64
    if case == 'short_rationale': row['rationale'] = ' '
    if case == 'severity': issue['severity'] = 'high'
    if case == 'unknown_family': issue['family'] = 'invented'
    if case == 'asset': issue['asset'] = 'invented'
    if case == 'asset_family': issue['asset'] = 'carcass'
    if case == 'kind': issue['issue_kind'] = 'invented'
    if case == 'duplicate_issue': row['issues'].append(deepcopy(issue))
    if case == 'empty_evidence': issue['evidence'] = []
    if case == 'offset': issue['evidence'][0]['end'] = 9999
    if case == 'bool_offset': issue['evidence'][0]['start'] = False
    if case == 'overlap': issue['evidence'].append(dict(issue['evidence'][0]))
    if case == 'whitespace': issue['evidence'] = [{'start': 5, 'end': 6}]
    if case == 'event_verified': issue['basis'] = 'verified_incident'
    if case == 'context_without_evidence': issue['setting'] = 'public'
    if case == 'unknown_with_evidence': issue['time_evidence'] = deepcopy(issue['evidence'])
    if case == 'invalid_context': issue['time_state'] = 'urgent'
    if case == 'unusable_with_issues': row['outcome'] = 'unusable_text'
    if case == 'described_without_issues': row['issues'] = []
    if case == 'unknown_source_described': data['rows'][1]['outcome'] = 'described_issue'
    write_json(annotations, data)
    with pytest.raises(ValueError): module.run(pilot, draft, annotations, tmp_path / 'out')
    assert not (tmp_path / 'out').exists()


def test_context_and_multiple_components_require_separate_evidence(tmp_path):
    pilot, draft, annotations, data, tasks, prior, bindings = fixture(tmp_path)
    issue = data['rows'][0]['issues'][0]
    issue['setting'] = 'public'; issue['setting_evidence'] = deepcopy(issue['evidence'])
    second = deepcopy(issue); second['issue_kind'] = 'maintenance'
    data['rows'][0]['issues'].append(second)
    # Validates shape/binding only, not that the synthetic quote entails public ownership.
    rows, _ = module.validate(data, tasks, prior, bindings)
    assert len(rows['a']['issues']) == 2


@pytest.mark.parametrize('relative', ['annotations.json', 'contract.json', 'summary.json'])
def test_stale_draft_inputs_refused(tmp_path, relative):
    pilot, draft, annotations, *_ = fixture(tmp_path)
    path = draft / relative; path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ValueError): module.run(pilot, draft, annotations, tmp_path / 'out')


def test_interruption_cannot_publish_complete(tmp_path, monkeypatch):
    pilot, draft, annotations, *_ = fixture(tmp_path)
    def fail(*args): raise OSError('Synthetic interruption')
    monkeypatch.setattr(module, 'write_json', fail)
    with pytest.raises(OSError): module.run(pilot, draft, annotations, tmp_path / 'out')
    assert (tmp_path / 'out/INCOMPLETE').exists()
    assert not (tmp_path / 'out/COMPLETE').exists()
