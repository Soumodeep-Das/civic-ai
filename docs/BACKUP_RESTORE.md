# Database and evidence backup/restore

PostgreSQL rows and evidence files are one logical dataset but live in separate volumes. Back up both in one maintenance window. The scripts never include `research/`, raw OpenCity data, source code, or `.env.production`.

## Create a backup

With the production stack healthy:

```powershell
.\scripts\backup-production.ps1
```

This creates `backups/<yyyyMMdd-HHmmss>/database.dump`, `evidence.tar.gz` and `SHA256SUMS.txt`. `pg_dump --format=custom` makes a logical archive and a read-only evidence-volume container creates the media archive. Any non-zero tool result fails the script. `backups/` is ignored by Git.

For stronger database/media consistency, briefly pause citizen writes at the proxy or run this during a declared maintenance window. The current small deployment does not provide a cross-volume atomic snapshot. Never copy PostgreSQL data files while PostgreSQL is running as a substitute for `pg_dump`.

Copy completed backups to encrypted, access-controlled storage outside the application host and test that the checksums still match. Do not put backups in Git or ordinary public cloud folders.

## Verify by restoring

Start the base stack, then restore only into a new disposable name:

```powershell
.\scripts\verify-backup-restore.ps1 -BackupDirectory '.\backups\20261002-120000'
```

The script enforces a `civicai_restore_*` target, creates a fresh PostgreSQL database, restores with `pg_restore --exit-on-error`, restores media into a fresh named volume and runs the read-only database-to-media consistency audit. It never targets the `civicai` database.

The successful output names the disposable database and volume. Inspect row counts or run an application smoke test against them if required. When finished, remove only the exact printed disposable targets:

```powershell
docker compose --env-file .env.production -f compose.production.yml exec -T db dropdb --username civicai civicai_restore_EXACT_NAME
docker volume rm civicai_civicai_restore_EXACT_NAME_evidence
```

Never substitute a production database or volume name into those cleanup commands.

## Media consistency and orphan handling

Run the dry-run audit at any time:

```powershell
docker compose --env-file .env.production -f compose.production.yml exec -T backend python -m civicai.media_audit
```

It reports only counts and filenames: referenced-but-missing evidence, stored-but-unreferenced files and invalid references. It never deletes. Treat a database outage as audit failure, not proof that every file is orphaned. Investigate transaction logs/backups and repeat the audit before quarantine. Move a confirmed orphan to restricted quarantine first; delete only after a documented retention decision. Restore missing referenced evidence from a matching backup.

## Retention

**Project operational default (example):** keep seven daily, four weekly and three monthly verified backup sets, subject to disk capacity; keep at least one encrypted copy off-host. Rotate only after a newer set has passed checksum and restore testing.

**Legal municipal retention policy: unresolved.** CivicAI does not claim an Indian government retention period and does not automatically delete complaints, evidence, audit history or backups. A competent authority must define that policy before real civic deployment.

## Recovery boundary

A full recovery requires the matching database dump, evidence archive, production configuration/secrets and a compatible application release. Losing `PUBLIC_TRACKING_SECRET` invalidates existing citizen tracking capabilities. Losing the database password/config prevents startup. Certificate state can be recreated for a valid public domain but should remain persistent during ordinary restarts.
