"""Bound development review packets and minimal redacted exports; not training authorization."""
import argparse
import hashlib
import json
from pathlib import Path
import unicodedata

from .curation_qa import indexed
from .issue_draft import FAMILIES
from .manifest import _file_hash
from .review_recommendations import read, require, keyed, spans_valid
from .text_proposal import write_json

ROOT = Path(__file__).resolve().parents[2]
GATES = ('indian_provenance', 'research_rights', 'privacy', 'labels', 'group_containment', 'target_definition')


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def redact(text, spans):
    spans_valid(spans, text)
    for span in reversed(spans):
        text = text[:span['start']] + '[REDACTED]' + text[span['end']:]
    require(text.replace('[REDACTED]', '').strip(), 'No useful text remains')
    return text


def fresh(output, inputs):
    resolved = output.resolve()
    require(not output.exists() and resolved.is_relative_to((ROOT / 'data/review').resolve())
            and not any(resolved.is_relative_to(p.resolve()) or p.resolve().is_relative_to(resolved)
                        for p in inputs), 'Fresh ignored output separate from inputs required')


def save(output, files, ledger=None):
    output.mkdir(parents=True)
    (output / 'INCOMPLETE').touch()
    for name, value in files.items():
        write_json(output / name, value)
    write_json(output / 'artifacts.json', {name: _file_hash(output / name) for name in files})
    if ledger is not None:
        ledger['packet_sha256'] = _file_hash(output / 'packet.json')
        write_json(output / 'decisions.json', ledger)
    (output / 'COMPLETE').touch()
    (output / 'INCOMPLETE').unlink()


def prepare(pilot, readiness, context, output):
    fresh(output, [pilot, readiness, context])
    paths = {'tasks': indexed(pilot, 'reviewer/tasks.json'),
             'inventory': indexed(readiness, 'inventory.json'),
             'summary': indexed(readiness, 'summary.json'),
             'privacy': indexed(context, 'privacy-spans.json')}
    tasks = keyed(read(paths['tasks']), lambda r: r['task_id'])
    inventory = keyed(read(paths['inventory']), lambda r: r['task_id'])
    privacy = keyed(read(paths['privacy']), lambda r: r['task_id'])
    summary = read(paths['summary'])
    require(set(tasks) == set(inventory) == set(privacy), 'Review coverage differs')
    require(summary['input_sha256']['tasks'] == _file_hash(paths['tasks'])
            and summary['input_sha256']['privacy'] == _file_hash(paths['privacy'])
            and summary['training_approved'] is False, 'Readiness binding differs')
    records, decisions = [], []
    for identity in sorted(tasks):
        text = tasks[identity]['text']
        require(text_hash(text) == privacy[identity]['text_sha256'], 'Text binding differs')
        spans_valid(privacy[identity]['proposed_spans'], text)
        row = inventory[identity]
        records.append({'task_id': identity, 'text': text, 'text_sha256': text_hash(text),
                        'group_id': row['component'], 'candidate_family': row['candidate_family'],
                        'disposition': row['disposition'], 'privacy_flags': row['privacy_flags'],
                        'proposed_spans': privacy[identity]['proposed_spans']})
        decisions.append({'task_id': identity, 'decision': 'pending', 'family': None,
                          'spans': [], 'rationale': '', 'text_sha256': text_hash(text)})
    packet = {'schema': 'development-review-v1', 'development_only': True,
              'input_sha256': {k: _file_hash(v) for k, v in paths.items()}, 'records': records}
    ledger = {'schema': 'development-decisions-v1', 'packet_sha256': None,
              'author_kind': 'pending', 'reviewer_id': '', 'reviewed_at': '',
              'gates': {g: {'approved': False, 'evidence': ''} for g in GATES}, 'records': decisions}
    # The editable ledger is deliberately outside the immutable packet index.
    save(output, {'packet.json': packet}, ledger)
    return {'records': len(records), 'training_approved': False, 'status': 'review_pending'}


def validate(packet, ledger, packet_hash):
    require(set(ledger) == {'schema', 'packet_sha256', 'author_kind', 'reviewer_id', 'reviewed_at', 'gates', 'records'}, 'Unexpected ledger fields')
    require(packet['schema'] == 'development-review-v1' and packet['development_only'] is True
            and ledger['schema'] == 'development-decisions-v1' and ledger['packet_sha256'] == packet_hash,
            'Packet binding differs')
    require(ledger['author_kind'] == 'human_reviewer' and isinstance(ledger['reviewer_id'], str)
            and bool(ledger['reviewer_id'].strip()), 'Independent accountable review required')
    from datetime import datetime
    reviewed = datetime.fromisoformat(ledger['reviewed_at'])
    require(reviewed.tzinfo is not None, 'Review timestamp must include timezone')
    require(set(ledger['gates']) == set(GATES), 'Required review gates missing')
    for gate in ledger['gates'].values():
        require(set(gate) == {'approved', 'evidence'} and gate['approved'] is True
                and isinstance(gate['evidence'], str) and len(gate['evidence'].strip()) >= 20,
                'Each gate requires an explicit decision and evidence reference')
    rows = keyed(packet['records'], lambda r: r['task_id'])
    decisions = keyed(ledger['records'], lambda r: r['task_id'])
    require(set(rows) == set(decisions), 'Every record requires a decision')
    exports, normalized, families = [], {}, {}
    for identity, row in sorted(rows.items()):
        decision = decisions[identity]
        require(set(decision) == {'task_id', 'decision', 'family', 'spans', 'rationale', 'text_sha256'}, 'Unexpected decision fields')
        require(text_hash(row['text']) == row['text_sha256'] == decision['text_sha256'], 'Stale text decision')
        require(decision['decision'] in {'include', 'exclude'} and isinstance(decision['rationale'], str)
                and len(decision['rationale'].strip()) >= 20, 'Unresolved record decision')
        spans_valid(decision['spans'], row['text'])
        if decision['decision'] == 'exclude':
            require(decision['family'] is None, 'Excluded records must not carry release labels')
            continue
        require(decision['family'] in set(FAMILIES) - {'unknown'}, 'Unknown reviewed family')
        require(isinstance(row['group_id'], str) and row['group_id'].strip(), 'Missing containment group')
        text = redact(row['text'], decision['spans'])
        normalized_text = ' '.join(unicodedata.normalize('NFKC', text).casefold().split())
        require(normalized_text not in normalized or normalized[normalized_text] == row['group_id'],
                'Redacted duplicate text crosses groups')
        normalized[normalized_text] = row['group_id']
        require(row['group_id'] not in families or families[row['group_id']] == decision['family'],
                'Conflicting labels in containment group')
        families[row['group_id']] = decision['family']
        exports.append({'record_id': identity, 'group_id': row['group_id'], 'text': text,
                        'label': decision['family'], 'label_origin': 'human_reviewed_development'})
    require(exports, 'No reviewed records to export')
    return exports


def export(packet_dir, decisions, output):
    fresh(output, [packet_dir, decisions])
    path = indexed(packet_dir, 'packet.json')
    rows = validate(read(path), read(decisions), _file_hash(path))
    summary = {'status': 'reviewed_development_export_not_training_authorization',
               'records': len(rows), 'groups': len({r['group_id'] for r in rows}),
               'packet_sha256': _file_hash(path), 'decisions_sha256': _file_hash(decisions),
               'training_approved': False, 'evaluation_holdout': False,
               'independent_test_performed': False, 'operational_release_approved': False}
    save(output, {'development.json': rows, 'summary.json': summary})
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    for flag in ('pilot', 'readiness', 'context', 'output'): prep.add_argument('--' + flag, type=Path, required=True)
    exp = commands.add_parser('export')
    for flag in ('packet', 'decisions', 'output'): exp.add_argument('--' + flag, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.pilot, args.readiness, args.context, args.output) if args.command == 'prepare' else export(args.packet, args.decisions, args.output)
    except (ValueError, OSError, KeyError, TypeError):
        parser.exit(1, 'Review packet/export refused: verify bindings, complete review and use fresh ignored output.\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
