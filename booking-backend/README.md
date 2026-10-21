# Booking backend — locked standby release

The locked standby release installs replacement APIs without opening dates or payments. This isolated replacement provides availability, authoritative server quotes, SQLite reservations, hosted Stripe Checkout and signed/idempotent payment webhooks. Existing success.php/webhook.php are not overwritten; this package uses dedicated completion routes.

The shipped `public/api/booking-disabled.php` release lock overrides all private enable flags. It must remain installed until the activation checks below are complete. Only test fixtures remove their own copied lock; tests never remove the source lock. The standby deployment preserves the existing booking page and JavaScript contact fallback.

## Activation dependencies

1. Confirm operator-approved prices and exact calendar periods, including school/bank holidays. The old designs show £595/£650/£795 weekly, £395/£475/£545 short breaks, £250 deposit and balance at 12 weeks. Generated designs are not final approval or physical caravan evidence. Unsupported durations, mixed bands and uncovered dates return a manual-quote response.
2. Confirm hire/insurance terms, security deposit (currently provisional on the live site), refund rules, towing approval process, and publish a linked hire-terms/privacy notice before checkout is enabled.
3. Reconcile/import existing bookings, personal-use blocks and maintenance. Mark the verified booking horizon. An empty new database is not evidence of availability.
4. Confirm the correct Stripe account, mode, enabled charges and signing secret through the existing private hosting setup. Never put keys/customer data in this repository. No live payment or email has been attempted.
5. Install PHP 8.2+ with PDO SQLite and cURL; create a private writable directory outside the document root. Copy config.example.php to a private file, populate it there, and set TOURING_BOOKING_CONFIG to that absolute path. Keep all verification flags false until these checks pass.
6. Review the dedicated booking-webhook.php endpoint in the merchant's Stripe setup for checkout.session.completed and checkout.session.expired. This creates a new integration endpoint and must be reviewed before merchant activation.
7. Deploy public/ files under the current document root and integrate the frontend candidate below. Existing production files must be backed up and hash-checked first. The standby workflow deploys only locked public backend files. Frontend integration and removal of the release lock require a separate activation release.

## Behaviour and operational limits

Collection and return intervals are end-exclusive. Turnaround buffers must be entered as explicit blocks if required. A database write transaction prevents overlapping holds. Selecting a complete date range now creates a fixed 15-minute exclusive hold. It expires locally only before checkout creation. Cancellation of an active checkout first expires it through Stripe and confirms it cannot be paid; a browser redirect is never sufficient payment evidence. A timeout keeps the hold for reconciliation because a payment session may already exist. For an unresolved `creating` row, retry using the original idempotency key/parameters or reconcile against Stripe before manually releasing it. Never free a hold just because it is old.

For payments made more than 12 weeks before collection, only the booking deposit is collected. This package records the balance and due date; it does not automatically charge balances or security deposits, send reminders, grant towing approval, issue refunds or deliver confirmation emails. These operational flows must be arranged before activation. No purchase analytics event is emitted: verified payment reporting and consent/deduplication require a separate implementation.

The completion page reads this browser's private booking session and the webhook-confirmed database state. It never trusts a success URL as payment evidence. Private booking/customer data stays outside the document root; application logs never print it. Hosts must configure rate limiting, retention, private backups, access controls, reconciliation and monitoring before public launch. Payment/customer support and a secure administration workflow are still required.

## Frontend candidate

`frontend/booking.js` is based on the latest tracking release, not the stale original site/ copy. It adds CSRF tokens, quote response validation and stale-response protection, server date coverage, and Stripe-only redirects. Production continues to show the contact fallback until the complete backend is configured.

## Validation

Run `php booking-backend/tests/booking.php` and `node booking-backend/tests/frontend.cjs`. The GitHub workflow uses no production secrets and no external payment/email requests. Tests cover calendar/date boundaries, payment timing, overlap rejection, idempotent reservation, webhook signature rejection/replay, wrong amount/mode, and late expiration after payment. A live Stripe test-mode roundtrip, concurrent HTTP test, hosting compatibility and actual merchant activation are separate release checks.

Primary references checked 20 October 2026:
- https://docs.stripe.com/api/checkout/sessions/create
- https://docs.stripe.com/webhooks/signature
- https://docs.stripe.com/payments/checkout/fulfill-orders


## 21 October review branch — approved hold and operational rules

This candidate is not deployed. Keep the existing production release lock in place.

- `quote.php` creates an exclusive 900-second selection hold inside a SQLite write transaction. Repeating the quote does not renew it. Changing or releasing selected dates must finish safe cancellation first.
- Availability distinguishes paid/blocked dates from other customers' temporary holds, omits customer details and IDs, and exposes only this browser's own selection. The candidate calendar polls every ten seconds and uses green/amber/red, text labels, a legend, peak markers from explicit configuration, and a server-clock countdown. No seasonal dates are invented.
- Stripe Checkout's native session expiry has a 30-minute minimum. The private CLI reconciler must run at least every minute and also runs during availability/quote reads. On deadline it expires an open Stripe session and verifies expiration before reopening dates. Failures and uncertain session creation keep dates blocked. Exact-to-the-second cancellation at minute 15 is not guaranteed by a minute scheduler or a remote payment service; do not advertise automatic release until scheduler and real Stripe tests are verified.
- Schedule the private `reconcile.php` with `TOURING_BOOKING_CONFIG` and `TOURING_BOOKING_DOCUMENT_ROOT` set to the real private config and document root. This entry point must stay outside the public document root. A scheduler-health monitor and real test-mode end-to-end check remain launch prerequisites.
- `operations.php` contains tested policy functions for commission due at the earlier of confirmed full balance or 12 weeks before arrival, funded from the owner's confirmed booking deposit. A missing agreed commission amount cannot become payable. Customer details become releasable only after balance confirmation. Identity, licence and insurance evidence and an office-hours appointment at least two working days after verification are required by the handover predicate; supply insurer/public holiday closures explicitly.
- The review candidate now connects those rules to a private owner-booking ledger: per-vehicle plan acceptance, owner-only receipt confirmations, Touring-only booking confirmation, append-only audit records, server-enforced owner isolation/contact withholding, appointments/evidence checks and reviewed diversion termination. See `owner-garage/README.md`. The new service remains disabled unless explicitly enabled in private configuration; it is separate from the own-Elddis Stripe calendar and does not move money. Existing public £49/no-commission advertising terms cannot silently become a commission contract. The owner has now selected £49 per vehicle per year plus a flat £25 admin fee per confirmed booking. `ownerPricingPlan()` records those amounts for a newly accepted agreement; the commission predicate still requires an explicitly agreed amount and does not reprice existing contracts. See `owner-garage/pricing-review.md` for candidate wording and transition requirements.
- The £250 booking deposit is separate from the still-unconfirmed refundable damage/security deposit. The 12-week forfeiture instruction is recorded for contract review; it has not been automatically applied to refunds or represented as approved legal wording. No automated balance collection, refunds or live notifications added.

Validation: existing payment integrity and frontend suites plus fixed-hold, cancellation, two-session privacy/exclusivity and independent-process concurrency checks. Tests use private fixtures and make no external Stripe requests or send emails. Actual merchant and scheduler validation remain outstanding.
