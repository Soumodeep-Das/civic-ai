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
