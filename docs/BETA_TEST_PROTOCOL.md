# CivicAI closed-beta test protocol

Use invented civic reports and non-sensitive photos. Never upload faces, identity documents, phone numbers, home interiors, or private correspondence.

Each tester should record browser/device, time, role, steps, expected result, actual result, screenshot if safe, complaint reference (never the private token), and severity.

Test these journeys:

1. Anonymous citizen submits a complaint with a valid photo and selected location, saves the private link, and tracks status.
2. Citizen registers, verifies email, signs in, submits, and sees My Complaints.
3. Password reset email arrives and the one-use flow works.
4. Google sign-in works for an allowed beta account and returns to CivicAI.
5. Municipal admin signs in, invites staff, assigns departments, and reviews evidence.
6. Operator sees only permitted complaints, claims/updates work, and cannot access another department's evidence.
7. Citizen sees a status change after refresh.
8. Invalid/expired/reused verification, reset, invitation, tracking, and CSRF inputs fail safely.
9. Mobile navigation, location search/map, form validation, slow-network retry, and accessibility keyboard flow remain usable.

Stop testing and report immediately if another user's evidence is visible, authorization can be bypassed, secrets appear in the browser/logs, or data is lost unexpectedly.

