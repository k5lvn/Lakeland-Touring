# Lakeland Touring booking diary

The guest calendar is at `/hire-calendar/`. The Bookings link in `/Admin/` opens the operator diary. The operator signs in with a short-lived code delivered to the Touring office inbox, or an explicitly configured hosting-authenticated account. Guests can request a stay without an account. An operator checks availability, the agreed price and receipt of the deposit before approving. Date intervals include the arrival night and exclude the departure night.

The diary uses the existing booking SQLite schema. If an existing private booking configuration is configured on the web host, the default configuration reuses its database directory and blocked dates. Unpriced dates can be requested up to twelve months ahead. Approved seasonal windows define the prices and stay lengths displayed to guests. Outside those windows the interface quotes on request. Operator and maintenance blocks appear in the same diary.

The release creates a private configuration, receipt key and initial anonymous hold outside the web root only when missing. Existing private files and database rows are preserved across releases. The initial entry is a six-night hold with a separately issued private guest link. Releasing it in Bookings prevents recreation on subsequent visits. Guest details, private links and credentials must not be committed.

Availability reads return only occupied date ranges and their status. Private guest links show the current decision and, for held or confirmed dates, a live countdown to the arrival day in Europe/London until an exact handover time is agreed. Confirmation email contains a dated countdown snapshot and the private live link. Notifications are queued atomically and attempted on submission, decision and operator visits. The optional CLI worker can drain the same queue from hosting cron.

For local checks, run `php booking-calendar/tests/approval.php` and `php booking-calendar/tests/diary.php`. The publish workflow backs up and updates the live entry points and verifies the calendar and private access checks before exposing them in navigation.
