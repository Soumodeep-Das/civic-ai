"""Validate contextual AI recommendations without approving or changing research data."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .curation_qa import indexed
from .manifest import _file_hash
from .text_proposal import write_json

SCOPE = {'defer_nonphysical_target', 'conditional_public_asset',
         'specialist_safety_review', 'record_context_required'}
PRIVACY = {'retain_context_proposal', 'hold_sensitive_context', 'redact_span_proposal'}
APPROVALS = ('training_approved', 'privacy_approved', 'independent_review_completed')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keyed(rows, key):
    result = {key(row): row for row in rows}
    require(len(result) == len(rows), 'Duplicate review identity')
    return result


def rationale(row):
    require(isinstance(row['rationale'], str) and len(row['rationale'].strip()) >= 20,
            'A concrete rationale is required')


def spans_valid(spans, text):
    end = 0
    for span in spans:
        require(set(span) == {'start', 'end', 'kinds'}, 'Unexpected span fields')
        require(type(span['start']) is int and type(span['end']) is int
                and end <= span['start'] < span['end'] <= len(text),
                'Invalid, overlapping or unsorted character offsets')
        require(isinstance(span['kinds'], list) and bool(span['kinds'])
                and all(isinstance(k, str) and k.strip() for k in span['kinds']),
                'Span kinds required')
        end = span['end']


def run(qa, pilot, prior_privacy, recommendations, output):
    inputs = [qa, pilot, prior_privacy.parent, recommendations.parent]
    require(not output.exists() and not any(output.resolve().is_relative_to(p.resolve())
            for p in inputs), 'Fresh output outside inputs required')
    paths = {name: indexed(qa, name + '.json')
             for name in ('source-coverage', 'near-duplicates', 'privacy-spans', 'summary')}
    paths['pilot-tasks'] = indexed(pilot, 'reviewer/tasks.json')
    paths['prior-privacy'] = prior_privacy
    bindings = {name: _file_hash(path) for name, path in paths.items()}
    ledger = read(recommendations)
    require(set(ledger) == {'schema_version', 'author_kind', 'input_sha256',
                           'scope', 'privacy', 'duplicates', *APPROVALS}, 'Unexpected ledger fields')
    require(ledger['schema_version'] == 'context-review-v1'
            and ledger['author_kind'] == 'ai_assistant', 'AI proposal ledger required')
    require(all(ledger[name] is False for name in APPROVALS), 'Approval forbidden in this tool')
    require(ledger['input_sha256'] == bindings, 'Recommendation input hashes differ')
    report = read(paths['summary'])
    require(report['input_sha256']['pilot_tasks'] == bindings['pilot-tasks'],
            'QA belongs to a different pilot')
    tasks = keyed(read(paths['pilot-tasks']), lambda r: r['task_id'])
    original = keyed(read(paths['privacy-spans']), lambda r: r['task_id'])
    prior = keyed(read(prior_privacy), lambda r: r['task_id'])
    require(set(tasks) == set(original) == set(prior), 'Privacy task coverage differs')
    for task_id, row in prior.items():
        text = tasks[task_id]['text']
        checksum = hashlib.sha256(text.encode('utf-8')).hexdigest()
        require(row['text_sha256'] == original[task_id]['text_sha256'] == checksum,
                'Privacy text hash differs')
        require(row['privacy_approved'] is False
                and row['ai_concerns'] == original[task_id]['ai_concerns'],
                'Prior review changes concern identity or asserts approval')
        spans_valid(row['proposed_spans'], text)

    pair_key = lambda r: (r['source_category'], r['source_subcategory'])
    coverage = read(paths['source-coverage'])
    scope_targets = keyed([r for r in coverage if r['disposition'] == 'scope_review'], pair_key)
    scope = keyed(ledger['scope'], pair_key)
    require(set(scope) == set(scope_targets), 'Exact scope-review coverage required')
    scope_records = Counter()
    for key, row in scope.items():
        require(set(row) == {'source_category', 'source_subcategory', 'recommendation', 'rationale'}
                and row['recommendation'] in SCOPE, 'Invalid scope recommendation')
        rationale(row)
        scope_records[row['recommendation']] += scope_targets[key]['records']

    targets = {k for k, r in prior.items() if r['ai_concerns'] and not r['proposed_spans']}
    privacy = keyed(ledger['privacy'], lambda r: r['task_id'])
    require(set(privacy) == targets, 'Exact pending contextual privacy coverage required')
    effective = deepcopy(prior)
    for task_id, row in privacy.items():
        require(set(row) == {'task_id', 'text_sha256', 'recommendation', 'rationale', 'proposed_spans'}
                and row['recommendation'] in PRIVACY, 'Invalid privacy recommendation')
        rationale(row)
        require(row['text_sha256'] == prior[task_id]['text_sha256'], 'Review text hash differs')
        spans_valid(row['proposed_spans'], tasks[task_id]['text'])
        require(bool(row['proposed_spans']) == (row['recommendation'] == 'redact_span_proposal'),
                'Redaction recommendations require spans; other dispositions cannot add spans')
        effective[task_id]['proposed_spans'] = row['proposed_spans']
        effective[task_id]['context_recommendation'] = row['recommendation']
        effective[task_id]['review_status'] = 'ai_proposal_only_pending_independent_review'

    duplicate_key = lambda r: (r['left'], r['right'])
    candidates = keyed(read(paths['near-duplicates']), duplicate_key)
    duplicates = keyed(ledger['duplicates'], duplicate_key)
    require(set(duplicates) == set(candidates), 'Exact duplicate candidate coverage required')
    for pair, row in duplicates.items():
        require(set(row) == {'left', 'right', 'recommendation', 'rationale', 'same_incident_verified'}
                and set(pair) <= set(tasks) and pair[0] != pair[1], 'Invalid duplicate review')
        require(row['same_incident_verified'] is False and row['recommendation'] in
                {'propose_split_containment_keep_both', 'hold_for_event_review'},
                'This tool cannot verify incident identity, merge or split records')
        rationale(row)

    summary = {
        'status': 'contextual_ai_recommendations_only',
        **{name: False for name in APPROVALS},
        'scope_pairs_reviewed': len(scope), 'scope_records_associated': sum(scope_records.values()),
        'scope_pair_recommendations': dict(Counter(r['recommendation'] for r in scope.values())),
        'scope_record_associations': dict(scope_records),
        'unresolved_source_pairs_unchanged': sum(r['disposition'] == 'unresolved' for r in coverage),
        'contextual_privacy_records_reviewed': len(privacy),
        'privacy_recommendations': dict(Counter(r['recommendation'] for r in privacy.values())),
        'additional_span_count': sum(len(r['proposed_spans']) for r in privacy.values()),
        'combined_span_records': sum(bool(r['proposed_spans']) for r in effective.values()),
        'combined_spans': sum(len(r['proposed_spans']) for r in effective.values()),
        'unflagged_records_not_reviewed_here': sum(not r['ai_concerns'] and not r['proposed_spans']
                                                 for r in prior.values()),
        'duplicate_candidates_reviewed': len(duplicates), 'source_texts_modified': 0,
        'raw_sha256': report['raw_sha256'],
        'input_sha256': {**bindings, 'recommendations': _file_hash(recommendations),
                         'validator': _file_hash(Path(__file__))},
    }
    output.mkdir(parents=True)
    (output / 'INCOMPLETE').write_text('Not a training release\n', encoding='utf-8')
    write_json(output / 'recommendations.json', ledger)
    write_json(output / 'privacy-spans.json', [effective[k] for k in sorted(effective)])
    write_json(output / 'summary.json', summary)
    write_json(output / 'artifacts.json', {p.name: _file_hash(p) for p in sorted(output.iterdir())
                                          if p.name != 'INCOMPLETE'})
    (output / 'COMPLETE').write_text('AI recommendations only; no release approval.\n', encoding='utf-8')
    (output / 'INCOMPLETE').unlink()
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('qa', 'pilot', 'prior-privacy', 'recommendations', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.qa, args.pilot, args.prior_privacy, args.recommendations, args.output)
    except (OSError, ValueError, KeyError, TypeError):
        parser.exit(1, 'Context review failed; inspect restricted local inputs.\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
