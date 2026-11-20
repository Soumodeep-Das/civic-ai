"""Offline, reported-context priority prototype; no workflow authority."""
from typing import Literal
from pydantic import BaseModel, ConfigDict

Fact = Literal["yes", "no", "unknown", "conflict"]
FIELDS = ("immediate_danger", "access_blocked", "essential_service_interrupted")

class ReportedContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source: Literal["citizen_report", "municipal_report"]
    immediate_danger: Fact = "unknown"
    access_blocked: Fact = "unknown"
    essential_service_interrupted: Fact = "unknown"

class PrioritySuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy_version: Literal["reported-context-v1"] = "reported-context-v1"
    state: Literal["suggested", "needs_review"]
    band: Literal["High", "Medium"] | None = None
    reasons: tuple[str, ...]
    unknowns: tuple[str, ...]
    emergency_review: bool = False
    human_review_required: Literal[True] = True
    experimental: Literal[True] = True


def suggest_priority(context: ReportedContext) -> PrioritySuggestion:
    unknowns = tuple(f for f in FIELDS if getattr(context, f) == "unknown")
    conflicts = tuple(f for f in FIELDS if getattr(context, f) == "conflict")
    emergency = context.immediate_danger in ("yes", "conflict")
    if conflicts:
        return PrioritySuggestion(state="needs_review", reasons=tuple("conflicting_" + f for f in conflicts), unknowns=unknowns, emergency_review=emergency)
    if context.immediate_danger != "no":
        return PrioritySuggestion(state="needs_review", reasons=("reported_immediate_danger" if emergency else "unknown_immediate_danger",), unknowns=unknowns, emergency_review=emergency)
    disruption = tuple("reported_" + f for f in FIELDS[1:] if getattr(context, f) == "yes")
    if disruption:
        return PrioritySuggestion(state="suggested", band="High", reasons=disruption, unknowns=unknowns)
    if unknowns:
        return PrioritySuggestion(state="needs_review", reasons=("missing_disruption_context",), unknowns=unknowns)
    return PrioritySuggestion(state="suggested", band="Medium", reasons=("no_reported_danger_or_disruption",), unknowns=())
