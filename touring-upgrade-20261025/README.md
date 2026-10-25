# Lakeland Touring — 25 October 2026 upgrade

Owner authorised implementation with “Ok pal crack on with touring”. Existing IONOS hosting and k5lvn/Lakeland-Touring release workflow are retained; no Sites migration.

## Verified baseline

- Homepage and all 19 sitemap routes responded HTTP 200 during this session. The earlier external retrieval failure is not a confirmed DNS/hosting outage.
- Search Console tracker returned 6 indexed and 13 not indexed on its latest per-URL checks (timestamps vary). The 11 regional guides and hub are not indexed; Google reports unknown or discovered, currently not indexed. These states do not establish a technical crawl block.
- Availability API returned HTTP 503 with “Online booking is unavailable. Please contact us.” The backend exists and is locked; the old 404/missing-backend finding is superseded.
- Live analytics script requests no Google tag until opt-in, but its Cookie settings control is fixed over the page and WhatsApp button.
- The homepage and booking metadata promote online availability despite checkout being closed. Booking shows an unconfirmed £1,000 security-deposit amount; preserved policy text identifies insurer confirmation as outstanding.

## Exact release

- 12 dedicated hire FAQs covering enquiries, collection, layout, guide prices, deposit/payment timing, separate pitch bookings, territory, towing checks, inventory, special arrangements, cancellation and Owner’s Garage.
- Native homepage planning section replaces repetitive existing SEO prose, retaining landscape, photographs, gallery, typography, rates and brand presentation.
- Prominent booking-page WhatsApp/phone/email enquiry panel; no customer data is submitted by tests. Calendar offline label and explicit security-deposit confirmation replace misleading wording. Booking JS/API/lock, private records and merchant setup are unchanged.
- Individual planning advice and two relevant guide links on each of 11 regions; breadcrumb JSON-LD. Existing campsite research/source dates are retained as 20 October, not represented as reverified or operator-approved.
- FAQ navigation/footer links; footer Cookie Settings across all 19 static content pages; consent colour matched to established turquoise. Dynamic garage templates are not modified.
- Consent preserves 180-day expiry, opt-in-only Analytics, existing contact event gating, withdrawal and cookie cleanup. Focus returns without scrolling visitors to the footer.
- Existing 19 sitemap URLs retained, FAQ added for 20 total. Robots stays byte-for-byte unchanged.
- Tablet menu switches to hamburger up to 1250px to accommodate the added FAQ link.

## Verification and release

`check.py`: hashes, 19 HTML pages, H1, canonical, metadata, JSON-LD, footer control placement, 12 FAQ disclosures, 20 unique sitemap entries.

`check.cjs`: 390px/1440px page checks, broken images/overflow, FAQ expansion, no Google requests before consent or after rejection, accept/reject persistence/expiry/withdrawal, disabled booking. Google requests and all writes intercepted. These are lab/functionality checks, not real-user Core Web Vitals measurements.

`deploy.py`: pinned SSH host, exact current-file hash preflight, full originals backup, atomic replacements, remote and public SHA-256 verification, unchanged robots and booking lock. New FAQ must not pre-exist. Automatic rollback removes only the newly created FAQ and restores every modified original if any check fails. Evidence and screenshots retained as GitHub Actions artifacts.

## Remaining operational scope

Checkout activation needs confirmed calendar inventory/blocks/horizon, approved date-band prices, exact caravan plated specifications, insurer-approved hire/security-deposit/cancellation terms, merchant/webhook configuration and payment/confirmation operations. Current release intentionally does not remove the lock or claim paid-booking verification.

Campsite acceptance of hired caravans and actual outfit/pitch compatibility remain unconfirmed. No operator was contacted. Real enquiries/inbox delivery, customer payments, GBP exact-name visibility investigation and real-user performance evidence are separate outstanding work. No ranking or immediate indexing improvement is claimed.

Google guidance consulted: helpful reliable people-first content and crawlable descriptive links, https://developers.google.com/search/docs/fundamentals/creating-helpful-content and https://developers.google.com/search/docs/crawling-indexing/links-crawlable .
