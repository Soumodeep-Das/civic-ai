# Current State

## Foundation checkpoint

As of 19 September 2026, the repository contains planning documentation and reserved top-level directories only. Application implementation has not begun.

### Completed

- Created the repository structure and initialized Git.
- Established a concise root `AGENTS.md` that points to detailed documentation.
- Recorded the intended React, FastAPI, PostgreSQL, and Python ML direction.
- Defined the distinction between classification and prioritization.
- Drafted architecture, research, data, API, decision, and workflow documents.
- Preserved both the approved synopsis and the original blank template under `docs/reference/`.

### Not completed

- No frontend or backend project has been scaffolded.
- No dependencies have been installed.
- No database schema or migrations exist.
- No API endpoint or UI exists.
- No dataset has been acquired, licensed, curated, split, or labeled.
- No model has been trained or evaluated.
- No experiment result, metric, research finding, or novelty result is claimed.
- No deployment or GitHub remote has been configured.

## Synopsis reconciliation

The approved synopsis, `docs/reference/project-synopsis.docx`, has been reviewed against the foundation. It commits the proposed prototype to citizen and municipal roles, complaint submission with text/image/location, classification, a separate transparent priority mechanism, dashboard, department assignment, status tracking, map visualization, and comparative evaluation. These are staged targets rather than implemented features. Learned priority ranking, duplicate clustering, hotspot analysis, and richer spatial-temporal modeling remain future extensions.

## Assumptions used for this foundation

- The current project title and scope in the latest conversation supersede older distributed-team development plans.
- The student and Codex will own engineering and experiment execution; other team members may support literature and dataset review without owning core code.
- The eight-category taxonomy is provisional.
- The minor research centers on modality comparison and conditionally evaluates a transparent contextual priority mechanism; learned ranking and richer context modeling are future directions.
- A web application is the initial delivery vehicle; a mobile app is only a possible extension.

## Unresolved decisions before implementation

1. Fill or verify the group number, member enrolment numbers, and guide name placeholders in the approved synopsis outside this repository workflow.
2. Confirm the first complaint domain fields and whether location is required in the first vertical slice.
3. Decide the initial local PostgreSQL development method and migration tooling.
4. Define repository language/runtime versions and dependency-management conventions.
5. Confirm whether the first API is anonymous development-only input or includes a minimal identity concept.
6. Establish an initial test strategy and CI choice before merging substantial code.

## Exactly one recommended next issue

**Bootstrap the minimal FastAPI and PostgreSQL backend and implement a tested complaint domain model and persistence flow, without authentication, frontend, image upload, prioritization, or ML.**

Do not start this issue until the first complaint fields and local database approach have been reviewed.
