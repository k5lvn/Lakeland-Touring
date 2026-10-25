# Your Holiday, Mapped Out

Adds the approved interactive planner to the existing Lakeland Touring website with its real logo, silver/turquoise identity and established footer. Links from the homepage, destinations hub and FAQ; sitemap and privacy notice updated. Existing enquiry, booking lock, merchant configuration, robots, private records and hire terms are preserved.

Editable starting point, destination, date, arrival time, caravan, three stops and notes; current Google Maps route links; optional click-to-load destination map; printable/PDF snapshot; text download; explicit local-device save/delete. Twelve checks unlock the green Travel Ready message. Departure checks are never persisted and reset when the travel date changes. No account or countdown added.

Weather: ten fixed Lake District/Carlisle/Gretna forecast areas, clearly identified as area forecasts selected independently of campsite text. No geocoding or automatic caravan road validation is claimed. MET Norway Locationforecast 2.0 is served through a same-origin, fixed-input PHP cache: six-hour refresh interval, provider expiry/Last-Modified support, lock/backoff and a twelve-hour maximum retrieval age. Forecast dates outside the feed and failures show explicit unavailable states. Browser user IP/itinerary not forwarded. CC BY attribution links displayed. Twice-daily GitHub schedule warms all ten areas; first scheduled execution is not yet observed. No paid subscription.

Verification: static hash/HTML/schema/sitemap checks, JS/PHP syntax and CI browser checks at 390/768/1440px cover editing, safe text rendering, map URLs, save/restore, readiness reset, missing forecasts, provider failure and print/PDF. Fixture forecasts are used in CI; production deployment separately requires an actual successful forecast response. No customer enquiry/payment test is submitted.

Deployment uses existing pinned SFTP identity and exact current-byte baselines with backups, atomic writes, remote checksums, public HTML/assets checksums, actual weather response and rollback. PHP source is verified remotely, never exposed publicly. All modified originals must still match the baseline or publication stops. Release evidence retained 90 days.

Provider documentation checked 25 October 2026: https://docs.api.met.no/doc/TermsOfService.html ; https://docs.api.met.no/doc/FAQ.html ; https://api.met.no/weatherapi/locationforecast/2.0/documentation . Google Maps driving directions do not establish caravan road suitability.
