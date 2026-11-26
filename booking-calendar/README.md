# Lakeland Touring approval calendar

The public calendar offers the operator's released dates and stay prices. A request is pending until the operator approves it. Approved dates are reserved in the same SQLite bookings database used by the original booking API. The confirmation link shows the recorded decision immediately. The email queue alerts the office to new requests and sends the decision to the guest. No payment is taken.

## Host setup

* Copy the contents of `booking-backend/public/hire-calendar/` to `/hire-calendar/`. Install the associated updated `api/common.php` and `api/availability.php` together so legacy checkout sees operator reservations. Keep the existing payment standby lock.
* Outside the public web directory, create a private configuration from `booking-calendar/config.example.php`. Set `TOURING_CALENDAR_CONFIG` to its absolute path in web and cron environments. Set the existing booking database directory, official mail sender, receipt secret and approved periods. Use the same real diary and owner/maintenance blocks for both booking paths.
* Protect `/hire-calendar/admin/` using the host's HTTPS directory authentication. Set `operator_user` to the authenticated account name. The handler checks the server's REMOTE_USER, denies anonymous access, and requires a CSRF token on each decision.
* Set each period's start, exclusive end, season and approved total price in integer pence per permitted stay length. Peak offers seven nights from Saturday. Mid offers configured lengths of seven nights or longer. Low offers three, five or seven nights, with three-night arrivals on Friday. Dates outside configured periods or crossing periods are closed for online requests.
* Place the notification worker and source dependencies outside the web root, preserving their repository-relative paths. Schedule `php booking-calendar/notify.php` with the same private configuration and the real `TOURING_DOCUMENT_ROOT`. Confirm delivery to a test inbox using the site's mail service. Failed mail remains queued; the private status link always reads the stored record.
* Once real inventory, tariffs and operator review access are verified, add the `/hire-calendar/` link to the customer quote page using `booking-calendar/link.py`. Keep existing contact options. Run `php booking-calendar/tests/approval.php` to check request and approval behaviour locally.

The existing partner-owner advertising portal is separate from this operator diary.
