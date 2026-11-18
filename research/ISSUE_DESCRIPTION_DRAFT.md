# Rich issue-description draft: first transfer

2026-11-18. Implemented `issue_draft` as a conservative, versioned transfer of existing AI proposals. Active taxonomy v1 and application behavior are unchanged.

The draft represents service family, asset, issue kind, setting, time state and provenance separately, with explicit unknown values and multiple issues. It includes all 12 proposed service families plus unknown. The generated contract is an initial vocabulary/field specification, not a complete validation schema for future manual annotations. No severity, priority, legal jurisdiction or public ownership is inferred.

Applied to all 271 pilot records: 139 carry 153 provisional issue descriptions transferred from existing AI categories; 132 gap/unclear records remain without forced issues. Every record still requires text review. This is zero fresh text annotations, zero independent reference labels and zero training approvals. Existing waterlogging proposals retain unknown family/cause. Drainage and lighting labels do not invent a specific failure mechanism. Privacy concerns and previous rationales are retained; the contextual privacy artifact remains separate and authoritative for its own proposals.

Local output: ignored `data/review/issue-description-draft-v1` contains contract, annotations, summary, hashes and COMPLETE. Input SHA-256: `480611baaa909cce2c7dfaba2f5b3be7c7b5df82744027f53cf9218b2ad4ff3c`. No private annotations enter Git.

Run from the repository root with a fresh output directory:

```powershell
.\.venv\Scripts\python.exe -m research.civicai_research.issue_draft --pilot data/interim/label-pilot-v1 --responses data/review/ai-pilot-complete-v1/responses.json --output data/review/issue-description-draft-v2
```

The actual run used output v1 and completed successfully. The tool validates complete upstream pilot coverage and provenance, refuses existing output/input nesting, and preserves the original proposals. Interrupted output retains INCOMPLETE. It is a deterministic transfer, not a semantic classifier or a training release.

[Label Studio documentation](https://labelstud.io/guide/predictions.html) treats pre-annotations as predictions for review/correction. This implementation follows that separation without installing Label Studio or sending data to an external service.

Next: read and annotate the 132 unresolved texts under the richer vocabulary, then check transferred proposals against their actual text. Add a strict evidence-based annotation validator before accepting edited annotations. Do not count transferred fields as fresh judgments or independent evaluation truth.

Verification: 173 research tests passed in 20.07s (`--basetemp tmp/pytest-issue-draft-final2`); 11 new transfer tests. An initial test fixture placed output inside its source directory and correctly triggered the guard; the fixture was corrected and the complete suite rerun. Actual transfer exited 0. Application tests/builds were not rerun because runtime code/dependencies are unchanged. `git diff --check` passed.
