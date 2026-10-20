# Booking backend review — not deployed or enabled

The live APIs are missing. This isolated replacement provides availability, authoritative server quotes, SQLite reservations, hosted Stripe Checkout and signed/idempotent payment webhooks. Existing success.php/webhook.php are not overwritten; this package uses dedicated completion routes.

## Activation dependencies

1. Confirm operator-approved prices and exact calendar periods, including school/bank holidays. The old designs show £595/£650/£795 weekly, £395/£475/£545 short breaks, £250 deposit and balance at 12 weeks. Generated designs are not final approval or physical caravan evidence. Unsupported durations, mixed bands and uncovered dates return a manual-quote response.
2. Confirm hire/insurance terms, security deposit (currently provisional on the live site), refund rules, towing approval process, and publish a linked hire-terms/privacy notice before checkout is enabled.
3. Reconcile/import existing bookings, personal-use blocks and maintenance. Mark the verified booking horizon. An empty new database is not evidence of availability.
4. Confirm the correct Stripe account, mode, enabled charges and signing secret through the existing private hosting setup. Never put keys/customer data in this repository. No live payment or email has been attempted.
5. Install PHP 8.2+ with PDO SQLite and cURL; create a private writable directory outside the document root. Copy config.example.php to a private file, populate it there, and set TOURING_BOOKING_CONFIG to that absolute path. Keep all verification flags false until these checks pass.
6. Review the dedicated booking-webhook.php endpoint in the merchant's Stripe setup for checkout.session.completed and checkout.session.expired. This creates a new integration endpoint and must be reviewed before merchant activation.
7. Deploy public/ files under the current document root and integrate the frontend candidate below. Existing production files must be backed up and hash-checked first. No automatic deployment is included in this PR.

## Behaviour and operational limits

Collection and return intervals are end-exclusive. Turnaround buffers must be entered as explicit blocks if required. A database write transaction prevents overlapping holds. Only a verified Stripe expiration releases an unpaid hold; browser cancellation and clock expiry do not. A timeout keeps the hold for reconciliation because a payment session may already exist. For an unresolved `creating` row, retry using the original idempotency key/parameters or reconcile against Stripe before manually releasing it. Never free a hold just because it is old.

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
