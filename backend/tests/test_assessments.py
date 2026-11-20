def test_empty_assessments(client):
    created=client.post('/api/v1/complaints',files={'description':(None,'Blocked drain')})
    assert created.status_code==201
    identity=created.json()['complaint_id']
    response=client.get(f'/api/v1/admin/complaints/{identity}/assessments')
    assert response.status_code==200 and response.json()==[]


def test_assessments_require_auth(anonymous_client):
    response=anonymous_client.get('/api/v1/admin/complaints/00000000-0000-0000-0000-000000000001/assessments')
    assert response.status_code==401


def test_review_persists_without_status_change(client):
    from uuid import UUID, uuid4
    from datetime import datetime, timezone
    import hashlib
    from sqlalchemy.orm import Session
    from sqlalchemy import select
    from civicai.models import ComplaintAssessment, ComplaintAssessmentReview
    from civicai.assessment_contract import AssessmentRecord
    created=client.post('/api/v1/complaints',files={'description':(None,'Blocked drain')}).json()
    identity=created['complaint_id']; assessment_id=uuid4()
    record=AssessmentRecord(assessment_id=assessment_id,complaint_id=UUID(identity),input_sha256=hashlib.sha256(b'Blocked drain').hexdigest(),model_sha256='a'*64,policy_version='test',created_at=datetime.now(timezone.utc),state='suggested',suggested_family='drainage_and_sewerage',reasons=['test'])
    with Session(bind=client.app.state.test_connection,join_transaction_mode='create_savepoint') as session:
        session.add(ComplaintAssessment(assessment_id=assessment_id,complaint_id=UUID(identity),payload=record.model_dump_json()));session.commit()
    url=f'/api/v1/admin/complaints/{identity}/assessments'
    assert client.get(url).json()[0]['suggested_family']=='drainage_and_sewerage'
    response=client.post(f'{url}/{assessment_id}/reviews',json={'decision':'accepted','note':'Checked evidence'})
    assert response.status_code==201
    assert client.get(f'/api/v1/admin/complaints/{identity}').json()['status']==created['status']
    with Session(bind=client.app.state.test_connection,join_transaction_mode='create_savepoint') as session:
        saved=session.scalar(select(ComplaintAssessmentReview).where(ComplaintAssessmentReview.assessment_id==assessment_id))
        assert saved is not None and saved.actor_id is not None
    client.headers.pop('X-CSRF-Token')
    assert client.post(f'{url}/{assessment_id}/reviews',json={'decision':'accepted','note':'Checked evidence'}).status_code==403


def test_generation_disabled_and_hash_failure(client,monkeypatch,tmp_path):
    identity=client.post('/api/v1/complaints',files={'description':(None,'Blocked drain')}).json()['complaint_id']
    url=f'/api/v1/admin/complaints/{identity}/assessments'
    monkeypatch.delenv('CIVICAI_EXPERIMENTAL_MODEL_PATH',raising=False)
    assert client.post(url,json={}).status_code==503
    model=tmp_path/'invalid.joblib';model.write_bytes(b'not a model')
    monkeypatch.setenv('CIVICAI_EXPERIMENTAL_MODEL_PATH',str(model))
    monkeypatch.setenv('CIVICAI_EXPERIMENTAL_MODEL_SHA256','a'*64)
    assert client.post(url,json={}).status_code==503
    assert client.get(url).json()==[]


def test_actual_local_model_generation(client,monkeypatch):
    import hashlib
    from pathlib import Path
    import pytest
    model=Path('research/results/exploratory-ai-labels-v1/experimental-model.joblib')
    if not model.exists(): pytest.skip('Private local artifact not shipped in CI')
    monkeypatch.setenv('CIVICAI_EXPERIMENTAL_MODEL_PATH',str(model.resolve()))
    monkeypatch.setenv('CIVICAI_EXPERIMENTAL_MODEL_SHA256',hashlib.sha256(model.read_bytes()).hexdigest())
    identity=client.post('/api/v1/complaints',files={'description':(None,'The drain is overflowing')}).json()['complaint_id']
    url=f'/api/v1/admin/complaints/{identity}/assessments'
    generated=client.post(url,json={});assert generated.status_code==201
    assert generated.json()['suggested_family']=='drainage_and_sewerage'
    aid=generated.json()['assessment_id']
    assert client.post(f'{url}/{aid}/reviews',json={'decision':'corrected','corrected_family':'solid_waste','note':'Synthetic integration test correction'}).status_code==201
    history=client.get(f'{url}/{aid}/reviews').json()
    assert len(history)==1 and history[0]['corrected_family']=='solid_waste'
    assert client.get(url).json()[0]['suggested_family']=='drainage_and_sewerage'


def test_operator_cannot_access_unassigned_complaint(operator_client):
    from uuid import uuid4
    client=operator_client
    identity=client.post('/api/v1/complaints',files={'description':(None,'Blocked drain')}).json()['complaint_id']
    url=f'/api/v1/admin/complaints/{identity}/assessments'
    assert client.get(url).status_code==403
    assert client.post(url,json={}).status_code==403
    assert client.get(f'{url}/{uuid4()}/reviews').status_code==403
    assert client.post(f'{url}/{uuid4()}/reviews',json={'decision':'deferred','note':'review'}).status_code==403


import pytest

@pytest.mark.parametrize('state,stale,decision,expected',[
    ('suggested',False,'corrected',201),('needs_review',False,'deferred',201),
    ('needs_review',False,'accepted',422),('suggested',True,'accepted',409)])
def test_review_boundaries(client,state,stale,decision,expected):
    from uuid import UUID,uuid4
    from datetime import datetime,timezone
    import hashlib
    from sqlalchemy.orm import Session
    from civicai.models import ComplaintAssessment
    from civicai.assessment_contract import AssessmentRecord
    created=client.post('/api/v1/complaints',files={'description':(None,'Blocked drain')}).json()
    cid=created['complaint_id'];aid=uuid4()
    record=AssessmentRecord(assessment_id=aid,complaint_id=UUID(cid),input_sha256='0'*64 if stale else hashlib.sha256(b'Blocked drain').hexdigest(),model_sha256='a'*64,policy_version='test',created_at=datetime.now(timezone.utc),state=state,suggested_family='drainage_and_sewerage' if state=='suggested' else None,reasons=['test'])
    with Session(bind=client.app.state.test_connection,join_transaction_mode='create_savepoint') as session:
        session.add(ComplaintAssessment(assessment_id=aid,complaint_id=UUID(cid),payload=record.model_dump_json()));session.commit()
    url=f'/api/v1/admin/complaints/{cid}/assessments/{aid}/reviews'
    body={'decision':decision,'note':'Isolated regression review'}
    if decision=='corrected':body['corrected_family']='solid_waste'
    assert client.post(url,json=body).status_code==expected
    history=client.get(url).json()
    assert len(history)==(1 if expected==201 else 0)
    if expected==201: assert history[0]['decision']==decision and history[0]['note']==body['note']
    after=client.get(f'/api/v1/admin/complaints/{cid}').json()
    assert after['status']==created['status'] and after['updated_at']==created['updated_at']
    other=client.post('/api/v1/complaints',files={'description':(None,'Another report')}).json()['complaint_id']
    assert client.get(f'/api/v1/admin/complaints/{other}/assessments/{aid}/reviews').status_code==404
    assert client.post(f'/api/v1/admin/complaints/{other}/assessments/{aid}/reviews',json=body).status_code==404
