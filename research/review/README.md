# Issue #7 offline human-review format

Status: Stage A infrastructure. No committed file in this directory contains a human decision or citizen complaint text.

`review_schema_v1.json` defines the allowed decisions and outcome fields for taxonomy, mapping, privacy, record, duplicate, license and final dataset-approval reviews. Generated forms live under ignored `data/interim`, not Git.

Each reviewer uses a pseudonymous code and a timezone-aware ISO-8601 timestamp. Reviewers copy a generated form, work independently, and may submit a partial form. Immutable provenance/context columns must not be changed. Validation rejects altered context, invalid decisions, duplicate item IDs, malformed reviewer metadata and incomplete decision-specific fields.

Multiple validated submissions are merged by item. Identical semantic decisions are recorded as single-review or consensus; differing decisions remain explicit conflicts and generate an adjudication CSV. Notes do not silently resolve disagreements. An adjudicator must preserve the conflict payload, choose an allowed final decision and record a rationale.

Generated CSVs quote every cell and prefix potentially formula-leading values. This reduces spreadsheet formula-injection risk described by [OWASP](https://community.owasp.org/attacks/CSV_Injection), but no CSV mitigation is universal. Open review files in Protected View and never enable macros or external content.

The curation module currently supplies deterministic redaction primitives and a fail-closed readiness report. It does not build the real derivative during Stage A. Stage B must consume actual validated decisions, implement any approved taxonomy/mapping revision as a new version, and only then create a curated manifest.
