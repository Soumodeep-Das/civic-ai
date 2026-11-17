"""Audit draft source coverage and propose pilot privacy/duplicate review; no release approval."""
import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from .ai_labels import validate
from .manifest import _file_hash
from .text_proposal import screen, write_json

DEFAULT_CROSSWALK=Path(__file__).parents[1]/'mappings/icmyc_family_draft_v1.json'
PRIVACY_PATTERNS={
    'signature':re.compile(r'(?im)^(?:thanks(?:\s*&\s*regards)?|regards|yours truly|with regards|thank you)[, .:]*[ \t]*\n+(?P<value>[^\n]{2,100})'),
    'self_named_person':re.compile(r'(?i:\b(?:my name is|name\s*:))\s*(?P<value>[A-Z][a-zA-Z]*(?:[ \t]+[A-Z][a-zA-Z]*){0,3})'),
    'named_person':re.compile(r'\b(?:Mr|Ms|Mrs|Dr)(?:\.\s*|\s+)(?P<value>[A-Z][a-zA-Z]*(?:[ \t]+[A-Z][a-zA-Z]*){0,2})'),
    'address_cue':re.compile(r'(?i)\b(?:address|adress|home details)\s*[:#-]\s*(?P<value>[^\n]{2,300})'),
    'address_line':re.compile(r'(?im)^(?P<value>(?:Site\s+no\.?|No\.|\#|H\s*no)\s*\d[^\n]{0,250})'),
    'complaint_identifier':re.compile(r'(?i)\bcomplaint\s*(?:id|\#|no\.?)\s*[:#-]?\s*(?P<value>\d[\d-]{3,})'),
}


def privacy_spans(text):
    """Offsets refer to the supplied pilot text, not the original raw CSV."""
    _, candidates=screen(text)
    for kind,pattern in PRIVACY_PATTERNS.items():
        for match in pattern.finditer(text):
            start,end=match.span('value')
            candidates.append({'start':start,'end':end,'kinds':[kind]})
    merged=[]
    for span in sorted(candidates,key=lambda s:(s['start'],s['end'])):
        if merged and span['start']<merged[-1]['end']:
            merged[-1]['end']=max(span['end'],merged[-1]['end'])
            merged[-1]['kinds']=sorted(set(merged[-1]['kinds'])|set(span['kinds']))
        else: merged.append(dict(span))
    return merged


def tokens(text):
    return re.findall(r'\w+',unicodedata.normalize('NFKC',text).casefold())


def near_pairs(tasks, threshold=0.82):
    """Bounded lexical candidates; symmetric conservative score, no event identity claim."""
    if not 0.5<=threshold<=1 or len(tasks)>1000:
        raise ValueError('Invalid threshold or pilot exceeds 1000 records')
    if len({t['task_id'] for t in tasks})!=len(tasks): raise ValueError('Duplicate task ID')
    if any(len(t['text'])>20000 for t in tasks): raise ValueError('Text exceeds pilot comparison bound')
    ordered=sorted(tasks,key=lambda t:t['task_id']); seq=[tokens(t['text']) for t in ordered]
    pairs=[]; negations={'no','not','never','without','cannot'}
    for i,a in enumerate(seq):
        for j in range(i+1,len(seq)):
            b=seq[j]
            if not a or not b: continue
            exact=a==b
            if not exact and min(len(a),len(b))<5: continue
            if 2*min(len(a),len(b))/(len(a)+len(b))<threshold: continue
            forward=SequenceMatcher(None,a,b,autojunk=False)
            if forward.quick_ratio()<threshold: continue
            score=min(forward.ratio(),SequenceMatcher(None,b,a,autojunk=False).ratio())
            if score<threshold: continue
            pairs.append({'left':ordered[i]['task_id'],'right':ordered[j]['task_id'],
                          'score':round(score,6),'method':'min_bidirectional_token_sequence_ratio',
                          'exact_normalized_text':exact,'short_generic_text':min(len(a),len(b))<5,
                          'negation_difference':(set(a)&negations)!=(set(b)&negations),
                          'numeric_difference':{x for x in a if x.isdigit()}!={x for x in b if x.isdigit()},
                          'same_incident_verified':False,'review_status':'pending'})
    return pairs


def source_coverage(groups, config):
    if config['status']!='proposed_not_training_labels': raise ValueError('Crosswalk not a proposal')
    families=set(config['families']);rules={}
    for r in config['rules']:
        key=(r['source_category'],r['source_subcategory'].strip())
        if (key in rules or not set(r['proposed_families'])<=families
                or len(set(r['proposed_families']))!=len(r['proposed_families'])
                or r['disposition'] not in {'family_proposal','scope_review','unresolved'}
                or not r['rationale'].strip()
                or (r['disposition']=='family_proposal' and not r['proposed_families'])):
            raise ValueError('Invalid or duplicate crosswalk rule')
        rules[key]=r
    seen=set(); records=set(); output=[]; totals=Counter(); support=Counter()
    for group in groups:
        key=(group['source_category'],group['source_subcategory'].strip())
        if key in seen: raise ValueError('Duplicate source pair')
        seen.add(key)
        ids=group['record_ids']
        if group['records']!=len(ids) or len(set(ids))!=len(ids) or records.intersection(ids):
            raise ValueError('Source membership counts overlap or differ')
        records.update(ids)
        rule=rules.get(key,{'proposed_families':[],'disposition':'unresolved',
                           'rationale':'No exact crosswalk rule; record-level review required.'})
        output.append({'source_category':key[0],'source_subcategory':key[1],'records':len(ids),
                       'proposed_families':rule['proposed_families'],'disposition':rule['disposition'],
                       'rationale':rule['rationale'],'issue_kind_status':'requires_record_review',
                       'annotation_status':'pending','training_approved':False})
        totals[rule['disposition']]+=len(ids)
        for family in rule['proposed_families']: support[family]+=len(ids)
    return output,{'pairs':len(output),'records':len(records),'disposition_records':dict(totals),
                   'family_candidate_records_nonexclusive':dict(support),
                   'unmatched_pairs':len(seen-set(rules)),'unused_rules':len(set(rules)-seen)}


def indexed(root, relative):
    if not (root/'COMPLETE').is_file() or (root/'INCOMPLETE').exists(): raise ValueError('Incomplete input')
    index=json.loads((root/'artifacts.json').read_text(encoding='utf-8'))
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()) or _file_hash(path)!=index[relative]:
        raise ValueError('Input integrity failure')
    return path


def run(proposal, pilot, responses, output, crosswalk=DEFAULT_CROSSWALK):
    roots=[proposal,pilot]
    if (responses.parent/'COMPLETE').exists(): roots.append(responses.parent)
    if output.exists() or any(output.resolve().is_relative_to(p.resolve()) for p in roots):
        raise ValueError('Fresh output outside inputs required')
    approved=validate(pilot,responses)
    if approved['remaining']: raise ValueError('Complete AI pilot required for this checkpoint')
    group_path=indexed(proposal,'mapping-groups.json')
    config=json.loads(crosswalk.read_text(encoding='utf-8'))
    if config['basis_mapping_groups_sha256']!=_file_hash(group_path): raise ValueError('Crosswalk source mismatch')
    coverage,summary=source_coverage(json.loads(group_path.read_text(encoding='utf-8')),config)
    readiness=json.loads(indexed(proposal,'readiness.json').read_text(encoding='utf-8'))
    if summary['records']!=readiness['records']: raise ValueError('Source total mismatch')
    pilot_summary=json.loads(indexed(pilot,'coordinator/summary.json').read_text(encoding='utf-8'))
    if (pilot_summary['input_artifacts_sha256']!=_file_hash(proposal/'artifacts.json')
            or pilot_summary['raw_sha256']!=readiness['provenance']['raw_sha256']):
        raise ValueError('Pilot belongs to a different proposal')
    tasks_path=indexed(pilot,'reviewer/tasks.json');key_path=indexed(pilot,'coordinator/key.json')
    tasks=json.loads(tasks_path.read_text(encoding='utf-8'))
    keys=json.loads(key_path.read_text(encoding='utf-8'));by_key={r['task_id']:r for r in keys}
    if len(by_key)!=len(keys) or set(by_key)!={t['task_id'] for t in tasks}: raise ValueError('Pilot key mismatch')
    ai={r['task_id']:r for r in json.loads(responses.read_text(encoding='utf-8'))['responses']}
    privacy=[]
    for task in tasks:
        checksum=hashlib.sha256(task['text'].encode('utf-8')).hexdigest()
        if checksum!=by_key[task['task_id']]['text_sha256']: raise ValueError('Pilot key text mismatch')
        spans=privacy_spans(task['text'])
        privacy.append({'task_id':task['task_id'],'text_sha256':checksum,'proposed_spans':spans,
                        'ai_concerns':ai[task['task_id']]['privacy_concerns'],
                        'review_status':'pending','privacy_approved':False})
    pairs=near_pairs(tasks)
    for pair in pairs:
        pair['crosses_existing_groups']=by_key[pair['left']]['proposed_group_id']!=by_key[pair['right']]['proposed_group_id']
    report={'status':'coverage_and_pilot_qa_proposal','training_approved':False,'coverage':summary,
            'pilot_records':len(tasks),'near_duplicate_candidates':len(pairs),
            'cross_group_candidates':sum(p['crosses_existing_groups'] for p in pairs),
            'privacy_span_records':sum(bool(r['proposed_spans']) for r in privacy),
            'privacy_spans':sum(len(r['proposed_spans']) for r in privacy),
            'ai_flagged_without_pattern_span':sum(bool(r['ai_concerns']) and not r['proposed_spans'] for r in privacy),
            'privacy_approved':False,'threshold':0.82,'raw_sha256':readiness['provenance']['raw_sha256'],
            'input_sha256':{'mapping_groups':_file_hash(group_path),'crosswalk':_file_hash(crosswalk),
                            'pilot_tasks':_file_hash(tasks_path),'pilot_key':_file_hash(key_path),
                            'ai_responses':_file_hash(responses),'generator':_file_hash(Path(__file__))}}
    output.mkdir(parents=True)
    (output/'INCOMPLETE').write_text('Not a training release\n',encoding='utf-8')
    for name,value in [('source-coverage.json',coverage),('near-duplicates.json',pairs),('privacy-spans.json',privacy),('summary.json',report)]:
        write_json(output/name,value)
    write_json(output/'artifacts.json',{p.name:_file_hash(p) for p in sorted(output.iterdir()) if p.name!='INCOMPLETE'})
    (output/'COMPLETE').write_text('Proposals only; no privacy, event or training approval.\n',encoding='utf-8')
    (output/'INCOMPLETE').unlink()
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('proposal','pilot','responses','output'): p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    try: result=run(a.proposal,a.pilot,a.responses,a.output)
    except (OSError,ValueError,KeyError,TypeError): p.exit(1,'Curation QA failed; inspect local inputs.\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
