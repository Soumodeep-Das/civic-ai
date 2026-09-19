# CivicAI repository guidance

- Read `docs/CURRENT_STATE.md` first, then consult the relevant files under `docs/`; they are the detailed source of truth.
- Preserve the distinction between complaint classification (what the issue is) and prioritization (how urgently it should be handled).
- Do not fabricate citations, datasets, licenses, labels, metrics, experimental results, statistical claims, or novelty claims.
- Keep changes small and milestone-driven. Inspect existing work, implement only the requested scope, test it, and update affected documentation.
- Show visible progress. Update documentation, commit and push each coherent task incrementally; explicitly report verification or publishing blockers (see docs/DEVELOPMENT_WORKFLOW.md).
- Do not change the agreed React, FastAPI, PostgreSQL, and Python ML direction without recording the proposal and trade-offs in `docs/DECISIONS.md` before implementation.
- Treat dataset provenance, licensing, leakage prevention, reproducibility, and human review as first-class requirements.
- Keep the application explainable enough for the student developer to understand, demonstrate, and defend in an MCA viva.
- Never commit secrets, personal data, large datasets, trained model binaries, uploads, or generated experiment artifacts unless a documented decision explicitly permits it.
