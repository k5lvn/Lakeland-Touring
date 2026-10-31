# Lakeland Touring 2.0 — first luxury release

Approved service: delivered, set up and collected; bespoke quotes. Customer books and pays campsite separately. Teal boutique design, real existing gallery and scenery, no invented reviews or live booking promises. No fixed hire prices advertised.

Existing public URLs, canonicals, robots, sitemap, analytics consent, gallery and backend/owner files are retained. The old public booking form and self-tow planner are replaced by personal quote enquiries at their existing URLs. Public Gigi preview is removed pending service-knowledge updates; its infrastructure remains untouched.

The release reads the current live sitemap and customer pages, snapshots exact original bytes, validates candidates, persists a 90-day Actions backup, tests 390px and 1440px layouts and the gallery, then performs guarded SFTP writes. It refuses changed remote originals, pins the SSH host key, verifies exact live bytes and restores changed originals on publication failure. Source restore point: backup/pre-luxury-20261031.

No customer records, API routes, credentials, database contents, payment configuration, owner agreements or booking state are modified. Existing destination research remains dated and delivery is subject to campsite approval, access, feasibility and availability.

To evolve: edit home.html and luxury.css; update release.py for specific page content. The public PHP booking backend remains disabled as previously configured. Publication requires the existing repository SFTP secrets; these never enter the source tree or artifacts.
