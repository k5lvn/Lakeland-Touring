"""Focused destination update; retains approved pixels and existing public URLs."""
import hashlib, importlib.util, json, sys
from pathlib import Path
from urllib.error import HTTPError
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('luxury','luxury-release-20261031/release.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
ROOT=Path(__file__).parent
release.OUT=Path('destinations-qa');release.OUT.mkdir(exist_ok=True)
release.ORIGINAL=Path('destinations-backup');release.ORIGINAL.mkdir(exist_ok=True)
release.ASSET='touring-approved-destinations-20261031.png'
CSS=(ROOT/'destinations.css').read_text()
PLACES=[('keswick','Keswick & Derwentwater','Lakeside walks, mountain views and time in Keswick.'),('braithwaite','Braithwaite','A village base beneath the north-western fells.'),('windermere','Windermere','Lake days and an easy-going escape together.'),('ambleside','Ambleside','Village evenings and adventures around the central Lakes.'),('ullswater','Ullswater','Peaceful shores and a slower pace among the fells.'),('coniston','Coniston','Water, woodland and a welcoming village base.')]
def content(home=False):
 heading='h2' if home else 'h1'
 cards=''.join(f'<a class="lt-place" href="lake-district-caravan-guide.html#{slug}"><span class="lt-place-photo lt-place-{i}" role="img" aria-label="Illustrative evening scenery for {name}"></span><span class="lt-place-text"><strong>{name}</strong><span>{desc}</span><b aria-hidden="true">Explore →</b></span></a>' for i,(slug,name,desc) in enumerate(PLACES))
 return f'''<section class="lt-lakes-showcase" id="destinations"><div class="lt-dest-intro"><p class="lt-kicker">DESTINATIONS</p><{heading}>The Lake District, at your doorstep.</{heading}><p>Your caravan, delivered and set up for your escape.</p></div><div class="lt-place-grid">{cards}</div><div class="lt-nearby"><h2>A little further afield</h2><div><a href="dumfries-galloway-caravan-guide.html">Dumfries &amp; Galloway →</a><a href="scottish-borders-caravan-guide.html">Scottish Borders →</a><a href="northumberland-caravan-guide.html">Northumberland →</a></div></div><aside class="lt-bespoke"><h2>Somewhere else in mind?</h2><p>Further afield stays considered individually, subject to delivery feasibility and a bespoke quotation.</p><p>You book and pay for your campsite separately. All stays depend on availability, suitable access and campsite approval.</p><a class="lt-button lt-outline" href="/#contact">Enquire about your destination →</a></aside><p class="lt-dest-credit">Destination scenes are illustrative artwork.</p></section>'''
def transform(name,b):
 s=BeautifulSoup(b,'html.parser')
 if name=='index.html':
  target=s.select_one('#destinations');assert target
  target.replace_with(BeautifulSoup(content(True),'html.parser'))
 elif name=='explore-destinations.html':
  main=s.find('main');assert main
  main.clear();main.append(BeautifulSoup(content(),'html.parser'))
  s.title.string='Lake District Caravan Holidays & Nearby Escapes | Lakeland Touring'
  desc='Discover Keswick, Braithwaite, Windermere, Ambleside, Ullswater and Coniston. Delivered caravan stays from Carlisle, with bespoke quotations and nearby escapes.'
  s.select_one('meta[name="description"]')['content']=desc
  for tag in s.select('script[type="application/ld+json"]'):
   tag.string=json.dumps({'@context':'https://schema.org','@type':'WebPage','name':s.title.get_text(),'url':release.BASE+name,'description':desc})
 elif name=='lake-district-caravan-guide.html':
  old=s.select_one('#lt-local-bases')
  if old:old.decompose()
  section=s.new_tag('section',id='lt-local-bases')
  section.append(BeautifulSoup('<h2>Find your Lake District base</h2>'+''.join(f'<article id="{slug}"><h3>{title}</h3><p>{desc} Tell us your preferred campsite and dates so we can confirm delivery, access and availability. You book and pay the campsite separately.</p><p><a href="/#contact">Request a bespoke quotation →</a></p></article>' for slug,title,desc in PLACES),'html.parser'))
  target=s.select_one('.guide-inner') or s.find('main');assert target
  target.append(section)
 for old in s.select('#lt-destinations-20261031'):old.decompose()
 style=s.new_tag('style',id='lt-destinations-20261031');style.string=CSS;s.head.append(style)
 return str(s).encode()
def validate(name,before,after):
 a=BeautifulSoup(before,'html.parser');b=BeautifulSoup(after,'html.parser')
 assert a.select_one('link[rel="canonical"]')['href']==b.select_one('link[rel="canonical"]')['href'],name
 assert len(b.select('h1'))==1,name
 assert b.select_one('.lt-main-logo') and b.select_one('#lt-navigation'),name
 for script in a.select('script[src]'):
  assert b.select(f'script[src="{script["src"]}"]'),(name,script['src'])
 if name in ['index.html','explore-destinations.html']:
  assert len(b.select('.lt-place'))==6
  assert len(b.select('.lt-nearby a'))==3
  for text in ['Cornwall','Devon','Dorset','Somerset','Cotswolds','Yorkshire','Peak District']:
   assert text not in b.select_one('#destinations').get_text(),text
 if name=='index.html':
  assert len(a.select('.touring-gallery img'))==len(b.select('.touring-gallery img'))
  assert b.select_one('#contact') and b.select_one('dialog#touring-photo-viewer')
 if name=='lake-district-caravan-guide.html':
  for slug,_,_ in PLACES:assert b.select_one('#'+slug)
 return True
release.validate=validate

def prepare():
 originals={n:release.prior.fetch(n) for n in ['index.html','explore-destinations.html','lake-district-caravan-guide.html','brand.css']}
 changes={n:transform(n,b) if n.endswith('.html') else b for n,b in originals.items()}
 for n,b in changes.items():
  if n.endswith('.html'):validate(n,originals[n],b)
 for n in ['robots.txt','sitemap.xml']:(release.ORIGINAL/n).write_bytes(release.prior.fetch(n))
 try:originals[release.ASSET]=release.prior.fetch(release.ASSET)
 except HTTPError as e:
  if e.code!=404:raise
  originals[release.ASSET]=None
 changes[release.ASSET]=(ROOT/'approved-destinations.png').read_bytes()
 assert changes[release.ASSET].startswith(b'\x89PNG\r\n\x1a\n')
 for n,b in changes.items():
  (release.OUT/n).write_bytes(b)
  if originals[n] is not None:(release.ORIGINAL/n).write_bytes(originals[n])
 manifest={n:{'before':hashlib.sha256(originals[n]).hexdigest() if originals[n] is not None else None,'after':hashlib.sha256(b).hexdigest()} for n,b in changes.items()}
 (release.OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
 print('PASS: exact approved artwork, six local destinations, nearby links, canonical URLs, gallery, scripts and legacy guide URLs preserved',flush=True)
if __name__=='__main__':
 if '--publish' in sys.argv:release.deploy()
 else:prepare()
