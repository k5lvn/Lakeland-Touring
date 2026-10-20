from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import urllib.request, json, hashlib, io, difflib, re
import xml.etree.ElementTree as ET

ROOT = Path('site-release-20261020')
cfg = json.loads((ROOT / 'config.json').read_text())
site = cfg['site']
out = ROOT / 'files'
originals = ROOT / 'originals'
out.mkdir(exist_ok=True)
originals.mkdir(exist_ok=True)
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'Cache-Control': 'no-cache'}), timeout=60) as r:
        assert r.status == 200
        return r.read()
def sha(data): return hashlib.sha256(data).hexdigest()
manifest = {'site': site['id'], 'base_url': site['url'], 'remote_root': cfg['remote_root'], 'files': {}}
def stage(name, data, original=None):
    p = out / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    if original is not None:
        p = originals / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(original)
    manifest['files'][name] = {'original_sha256': sha(original) if original is not None else None, 'updated_sha256': sha(data)}
raw = get(site['url'])
assert sha(raw) == site['index_sha256'], 'Homepage changed since review'
source = raw.decode()
def convert(a):
    data = get(a['url'])
    assert sha(data) == a['source_sha256'], 'Original image changed: ' + a['original_path']
    img = Image.open(io.BytesIO(data)); img.load()
    target = (a['encoded_width'], a['encoded_height'])
    if img.size != target: img = img.resize(target, Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    lossless = a['encoding'] == 'lossless WebP'
    img.save(buf, format='WEBP', lossless=lossless, quality=100 if lossless else 94, method=6)
    result = buf.getvalue()
    assert sha(result) == a['updated_sha256'], 'Image encoding differs from reviewed bytes'
    return a, result
with ThreadPoolExecutor(max_workers=4) as pool: converted = list(pool.map(convert, site['assets']))
for a, data in converted:
    stage(a['new_path'].lstrip('/'), data)
    source = source.replace(a['url'], a['new_path']).replace(a['original_path'].lstrip('/'), a['new_path'].lstrip('/'))
if site['id'] == 'dk':
    css = get(site['url'] + 'concept.css')
    assert sha(css) == site['css_sha256'], 'CSS changed since review'
    text = css.decode()
    for a, _ in converted: text = text.replace(a['original_path'].lstrip('/'), a['new_path'])
    stage('concept.css', text.encode(), css)
    hero = next(a for a, _ in converted if 'hero-premium' in a['url'])
    source = source.replace('</head>', '<link rel="preload" as="image" type="image/webp" href="'+hero['new_path']+'" fetchpriority="high"></head>', 1).replace('href="concept.css"', 'href="concept.css?v=20261020-perf"')
if site['id'] == 'touring':
    nav = '<a href="#destinations">Destinations</a>'
    assert source.count(nav) == 1, 'Unexpected destination navigation'
    source = source.replace(nav, '<a href="explore-destinations.html">Destinations</a>')
    cta = '<a class="button ghost" href="booking.html">Plan your escape →</a>'
    assert source.count(cta) == 1, 'Unexpected destination CTA'
    source = source.replace(cta, '<a class="button ghost" href="explore-destinations.html">Explore our destination guides →</a>')
    old = 'From the Lake District to the Scottish Borders and beyond, choose your own perfect escape. Collect in Carlisle and set off on your adventure.'
    assert source.count(old) == 1
    source = source.replace(old, 'Start with the Lake District, then explore nine more regions with practical campsite notes, published price examples and the checks to make before you book. Collect in Carlisle and make it your home for the week.')
    guides = sorted((ROOT / 'guides').glob('*.html'))
    assert len(guides) == 12
    names = {p.name for p in guides}
    for p in guides:
        text = p.read_text()
        assert len(re.findall(r'<h1(?:\s|>)', text)) == 1
        assert 'https://lakelandtouring.uk/' + p.name in text
        assert 'name="robots" content="index,follow"' in text
        stage(p.name, p.read_bytes())
    xml = get(site['url'] + 'sitemap.xml')
    assert sha(xml) == cfg['sitemap_sha256'], 'Sitemap changed since preflight'
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', ns)
    tree = ET.fromstring(xml)
    existing = {x.text for x in tree.findall('{'+ns+'}url/{'+ns+'}loc')}
    for name in sorted(names):
        url = site['url'] + name
        if url not in existing:
            node = ET.SubElement(tree, '{'+ns+'}url')
            ET.SubElement(node, '{'+ns+'}loc').text = url
            ET.SubElement(node, '{'+ns+'}lastmod').text = '2026-10-20'
    stage('sitemap.xml', ET.tostring(tree, encoding='utf-8', xml_declaration=True), xml)
stage('index.html', source.encode(), raw)
robots = get(site['url'] + 'robots.txt')
assert sha(robots) == cfg['robots_sha256'], 'Robots changed since preflight'
manifest['robots_sha256'] = sha(robots)
(ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
(ROOT / 'index.html.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True), source.splitlines(True), fromfile='live/index.html', tofile='release/index.html')))
print('Prepared', site['id'], len(manifest['files']), 'files with reviewed source hashes')
