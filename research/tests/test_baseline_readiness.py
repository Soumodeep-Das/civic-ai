"""Synthetic planning tests, never research model metrics."""
from copy import deepcopy
import pytest

from research.civicai_research import baseline_readiness as module
from research.civicai_research.manifest import _file_hash
from research.civicai_research.text_proposal import write_json
from research.tests.test_issue_annotations import fixture as annotation_fixture


def planning_rows():
    rows = {k: {'outcome': 'described_issue', 'issues': [
        {'family': 'solid_waste', 'asset': 'waste', 'issue_kind': 'accumulation'}]} for k in 'abcd'}
    keys = {k: {'proposed_group_id': 'group-' + k} for k in rows}
    privacy = {k: {'proposed_spans': [], 'privacy_approved': False} for k in rows}
    return rows, keys, privacy


def link(a, b):
    return {'left': a, 'right': b, 'same_incident_verified': False,
            'recommendation': 'propose_split_containment_keep_both'}


def test_same_family_components_retained_and_related_records_not_double_counted():
    rows, keys, privacy = planning_rows()
    rows['a']['issues'].append({'family': 'solid_waste', 'asset': 'collection_service', 'issue_kind': 'missing_service'})
    inventory, support, summary = module.assess(rows, keys, privacy, [link('a', 'b')], 3)
    assert summary['annotation_candidates'] == 4 and summary['candidate_containment_components'] == 3
    assert summary['same_family_multi_component_candidates'] == 1
    assert summary['proposed_development_families'] == ['solid_waste']
    assert all(not r['training_eligible'] and r['development_only'] for r in inventory)
    assert summary['training_eligible_records'] == summary['split_assignments_created'] == 0
    assert summary['candidate_privacy_flags_nonexclusive'] == {'context_not_reviewed': 4}
    assert next(r for r in support if r['family'] == 'parks_trees_and_waterbodies')['candidate_records'] == 0


def test_containment_is_transitive_before_exclusion_and_order_independent():
    rows, keys, privacy = planning_rows()
    rows['b']['outcome'] = 'clarification_needed'
    links = [link('a', 'b'), link('b', 'c')]
    inventory, _, summary = module.assess(rows, keys, privacy, links, 3)
    assert summary['dispositions'] == {'group_uncertainty': 2, 'clarification_needed': 1, 'annotation_candidate': 1}
    assert module.assess(dict(reversed(list(rows.items()))), keys, privacy, list(reversed(links)), 3) == (inventory, _, summary)
    assert len({r['component'] for r in inventory if r['task_id'] in 'abc'}) == 1


def test_base_groups_and_cross_family_conflict_are_not_ignored():
    rows, keys, privacy = planning_rows()
    keys['b']['proposed_group_id'] = keys['a']['proposed_group_id']
    rows['b']['issues'][0]['family'] = 'drainage_and_sewerage'
    inventory, _, summary = module.assess(rows, keys, privacy, [], 3)
    assert summary['dispositions']['group_conflict'] == 2
    assert summary['annotation_candidates'] == 2
    rows['c']['issues'].append({'family': 'drainage_and_sewerage'})
    assert module.assess(rows, keys, privacy, [], 3)[2]['dispositions']['cross_family'] == 1


def test_privacy_risks_are_reported_not_silently_cleared_or_dropped():
    rows, keys, privacy = planning_rows()
    privacy['a']['proposed_spans'] = [{'start': 0, 'end': 2, 'kinds': ['synthetic']}]
    privacy['a']['context_recommendation'] = 'hold_sensitive_context'
    privacy['b']['context_recommendation'] = 'retain_context_proposal'
    summary = module.assess(rows, keys, privacy, [], 3)[2]
    assert summary['annotation_candidates'] == 4
    assert summary['candidate_privacy_flags_nonexclusive'] == {
        'span_proposal': 1, 'context_hold': 1, 'retain_proposal_not_clearance': 1, 'context_not_reviewed': 2}
    assert summary['privacy_approved_records'] == 0


@pytest.mark.parametrize('case', ['unknown_link', 'self_link', 'reverse_duplicate', 'verified_event',
    'unknown_action', 'missing_privacy', 'privacy_approval', 'unknown_privacy', 'empty_redaction', 'bool_floor'])
def test_invalid_planning_inputs_refused(case):
    rows, keys, privacy = planning_rows(); links = []; minimum = 3
    if case == 'unknown_link': links = [link('a', 'z')]
    if case == 'self_link': links = [link('a', 'a')]
    if case == 'reverse_duplicate': links = [link('a', 'b'), link('b', 'a')]
    if case == 'verified_event': links = [dict(link('a', 'b'), same_incident_verified=True)]
    if case == 'unknown_action': links = [dict(link('a', 'b'), recommendation='merge')]
    if case == 'missing_privacy': privacy.pop('a')
    if case == 'privacy_approval': privacy['a']['privacy_approved'] = True
    if case == 'unknown_privacy': privacy['a']['context_recommendation'] = 'approved'
    if case == 'empty_redaction': privacy['a']['context_recommendation'] = 'redact_span_proposal'
    if case == 'bool_floor': minimum = True
    with pytest.raises(ValueError): module.assess(rows, keys, privacy, links, minimum)


def reindex(root):
    write_json(root / 'artifacts.json', {p.relative_to(root).as_posix(): _file_hash(p)
               for p in root.rglob('*.json') if p.name != 'artifacts.json'})
    (root / 'COMPLETE').touch()


def fixture(tmp_path):
    pilot, draft, authored, data, tasks, prior, bindings = annotation_fixture(tmp_path)
    annotations = tmp_path / 'annotations'; annotations.mkdir()
    write_json(annotations / 'annotations.json', data); reindex(annotations)
    (pilot / 'coordinator').mkdir()
    keys = [dict(r, record_id='source-' + r['task_id'], proposed_group_id='group-' + r['task_id']) for r in prior]
    write_json(pilot / 'coordinator/key.json', keys)
    write_json(pilot / 'coordinator/summary.json', {'raw_sha256': '0' * 64, 'evaluation_holdout': False, 'training_approved': False})
    reindex(pilot)
    context = tmp_path / 'context'; context.mkdir()
    privacy = [dict(task_id=r['task_id'], text_sha256=r['text_sha256'], proposed_spans=[], privacy_approved=False) for r in prior]
    write_json(context / 'privacy-spans.json', privacy)
    write_json(context / 'summary.json', {'raw_sha256': '0' * 64, 'training_approved': False, 'privacy_approved': False,
               'input_sha256': {'pilot-tasks': bindings['pilot_tasks']}})
    write_json(context / 'recommendations.json', {'author_kind': 'ai_assistant', 'training_approved': False,
               'privacy_approved': False, 'independent_review_completed': False,
               'input_sha256': {'pilot-tasks': bindings['pilot_tasks']}, 'duplicates': []})
    reindex(context)
    return pilot, draft, annotations, context


def test_bound_complete_run_is_reproducible_and_never_overwrites(tmp_path):
    args = fixture(tmp_path)
    before = {p: p.read_bytes() for root in args for p in root.rglob('*') if p.is_file()}
    outputs = [tmp_path / 'out-a', tmp_path / 'out-b']
    for output in outputs:
        report = module.run(*args, output)
        assert report['annotation_candidates'] == 1 and report['records'] == 2
        assert report['proposed_development_families'] == []
        assert report['training_approved'] is False and report['evaluation_holdout'] is False
    assert all(p.read_bytes() == content for p, content in before.items())
    assert {p.name: p.read_bytes() for p in outputs[0].iterdir()} == {p.name: p.read_bytes() for p in outputs[1].iterdir()}
    with pytest.raises(ValueError): module.run(*args, outputs[0])
    with pytest.raises(ValueError): module.run(*args, args[0] / 'nested')


@pytest.mark.parametrize('case', ['stale_annotation', 'stale_privacy', 'key_hash', 'different_pilot', 'duplicate_record', 'holdout'])
def test_provenance_and_pilot_role_checks(tmp_path, case):
    pilot, draft, annotations, context = fixture(tmp_path)
    if case == 'stale_annotation': (annotations / 'annotations.json').write_text('{}')
    if case == 'stale_privacy': (context / 'privacy-spans.json').write_text('[]')
    if case in {'key_hash', 'duplicate_record'}:
        keys = module.read(pilot / 'coordinator/key.json')
        if case == 'key_hash': keys[0]['text_sha256'] = 'f' * 64
        else: keys[1]['record_id'] = keys[0]['record_id']
        write_json(pilot / 'coordinator/key.json', keys); reindex(pilot)
    if case == 'different_pilot':
        data = module.read(context / 'summary.json'); data['raw_sha256'] = 'f' * 64
        write_json(context / 'summary.json', data); reindex(context)
    if case == 'holdout':
        data = module.read(pilot / 'coordinator/summary.json'); data['evaluation_holdout'] = True
        write_json(pilot / 'coordinator/summary.json', data); reindex(pilot)
    with pytest.raises(ValueError): module.run(pilot, draft, annotations, context, tmp_path / 'out')
    assert not (tmp_path / 'out').exists()


def test_interrupted_write_is_not_complete(tmp_path, monkeypatch):
    args = fixture(tmp_path)
    def fail(*args): raise OSError('Synthetic write interruption')
    monkeypatch.setattr(module, 'write_json', fail)
    with pytest.raises(OSError): module.run(*args, tmp_path / 'out')
    assert (tmp_path / 'out/INCOMPLETE').exists()
    assert not (tmp_path / 'out/COMPLETE').exists()
