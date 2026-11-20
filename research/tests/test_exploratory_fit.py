import hashlib
import pytest
pytest.importorskip('sklearn')
from research.civicai_research.exploratory_fit import checked_rows


def inputs():
    h=hashlib.sha256(b'Blocked drain').hexdigest()
    p={'records':[{'task_id':'toy','text':'Blocked drain','text_sha256':h,'candidate_family':'drain','disposition':'annotation_candidate','group_id':'g','proposed_spans':[],'privacy_flags':[]}]}
    d=[{'task_id':'toy','text_sha256':h,'family_proposal':'drain','group_id':'g','author_kind':'ai_assistant','training_approved':False,'decision':'candidate_local_exploration'}]
    return p,d


def test_valid():
    p,d=inputs(); assert checked_rows(p,d,['drain'])[0]['text']=='Blocked drain'


@pytest.mark.parametrize('case',['duplicate','text','author','hold','missing','decision'])
def test_invalid(case):
    p,d=inputs()
    if case=='duplicate': d.append(d[0])
    if case=='text': p['records'][0]['text']='Changed'
    if case=='author': d[0]['author_kind']='human'
    if case=='hold': p['records'][0]['privacy_flags']=['context_hold']
    if case=='missing': d.clear()
    if case=='decision': d[0]['decision']='approved'
    with pytest.raises(ValueError): checked_rows(p,d,['drain'])
