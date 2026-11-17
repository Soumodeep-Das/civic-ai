"""Validate AI label proposals without converting them to human reference labels."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from .manifest import _file_hash, load_taxonomy


def validate(pilot: Path, response: Path):
    if not (pilot/'COMPLETE').exists() or (pilot/'INCOMPLETE').exists():
        raise ValueError('Pilot incomplete')
    index=json.loads((pilot/'artifacts.json').read_text(encoding='utf-8'))
    tasks_path=pilot/'reviewer/tasks.json'
    if _file_hash(tasks_path)!=index['reviewer/tasks.json']:
        raise ValueError('Pilot tasks changed')
    tasks=json.loads(tasks_path.read_text(encoding='utf-8'))
    by_id={r['task_id']:r for r in tasks}
    if len(by_id)!=len(tasks): raise ValueError('Duplicate pilot task')
    data=json.loads(response.read_text(encoding='utf-8'))
    if (data.get('kind')!='ai_assisted_proposals' or data.get('training_approved') is not False
            or data.get('independent_human_review') is not False
            or data.get('privacy_approved') is not False
            or data.get('pilot_tasks_sha256')!=_file_hash(tasks_path)):
        raise ValueError('Invalid provenance or approval claim')
    if not data.get('author') or not data.get('limitations'):
        raise ValueError('Missing AI attribution/limitations')
    _, categories=load_taxonomy()
    if data.get('taxonomy_sha256')!=index['reviewer/taxonomy.json']:
        raise ValueError('Taxonomy binding mismatch')
    from .manifest import DEFAULT_TAXONOMY
    if _file_hash(DEFAULT_TAXONOMY)!=data['taxonomy_sha256']:
        raise ValueError('Current taxonomy differs')
    seen=set(); counts=Counter(); labels=Counter()
    fields={'task_id','text_sha256','decision','proposed_categories','rationale','privacy_concerns'}
    for row in data['responses']:
        if set(row)!=fields: raise ValueError('Unexpected response fields')
        identity=row['task_id']
        if identity not in by_id or identity in seen: raise ValueError('Unknown/duplicate task')
        seen.add(identity)
        if hashlib.sha256(by_id[identity]['text'].encode()).hexdigest()!=row['text_sha256']:
            raise ValueError('Text binding mismatch')
        decision=row['decision']; proposed=row['proposed_categories']
        if decision not in {'supported','multiple_issues','taxonomy_gap','unclear'}:
            raise ValueError('Unsupported decision')
        if (not isinstance(proposed,list) or any(x not in categories for x in proposed)
                or len(set(proposed))!=len(proposed)):
            raise ValueError('Invalid category')
        if ((decision=='supported' and len(proposed)!=1)
                or (decision=='multiple_issues' and len(proposed)<2)
                or (decision in {'taxonomy_gap','unclear'} and proposed)):
            raise ValueError('Decision/category mismatch')
        if not isinstance(row['rationale'],str) or not row['rationale'].strip():
            raise ValueError('Rationale missing')
        if not isinstance(row['privacy_concerns'],list) or any(
                not isinstance(x,str) or not x.strip() for x in row['privacy_concerns']):
            raise ValueError('Invalid privacy observations')
        counts[decision]+=1; labels.update(proposed)
    if not seen: raise ValueError('Empty response batch')
    return {'status':'structurally_valid_ai_proposals_not_reference_labels',
            'reviewed_by_ai':len(seen),'pilot_total':len(tasks),'remaining':len(tasks)-len(seen),
            'decisions':dict(counts),'proposed_label_counts':dict(labels),
            'privacy_concern_records':sum(bool(r['privacy_concerns']) for r in data['responses']),
            'training_approved':False,'independent_human_review':False,
            'responses_sha256':_file_hash(response)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pilot',type=Path,required=True);p.add_argument('--responses',type=Path,required=True)
    a=p.parse_args()
    try: result=validate(a.pilot,a.responses)
    except (OSError,ValueError,KeyError,TypeError): p.exit(1,'AI proposal validation failed; inspect local inputs.\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
