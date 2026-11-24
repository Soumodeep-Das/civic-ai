"""Read staff decisions for a bounded page of authorized complaints."""
import hashlib
import json

from sqlalchemy import select

from civicai.models import ComplaintAssessment, ComplaintAssessmentReview, ComplaintPriorityEvent


def latest(session, model, key, ids, tie):
    statement = (select(model).where(key.in_(ids)).distinct(key)
                 .order_by(key, model.created_at.desc(), tie.desc()))
    return {getattr(row, key.key): row for row in session.scalars(statement)}


def decision(snapshot, review, fingerprint, proposed, corrected, superseded=False):
    if not snapshot:
        return "awaiting review", None
    if snapshot["input_sha256"] != fingerprint or superseded:
        return "needs reassessment", None
    if not review:
        return "awaiting review", None
    if review["decision"] == "deferred":
        return "deferred", None
    value = review.get(corrected) if review["decision"] == "corrected" else proposed
    return "reviewed", value


def summarize(session, complaints):
    if not complaints:
        return {}
    ids = [c.complaint_id for c in complaints]
    a, r, p = ComplaintAssessment, ComplaintAssessmentReview, ComplaintPriorityEvent
    assessments = latest(session, a, a.complaint_id, ids, a.assessment_id)
    reviews = latest(session, r, r.assessment_id, [v.assessment_id for v in assessments.values()], r.review_id)
    events = session.scalars(select(p).where(p.complaint_id.in_(ids)).order_by(p.created_at, p.event_id))
    contexts, decisions = {}, {}
    for event in events:
        payload = json.loads(event.payload)
        if payload["kind"] == "context":
            contexts[event.complaint_id] = (str(event.event_id), payload)
        else:
            decisions[event.complaint_id] = payload
    summaries = {}
    for c in complaints:
        fingerprint = hashlib.sha256(c.description.encode()).hexdigest()
        row = assessments.get(c.complaint_id)
        assessment = json.loads(row.payload) if row else {}
        review = reviews.get(row.assessment_id) if row else None
        cs, family = decision(assessment, json.loads(review.payload) if review else None,
                              fingerprint, assessment.get("suggested_family"), "corrected_family")
        snapshot_id, context = contexts.get(c.complaint_id, (None, {}))
        previous = decisions.get(c.complaint_id)
        ps, band = decision(context, previous, fingerprint, context.get("suggestion", {}).get("band"),
                            "corrected_band", bool(previous and previous["snapshot_id"] != snapshot_id))
        summaries[c.complaint_id] = dict(category_state=cs, category=family, priority_state=ps, priority=band)
    return summaries
