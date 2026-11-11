# Touring booking launch review — 22 October 2026

The candidate remains on draft PR #7. No production activation, payment, refund or customer email is authorised by this review pack. Current booking APIs keep their release lock. The owner ledger and own-Elddis checkout are separate flows.

## Decisions already settled

| Item | Position |
| --- | --- |
| Seven-night hire | Kelvin confirmed keeping £595 low / £650 standard / £795 peak in this review session. |
| Booking deposit | Candidate uses £250, separately from the damage/security deposit. |
| Balance | Candidate uses the 12-week threshold; dates inside it collect the full hire price. |
| Owner advertising/admin fee | £49 per vehicle/year plus £25 per confirmed booking, after explicit owner acceptance. |
| Damage/security deposit | Public page states £1,000 subject to insurer/excess confirmation; not final or collected by this backend. |

## Information still needed from the operator

1. Exact low/standard/peak date windows and the last date for which the availability calendar is verified. Adjacent windows are permitted; mixed-season stays need a manual quote unless separately priced.
2. Which short breaks to sell, their exact prices and any collection/return restrictions. Historical £395/£475/£545 figures for 3/4/5 nights remain examples until explicitly agreed.
3. Existing bookings, maintenance, owner-use and turnaround blocks, plus actual office/insurer closure dates. Empty arrays must not be treated as an empty booking calendar.
4. Actual vehicle plate/year/weights and towing facts; insurer's hire permission, excess/security-deposit requirements and driver/vehicle checks. No model-specific specification is inferred from the model name.
5. Approved hire/cancellation/refund/security-deposit documents and private operational processes. Record the requested deposit-forfeiture policy for contract review; do not represent it as reviewed legal wording.

## Technical work prepared

A private, read-only `preflight.php` checks config paths, storage, mode/key/account shape, dates/prices/blocks, verification flags, release lock and PHP extensions. Its test suite covers malformed and overlapping calendars, invalid prices, missing approvals, payment-mode mismatch, secret-output suppression, public-config rejection and unchanged lock/storage. The tool does not connect to Stripe or open/create the booking database. Even an all-pass offline report explicitly states that public launch is unverified.

There is no current session access to the private production booking config, correct merchant dashboard or scheduler. Do not describe those as checked. Credentials must be entered through the private hosting/merchant setup, not chat, Git or this worksheet.

## Staged end-to-end acceptance

After the real facts/config are available, use a separate test-mode staging setup and fixture customer:

1. Inspect runtime/private permissions and run the offline check. Reconcile/import the actual inventory before enabling any real availability.
2. Select a seven-night low/standard/peak fixture stay; assert the server price and the £250-versus-full-hire boundary at exactly 12 weeks. Unsupported short/mixed stays must request a manual quote.
3. Verify a second browser cannot reserve the held dates; repeating a quote must not extend its fixed 15-minute hold. Change/release dates and retry expired selections.
4. Complete Stripe test-mode Checkout in the correct test merchant. Verify signed webhook amount/currency/mode/reference, duplicate-event handling and private paid state; a return URL alone must never mark payment received.
5. Cancel/abandon a test checkout; observe the private reconciler expire the real Stripe test session before reopening dates. Demonstrate scheduler health and failure monitoring; an uncertain request must keep the dates blocked.
6. Check confirmation/fallback on phone and desktop, public/private data separation, backups/retention and operator support procedures. Separately test owner/admin permissions, plan acceptance, fee timing, evidence withdrawal and handover rules in the owner ledger.
7. Review exact changed files, rollback originals, host config and test evidence. Only then approve a production activation release and observe live runtime without making an unsolicited real charge.

## Review result

New preflight and full candidate CI: pending at preparation; record the exact successful head/workflow before presenting as passed. Real Stripe staging roundtrip, live private-config inspection and business readiness remain outstanding.
