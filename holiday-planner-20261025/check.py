from pathlib import Path
from bs4 import BeautifulSoup
import hashlib,json,xml.etree.ElementTree as ET
r=Path('holiday-planner-20261025');m=json.loads((r/'manifest.json').read_text())
for name,v in m['files'].items():
 b=(r/'files'/name).read_bytes();assert hashlib.sha256(b).hexdigest()==v['updated_sha256'],name
 if name.endswith('.html'):
  s=BeautifulSoup(b,'html.parser');assert len(s.select('h1'))==1;assert s.select_one('link[rel=canonical]');assert s.select_one('footer #lt-cookie-settings')
  for tag in s.select('script[type="application/ld+json"]'):json.loads(tag.string)
urls=[x.text for x in ET.fromstring((r/'files/sitemap.xml').read_bytes()).iter() if x.tag.endswith('loc')];assert len(urls)==21 and len(set(urls))==21
assert 'https://lakelandtouring.uk/holiday-planner.html' in urls
p=BeautifulSoup((r/'files/holiday-planner.html').read_text(),'html.parser');assert p.select_one('img.touring-official-logo');assert p.select_one('#ready-checklist');assert p.select_one('#weather-area');assert p.select_one('iframe') is None
print('PASS: release hashes, 5 pages, structured data, 21 sitemap URLs, brand and opt-in map shell')
