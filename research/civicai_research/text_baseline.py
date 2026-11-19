"""Offline baseline engineering smoke test. Real complaint releases are disabled."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from numbers import Integral
import os
from pathlib import Path
import platform
import subprocess
import time
import unicodedata
import warnings

from .baseline_readiness import POLICY
from .manifest import _file_hash
from .review_recommendations import read, require
from .text_proposal import write_json

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ('scikit-learn', 'numpy', 'scipy', 'joblib', 'threadpoolctl')


class BaselineError(ValueError):
    """Sanitized failure; no complaint content in errors or ordinary logs."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def synthetic_fixture():
    """Authored toy sentences, not observations or Indian research data."""
    templates = {
        'roads_and_pedestrian_access': 'The road surface is broken with a pothole beside the footpath.',
        'solid_waste': 'Garbage collection has stopped and rubbish is accumulating beside the bin.',
        'public_lighting': 'The streetlight lamp is not working and the lane remains dark.',
        'drainage_and_sewerage': 'The drain is blocked and sewage is overflowing from the manhole.',
    }
    rows = []
    serial = 0
    for family, text in sorted(templates.items()):
        for _ in range(20):
            # Unique sentinel permits tests to detect validation vocabulary leakage.
            marker = f'fixturetoken{serial:03d}'
            for variant in range(2):
                rows.append({'record_id': f'synthetic-{serial:03d}-{variant}',
                             'group_id': f'synthetic-group-{serial:03d}',
                             'text': f'{text} {marker} ' + ('Please inspect.' if variant else 'Please repair.'),
                             'label': family, 'synthetic': True})
            serial += 1
    return rows


def validate_records(rows):
    require(isinstance(rows, list) and 1 <= len(rows) <= 10000, 'Invalid bounded fixture')
    ids, normalized, group_labels = set(), {}, defaultdict(set)
    for row in rows:
        require(set(row) == {'record_id', 'group_id', 'text', 'label', 'synthetic'}
                and row['synthetic'] is True, 'Only synthetic fixture records are supported')
        require(all(isinstance(row[k], str) and row[k].strip()
                    for k in ('record_id', 'group_id', 'text', 'label'))
                and len(row['text']) <= 20000, 'Missing or oversized fixture fields')
        require(row['record_id'] not in ids, 'Duplicate record identity')
        ids.add(row['record_id'])
        group_labels[row['group_id']].add(row['label'])
        text = ' '.join(unicodedata.normalize('NFKC', row['text']).casefold().split())
        require(text not in normalized or normalized[text] == row['group_id'],
                'Identical normalized text crosses declared groups')
        normalized[text] = row['group_id']
    require(all(len(labels) == 1 for labels in group_labels.values()), 'Conflicting group labels')
    labels = sorted({row['label'] for row in rows})
    require(len(labels) >= 2, 'At least two classes required')
    return labels


def validate_folds(rows, folds, labels, n_splits):
    """Inspect actual partitions; splitter stratification is not a guarantee."""
    universe = set(range(len(rows)))
    validation_counts = Counter()
    require(len(folds) == n_splits, 'Incorrect number of folds')
    for train, valid in folds:
        require(all(isinstance(i, Integral) and not isinstance(i, bool) for i in [*train, *valid]),
                'Fold indexes must be integers')
        tr, va = set(map(int, train)), set(map(int, valid))
        require(tr and va and len(tr) == len(train) and len(va) == len(valid)
                and tr.isdisjoint(va) and tr | va == universe, 'Invalid record partition')
        require({rows[i]['group_id'] for i in tr}.isdisjoint({rows[i]['group_id'] for i in va}),
                'Group crosses training and validation')
        require({rows[i]['label'] for i in tr} == set(labels)
                and {rows[i]['label'] for i in va} == set(labels), 'A fold is missing a class')
        validation_counts.update(va)
    require(validation_counts == Counter({i: 1 for i in universe}), 'Validation coverage is not exactly once')


def build_folds(rows, protocol):
    from sklearn.model_selection import StratifiedGroupKFold
    labels = validate_records(rows)
    config = protocol['development_validation']
    require(config['method'] == 'StratifiedGroupKFold' and config['n_splits'] == 3
            and config['shuffle'] is True and config['random_state'] == 42,
            'Unsupported development protocol')
    counts = {label: len({r['group_id'] for r in rows if r['label'] == label}) for label in labels}
    require(min(counts.values()) >= config['n_splits'], 'Insufficient groups for class-complete folds')
    splitter = StratifiedGroupKFold(n_splits=config['n_splits'], shuffle=True, random_state=42)
    folds = list(splitter.split([r['text'] for r in rows], [r['label'] for r in rows],
                               [r['group_id'] for r in rows]))
    validate_folds(rows, folds, labels, config['n_splits'])
    return labels, folds


def fit_pipeline(texts, labels, protocol, params):
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    model = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), **protocol['tfidf'])),
        ('classifier', LogisticRegression(C=params['C'], class_weight=params['class_weight'],
                                          solver=protocol['logistic_regression']['solver'],
                                          max_iter=protocol['logistic_regression']['max_iter'], random_state=42)),
    ])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        try:
            model.fit(texts, labels)
        except ValueError as exc:
            raise BaselineError('Training failed; empty vocabulary or invalid training input') from exc
    if any(issubclass(w.category, ConvergenceWarning) for w in caught):
        raise BaselineError('Convergence warning: run incomplete')
    return model, dict(Counter(w.category.__name__ for w in caught))


def measure(truth, predicted, labels):
    from sklearn.metrics import balanced_accuracy_score, confusion_matrix, precision_recall_fscore_support
    require(bool(truth) and len(truth) == len(predicted) and set(truth) == set(labels)
            and set(predicted) <= set(labels), 'Invalid metric labels or coverage')
    p, r, f, support = precision_recall_fscore_support(truth, predicted, labels=labels, zero_division=0)
    return {'macro_f1': float(f.mean()), 'balanced_accuracy': float(balanced_accuracy_score(truth, predicted)),
            'per_class': {label: {'precision': float(p[i]), 'recall': float(r[i]),
                                  'f1': float(f[i]), 'support': int(support[i])}
                          for i, label in enumerate(labels)},
            'confusion_matrix': confusion_matrix(truth, predicted, labels=labels).tolist(),
            'label_order': labels}


def select_best(results):
    require(bool(results), 'No model results')
    return min(results, key=lambda r: (-r['mean_macro_f1'], r['parameters']['C'],
                                       r['parameters']['class_weight'] is not None))


def evaluate(rows, protocol, labels, folds):
    """Internal development engine; CLI supplies only the built-in synthetic fixture."""
    import numpy as np
    from sklearn.dummy import DummyClassifier
    results, predictions, dummy_folds = [], [], []
    warnings_seen = Counter()

    def record_predictions(model_id, fold_id, valid, predicted):
        for index, prediction in zip(valid, predicted, strict=True):
            row = rows[int(index)]
            predictions.append({'record_id': row['record_id'], 'group_id': row['group_id'],
                                'fold': fold_id, 'model': model_id, 'truth': row['label'],
                                'prediction': str(prediction), 'synthetic': True})

    for fold_id, (train, valid) in enumerate(folds):
        dummy = DummyClassifier(strategy='most_frequent')
        dummy.fit(np.zeros((len(train), 1)), [rows[int(i)]['label'] for i in train])
        predicted = dummy.predict(np.zeros((len(valid), 1)))
        dummy_folds.append(measure([rows[int(i)]['label'] for i in valid], list(predicted), labels))
        record_predictions('dummy_most_frequent', fold_id, valid, predicted)
    for c in protocol['logistic_regression']['C']:
        for weight in protocol['logistic_regression']['class_weight']:
            params = {'C': c, 'class_weight': weight}
            model_id = f'linear_C{c}_weight{weight}'
            metrics = []
            for fold_id, (train, valid) in enumerate(folds):
                model, warning_counts = fit_pipeline([rows[int(i)]['text'] for i in train],
                                                     [rows[int(i)]['label'] for i in train], protocol, params)
                warnings_seen.update(warning_counts)
                predicted = model.predict([rows[int(i)]['text'] for i in valid])
                metrics.append(measure([rows[int(i)]['label'] for i in valid], list(predicted), labels))
                record_predictions(model_id, fold_id, valid, predicted)
            results.append({'model': model_id, 'parameters': params, 'folds': metrics,
                            'mean_macro_f1': sum(m['macro_f1'] for m in metrics) / len(metrics)})
    winner = select_best(results)
    final, warning_counts = fit_pipeline([r['text'] for r in rows], [r['label'] for r in rows],
                                         protocol, winner['parameters'])
    warnings_seen.update(warning_counts)
    return final, {'synthetic': True, 'candidates': results, 'dummy_folds': dummy_folds, 'selected_model': winner['model'],
                   'selected_parameters': winner['parameters'], 'warning_categories': dict(warnings_seen),
                   'score_role': 'synthetic_development_selection_only_not_independent_test'}, predictions


def git_state():
    def git(*args):
        return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    try:
        return {'revision': git('rev-parse', 'HEAD'), 'worktree_dirty': bool(git('status', '--porcelain'))}
    except (OSError, subprocess.CalledProcessError):
        return {'revision': None, 'worktree_dirty': None}


def run(output, *, synthetic=False, release=None):
    # Reject any release before opening it or importing a fitting library.
    if release is not None or synthetic is not True:
        raise BaselineError('Real-data execution is disabled pending a reviewed release loader; use --synthetic')
    require(not output.exists() and output.resolve().is_relative_to((ROOT / 'research/results').resolve()),
            'Use a fresh directory inside ignored research/results')
    protocol = read(POLICY)
    require(protocol['version'] == 'civicai-text-baseline-protocol-v1'
            and protocol['training_approved'] is False and protocol['evaluation_holdout'] is False,
            'Unsupported or approved-real-data protocol')
    import joblib
    from threadpoolctl import threadpool_limits
    rows = synthetic_fixture()
    labels, folds = build_folds(rows, protocol)
    splits = [{'fold': fold_id, 'train': [rows[int(i)]['record_id'] for i in train],
               'validation': [rows[int(i)]['record_id'] for i in valid],
               'train_groups': sorted({rows[int(i)]['group_id'] for i in train}),
               'validation_groups': sorted({rows[int(i)]['group_id'] for i in valid})}
              for fold_id, (train, valid) in enumerate(folds)]
    output.mkdir(parents=True)
    (output / 'INCOMPLETE').write_text('Synthetic development smoke test, not a research result.\n')
    started = datetime.now(timezone.utc).isoformat()
    tick = time.perf_counter()
    try:
        write_json(output / 'synthetic-fixture.json', rows)
        write_json(output / 'protocol.json', protocol)
        write_json(output / 'split-plan.json', splits)
        with threadpool_limits(limits=1):
            model, cv_results, predictions = evaluate(rows, protocol, labels, folds)
        write_json(output / 'cv-results.json', cv_results)
        write_json(output / 'predictions.json', predictions)
        joblib.dump({'artifact_kind': 'synthetic_smoke_model_not_for_deployment',
                     'real_data_training_approved': False, 'pipeline': model,
                     'label_order': labels, 'protocol_sha256': _file_hash(POLICY)},
                    output / 'synthetic-model.joblib', compress=3)
        summary = {
            'status': 'synthetic_smoke_test_complete_not_research_results', 'synthetic': True,
            'real_data_training_approved': False, 'independent_test_performed': False,
            'operational_release_approved': False, 'records': len(rows),
            'groups': len({r['group_id'] for r in rows}), 'label_order': labels,
            'folds': len(folds), 'model_candidates': len(cv_results['candidates']),
            'out_of_fold_predictions': len(predictions), 'selected_parameters': cv_results['selected_parameters'],
            'warning_categories': cv_results['warning_categories'], 'convergence_warnings': 0,
            'excluded_records': 0, 'record_coverage': 1.0, 'group_coverage': 1.0,
            'final_fit_role': 'all_synthetic_development_records_not_holdout_evaluation',
            'fixture_sha256': digest(rows), 'split_plan_sha256': digest(splits),
            'implementation_sha256': _file_hash(Path(__file__)), 'protocol_sha256': _file_hash(POLICY),
            'git': git_state(), 'packages': {name: version(name) for name in PACKAGES},
            'python': platform.python_version(), 'platform': platform.platform(),
            'machine': platform.machine(), 'cpu_count': os.cpu_count(), 'numeric_threads': 1,
            'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(),
            'elapsed_seconds': round(time.perf_counter() - tick, 6),
        }
        write_json(output / 'summary.json', summary)
        write_json(output / 'artifacts.json', {p.name: _file_hash(p) for p in sorted(output.iterdir()) if p.name != 'INCOMPLETE'})
        (output / 'COMPLETE').write_text('Synthetic-only engine verification; not CivicAI model performance.\n')
        (output / 'INCOMPLETE').unlink()
        return summary
    except Exception as exc:
        # Never mark a partial model/run complete; avoid raw exception text in artifacts.
        write_json(output / 'failure.json', {'status': 'incomplete', 'error_type': type(exc).__name__,
                                            'synthetic': True, 'convergence_warning': isinstance(exc, BaselineError)
                                            and 'Convergence' in str(exc)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--synthetic', action='store_true')
    mode.add_argument('--release', type=Path, help='Reserved: real-data execution fails closed')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        summary = run(args.output, synthetic=args.synthetic, release=args.release)
    except ModuleNotFoundError:
        parser.exit(1, 'Install the optional research dependencies: python -m pip install -e ".[test,research]"\n')
    except (ValueError, OSError, KeyError, TypeError):
        parser.exit(1, 'Baseline run refused or incomplete; use a fresh ignored output and the supported synthetic mode.\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
