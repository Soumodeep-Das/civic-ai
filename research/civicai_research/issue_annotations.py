"""Validate text-anchored AI issue annotations; never grant reference/release approval."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .curation_qa import indexed
from .issue_draft import FAMILIES, KINDS
from .manifest import _file_hash
from .review_recommendations import keyed, read, require
from .text_proposal import write_json

VERSION = 'civicai-text-issue-annotation-draft-v1'
ASSETS = {'unknown', 'carriageway', 'footpath', 'streetlight', 'signal', 'divider',
          'speed_hump', 'barricade', 'bus_stop', 'drain', 'sewer', 'manhole',
          'cover', 'pipe', 'meter', 'tank', 'borewell', 'electricity_supply',
          'cable', 'pole', 'collection_service', 'sweeping_service', 'waste', 'bin',
          'public_space', 'toilet', 'animal', 'carcass', 'vector_control', 'lake',
          'park', 'vegetation', 'vehicle', 'building'}
OUTCOMES = {'described_issue', 'clarification_needed', 'unusable_text', 'scope_review'}
FLAGS = ('training_approved', 'privacy_approved', 'independent_reference')
FAMILY_ASSETS = {
    'roads_and_pedestrian_access': {'carriageway', 'footpath'},
    'drainage_and_sewerage': {'drain', 'sewer', 'manhole', 'cover', 'pipe'},
    'solid_waste': {'collection_service', 'sweeping_service', 'waste', 'bin'},
    'public_lighting': {'streetlight'},
    'water_services': {'pipe', 'meter', 'tank', 'borewell'},
    'sanitation_and_public_health': {'public_space', 'toilet', 'carcass', 'vector_control'},
    'mobility_and_traffic_infrastructure': {'signal', 'divider', 'speed_hump', 'barricade', 'bus_stop', 'public_space', 'vehicle'},
    'animals': {'animal'},
    'parks_trees_and_waterbodies': {'lake', 'park', 'vegetation'},
    'pollution_and_nuisance': {'waste', 'public_space'},
    'electricity_services': {'electricity_supply', 'cable', 'pole'},
    'public_assets_and_space': {'public_space', 'vehicle', 'building'},
    'unknown': ASSETS,
}


def evidence_valid(spans, text):
    require(isinstance(spans, list) and bool(spans), 'Evidence required')
    previous = 0
    for span in spans:
        require(set(span) == {'start', 'end'} and type(span['start']) is int
                and type(span['end']) is int
                and previous <= span['start'] < span['end'] <= len(text)
                and text[span['start']:span['end']].strip(), 'Invalid evidence offsets')
        previous = span['end']


def validate(annotations, tasks, prior, bindings):
    require(set(annotations) == {'version', 'author_kind', 'input_sha256', 'rows', *FLAGS},
            'Unexpected annotation fields')
    require(annotations['version'] == VERSION and annotations['author_kind'] == 'ai_assistant'
            and all(annotations[f] is False for f in FLAGS), 'AI-only unapproved annotations required')
    require(annotations['input_sha256'] == bindings, 'Input bindings differ')
    by_task = keyed(tasks, lambda r: r['task_id'])
    by_prior = keyed(prior, lambda r: r['task_id'])
    rows = keyed(annotations['rows'], lambda r: r['task_id'])
    require(set(rows) == set(by_task) == set(by_prior), 'Exact complete pilot coverage required')
    for identity, row in rows.items():
        require(set(row) == {'task_id', 'text_sha256', 'outcome', 'rationale', 'issues'},
                'Unexpected row fields')
        text = by_task[identity]['text']
        require(row['text_sha256'] == by_prior[identity]['text_sha256']
                == hashlib.sha256(text.encode('utf-8')).hexdigest(), 'Text hash mismatch')
        require(row['outcome'] in OUTCOMES and isinstance(row['rationale'], str)
                and len(row['rationale'].strip()) >= 20, 'Outcome and rationale required')
        require(isinstance(row['issues'], list), 'Issues must be a list')
        require(row['outcome'] != 'unusable_text' or not row['issues'], 'Unusable text cannot supply issues')
        require(row['outcome'] != 'described_issue' or row['issues'], 'Described issue needs evidence')
        seen = set()
        for issue in row['issues']:
            require(set(issue) == {'family', 'asset', 'issue_kind', 'evidence', 'basis',
                                   'setting', 'time_state', 'setting_evidence', 'time_evidence'},
                    'Unexpected issue fields')
            triple = (issue['family'], issue['asset'], issue['issue_kind'])
            require(issue['family'] in FAMILIES and issue['asset'] in ASSETS
                    and issue['issue_kind'] in KINDS and triple not in seen,
                    'Unknown or duplicated issue description')
            seen.add(triple)
            require(issue['asset'] == 'unknown' or issue['asset'] in FAMILY_ASSETS[issue['family']],
                    'Asset does not belong to the draft family')
            require(issue['basis'] == 'complainant_report_not_verified_event', 'Event verification forbidden')
            evidence_valid(issue['evidence'], text)
            for field, options in [('setting', {'public', 'private', 'mixed', 'unknown'}),
                                   ('time_state', {'present', 'recurring', 'future_request', 'resolved', 'unknown'})]:
                require(issue[field] in options, 'Unknown context value')
                spans = issue['setting_evidence' if field == 'setting' else 'time_evidence']
                if issue[field] == 'unknown':
                    require(spans == [], 'Unknown context cannot claim evidence')
                else:
                    evidence_valid(spans, text)
            require(row['outcome'] != 'described_issue' or issue['family'] != 'unknown',
                    'Unknown family needs explicit clarification/scope outcome')
    return rows, by_prior


def run(pilot, draft, annotations, output):
    require(not output.exists() and not any(output.resolve().is_relative_to(p.resolve())
            for p in (pilot, draft, annotations.parent)), 'Fresh output outside inputs required')
    tasks_path = indexed(pilot, 'reviewer/tasks.json')
    prior_path = indexed(draft, 'annotations.json')
    contract_path = indexed(draft, 'contract.json')
    draft_summary = read(indexed(draft, 'summary.json'))
    bindings = {'pilot_tasks': _file_hash(tasks_path), 'prior_annotations': _file_hash(prior_path),
                'prior_contract': _file_hash(contract_path)}
    require(draft_summary['input_sha256']['pilot_tasks'] == bindings['pilot_tasks'],
            'Draft belongs to another pilot')
    data = read(annotations)
    rows, prior = validate(data, read(tasks_path), read(prior_path), bindings)
    comparison = []
    for identity, row in sorted(rows.items()):
        old = {(i['family'], i['asset'], i['issue_kind']) for i in prior[identity]['issues']}
        new = {(i['family'], i['asset'], i['issue_kind']) for i in row['issues']}
        comparison.append({'task_id': identity, 'prior_state': prior[identity]['annotation_state'],
                           'outcome': row['outcome'], 'issue_triples_changed': old != new,
                           'old_issues': len(old), 'new_issues': len(new)})
    summary = {'version': VERSION, **{f: False for f in FLAGS}, 'records_read_by_ai': len(rows),
               'outcomes': dict(Counter(r['outcome'] for r in rows.values())),
               'records_with_multiple_issue_descriptions': sum(len(r['issues']) > 1 for r in rows.values()),
               'issue_descriptions': sum(len(r['issues']) for r in rows.values()),
               'family_record_counts_nonexclusive': dict(Counter(
                   f for r in rows.values() for f in {i['family'] for i in r['issues']})),
               'previously_unresolved_reviewed': sum(p['annotation_state'] == 'needs_richer_annotation' for p in prior.values()),
               'previously_transferred_reviewed': sum(p['annotation_state'] == 'transferred_needs_text_review' for p in prior.values()),
               'changed_transferred_records': sum(c['prior_state'] == 'transferred_needs_text_review'
                                                   and c['issue_triples_changed'] for c in comparison),
               'input_sha256': {**bindings, 'annotations': _file_hash(annotations),
                                'validator': _file_hash(Path(__file__))}}
    output.mkdir(parents=True)
    (output / 'INCOMPLETE').touch()
    for name, value in [('annotations.json', data), ('comparison.json', comparison), ('summary.json', summary)]:
        write_json(output / name, value)
    write_json(output / 'artifacts.json', {p.name: _file_hash(p) for p in sorted(output.iterdir()) if p.name != 'INCOMPLETE'})
    (output / 'COMPLETE').write_text('AI text review only; no privacy or training approval.\n')
    (output / 'INCOMPLETE').unlink()
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pilot', 'draft', 'annotations', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.pilot, args.draft, args.annotations, args.output)
    except (OSError, ValueError, KeyError, TypeError):
        parser.exit(1, 'Issue annotation validation failed; inspect restricted local inputs.\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
