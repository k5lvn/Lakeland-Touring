# Lakeland Touring Analytics

Requested 20 October 2026: extend the established LD/DK opt-in implementation. Worx365 Group account 412470404; property 559721087; stream 16162560942; measurement ID G-5W12LPB0KK; website https://lakelandtouring.uk/. Enhanced measurement verified off during setup. No duplicate property was created for Worx365 Group.

No Google traffic before acceptance or after rejection. Separate hostname restrictions and consent key, 180-day preference expiry, advertising consent denied, Signals and ad personalisation disabled in tag configuration. Query strings, fragments and full referrer paths excluded. Only public HTML pages: PHP endpoints and admin/account/login/rider/passport/Performance 365 routes excluded.

Deployment patches current files in /public, checks robots/sitemap and hosting identity, rejects conflicting tags, backs up originals and verifies staged/remote/public bytes with rollback on failure. Preserve the shared script reference in future page releases.

Not proof of real collection: after publishing, verify a real consented visit in GA4. Performance 365 reporting access and feed mapping are separate follow-up checks. No synthetic visits or conversions are sent.

Checks: node --check analytics/analytics-consent.js; node analytics/test-consent.cjs; python3 -m py_compile analytics/deploy.py. GitHub repeats checks and performs live no-Google-before-consent/rejection verification after approved publishing.
