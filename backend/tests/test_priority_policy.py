from itertools import product
import pytest
from pydantic import ValidationError
from civicai.priority_policy import ReportedContext, suggest_priority

@pytest.mark.parametrize("danger,access,service", list(product(("yes", "no", "unknown", "conflict"), repeat=3)))
def test_context_matrix(danger, access, service):
    context = ReportedContext(source="citizen_report", immediate_danger=danger, access_blocked=access, essential_service_interrupted=service)
    result = suggest_priority(context)
    assert result == suggest_priority(context)
    assert result.human_review_required and result.experimental
    assert result.emergency_review == (danger in ("yes", "conflict"))
    if "conflict" in (danger, access, service) or danger != "no":
        assert result.state == "needs_review" and result.band is None
    elif "yes" in (access, service):
        assert result.band == "High"
    elif "unknown" in (access, service):
        assert result.state == "needs_review" and result.band is None
    else:
        assert result.band == "Medium"
    assert len(result.unknowns) == (danger, access, service).count("unknown")

@pytest.mark.parametrize("values", [{}, {"source":"image_observation"}, {"source":"citizen_report", "access_blocked":True}, {"source":"citizen_report", "traffic":100}])
def test_invalid_or_unattributed_context(values):
    with pytest.raises(ValidationError):
        ReportedContext(**values)

def test_default_unknown_is_not_low_priority():
    result = suggest_priority(ReportedContext(source="municipal_report"))
    assert result.state == "needs_review" and result.band is None
    assert len(result.unknowns) == 3
