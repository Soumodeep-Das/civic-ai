# Development Workflow

## Work units

Use one narrowly scoped issue at a time. Before implementation, read `CURRENT_STATE.md`, the relevant design documents, and existing code. State acceptance criteria and explicit exclusions. Finish with tests, documentation updates, and a short record of unresolved risks.

## Git workflow

- Keep the default branch releasable and avoid direct experimental work on it once collaboration begins.
- Use short-lived branches named by purpose, such as `feat/complaint-create` or `docs/data-guideline`.
- Rebase or merge according to the repository's eventual hosting policy; no policy is selected yet.
- Never rewrite shared history without explicit agreement.
- Do not commit secrets, real personal data, unrestricted datasets, uploads, large model artifacts, or generated experiment runs.

## Commits

Each commit should represent one coherent change, use an imperative subject, and include tests or documentation needed to understand it. Avoid combining unrelated formatting, dependency, feature, and research changes. Generated lockfiles belong with the dependency change that produced them.

## Review of AI-generated work

The human developer remains accountable for all generated code and prose. Review diffs, understand control flow and data handling, verify dependency and license choices, run tests, and check that the implementation matches documented acceptance criteria. Code that cannot be explained in a viva is not ready to merge.

AI output must not be treated as evidence for citations, security, correctness, dataset licensing, or research results. Verify those independently.

## Testing expectations

- Add unit tests for domain rules and validation.
- Add integration tests for persistence and API behavior at component boundaries.
- Add contract or end-to-end tests only where they protect an important user flow.
- Reproduce reported defects with a test when practical.
- Run the smallest relevant suite during development and the full required suite before merge.

Exact commands will be documented after scaffolding selects the tools. A change is not considered verified if tests were skipped silently.

## Documentation expectations

Update documentation in the same change when behavior, architecture, data fields, API contracts, research methods, or decisions change. Add accepted architecture or research decisions to `DECISIONS.md`. Keep `CURRENT_STATE.md` factual and remove stale next steps.

## Dependencies and configuration

Add the smallest justified dependency, pin or lock it through the chosen package manager, and record any operational or licensing consequence. Configuration comes from environment variables with a committed example file containing no secrets. Database changes use migrations once tooling is chosen.

## Research experiment workflow

1. Write the question, dataset version, split, metrics, baseline, and acceptance criteria before the final run.
2. Run experiments from version-controlled code and saved configuration.
3. Record the Git revision, environment, seed, hardware, data manifest/checksums, parameters, start/end time, and failures.
4. Save raw predictions and machine-readable metrics before creating tables or plots.
5. Keep the untouched test set unavailable to iterative model selection.
6. Review anomalous results and leakage risks before interpreting performance.
7. Link paper claims to a specific accepted run; never transcribe unverified console output as a final result.

## Definition of done

A work item is done when its acceptance criteria are met, relevant tests pass, docs and decisions are current, no secret or prohibited artifact is staged, and remaining limitations are stated. Deployment, performance, accessibility, privacy, and security checks should be proportional to the scope of the item rather than assumed complete.

