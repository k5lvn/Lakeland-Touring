# Owner booking review

The new owner booking service is a review candidate. It is separate from the own-Elddis Stripe checkout. No source change enables it automatically.

`build.py` publishes the garage entry point, `garage-bookings.php`, `garage-bookings-ui.php`, and a generated `booking-policy.php` from the canonical `booking-backend/operations.php`. Existing public robots rules and sitemap URLs are preserved by deployment; new public information pages are added to the existing sitemap.

## Completed workflow

- Each owner explicitly accepts the versioned £49 annual advertising / £25 confirmed-booking admin plan per vehicle. Acceptance and fee snapshots are immutable; it neither bills nor extends the existing annual term.
- Touring administrators record bookings only against active paid vehicles with the accepted plan. Overlapping booking records are rejected inside a SQLite write transaction. Owner bookings use this private ledger; they are not automatically joined to the own-Elddis availability calendar.
- Only the vehicle owner can confirm actual deposit and full-balance receipt, with a reference and server timestamp. Only Touring can confirm the booking and record receipt of its admin fee. Repeated confirmations do not duplicate events.
- The owner sees customer names/email/phone only after balance confirmation. Other owners and anonymous visitors cannot access that booking. Administrators can see customer details to administer bookings.
- The admin fee becomes due from the owner's deposit at the earlier of full-balance confirmation or 12 weeks before arrival, only for a confirmed booking. Cancellation cannot earn a fee later; an already-earned fee survives cancellation. Refunds and bank transfers are manual, never simulated by a checkbox.
- Appointment and identity/licence/insurance references use server-recorded actors and times. Handover requires full balance, a confirmed booking, office hours and evidence at least two working days before collection. Explicit private closure dates apply. The screen stores references, not identity documents.
- SQLite triggers prevent application updates/deletes to audit and acceptance rows. This is an application audit trail, not tamper-proof against a server/database administrator. A reviewed diversion termination unpublishes the owner's adverts and blocks new bookings while retaining existing records.

## Activation gate

Existing garage service remains the legacy £49/no-commission advert service while the feature flag is off. Do not overwrite existing owner terms with a new contract silently.

The private sibling directory `.touring-garage` holds the existing database and photos. A private `booking-config.php` can return `['enabled'=>true,'non_working_dates'=>[/* actual closed YYYY-MM-DD dates */]]`. Missing config, missing closure configuration or `enabled=false` keeps the feature off. Never place this file in the public document root or commit production settings. Empty closure dates are valid only after the operator explicitly confirms no additional closures for the relevant period.

Before activation: review the new booking terms/privacy pages together with final hire/cancellation/refund/insurance/security-deposit documents; establish secure evidence storage, retention, backups and correction/dispute handling; confirm the live admin account and secure login/HTTPS; verify the deployment bundle, existing listings and owner acceptance on staging. Passkey/admin MFA rollout remains a separate cross-site security requirement. The current garage retains its existing password/email recovery flow; this change does not claim biometric authentication.

The own-Elddis Stripe flow still requires its separate merchant/calendar/pricing, webhook, scheduler and end-to-end checks. This ledger does not collect payments, send customer confirmations, synchronise calendars or make external bank checks.

## Validation

`python3 owner-garage/test_bookings.py` runs a disposable PHP server, private SQLite fixture and policy checks. Add `--browser` for Playwright phone/desktop screenshots. Tests create only local fixture accounts and disable email delivery. CI runs these together with the existing booking integrity, hold, concurrency, HTTP and calendar browser suites.
