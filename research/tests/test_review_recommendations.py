"""Synthetic review-contract tests; no real complaint text or labels."""
import hashlib
import json

import pytest

from research.civicai_research import review_recommendations as review
from research.civicai_research.manifest import _file_hash
from research.civicai_research.text_proposal import write_json


def fixture(tmp_path):
    qa, pilot = tmp_path / 'qa', tmp_path / 'pilot'
    qa.mkdir(); (pilot / 'reviewer').mkdir(parents=True)
    texts = {'a': 'বাংলা Alice reports debris', 'b': 'Public road is damaged',
             'c': 'A sensitive household dispute', 'd': 'Example signature'}
    tasks = [{'task_id': k, 'text': v} for k, v in texts.items()]
    write_json(pilot / 'reviewer/tasks.json', tasks)
    write_json(pilot / 'artifacts.json', {'reviewer/tasks.json': _file_hash(pilot / 'reviewer/tasks.json')})
    (pilot / 'COMPLETE').touch()
    privacy = [{'task_id': k, 'text_sha256': hashlib.sha256(v.encode()).hexdigest(),
                'ai_concerns': ['synthetic'], 'proposed_spans': [],
                'review_status': 'pending', 'privacy_approved': False} for k, v in texts.items()]
    privacy[-1]['proposed_spans'] = [{'start': 0, 'end': 7, 'kinds': ['signature']}]
    write_json(qa / 'privacy-spans.json', privacy)
    write_json(qa / 'source-coverage.json', [
        {'source_category': 'Fixture', 'source_subcategory': 'Scope', 'disposition': 'scope_review', 'records': 5},
        {'source_category': 'Fixture', 'source_subcategory': 'Unknown', 'disposition': 'unresolved', 'records': 2}])
    write_json(qa / 'near-duplicates.json', [{'left': 'a', 'right': 'b'}])
    write_json(qa / 'summary.json', {'raw_sha256': '0' * 64,
                                   'input_sha256': {'pilot_tasks': _file_hash(pilot / 'reviewer/tasks.json')}})
    write_json(qa / 'artifacts.json', {p.name: _file_hash(p) for p in qa.iterdir()})
    (qa / 'COMPLETE').touch()
    authored = tmp_path / 'authored'; authored.mkdir()
    prior = authored / 'prior.json'; write_json(prior, privacy)
    paths = {n: qa / (n + '.json') for n in ('source-coverage', 'near-duplicates', 'privacy-spans', 'summary')}
    paths.update({'pilot-tasks': pilot / 'reviewer/tasks.json', 'prior-privacy': prior})
    rows = []
    for r, decision in zip(privacy, ['redact_span_proposal', 'retain_context_proposal', 'hold_sensitive_context']):
        rows.append({'task_id': r['task_id'], 'text_sha256': r['text_sha256'],
                     'recommendation': decision, 'rationale': 'Synthetic contextual judgment for testing.',
                     'proposed_spans': [{'start': 6, 'end': 11, 'kinds': ['name']}] if r['task_id'] == 'a' else []})
    ledger = {'schema_version': 'context-review-v1', 'author_kind': 'ai_assistant',
              **{k: False for k in review.APPROVALS}, 'input_sha256': {k: _file_hash(p) for k, p in paths.items()},
              'scope': [{'source_category': 'Fixture', 'source_subcategory': 'Scope',
                         'recommendation': 'record_context_required', 'rationale': 'Synthetic ambiguous scope needs text review.'}],
              'privacy': rows,
              'duplicates': [{'left': 'a', 'right': 'b', 'recommendation': 'propose_split_containment_keep_both',
                              'same_incident_verified': False, 'rationale': 'Synthetic lexical candidate; identity unverified.'}]}
    recommendations = authored / 'recommendations.json'; write_json(recommendations, ledger)
    return qa, pilot, prior, recommendations, ledger


def test_complete_deterministic_review_preserves_inputs_and_keeps_gates_closed(tmp_path):
    qa, pilot, prior, recommendations, _ = fixture(tmp_path)
    before = {p: p.read_bytes() for root in (qa, pilot, prior.parent) for p in root.rglob('*') if p.is_file()}
    outputs = [tmp_path / 'out-a', tmp_path / 'out-b']
    for output in outputs:
        summary = review.run(qa, pilot, prior, recommendations, output)
        assert summary['contextual_privacy_records_reviewed'] == 3
        assert summary['scope_records_associated'] == 5
        assert summary['unresolved_source_pairs_unchanged'] == 1
        assert summary['combined_spans'] == 2 and summary['source_texts_modified'] == 0
        assert all(summary[k] is False for k in review.APPROVALS)
        effective = review.read(output / 'privacy-spans.json')
        assert effective[-1] == review.read(prior)[-1]
        assert all(r['privacy_approved'] is False for r in effective)
        span = effective[0]['proposed_spans'][0]
        assert 'বাংলা Alice reports debris'[span['start']:span['end']] == 'Alice'
    assert before == {p: p.read_bytes() for p in before}
    assert {p.name: p.read_bytes() for p in outputs[0].iterdir()} == {p.name: p.read_bytes() for p in outputs[1].iterdir()}
    with pytest.raises(ValueError): review.run(qa, pilot, prior, recommendations, outputs[0])
    with pytest.raises(ValueError): review.run(qa, pilot, prior, recommendations, pilot / 'nested')


@pytest.mark.parametrize('case', ['approval', 'human_author', 'missing_privacy', 'extra_privacy',
    'duplicate_privacy', 'missing_scope', 'invalid_scope', 'missing_duplicate', 'verified_event',
    'merge_request', 'text_hash', 'input_hash', 'negative_offset', 'bool_offset', 'too_long',
    'overlap', 'empty_redaction', 'unexpected_spans', 'empty_rationale', 'injected_field'])
def test_invalid_recommendations_fail_before_output(tmp_path, case):
    qa, pilot, prior, recommendations, ledger = fixture(tmp_path)
    row = ledger['privacy'][0]
    if case == 'approval': ledger['privacy_approved'] = True
    if case == 'human_author': ledger['author_kind'] = 'human'
    if case == 'missing_privacy': ledger['privacy'].pop()
    if case == 'extra_privacy': ledger['privacy'].append(dict(row, task_id='unknown'))
    if case == 'duplicate_privacy': ledger['privacy'].append(dict(row))
    if case == 'missing_scope': ledger['scope'].clear()
    if case == 'invalid_scope': ledger['scope'][0]['recommendation'] = 'training_approved'
    if case == 'missing_duplicate': ledger['duplicates'].clear()
    if case == 'verified_event': ledger['duplicates'][0]['same_incident_verified'] = True
    if case == 'merge_request': ledger['duplicates'][0]['recommendation'] = 'merge'
    if case == 'text_hash': row['text_sha256'] = '1' * 64
    if case == 'input_hash': ledger['input_sha256']['prior-privacy'] = '1' * 64
    if case == 'negative_offset': row['proposed_spans'][0]['start'] = -1
    if case == 'bool_offset': row['proposed_spans'][0]['start'] = True
    if case == 'too_long': row['proposed_spans'][0]['end'] = 10000
    if case == 'overlap': row['proposed_spans'].append(dict(row['proposed_spans'][0]))
    if case == 'empty_redaction': row['proposed_spans'].clear()
    if case == 'unexpected_spans': row['recommendation'] = 'retain_context_proposal'
    if case == 'empty_rationale': row['rationale'] = ' '
    if case == 'injected_field': row['privacy_approved'] = True
    write_json(recommendations, ledger)
    with pytest.raises(ValueError): review.run(qa, pilot, prior, recommendations, tmp_path / 'out')
    assert not (tmp_path / 'out').exists()


@pytest.mark.parametrize('case', ['task_mutation', 'qa_mutation', 'prior_concern', 'prior_offset', 'other_pilot'])
def test_changed_or_mismatched_inputs_refused(tmp_path, case):
    qa, pilot, prior, recommendations, ledger = fixture(tmp_path)
    if case == 'task_mutation': (pilot / 'reviewer/tasks.json').write_text('[]')
    if case == 'qa_mutation': (qa / 'source-coverage.json').write_text('[]')
    if case.startswith('prior_'):
        rows = review.read(prior)
        if case == 'prior_concern': rows[0]['ai_concerns'] = []
        else: rows[-1]['proposed_spans'][0]['end'] = 10000
        write_json(prior, rows)
        ledger['input_sha256']['prior-privacy'] = _file_hash(prior)
    if case == 'other_pilot':
        summary = review.read(qa / 'summary.json'); summary['input_sha256']['pilot_tasks'] = '1' * 64
        write_json(qa / 'summary.json', summary)
        index = review.read(qa / 'artifacts.json'); index['summary.json'] = _file_hash(qa / 'summary.json')
        write_json(qa / 'artifacts.json', index)
        ledger['input_sha256']['summary'] = index['summary.json']
    write_json(recommendations, ledger)
    with pytest.raises(ValueError): review.run(qa, pilot, prior, recommendations, tmp_path / 'out')
    assert not (tmp_path / 'out').exists()


def test_interruption_does_not_mark_complete(tmp_path, monkeypatch):
    qa, pilot, prior, recommendations, _ = fixture(tmp_path)
    def fail(*args): raise OSError('Synthetic interruption')
    monkeypatch.setattr(review, 'write_json', fail)
    with pytest.raises(OSError): review.run(qa, pilot, prior, recommendations, tmp_path / 'out')
    assert (tmp_path / 'out/INCOMPLETE').exists()
    assert not (tmp_path / 'out/COMPLETE').exists()
