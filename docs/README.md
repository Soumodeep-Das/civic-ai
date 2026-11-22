# Documentation guide
Updated November 22, 2026.

## Choose a reading path

| Reader | Start here | Then explore |
|---|---|---|
| Teacher / examiner | [Root overview](../README.md), [demo runbook](MINOR_DEMO_RUNBOOK.md) | [Actual experiment](../research/EXPLORATORY_BASELINE_RESULTS.md), [limitations and major scope](ROADMAP.md) |
| Developer | [Root setup](../README.md#run-locally-on-windows), [architecture](ARCHITECTURE.md) | [API contract](API_CONTRACT.md), [data specification](DATA_SPECIFICATION.md), [workflow](DEVELOPMENT_WORKFLOW.md) |
| Research contributor | [Research overview](../research/README.md), [research plan](RESEARCH_PLAN.md) | [Source register](../research/SOURCE_REGISTER.md), [protocol](../research/protocols/exploratory_ai_labels_v1.json) |
| Deployment operator | [Deployment](DEPLOYMENT.md), [operations](OPERATIONS_RUNBOOK.md) | [Recovery](BACKUP_RESTORE.md), [closed beta](ISSUE_014_CLOSED_BETA.md) |
| Continuing engineering agent | [Handoff](AGENT_HANDOFF.md), [current state](CURRENT_STATE.md) | [Decisions](DECISIONS.md), [development log](DEVELOPMENT_LOG.md) |

## How to interpret these documents

The root README and architecture describe current implemented behavior. The current-state page records dated verification with environment and limitations. Research result reports describe only the named experiment. The roadmap describes proposed future work.

The [approved synopsis](reference/project-synopsis.docx) records original academic intent; it does not prove implementation or experimental completion. Numbered issue documents, the development log and older dated handoff entries preserve engineering history. Their “next” and “not yet implemented” statements apply to their checkpoint dates, not automatically to today's product.

Current code is authoritative for API behavior. When code and prose disagree, record the mismatch and correct documentation; do not silently change code merely to fit a document.

## Core reference set

- [Project context](PROJECT_CONTEXT.md): intended academic contribution and delivered scope.
- [System architecture](ARCHITECTURE.md): components, submission sequence, data relationships and deployment.
- [API contract](API_CONTRACT.md): request/response and authorization semantics.
- [Contextual priority](CONTEXTUAL_PRIORITY.md): explicit rules, unknowns and human review.
- [ML design specification](ML_DECISION_SPEC.md): original assessment design and unfinished requirements.
- [Photo-assistance assessment](PHOTO_ASSISTANCE_DECISION.md): reasons for deferral and re-entry conditions.
- [Roadmap](ROADMAP.md): limitations, minor/major scope and completion criteria.
- [Documentation review](DOCUMENTATION_REVIEW_2026_11_22.md): inconsistencies corrected and residual uncertainty.

The repository retains all historical issue files, reference attachments and research artifacts already under version control. Private datasets, credentials and model binaries are intentionally absent.
