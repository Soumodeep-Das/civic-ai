"""Synthetic engine tests; scores here say nothing about real complaints."""
from collections import Counter
import math
import warnings
import pytest

pytest.importorskip('sklearn', reason='Install .[test,research] for ML engine tests; CI requires it')
import joblib
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from research.civicai_research import text_baseline as runner
from research.civicai_research.manifest import _file_hash


@pytest.fixture
def protocol(): return runner.read(runner.POLICY)


def test_grouped_folds_are_deterministic_and_each_record_validated_once(protocol):
    rows = runner.synthetic_fixture()
    labels, folds = runner.build_folds(rows, protocol)
    assert len(rows) == 160 and len({r['group_id'] for r in rows}) == 80
    assert all(r['synthetic'] is True for r in rows)
    assert len(labels) == 4
    second = runner.build_folds(rows, protocol)[1]
    assert all(np.array_equal(a, c) and np.array_equal(b, d) for (a, b), (c, d) in zip(folds, second))
    assert Counter(int(i) for _, va in folds for i in va) == Counter({i: 1 for i in range(160)})
    for tr, va in folds:
        assert {rows[int(i)]['group_id'] for i in tr}.isdisjoint({rows[int(i)]['group_id'] for i in va})


@pytest.mark.parametrize('case', ['blank', 'duplicate_id', 'conflict', 'false_synthetic', 'forbidden_feature',
                                  'exact_duplicate_other_group', 'one_class', 'missing_group'])
def test_invalid_records_fail_before_fitting(case):
    rows = runner.synthetic_fixture()
    if case == 'blank': rows[0]['text'] = '  '
    if case == 'duplicate_id': rows[1]['record_id'] = rows[0]['record_id']
    if case == 'conflict': rows[1]['label'] = 'different'
    if case == 'false_synthetic': rows[0]['synthetic'] = False
    if case == 'forbidden_feature': rows[0]['source_category'] = 'secret-label'
    if case == 'exact_duplicate_other_group': rows[2]['text'] = '  ' + rows[0]['text'].upper() + ' '
    if case == 'one_class': rows = rows[:40]
    if case == 'missing_group': rows[0]['group_id'] = ''
    with pytest.raises(ValueError): runner.validate_records(rows)


def test_insufficient_groups_not_rescued_by_repeating_records(protocol):
    rows = runner.synthetic_fixture()
    for row in rows: row['group_id'] = row['label']
    with pytest.raises(ValueError, match='Insufficient groups'): runner.build_folds(rows, protocol)


@pytest.mark.parametrize('case', ['group_leak', 'missing_class', 'duplicate_validation', 'fractional_index'])
def test_actual_partitions_checked_before_fitting(protocol, case):
    rows = runner.synthetic_fixture(); labels, folds = runner.build_folds(rows, protocol)
    if case == 'group_leak':
        tr, va = folds[0]; folds[0] = (np.append(tr, va[0]), va[1:])
    if case == 'missing_class':
        va = [i for i, r in enumerate(rows) if r['label'] == labels[0]]
        folds[0] = ([i for i in range(len(rows)) if i not in va], va)
    if case == 'duplicate_validation': folds[1] = folds[0]
    if case == 'fractional_index':
        tr, va = folds[0]; folds[0] = ([float(i) for i in tr], va)
    with pytest.raises(ValueError): runner.validate_folds(rows, folds, labels, 3)


def test_vocabulary_and_idf_use_training_only_and_keep_negation(protocol):
    texts = ['not broken lamp raretraining', 'broken lamp', 'rubbish waste', 'rubbish collection']
    model, caught = runner.fit_pipeline(texts, ['light', 'light', 'waste', 'waste'], protocol,
                                        {'C': 1.0, 'class_weight': None})
    vectorizer = model.named_steps['tfidf']
    assert 'not' in vectorizer.vocabulary_ and 'not broken' in vectorizer.vocabulary_
    before = dict(vectorizer.vocabulary_); idf = vectorizer.idf_.copy()
    model.predict(['validationonlytoken lamp'])
    assert vectorizer.vocabulary_ == before and 'validationonlytoken' not in before
    assert np.array_equal(vectorizer.idf_, idf)
    assert idf[before['raretraining']] == pytest.approx(math.log(5 / 2) + 1)
    assert not caught


def test_empty_vocabulary_and_convergence_fail_instead_of_fake_success(protocol, monkeypatch):
    with pytest.raises(runner.BaselineError, match='empty vocabulary'):
        runner.fit_pipeline(['!!!', '???'], ['a', 'b'], protocol, {'C': 1.0, 'class_weight': None})
    def fake_fit(self, *args, **kwargs):
        warnings.warn('Synthetic failure', ConvergenceWarning)
        return self
    monkeypatch.setattr(LogisticRegression, 'fit', fake_fit)
    with pytest.raises(runner.BaselineError, match='Convergence'):
        runner.fit_pipeline(['broken lamp', 'rubbish pile'], ['a', 'b'], protocol, {'C': 1.0, 'class_weight': None})


def test_metrics_zero_prediction_class_and_fixed_label_order():
    result = runner.measure(['a', 'a', 'b', 'b'], ['a'] * 4, ['b', 'a'])
    assert result['macro_f1'] == pytest.approx(1 / 3)
    assert result['balanced_accuracy'] == 0.5
    assert result['per_class']['b'] == {'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'support': 2}
    assert result['confusion_matrix'] == [[0, 2], [0, 2]]
    with pytest.raises(ValueError): runner.measure(['a'], ['a'], ['a', 'b'])


def test_selection_tie_break_is_predeclared():
    rows = [{'mean_macro_f1': 0.5, 'parameters': {'C': c, 'class_weight': weight}}
            for c in (10.0, 1.0, 0.1) for weight in ('balanced', None)]
    assert runner.select_best(rows)['parameters'] == {'C': 0.1, 'class_weight': None}


def test_end_to_end_artifacts_repeat_predictions_and_keep_every_fit_fold_local(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    inputs = []; original = runner.fit_pipeline
    def observe(texts, labels, protocol, params):
        inputs.append(set(texts))
        return original(texts, labels, protocol, params)
    monkeypatch.setattr(runner, 'fit_pipeline', observe)
    outputs = [tmp_path / 'research/results/a', tmp_path / 'research/results/b']
    fixture = runner.synthetic_fixture()
    for output in outputs:
        result = runner.run(output, synthetic=True)
        assert result['out_of_fold_predictions'] == 1120 and result['model_candidates'] == 6
        assert not result['real_data_training_approved'] and not result['independent_test_performed']
        assert result['convergence_warnings'] == 0
        assert (output / 'COMPLETE').exists() and not (output / 'INCOMPLETE').exists()
        for name, value in runner.read(output / 'artifacts.json').items(): assert _file_hash(output / name) == value
        wrapped = joblib.load(output / 'synthetic-model.joblib')  # Own freshly produced trusted fixture artifact only.
        assert wrapped['artifact_kind'] == 'synthetic_smoke_model_not_for_deployment'
        assert len(wrapped['pipeline'].predict([r['text'] for r in fixture])) == 160
        preds = runner.read(output / 'predictions.json')
        assert set(Counter(p['model'] for p in preds).values()) == {160}
    for name in ('synthetic-fixture.json', 'split-plan.json', 'cv-results.json', 'predictions.json'):
        assert (outputs[0] / name).read_bytes() == (outputs[1] / name).read_bytes()
    _, folds = runner.build_folds(fixture, runner.read(runner.POLICY))
    expected_train = [{fixture[int(i)]['text'] for i in tr} for tr, _ in folds]
    assert inputs[:18] == expected_train * 6
    assert inputs[18] == {r['text'] for r in fixture}  # Final synthetic development refit only.


def test_failed_fit_preserves_incomplete_and_has_no_model(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    def fail(*args): raise runner.BaselineError('Convergence warning: run incomplete')
    monkeypatch.setattr(runner, 'fit_pipeline', fail)
    output = tmp_path / 'research/results/failed'
    with pytest.raises(runner.BaselineError): runner.run(output, synthetic=True)
    assert (output / 'INCOMPLETE').exists() and not (output / 'COMPLETE').exists()
    assert not (output / 'synthetic-model.joblib').exists()
    assert runner.read(output / 'failure.json')['convergence_warning'] is True
