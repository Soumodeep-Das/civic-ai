import pytest
from types import SimpleNamespace
from research.civicai_research.assessment import assess

class Model:
    def __init__(self,label='drainage_and_sewerage',nnz=2):
        self.label=label; self.named_steps={'tfidf':SimpleNamespace(transform=lambda _:SimpleNamespace(nnz=nnz))}
    def predict(self,_): return [self.label]

@pytest.mark.parametrize('text,reason',[
 ('','empty_description'),(None,'empty_description'),('x'*10001,'description_too_long'),
 ('রাস্তার আলো জ্বলছে না','unsupported_script'),('The road was repaired','possible_resolved_or_negated_issue'),
 ('The drain is not blocked','possible_resolved_or_negated_issue'),('My passport renewal is delayed','outside_supported_vocabulary'),
 ('Garbage and streetlight issues','multiple_family_cues'),('asdf qwerty','outside_supported_vocabulary')])
def test_review(text,reason):
    result=assess(text,Model()); assert result['suggested_family'] is None; assert reason in result['reasons']

def test_suggestion():
    result=assess('The drain is overflowing',Model()); assert result['state']=='suggested'; assert result['human_review_required']


def test_non_road_issue_can_use_road_as_location_context():
    result=assess('Garbage has accumulated beside the public road',Model('solid_waste'))
    assert result['state']=='suggested'
    assert result['suggested_family']=='solid_waste'


def test_genuine_mixed_road_and_waste_issue_still_requires_review():
    result=assess('Garbage is filling a large pothole in the road',Model('solid_waste'))
    assert result['state']=='needs_review'
    assert result['reasons']==['multiple_family_cues']

@pytest.mark.parametrize('model,reason',[(None,'model_unavailable'),(Model(nnz=0),'no_known_model_features'),(Model('solid_waste'),'model_cue_disagreement'),(Model('invented'),'invalid_model_output')])
def test_failures(model,reason): assert reason in assess('Drain overflowing',model)['reasons']

def test_exception_not_exposed():
    class Broken(Model):
        def predict(self,_): raise RuntimeError('private content')
    assert assess('Drain overflowing',Broken())['reasons']==['assessment_failed']
