import pytest
from research.civicai_research.issue_draft import transfer, run, MAPPING
from research.tests.test_curation_qa import setup

@pytest.mark.parametrize('label', list(MAPPING))
def test_transfer_never_invents_evidence_or_approval(label):
    row = {'task_id':'fixture', 'text_sha256':'0'*64, 'decision':'supported',
           'proposed_categories':[label], 'rationale':'Synthetic prior judgment.', 'privacy_concerns':['context']}
    result = transfer(row)
    assert not result['training_approved'] and not result['independent_reference']
    assert result['privacy_concerns'] == ['context']
    issue = result['issues'][0]
    assert issue['setting'] == issue['time_state'] == 'unknown'
    assert issue['text_evidence_verified'] is False
    if label == 'waterlogging': assert issue['family'] == 'unknown'


def test_gap_is_not_forced_into_other():
    row = {'task_id':'fixture', 'text_sha256':'0'*64, 'decision':'taxonomy_gap',
           'proposed_categories':[], 'rationale':'Synthetic gap.', 'privacy_concerns':[]}
    assert transfer(row)['issues'] == []
    assert transfer(row)['annotation_state'] == 'needs_richer_annotation'


def test_complete_transfer_preserves_inputs_and_refuses_overwrite(tmp_path):
    proposal, pilot, responses, config = setup(tmp_path)
    source = tmp_path / "source"
    source.mkdir()
    target = source / "responses.json"
    target.write_bytes(responses.read_bytes())
    responses = target
    before = responses.read_bytes()
    result = run(pilot, responses, tmp_path/'draft')
    assert result['records'] == 2 and result['fresh_text_annotations'] == 0
    assert responses.read_bytes() == before
    assert (tmp_path/'draft/COMPLETE').exists()
    with pytest.raises(ValueError): run(pilot, responses, tmp_path/'draft')
    with pytest.raises(ValueError): run(pilot, responses, pilot/'nested')


def test_partial_or_tampered_inputs_refused(tmp_path):
    from research.tests.test_ai_labels import batch, save
    pilot, data = batch(tmp_path)
    response = save(tmp_path, data)
    with pytest.raises(ValueError): run(pilot, response, tmp_path/'draft')
    assert not (tmp_path/'draft').exists()
