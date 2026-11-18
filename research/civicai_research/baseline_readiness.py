"""Assess pilot support and leakage/privacy constraints; never create a training release."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from .curation_qa import indexed
from .issue_annotations import validate
from .issue_draft import FAMILIES
from .manifest import _file_hash
from .review_recommendations import keyed, read, require, spans_valid
from .text_proposal import write_json

POLICY = Path(__file__).parents[1] / 'protocols/text_baseline_v1.json'


def assess(rows, keys, privacy, links, minimum):
    """Count AI candidates, with transitive containment before any record filtering."""
    require(type(minimum) is int and minimum >= 3, 'Invalid planning support floor')
    require(set(rows) == set(keys) == set(privacy), 'Pilot/key/privacy identities differ')
    parents = {k: k for k in rows}

    def root(k):
        while parents[k] != k:
            parents[k] = parents[parents[k]]
            k = parents[k]
        return k

    def union(left, right):
        a, b = sorted((root(left), root(right)))
        parents[b] = a

    base = {}
    for identity, key in sorted(keys.items()):
        group = key['proposed_group_id']
        require(isinstance(group, str) and bool(group.strip()), 'Missing proposed group')
        if group in base:
            union(identity, base[group])
        else:
            base[group] = identity
    seen = set()
    for link in links:
        left, right = link['left'], link['right']
        require(left in rows and right in rows and left != right, 'Invalid duplicate link')
        pair = tuple(sorted((left, right)))
        require(pair not in seen and link['same_incident_verified'] is False
                and link['recommendation'] in {'propose_split_containment_keep_both', 'hold_for_event_review'},
                'Invalid or repeated duplicate recommendation')
        seen.add(pair)
        # Even a pending candidate is contained conservatively, not asserted to be one event.
        union(left, right)
    components = defaultdict(list)
    for identity in sorted(rows): components[root(identity)].append(identity)
    group_flags = {}
    for component, members in components.items():
        families = {i['family'] for k in members for i in rows[k]['issues'] if i['family'] != 'unknown'}
        group_flags[component] = (len(families) > 1,
                                 any(rows[k]['outcome'] != 'described_issue' for k in members))
    inventory = []
    for identity, row in sorted(rows.items()):
        families = {i['family'] for i in row['issues']}
        family = next(iter(families)) if len(families) == 1 and 'unknown' not in families else None
        group = root(identity)
        conflict, uncertainty = group_flags[group]
        reason = row['outcome'] if row['outcome'] != 'described_issue' else (
            'cross_family' if family is None else 'group_conflict' if conflict else
            'group_uncertainty' if uncertainty else 'annotation_candidate')
        p = privacy[identity]
        flags = []
        if p['proposed_spans']: flags.append('span_proposal')
        context = p.get('context_recommendation')
        require(context in {None, 'retain_context_proposal', 'hold_sensitive_context', 'redact_span_proposal'},
                'Unknown contextual privacy recommendation')
        require(context != 'redact_span_proposal' or bool(p['proposed_spans']),
                'Redaction recommendation lacks spans')
        if context == 'hold_sensitive_context': flags.append('context_hold')
        elif context == 'retain_context_proposal': flags.append('retain_proposal_not_clearance')
        elif context is None and not p['proposed_spans']: flags.append('context_not_reviewed')
        require(p['privacy_approved'] is False, 'Pilot privacy approval cannot be inferred')
        inventory.append({'task_id': identity, 'candidate_family': family, 'disposition': reason,
                          'component': group, 'component_count': len(row['issues']), 'privacy_flags': flags,
                          'development_only': True, 'training_eligible': False})
    candidates = [r for r in inventory if r['disposition'] == 'annotation_candidate']
    support = []
    for family in sorted(set(FAMILIES) - {'unknown'}):
        selected = [r for r in candidates if r['candidate_family'] == family]
        groups = {r['component'] for r in selected}
        support.append({'family': family, 'candidate_records': len(selected),
                        'containment_components': len(groups),
                        'single_component_records': sum(r['component_count'] == 1 for r in selected),
                        'span_proposal_records': sum('span_proposal' in r['privacy_flags'] for r in selected),
                        'context_hold_records': sum('context_hold' in r['privacy_flags'] for r in selected),
                        'meets_development_planning_floor': len(groups) >= minimum})
    selected_families = [s['family'] for s in support if s['meets_development_planning_floor']]
    summary = {
        'records': len(rows), 'dispositions': dict(Counter(r['disposition'] for r in inventory)),
        'annotation_candidates': len(candidates),
        'candidate_containment_components': len({r['component'] for r in candidates}),
        'pilot_containment_components': len(components),
        'same_family_multi_component_candidates': sum(r['component_count'] > 1 for r in candidates),
        'candidate_privacy_flags_nonexclusive': dict(Counter(f for r in candidates for f in r['privacy_flags'])),
        'proposed_development_families': selected_families,
        'proposed_development_records': sum(r['candidate_family'] in selected_families for r in candidates),
        'proposed_development_components': len({r['component'] for r in candidates if r['candidate_family'] in selected_families}),
        'independent_reference_records': 0, 'privacy_approved_records': 0, 'training_eligible_records': 0,
        'training_approved': False, 'evaluation_approved': False, 'evaluation_holdout': False,
        'split_assignments_created': 0, 'planning_min_components_per_family': minimum,
    }
    return inventory, support, summary


def run(pilot, draft, annotations, context, output, policy=POLICY):
    require(not output.exists() and not any(output.resolve().is_relative_to(p.resolve())
            for p in (pilot, draft, annotations, context)), 'Fresh output outside inputs required')
    paths = {
        'tasks': indexed(pilot, 'reviewer/tasks.json'), 'key': indexed(pilot, 'coordinator/key.json'),
        'pilot_summary': indexed(pilot, 'coordinator/summary.json'),
        'prior': indexed(draft, 'annotations.json'), 'contract': indexed(draft, 'contract.json'),
        'annotations': indexed(annotations, 'annotations.json'),
        'privacy': indexed(context, 'privacy-spans.json'),
        'recommendations': indexed(context, 'recommendations.json'),
        'context_summary': indexed(context, 'summary.json'), 'policy': policy,
    }
    bindings = {'pilot_tasks': _file_hash(paths['tasks']), 'prior_annotations': _file_hash(paths['prior']),
                'prior_contract': _file_hash(paths['contract'])}
    tasks = read(paths['tasks'])
    rows, _ = validate(read(paths['annotations']), tasks, read(paths['prior']), bindings)
    pilot_summary, context_summary = read(paths['pilot_summary']), read(paths['context_summary'])
    require(pilot_summary['evaluation_holdout'] is False and pilot_summary['training_approved'] is False,
            'This command is only for a development pilot')
    require(context_summary['input_sha256']['pilot-tasks'] == bindings['pilot_tasks']
            and context_summary['raw_sha256'] == pilot_summary['raw_sha256']
            and context_summary['training_approved'] is False and context_summary['privacy_approved'] is False,
            'Context/pilot provenance or approval differs')
    recommendations = read(paths['recommendations'])
    require(recommendations['author_kind'] == 'ai_assistant'
            and recommendations['input_sha256']['pilot-tasks'] == bindings['pilot_tasks']
            and all(recommendations[f] is False for f in
                    ('training_approved', 'privacy_approved', 'independent_review_completed')),
            'Only unapproved bound AI recommendations allowed')
    keys = keyed(read(paths['key']), lambda r: r['task_id'])
    privacy = keyed(read(paths['privacy']), lambda r: r['task_id'])
    require(set(rows) == set(keys) == set(privacy), 'Coverage differs')
    require(len({k['record_id'] for k in keys.values()}) == len(keys), 'Duplicate source identity')
    for task in tasks:
        identity = task['task_id']
        require(keys[identity]['text_sha256'] == privacy[identity]['text_sha256'] == rows[identity]['text_sha256'],
                'Key/privacy text hash differs')
        spans_valid(privacy[identity]['proposed_spans'], task['text'])
    protocol = read(policy)
    require(protocol['version'] == 'civicai-text-baseline-protocol-v1'
            and protocol['training_approved'] is False and protocol['evaluation_holdout'] is False,
            'Proposal-only development protocol required')
    inventory, support, summary = assess(rows, keys, privacy, recommendations['duplicates'],
                                         protocol['planning_min_components_per_family'])
    summary.update(status='readiness_assessment_not_training_release', raw_sha256=pilot_summary['raw_sha256'],
                   input_sha256={**{k: _file_hash(v) for k, v in paths.items()},
                                 'implementation': _file_hash(Path(__file__))},
                   blockers=['independent_reference_labels_absent', 'privacy_release_not_approved',
                             'rights_and_derivative_release_pending', 'full_corpus_event_groups_unverified',
                             'untouched_independent_evaluation_set_absent', 'draft_target_not_adopted'])
    output.mkdir(parents=True)
    (output / 'INCOMPLETE').touch()
    for name, value in [('inventory.json', inventory), ('support.json', support), ('summary.json', summary), ('protocol.json', protocol)]:
        write_json(output / name, value)
    write_json(output / 'artifacts.json', {p.name: _file_hash(p) for p in sorted(output.iterdir()) if p.name != 'INCOMPLETE'})
    (output / 'COMPLETE').write_text('Readiness assessment only. No training, split or evaluation approval.\n')
    (output / 'INCOMPLETE').unlink()
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pilot', 'draft', 'annotations', 'context', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.pilot, args.draft, args.annotations, args.context, args.output)
    except (OSError, ValueError, KeyError, TypeError):
        parser.exit(1, 'Baseline readiness failed; inspect restricted inputs.\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
