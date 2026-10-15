# Lakeland Touring — SEO deployment pack
Prepared 15 October 2026. **Staged guidance, not deployed to production.**

## Priority and current findings
- Domain property in Search Console: `sc-domain:lakelandtouring.uk` (connected).
- Submitted XML sitemaps: none.
- 28-day search performance: zero reported impressions and clicks.
- Stored URL inspections: none.
- Live URL, robots.txt and sitemap.xml were not accessible from verification tools today; environmental DNS lookup also fails for unrelated websites and is **not proof** of a Touring DNS fault.
- GitHub main currently lacks a known root website entrypoint and deployment is unconfigured. DO NOT deploy these examples without matching them to actual site architecture and verifying published content.

## Homepage metadata (adapt into authoritative live website)
```html
<title>Lakeland Touring | Caravan Hire in Cumbria & the Lake District</title>
<meta name="description" content="Discover caravan touring with Lakeland Touring in Cumbria and the Lake District. Explore our six-berth Elddis Avante 866 and enquire about availability.">
<link rel="canonical" href="https://lakelandtouring.uk/">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta property="og:type" content="website">
<meta property="og:title" content="Lakeland Touring | Caravan Hire in Cumbria">
<meta property="og:description" content="Explore our six-berth Elddis Avante 866 caravan and enquire about availability.">
<meta property="og:url" content="https://lakelandtouring.uk/">
```
Avoid OG image until an actual publicly available image URL is verified. Never claim specific rentals or booking terms that the site does not actually provide. Main heading suggested: **Caravan hire for your next adventure**. Natural copy should mention Carlisle, Cumbria, Lake District and six-berth Elddis Avante 866 where relevant, not stuff repeated phrases.

## Robots draft (publish only if relevant paths exist and no conflicts)
```txt
User-agent: *
Allow: /
Sitemap: https://lakelandtouring.uk/sitemap.xml
```
Private Owner's Garage and admin areas require strong authentication; avoid putting sensitive URL paths into robots as a security measure. Never use sitewide noindex, Disallow: / or an unverified canonical redirect.

## Minimal sitemap draft (expand only with confirmed canonical live pages)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://lakelandtouring.uk/</loc></url>
</urlset>
```
Include only live indexable canonical URLs; no placeholder gallery, advert, login, basket or enquiry URLs. Test sitemap as XML and ensure HTTPS GET responds successfully before submitting to GSC.

## Suggested page structure (only if these pages actually exist)
- Home: brand + caravan hire
- Our Fleet: individual vehicle data including capacities, features and real original photos
- Gallery: image alt text and clean image display (visible overlay text removed)
- Owner's Garage: explain third-party advertising and clear owner/advertiser responsibility; no indexed empty listings
- Contact: accessible contact form and LakelandTouring@Worx365Group.uk
All public pages should have unique title, meta description, H1, real copy, canonical, image alt text, open graph metadata and internal links. Avoid creating thin location doorway pages.

## Schema after verification
Use Organization/WebSite JSON-LD only with authentic verified identifiers, name, URL, logo and contact data. For individual vehicle listings, use only supported schema that accurately reflects rental/advertising; no fake reviews, prices, ratings, booking availability or LocalBusiness address.

## Live verification acceptance checklist
1. Verify DNS using an external authoritative resolver and verify both www and non-www HTTPS.
2. Check homepage status, redirects and rendered head tags on mobile and desktop.
3. Check robots.txt (no sitewide disallow), canonical URLs, public indexability, no sitewide noindex.
4. Confirm sitemap.xml responds 200, valid XML, and each URL is indexable.
5. Submit correct sitemap with GSC and inspect homepage, fleet and owner-garage public pages where live.
6. Check Core Web Vitals, image sizes, lazy loading, responsive navigation, LCP hero, missing alt, structured data, 404/500 errors, contact form.
7. Capture GSC baseline in performance dashboard; review again after Google's next crawl.

## Access limitation
The repository currently has no verified live source deployment mapping. Do not overwrite hosting or submit nonexistent sitemap. Implement in a safe reviewed branch, with backup, then verify on live hosting.
