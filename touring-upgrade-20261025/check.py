from pathlib import Path
from bs4 import BeautifulSoup
import json,hashlib,xml.etree.ElementTree as ET,urllib.parse
root=Path('touring-upgrade-20261025');m=json.loads((root/'manifest.json').read_text()); pages=[]
for name,info in m['files'].items():
 b=(root/'files'/name).read_bytes();assert hashlib.sha256(b).hexdigest()==info['updated_sha256']
 if not name.endswith('.html'):continue
 s=BeautifulSoup(b,'html.parser');assert len(s.select('h1'))==1,name;assert len(s.select('#lt-cookie-settings'))==1,name
 assert s.select_one('footer #lt-cookie-settings'),name
 assert len(s.select('link[rel=canonical]'))==1,name
 assert s.select_one('meta[name=description]').get('content'),name
 for x in s.select('script[type="application/ld+json"]'):json.loads(x.string)
 assert 'noindex' not in str(s.select('meta[name=robots]')).lower(),name
 assert s.select_one('a[href="caravan-hire-faq.html"],a[href="/caravan-hire-faq.html"]'),name
 pages.append(name)
urls=[e.text for e in ET.fromstring((root/'files/sitemap.xml').read_bytes()).iter() if e.tag.endswith('loc')]
assert len(urls)==20 and len(set(urls))==20
assert len(BeautifulSoup((root/'files/caravan-hire-faq.html').read_text(),'html.parser').select('details'))==12
print('PASS: 19 HTML pages, 12 FAQs, structured JSON, canonicals, footer controls and 20 sitemap URLs')
