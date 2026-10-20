# Authorized website release — 20 October 2026

Owner instructed completion and publication of the remaining destination integration and prepared image performance improvements. This release changes only the homepage, selected image references/assets, Digital Kinetics hero CSS, and Touring's destination guides and sitemap.

Preparation checks the exact reviewed homepage, original image and CSS hashes before producing assets. Homepage phone/desktop checks compare headings, forms, scripts, hero geometry, overflow and broken images with the live baseline. Touring additionally checks all twelve destination pages. Publication is conditional on these checks passing.

The deployment pins the configured SSH host key, validates live target and robots hashes, saves rollback originals before any writes, publishes new resources before links and the sitemap, and verifies remote and public bytes. On failure it restores modified targets. Production credentials are supplied only through the existing GitHub Actions secret environment.

Touring campsite records distinguish checked published details from outstanding operator acceptance and exact caravan/pitch fit. Prices are scoped examples and are not live quotes. No campsite operator is contacted and no bookings or enquiries are submitted by this release.

Successful publication is recorded in RELEASE-VERIFIED.json in the release workflow artifact alongside the exact originals and review screenshots. No ranking, real-user speed score or conversion increase is asserted by this release.
