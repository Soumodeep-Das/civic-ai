# Issue #3 edge-case research

Reviewed 2026-09-20. Sources inform engineering decisions, not research novelty or results.

- [FixMyStreet citizen training](https://fixmystreet.org/training/citizens/): location identifies the problem and a photo is optional. Adopt optional evidence and explicit guidance to capture location only near the problem. Map pin correction is deferred by Issue #3 scope.
- [FixMyStreet Pro citizen experience](https://fixmystreet.org/pro-manual/citizens-experience/): supports offline draft continuation. Preserve in-memory inputs on submission failure here; durable offline drafts are deferred pending a privacy/retention decision.
- [W3C Geolocation](https://www.w3.org/TR/geolocation/) and [MDN getCurrentPosition](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation/getCurrentPosition): permission, secure context, permissions policy, provider availability, timeout and cached locations affect capture. The acquisition timeout does not include time spent obtaining permission, and a device fix can take substantially longer than ten seconds. Use explicit action, a one-shot request that accepts a fix no older than five minutes, a 30-second acquisition timeout, denial/unavailable/timeout messages, optional submission and late-callback invalidation.
- [Microsoft Windows location service and privacy](https://support.microsoft.com/en-us/windows/privacy-windows-location-service-and-privacy): browser permission alone cannot provide a position when the operating-system location service/provider is unavailable. Timeout guidance should tell users to check device Location Services and Wi-Fi without changing system settings on their behalf.
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html): do not trust MIME or filenames; bound size, validate content, rewrite images and isolate storage. Decode JPEG/PNG, enforce matching MIME, re-encode without metadata, cap bytes/pixels, generate names and serve with explicit media type/nosniff.

## Checks and remaining tradeoffs

- Empty/corrupt/spoofed/unsupported/oversized images: reject clearly without inserting a complaint.
- User filenames/path traversal: filename is ignored; retrieval accepts generated names only.
- Existing records: nullable migration; old records have no image.
- Image selected/removed/replaced: explicit controls and feedback; optional photo.
- Location refused/unavailable/timed out: continue without coordinates; no manual coordinate knowledge needed. A recent device fix is accepted for up to five minutes to reduce avoidable desktop timeouts while the instruction still says to capture only when near the issue.
- Late location callback after removal/submission: invalidate request token.
- Database failure after saving file: roll back and remove file. A process crash can still leave an orphan; no background reconciliation in this local prototype.
- Filesystem failure: must produce a clear availability error and no successful complaint response.
- Retried submissions after an ambiguous connection loss can duplicate a record; no automatic POST retry. Idempotency is a future issue.
- Anonymous image retrieval is local-demo only. No malware-scanner or production access-control claim.
