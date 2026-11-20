"""Versioned internal assessment contract. No automatic workflow authority."""
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

Family = Literal['roads_and_pedestrian_access', 'solid_waste', 'drainage_and_sewerage', 'public_lighting']

class AssessmentRecord(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    assessment_id: UUID
    complaint_id: UUID
    input_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    model_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    policy_version: str = Field(min_length=1, max_length=100)
    created_at: datetime
    state: Literal['suggested', 'needs_review']
    suggested_family: Family | None = None
    reasons: list[str] = Field(min_length=1, max_length=20)
    experimental: Literal[True] = True
    human_review_required: Literal[True] = True

    @model_validator(mode='after')
    def consistent(self):
        if (self.state=='suggested') != (self.suggested_family is not None):
            raise ValueError('Suggestion and state must agree')
        if self.created_at.tzinfo is None:
            raise ValueError('Timestamp requires timezone')
        if any(not reason.strip() or len(reason)>100 for reason in self.reasons):
            raise ValueError('Bounded reason codes required')
        return self

class AssessmentReviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    decision: Literal['accepted', 'corrected', 'deferred']
    corrected_family: Family | None = None
    note: str = Field(min_length=1, max_length=1000)

    @model_validator(mode='after')
    def consistent(self):
        if (self.decision=='corrected') != (self.corrected_family is not None):
            raise ValueError('Correction requires exactly one supported family')
        if not self.note.strip():
            raise ValueError('Review explanation required')
        return self
