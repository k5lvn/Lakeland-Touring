# Lakeland Touring — implementation plan (15 October 2026)

Status: planning document only. No changes to live hosting are implied.

## Confirmed site requirements
- Fresh contemporary layout, not beige or brown. Use the agreed light colour scheme with a restrained accent colour.
- Premium identity with Lakeland Touring logo; transparent version for Digital Kinetics and Worx365 portfolio placement, backdrop version on Touring itself.
- Strong non-washed-out Lake District hero image, excellent contrast and consistent, aligned image crops.
- Image gallery: image-focused lightbox with prev/next, keyboard/touch navigation and uncluttered fullscreen view. Remove text overlays on pictures; keep descriptive alt text for accessibility and SEO.
- Standard Worx365 Group footer, with correct logo.
- Gigi as real interactive assistant, not a fake/static chatbot; accurate OpenAI attribution only if genuine OpenAI API integration is live and brand assets comply with brand guidance.
- Primary caravan: Elddis Avante 866 six-berth. Broader future inventory may include motorhomes and campervans.
- Contact address: LakelandTouring@Worx365Group.uk. Do not publish an unverified phone number.

## Owner's Garage (future development)
- Clearly identify service as **Owner's Garage** — independent owners can advertise their own vehicles.
- Annual fee, price pending explicit approval. Do not publish a fabricated price.
- Owners receive account access via secure registration/password setup and can create/edit their own adverts and upload multiple vehicle photographs.
- Ownership and authorisation verification, moderation prior to publication, role-based access isolation, upload file-size/type validation and image sanitisation.
- Secure authentication: hashed passwords, rate limiting, reset links, CSRF protection and HTTPS. Never distribute plaintext passwords.
- Owner dashboard: vehicle details, images, active/expired listings, renewal status, contact method.
- Transparent owner / customer terms: Lakeland Touring acts as an advertising platform for owner-listed vehicles, not vehicle owner, booking agent, insurer or guarantor unless specifically stated; the advertiser is responsible for accuracy, safety, availability and booking arrangements. Legal review needed: cannot exclude statutory consumer liability or responsibility for own negligence through blanket wording.
- Display ownership and contact details on each advert; clearly distinguish direct Lakeland Touring hires from third-party advertisements.
- Do not implement paid subscriptions or booking flows without approved pricing, refund/renewal rules, payment processing and privacy policy.

## Technical SEO checklist
- Verify live domain, HTTPS redirects, response codes, page source and canonical host.
- Ensure no noindex on public pages and robots.txt permits public crawling; protect private garage and account pages using authentication and appropriate indexing controls.
- Publish a validated XML sitemap listing only canonical public URLs, then submit to Search Console and inspect representative URLs.
- Unique metadata, H1s, accessible image alt text, Open Graph preview and relevant schema based on actual offering.
- Map business intent: caravan hire Carlisle / Cumbria / Lake District, Elddis Avante 866 hire; avoid inaccurate claims.
- Track contact and lead conversions with privacy-conscious analytics.
- Ensure contact forms submit correctly and visibly report errors. Test mobile navigation and the site's performance.

## Audit 15 October 2026
- Google Search Console domain property exists: sc-domain:lakelandtouring.uk.
- Search Console currently reports no submitted sitemaps for that property.
- Last 28-day GSC report showed 0 clicks and 0 impressions; this is not enough to conclude all pages are unindexed.
- URL inspection was unavailable in this session.
- HTTPS site, robots.txt and sitemap.xml could not be verified externally in this session. Do **not** submit sitemap until file is confirmed publicly reachable.
- GitHub repository: k5lvn/Lakeland-Touring (main). README says deployment not configured. No index.html, index.php, sitemap.xml or robots.txt found at repository root.
- Need actual live site source and deployment configuration, with backup and staged review before touching hosting.

## Order of work
1. Locate/import authoritative live site files and securely configure deployment; verify backup.
2. Fix media, gallery, footer, header, branding and mobile layout.
3. Build public Owner's Garage explanation and owner application flow; agree annual price.
4. Implement owner authentication + management with privacy/security testing.
5. Publish sitemap and complete Search Console audit.
6. Confirm all visual/functional changes on staging; then deploy and verify live.
