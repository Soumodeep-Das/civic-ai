"""These fail-closed checks run even without optional ML libraries installed."""
from pathlib import Path
import pytest
from research.civicai_research import text_baseline as runner


@pytest.mark.parametrize('synthetic', [False, True])
def test_real_release_rejected_before_reading_or_creating_output(tmp_path, monkeypatch, synthetic):
    def forbidden(*args, **kwargs): raise AssertionError('No input may be opened')
    monkeypatch.setattr(Path, 'read_text', forbidden)
    with pytest.raises(runner.BaselineError, match='Real-data execution is disabled'):
        runner.run(tmp_path / 'out', synthetic=synthetic, release=tmp_path / 'approval.json')
    assert not (tmp_path / 'out').exists()


def test_explicit_synthetic_mode_and_ignored_fresh_output_required(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    with pytest.raises(runner.BaselineError): runner.run(tmp_path / 'out')
    with pytest.raises(ValueError): runner.run(tmp_path / 'public-output', synthetic=True)
    output = tmp_path / 'research/results/existing'; output.mkdir(parents=True)
    with pytest.raises(ValueError): runner.run(output, synthetic=True)
