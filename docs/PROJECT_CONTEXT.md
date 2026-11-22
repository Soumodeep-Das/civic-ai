# Project Context

## Delivered scope and original intent

As of November 22, 2026, the application includes citizen identity/private tracking, municipal authentication, department ownership, status history, experimental text assessment and reported-context priority review. The minor presentation uses this integrated local workflow. The synopsis originally proposed text/image/multimodal comparison; only the bounded text experiment has been performed. Image classification, severity and paired comparison remain unfinished objectives carried into the [major-project roadmap](ROADMAP.md).

The sections below retain the original milestone and taxonomy context. The eight proposed categories are not the four families used by the current experimental classifier.

## Purpose

CivicAI addresses the delay and inconsistency that can occur when urban civic complaints are manually interpreted, categorized, and ordered for attention. Citizens need a simple way to report issues, while municipal or campus-style administrative users need structured records that support triage and follow-up.

The project has two connected outputs:

1. A functional complaint-management web application.
2. A reproducible ML study comparing complaint-classification approaches.

The software demonstrates and supports the research; it is not evidence by itself that a model is effective.

## Target users

- Citizens or community members submitting and tracking complaints.
- Administrative or municipal-style staff reviewing, filtering, and updating complaints.
- The student researcher, who curates data, runs experiments, and evaluates results.

No real municipal deployment, integration, service-level agreement, or production user base is currently claimed.

## Core scope

The first software milestone was the following narrow vertical slice:

`citizen complaint form -> FastAPI endpoint -> PostgreSQL persistence -> administrative complaint list`

The locally verified application now implements anonymous complaint persistence, bounded JPEG/PNG evidence, accurate searched/device location and map refinement. Authentication and status workflows are implemented; experimental text inference is integrated into the local municipal demonstration. Issue #5 begins the research track with taxonomy, annotation and dataset-manifest controls; it does not yet provide a dataset or model.

## Initial complaint categories

The current working taxonomy contains eight categories:

- pothole or road damage
- garbage or waste
- streetlight
- waterlogging
- broken footpath
- drainage or sewerage
- water leakage
- other

This taxonomy is provisional until dataset availability, class definitions, and annotation feasibility are reviewed. Category names and merge rules must be versioned before labeling begins.

## Classification and prioritization

**Classification** answers: “What type of civic problem is this?” Its expected output is a complaint category with confidence information where supported.

**Prioritization** answers: “How urgently should this complaint be addressed?” It may eventually consider severity, sensitive locations, repeat reports, public exposure, persistence, and available evidence. Category alone must not determine priority.

Severity describes the apparent magnitude or danger of an issue. Priority is an operational decision that may include severity plus context. These terms must not be used interchangeably.

## Minor and major directions

The original minor-project research objective was a controlled comparison of text-only, image-only, and text-image multimodal classification. That comparison remains unperformed; the delivered exploratory study is text-only. The minor software deliverable should remain a demonstrable, student-scale web system.

The approved prototype includes a transparent priority engine that combines documented factors such as reported severity, location significance, and repeated reports to assign Low, Medium, High, or Critical priority, with human verification. The likely major-project research direction is learned priority ranking and richer spatial-temporal context. Possible later extensions such as duplicate clustering, hotspot analysis, and explainable AI are not current commitments.

## Contribution boundaries

The project does not claim that civic complaint systems, automated classification, multimodal analysis, or context-aware prioritization are wholly novel. Any defensible contribution must be grounded in work actually completed, such as a documented dataset, controlled modality comparison, reproducible evaluation, error analysis, and a usable integrated prototype.

## Approved source

The approved synopsis is stored at `docs/reference/project-synopsis.docx`. It defines the intended prototype, research comparison, technology direction, roles, high-level functionality, and 8-10 week academic timeline. The blank university template is retained only as a historical source attachment.
