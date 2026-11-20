"""Append-only API for reported context and human priority decisions."""
import hashlib
import json
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
from fastapi import HTTPException
from sqlalchemy import select
from civicai import ownership, service
from civicai.models import Complaint, ComplaintPriorityEvent
from civicai.priority_policy import ReportedContext, suggest_priority

class ContextRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    context: ReportedContext
    note: str = Field(min_length=1, max_length=1000)

    @model_validator(mode='after')
    def nonblank(self):
        if not self.note.strip():
            raise ValueError('Evidence explanation required')
        return self

class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    snapshot_id: UUID
    decision: Literal['accepted', 'corrected', 'deferred']
    corrected_band: Literal['Low', 'Medium', 'High', 'Critical'] | None = None
    note: str = Field(min_length=1, max_length=1000)

    @model_validator(mode='after')
    def consistent(self):
        if not self.note.strip() or ((self.decision == 'corrected') != (self.corrected_band is not None)):
            raise ValueError('Explanation and consistent correction required')
        return self

def fingerprint(complaint):
    return hashlib.sha256(complaint.description.encode()).hexdigest()

def authorize(session, complaint_id, actor, lock=False):
    complaint = service.get_complaint(session, complaint_id)
    ownership.require_complaint_access(session, actor, complaint)
    if lock:
        session.execute(select(Complaint).where(Complaint.complaint_id == complaint_id).with_for_update())
        session.refresh(complaint)
        ownership.require_complaint_access(session, actor, complaint)
    return complaint

def history(session, complaint_id, actor):
    authorize(session, complaint_id, actor)
    rows = session.scalars(select(ComplaintPriorityEvent).where(ComplaintPriorityEvent.complaint_id == complaint_id).order_by(ComplaintPriorityEvent.created_at, ComplaintPriorityEvent.event_id))
    return [dict(event_id=r.event_id, actor_id=r.actor_id, created_at=r.created_at, **json.loads(r.payload)) for r in rows]

def save(session, complaint_id, actor, payload):
    row = ComplaintPriorityEvent(complaint_id=complaint_id, actor_id=actor.user_id, payload=json.dumps(payload))
    session.add(row)
    session.commit()
    session.refresh(row)
    return dict(event_id=row.event_id, actor_id=row.actor_id, created_at=row.created_at, **payload)

def create_context(session, complaint_id, actor, data):
    complaint = authorize(session, complaint_id, actor, lock=True)
    return save(session, complaint_id, actor, dict(kind='context', input_sha256=fingerprint(complaint), context=data.context.model_dump(), note=data.note, suggestion=suggest_priority(data.context).model_dump()))

def review(session, complaint_id, actor, data):
    complaint = authorize(session, complaint_id, actor, lock=True)
    events = history(session, complaint_id, actor)
    snapshots = [e for e in events if e['kind'] == 'context']
    target = next((e for e in snapshots if e['event_id'] == data.snapshot_id), None)
    if target is None:
        raise HTTPException(404, 'Priority snapshot not found')
    if target != snapshots[-1] or target['input_sha256'] != fingerprint(complaint):
        raise HTTPException(409, 'Context changed; reload before review')
    if data.decision == 'accepted' and target['suggestion']['state'] != 'suggested':
        raise HTTPException(422, 'There is no priority suggestion to accept')
    return save(session, complaint_id, actor, dict(kind='review', **data.model_dump(mode='json')))
