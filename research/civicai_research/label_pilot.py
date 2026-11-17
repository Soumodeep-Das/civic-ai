"""Create a local, source-label-blinded guideline pilot; never grant training approval."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from .manifest import _file_hash, DEFAULT_TAXONOMY
from .text_proposal import write_json


def build(proposal: Path, output: Path, per_stratum: int = 20):
    if not 1 <= per_stratum <= 100:
        raise ValueError("Pilot size must be between 1 and 100 per stratum")
    if output.exists() or output.resolve().is_relative_to(proposal.resolve()):
        raise ValueError("Use a fresh output outside the proposal")
    if not (proposal/'COMPLETE').is_file() or (proposal/'INCOMPLETE').exists():
        raise ValueError("Incomplete proposal")
    artifacts = json.loads((proposal/'artifacts.json').read_text(encoding='utf-8'))

    def verified(relative):
        path = (proposal/relative).resolve()
        if not path.is_relative_to(proposal.resolve()) or not path.is_file():
            raise ValueError("Invalid artifact path")
        if relative not in artifacts or _file_hash(path) != artifacts[relative]:
            raise ValueError("Artifact integrity failure")
        return path

    report = json.loads(verified('readiness.json').read_text(encoding='utf-8'))
    if report['training_approved'] is not False or report['status'] != 'automated_proposal_not_curated_release':
        raise ValueError("Unexpected proposal state")
    if report['provenance']['taxonomy_sha256'] != _file_hash(DEFAULT_TAXONOMY):
        raise ValueError("Taxonomy changed")
    records = [json.loads(line) for line in verified('proposals.jsonl').read_text(encoding='utf-8').splitlines()]
    if len(records) != report['records'] or len({r['record_id'] for r in records}) != len(records):
        raise ValueError("Record identity/count mismatch")
    strata = defaultdict(list)
    for r in records:
        if r['category_label'] is not None or r['annotation_status'] != 'pending' or r['split'] != 'unassigned':
            raise ValueError("Input has assigned labels or splits")
        # Source proposals influence sampling only; never appear in reviewer tasks.
        key = (r['review_route'], r['proposed_category'] or 'unmapped')
        strata[key].append(r)
    selected, seen_groups, counts = [], set(), {}
    rank = lambda r: hashlib.sha256(('label-pilot-v1:'+r['record_id']).encode()).hexdigest()
    for key, members in sorted(strata.items()):
        count = 0
        for r in sorted(members, key=rank):
            if r['proposed_group_id'] in seen_groups:
                continue
            seen_groups.add(r['proposed_group_id']); selected.append(r); count += 1
            if count == per_stratum:
                break
        counts['/'.join(key)] = {'available_records':len(members), 'selected':count}
    tasks, coordinator = [], []
    for i, r in enumerate(sorted(selected, key=rank), 1):
        task_id = f'pilot-{i:04d}'
        path = verified(r['derived_text_ref'])
        if _file_hash(path) != r['derived_text_sha256']:
            raise ValueError("Text reference mismatch")
        tasks.append({'task_id':task_id, 'text':path.read_text(encoding='utf-8'),
                      'reviewer_id':'', 'reviewed_at':'', 'decision':'', 'category':'',
                      'additional_categories':[], 'privacy_action':'', 'language':'', 'rationale':''})
        coordinator.append({'task_id':task_id, 'record_id':r['record_id'],
                            'proposed_group_id':r['proposed_group_id'],
                            'proposed_category':r['proposed_category'], 'review_route':r['review_route'],
                            'text_sha256':r['derived_text_sha256']})
    summary = {'status':'guideline_pilot_awaiting_independent_review', 'training_approved':False,
               'selected_records':len(tasks), 'selected_groups':len(seen_groups),
               'per_stratum_cap':per_stratum, 'strata':counts,
               'input_artifacts_sha256':_file_hash(proposal/'artifacts.json'),
               'raw_sha256':report['provenance']['raw_sha256'],
               'taxonomy_sha256':_file_hash(DEFAULT_TAXONOMY), 'generator_sha256':_file_hash(Path(__file__)),
               'evaluation_holdout':False, 'privacy_approved':False}
    output.mkdir(parents=True)
    (output/'INCOMPLETE').write_text('Not a training release\n',encoding='utf-8')
    (output/'reviewer').mkdir(); (output/'coordinator').mkdir()
    write_json(output/'reviewer/tasks.json',tasks)
    (output/'reviewer/taxonomy.json').write_bytes(DEFAULT_TAXONOMY.read_bytes())
    write_json(output/'coordinator/key.json',coordinator)
    write_json(output/'coordinator/summary.json',summary)
    write_json(output/'artifacts.json',{p.relative_to(output).as_posix():_file_hash(p)
               for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'INCOMPLETE'})
    (output/'COMPLETE').write_text('Pilot generated; no labels or training approval.\n',encoding='utf-8')
    (output/'INCOMPLETE').unlink()
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proposal',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--per-stratum',type=int,default=20)
    args=parser.parse_args()
    try:
        result=build(args.proposal,args.output,args.per_stratum)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        parser.exit(1,f'Pilot failed: {type(exc).__name__}; inspect inputs locally.\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
