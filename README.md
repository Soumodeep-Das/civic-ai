# CivicAI

CivicAI is an MCA final-year project currently titled **AI-Based Urban Civic Complaint Classification and Prioritization System**. It combines a civic complaint management application with reproducible machine-learning research.

The planned system will let citizens submit complaint text, an optional image, and a location; store and track complaints; and support a municipal-style administrative view. The research track will compare text-only, image-only, and text-image multimodal methods for complaint-category classification. A transparent contextual priority engine is part of the approved prototype, while learned priority ranking and richer spatial-temporal prioritization remain future major-project research.

## Current status

The repository is in the **foundation stage**. No frontend, backend, database schema, API, dataset, or ML model has been implemented. The files under `docs/` define the current project boundaries and working agreements.

The approved synopsis is preserved as `docs/reference/project-synopsis.docx`. The original blank university template is retained beside it for traceability.

## Intended technology direction

- Frontend: React
- Backend: Python and FastAPI
- Database: PostgreSQL
- ML and research: Python, scikit-learn, and, when justified, PyTorch and Hugging Face Transformers
- Collaboration: Git and GitHub

These are intended directions, not installed dependencies or completed components.

## Repository map

- `docs/`: project context, architecture, research and engineering plans
- `docs/reference/`: supplied source documents
- `frontend/`: reserved for the citizen and administrative web interface
- `backend/`: reserved for the API and application services
- `ml/`: reserved for training and inference code
- `research/`: reserved for experiment definitions, reports, and paper support material
- `data/`: reserved for documented local data workflows; datasets are not committed by default
- `tests/`: reserved for cross-component and acceptance tests

Start with `docs/CURRENT_STATE.md` and `docs/PROJECT_CONTEXT.md`.
