from datetime import datetime, timezone
from uuid import uuid4
import pytest
from pydantic import ValidationError
from civicai.assessment_contract import AssessmentRecord, AssessmentReviewRequest


def record():
    return dict(assessment_id=uuid4(), complaint_id=uuid4(), input_sha256='a'*64, model_sha256='b'*64, policy_version='v1', created_at=datetime.now(timezone.utc), state='needs_review', reasons=['unsupported'])


def test_valid_review_required():
    assert AssessmentRecord(**record()).human_review_required

@pytest.mark.parametrize('change',[{'state':'suggested'}, {'suggested_family':'solid_waste'}, {'human_review_required':False}, {'input_sha256':'bad'}, {'created_at':datetime(2026,1,1)}, {'status':'resolved'}, {'reasons':[' ']}])
def test_invalid_record(change):
    values=record();values.update(change)
    with pytest.raises(ValidationError): AssessmentRecord(**values)

@pytest.mark.parametrize('values',[{'decision':'corrected','note':'reviewed'}, {'decision':'accepted','note':'reviewed','corrected_family':'solid_waste'}, {'decision':'deferred','note':' '}, {'decision':'accepted','note':'reviewed','actor_id':'spoof'}])
def test_invalid_review(values):
    with pytest.raises(ValidationError): AssessmentReviewRequest(**values)


def test_correction():
    assert AssessmentReviewRequest(decision='corrected',corrected_family='solid_waste',note='Reviewed evidence').corrected_family=='solid_waste'
