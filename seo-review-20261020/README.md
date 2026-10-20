# SEO corrections — review only

- `analytics-privacy.html`: Add correct self-canonical and factual snippet; preserve privacy controls

No deployment workflow is added or dispatched. Before deployment, use the reviewed manifest and the existing pinned-host-key SFTP environment, verify every original hash against current server bytes, save rollback copies, and run `python3 seo-review-20261020/deploy.py`. Deployment aborts if any original changed. Preserve robots.txt, sitemap, consent, forms and visual styling. After deployment verify changed URLs and corrected link/image targets, reject analytics in automated checks, and inspect the actual rendered mobile and desktop layout. Rollback uses the saved server originals.
