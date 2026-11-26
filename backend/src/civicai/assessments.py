"""Staff-only assessment reads and separate review history."""
import hashlib
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from civicai import ownership, service
from civicai.models import ComplaintAssessment, ComplaintAssessmentReview
from civicai.assessment_contract import AssessmentRecord


def list_assessments(session, complaint_id, actor):
    complaint=service.get_complaint(session, complaint_id)
    ownership.require_complaint_access(session, actor, complaint)
    rows=session.scalars(select(ComplaintAssessment).where(ComplaintAssessment.complaint_id==complaint_id).order_by(ComplaintAssessment.created_at.desc(),ComplaintAssessment.assessment_id)).all()
    return [AssessmentRecord.model_validate_json(row.payload) for row in rows]


def review_assessment(session, complaint_id, assessment_id, data, actor):
    complaint=service.get_complaint(session, complaint_id)
    ownership.require_complaint_access(session, actor, complaint)
    row=session.get(ComplaintAssessment,assessment_id)
    if row is None or row.complaint_id!=complaint_id: raise HTTPException(404,'Assessment not found')
    assessment=AssessmentRecord.model_validate_json(row.payload)
    if assessment.input_sha256!=hashlib.sha256(complaint.description.encode()).hexdigest(): raise HTTPException(409,'Assessment is stale')
    if data.decision=='accepted' and assessment.state!='suggested': raise HTTPException(422,'There is no suggestion to accept')
    review=ComplaintAssessmentReview(assessment_id=assessment_id,actor_id=actor.user_id,payload=data.model_dump_json())
    session.add(review);session.commit();session.refresh(review)
    return {'review_id':review.review_id,'assessment_id':assessment_id,'decision':data.decision,'created_at':review.created_at}


def generate_assessment(session, complaint_id, actor):
    from uuid import uuid4
    from datetime import datetime, timezone
    from civicai.assessment_policy import assess, POLICY_VERSION
    from civicai.experimental_model import load_experimental_model
    complaint=service.get_complaint(session, complaint_id)
    ownership.require_complaint_access(session, actor, complaint)
    try:
        model, expected = load_experimental_model()
        result=assess(complaint.description,model)
    except Exception:
        raise HTTPException(503,'Experimental model unavailable') from None
    record=AssessmentRecord(assessment_id=uuid4(),complaint_id=complaint_id,
        input_sha256=hashlib.sha256(complaint.description.encode()).hexdigest(),model_sha256=expected,
        policy_version=POLICY_VERSION,created_at=datetime.now(timezone.utc),**{k:v for k,v in result.items() if k!='policy_version'})
    session.add(ComplaintAssessment(assessment_id=record.assessment_id,complaint_id=complaint_id,payload=record.model_dump_json()))
    session.commit()
    return record


def review_history(session, complaint_id, assessment_id, actor):
    complaint=service.get_complaint(session, complaint_id)
    ownership.require_complaint_access(session, actor, complaint)
    row=session.get(ComplaintAssessment,assessment_id)
    if row is None or row.complaint_id!=complaint_id: raise HTTPException(404,'Assessment not found')
    import json
    return [{'review_id':r.review_id,'actor_id':r.actor_id,'created_at':r.created_at,**json.loads(r.payload)} for r in session.scalars(select(ComplaintAssessmentReview).where(ComplaintAssessmentReview.assessment_id==assessment_id).order_by(ComplaintAssessmentReview.created_at,ComplaintAssessmentReview.review_id))]
