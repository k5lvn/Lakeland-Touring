# Lakeland Touring 2.0 — first luxury release

Approved service: delivered, set up and collected; bespoke quotes. Customer books and pays campsite separately. Teal boutique design, real existing gallery and scenery, no invented reviews or live booking promises. No fixed hire prices advertised.

Public destination, privacy, Reviews, booking and guide URLs retain their canonicals. Four obsolete Owner's Garage URLs are removed from the sitemap and deleted from the public site: `/garage.php?view=browse`, `/owners-garage.html`, `/owner-terms.html` and `/garage-privacy.html`. The retired URLs return 404 or 410; no redirects are added. The delivered stay remains the main offer, with self-tow mentioned only as a secondary option by arrangement. The old public booking form and planner are replaced by personal quote enquiries at their existing URLs. Public Gigi preview is removed pending service-knowledge updates; its infrastructure remains untouched.

The release reads the current live sitemap and customer pages, snapshots exact original bytes, validates candidates, persists a 90-day Actions backup, tests 390px and 1440px layouts and the gallery, then performs guarded SFTP writes. It refuses changed remote originals, pins the SSH host key, verifies exact live bytes, confirms retired URLs return 404 or 410, and restores changed originals on publication failure. Source restore point: backup/pre-luxury-20261031.

No customer records, API routes beyond the retired public Garage endpoint, credentials, database contents, payment configuration, owner agreements or booking state are changed. Existing destination research remains dated and delivery is subject to campsite approval, access, feasibility and availability.

To evolve: edit home.html and luxury.css; update release.py for specific page content. The public PHP booking backend remains disabled as previously configured. Publication requires the existing repository SFTP secrets; these never enter the source tree or artifacts.

Visual refinement: original silver/teal logo restored; all static sitemap pages share the dark charcoal/teal theme. New optimised illustrative Lake District dusk artwork replaces daytime homepage scenery. Shared brand.css carries the palette into retained owner/privacy surfaces. Image upload, guarded replacements and rollback are included in the release manifest. Browser checks cover dark backgrounds, logo/image loading, responsive guides, enquiries, navigation and gallery.

## 25 November 2026 hire options and extras

- The public offer presents exactly two hire options: self-tow from Carlisle, or delivery with setup and collection at an approved campsite.
- Delivery is £1.50 per mile across the four journeys (delivery out and return, then collection out and return). A 100-mile one-way delivery is 400 chargeable miles, or £600. Setup, dismantling and collection are included; there is no separate setup fee.
- The optional DJI portable power station is £10 per day or £69 per week.
- Homepage, quotation page and FAQs use the same rates. No third hire option is added.
