# Local experimental Docker demonstration

Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-ml-demo.ps1` from the repository root. Requires existing Docker Desktop, `.env.production` with `CIVICAI_SITE_ADDRESS=localhost`, the trusted private experiment artifact and its hash index. No new credentials are required. Do not use an uploaded/untrusted joblib file: pickle deserialization executes code; a hash comparison is integrity checking, not proof of trust.

The script checks Docker, backs up existing database/evidence using the existing backup script, builds the optional research dependency layer, mounts only the model read-only, applies migrations through the existing Compose dependency chain, and waits for health. Model and dataset remain outside image layers and Git. Base Docker builds retain default dependencies; only explicit `compose.demo.yml` enables research packages. No dataset directory is mounted. Backup creation is not restore verification.

Open https://localhost/municipal, sign in, open a complaint and generate an assessment. Check accept/correct/defer, reload review history, and confirm original prediction and complaint status remain unchanged. Unsupported complaints should request review, but heuristic guards are not comprehensive. Photos/severity/priority are not assessed. This is a local exploratory demo with AI-proposed training labels, not a validated municipal model.

Verification 2026-11-20: PowerShell syntax and diff checks passed. Agent access to Docker Desktop named pipe was denied; no Docker backup/build/migration/startup executed in this checkpoint. Owner must run the script; Linux model compatibility, actual readiness and browser workflow are not yet verified. No production certification or deployment completion claimed.

Keep the overlay for demo recreation: the model hash is set only in the script process and restored on exit. Running the base stack alone disables this overlay configuration. Existing data volumes are retained; never run down -v as part of this workflow.

## Local email configuration fix (2026-11-20)

The first owner-run stack failed at startup because `.env.production` omitted EMAIL_TRANSPORT, defaulting to capture, which production correctly rejects. The ML demo launcher now includes the existing `compose.production.mailpit.yml` after the model overlay. It selects SMTP to Mailpit inside the Compose network and binds the inbox only to `127.0.0.1:8025`. No external emails are delivered. Verification, reset and invitation links can be retrieved from that local inbox; do not copy them into logs or public reports. Normal `compose.production.yml` and the production capture prohibition are unchanged.

Rerun the same `scripts/start-ml-demo.ps1` command; it retains existing database/evidence volumes and backs them up again. This override is only for the localhost demonstration, not the public beta or a real municipal deployment. The startup root cause is confirmed by the supplied RuntimeError; successful recovery still needs a fresh owner-run Docker health result.

## Recovery result

Owner-run output on 2026-11-20 confirms all long-running services healthy and readiness 200 after adding the Mailpit overlay. Backup: `backups/20261120-093046`. Model generation and authenticated browser review/persistence remain the next verification; startup health alone does not load or evaluate the model.

## Owner workflow confirmation

2026-11-20: owner generated a solid_waste suggestion in Docker, accepted it with an explanation and confirmed review history survives refresh. This verifies the reported generation/acceptance/persistence path. The photo was not used by this text classifier; no independent image or category-accuracy result follows from this check.

## Priority workflow verification (migration 0010)

The municipal detail page now includes Experimental contextual priority in source. It is a separate reported-fact rules policy, not photo analysis. Rebuild with the same backup-first launcher above; do not use the base Compose stack alone.

After successful startup, use https://localhost/municipal (not the Vite development URL). Open a demo complaint and record its current status.

1. In Experimental contextual priority, leave all facts unknown, enter an explanation and save context. Expect Needs municipal review and disabled Accept priority.
2. Record a new context: immediate danger no, public access blocked yes, essential service unknown. Expect High, with the unknown service fact still displayed.
3. Enter a priority review explanation and accept. Refresh; confirm context and review history remain and complaint status is unchanged.
4. Record immediate danger yes. Expect an escalation warning and no automatically assigned priority. Defer with an explanation; confirm persisted history.
5. For a demo-only correction, select a corrected priority and save an explanation. Confirm history preserves both the original suggestion and correction.

Use honestly labelled demonstration facts; do not change a real report merely to exercise these scenarios. No emergency dispatch occurs. Direct citizen context fields are not implemented yet.

Agent execution attempt 2026-11-20: Docker Desktop named-pipe access denied before backup/build/migration, both before and after network permission. No new local-stack verification performed. Previous automated checks remain valid as recorded in CURRENT_STATE.md; owner-run rebuild and browser confirmation are pending.


## 2026-11-20 — Owner priority demo rebuild succeeded

Owner-provided launcher output confirms backup backups/20261120-210821, rebuilt backend/migrate/proxy images, healthy database/Mailpit/backend/proxy, completed migration/evidence-init containers and readiness HTTP 200. Current backend readiness requires schema 0010, so successful readiness supports the migration being applied. This is owner-run output, not direct agent Docker inspection. Authenticated priority generation/review/history browser verification remains pending. No further rebuild is needed before that check.
