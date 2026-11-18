"""Conservative transfer of reviewed AI pilot proposals into a richer draft contract."""
import argparse
from collections import Counter
import json
from pathlib import Path
from .ai_labels import validate
from .manifest import _file_hash
from .text_proposal import write_json

VERSION = 'civicai-issue-description-draft-v1'
# These are transfers of prior AI proposals, never new text-derived observations.
MAPPING = {
 'road_damage': ('roads_and_pedestrian_access', 'carriageway', 'damage'),
 'broken_footpath': ('roads_and_pedestrian_access', 'footpath', 'damage'),
 'drainage_sewerage': ('drainage_and_sewerage', 'unknown', 'unknown'),
 'waterlogging': ('unknown', 'unknown', 'accumulation'),
 'garbage_waste': ('solid_waste', 'unknown', 'accumulation'),
 'streetlight': ('public_lighting', 'streetlight', 'unknown'),
 'water_leakage': ('water_services', 'unknown', 'leakage'),
 'other': ('unknown', 'unknown', 'unknown'),
}
FAMILIES = sorted({v[0] for v in MAPPING.values()} | {
 'sanitation_and_public_health', 'mobility_and_traffic_infrastructure', 'animals',
 'parks_trees_and_waterbodies', 'pollution_and_nuisance', 'electricity_services',
 'public_assets_and_space'})
KINDS = ['damage', 'blockage', 'overflow', 'leakage', 'accumulation', 'outage',
         'obstruction', 'missing_service', 'new_installation', 'maintenance',
         'design', 'service_conduct', 'unknown']


def transfer(row):
    issues = []
    for label in row['proposed_categories']:
        family, asset, kind = MAPPING[label]
        issues.append({'family': family, 'asset': asset, 'issue_kind': kind,
                       'setting': 'unknown', 'time_state': 'unknown',
                       'basis': 'prior_ai_category_transfer', 'source_ai_category': label,
                       'text_evidence_verified': False})
    return {'task_id': row['task_id'], 'text_sha256': row['text_sha256'],
            'prior_decision': row['decision'], 'issues': issues,
            'annotation_state': 'transferred_needs_text_review' if issues else 'needs_richer_annotation',
            'prior_rationale': row['rationale'], 'privacy_concerns': row['privacy_concerns'],
            'scope_status': 'not_adjudicated', 'privacy_approved': False,
            'training_approved': False, 'independent_reference': False}


def run(pilot, responses, output):
    if output.exists() or any(output.resolve().is_relative_to(p.resolve())
                              for p in (pilot, responses.parent)):
        raise ValueError('Fresh output outside inputs required')
    report = validate(pilot, responses)
    if report['remaining']:
        raise ValueError('Complete pilot proposals required')
    rows = [transfer(row) for row in json.loads(responses.read_text(encoding='utf-8'))['responses']]
    contract = {'version': VERSION, 'status': 'draft_not_adopted', 'families': FAMILIES,
                'issue_kinds': KINDS, 'setting': ['public', 'private', 'mixed', 'unknown'],
                'time_state': ['present', 'recurring', 'future_request', 'resolved', 'unknown'],
                'multiple_issues_allowed': True, 'training_approved': False}
    summary = {'version': VERSION, 'records': len(rows),
               'states': dict(Counter(r['annotation_state'] for r in rows)),
               'issue_proposals': sum(len(r['issues']) for r in rows),
               'fresh_text_annotations': 0, 'training_approved': False,
               'independent_reference': False, 'privacy_approved': False,
               'input_sha256': {'responses': _file_hash(responses),
                                'pilot_tasks': _file_hash(pilot/'reviewer/tasks.json'),
                                'implementation': _file_hash(Path(__file__))}}
    output.mkdir(parents=True)
    (output/'INCOMPLETE').touch()
    for name, value in [('contract.json', contract), ('annotations.json', rows), ('summary.json', summary)]:
        write_json(output/name, value)
    write_json(output/'artifacts.json', {p.name: _file_hash(p) for p in sorted(output.iterdir())
                                        if p.name != 'INCOMPLETE'})
    (output/'COMPLETE').write_text('Draft transfer only; every record requires text review.\n')
    (output/'INCOMPLETE').unlink()
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pilot', 'responses', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.pilot, args.responses, args.output)
    except (ValueError, KeyError, TypeError, OSError):
        parser.exit(1, 'Draft transfer failed; inspect restricted local inputs.\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
