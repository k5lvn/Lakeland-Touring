from pathlib import Path
from bs4 import BeautifulSoup
import json,hashlib,urllib.request
R=Path('holiday-planner-20261025');F=R/'files'
# Use the currently published brand shell, with precise current-byte baselines.
originals={}
for name in ['index.html','explore-destinations.html','caravan-hire-faq.html','analytics-privacy.html','sitemap.xml']:
 with urllib.request.urlopen('https://lakelandtouring.uk/'+name,timeout=40) as r:originals[name]=r.read()
 (F/name).write_bytes(originals[name])
s=BeautifulSoup(originals['caravan-hire-faq.html'].decode().replace('@media(min-width:951px) and (max-width:1250px)','@media(min-width:951px) and (max-width:1700px)'),'html.parser')
s.title.string='Your Holiday, Mapped Out | Lakeland Touring'
s.select_one('link[rel=canonical]')['href']='https://lakelandtouring.uk/holiday-planner.html'
s.select_one('meta[name=description]')['content']='Build your own caravan holiday itinerary, open your route in Google Maps, check Lake District weather and print your Travel Ready checklist.'
for key,val in [('og:title','Your Holiday, Mapped Out | Lakeland Touring'),('og:description',s.select_one('meta[name=description]')['content']),('og:url','https://lakelandtouring.uk/holiday-planner.html')]:s.select_one('meta[property="'+key+'"]')['content']=val
s.select_one('script[type="application/ld+json"]').string=json.dumps({'@context':'https://schema.org','@type':'WebPage','name':'Your Holiday, Mapped Out','url':'https://lakelandtouring.uk/holiday-planner.html','isPartOf':{'@type':'WebSite','name':'Lakeland Touring','url':'https://lakelandtouring.uk/'}})
s.select_one('main').replace_with(BeautifulSoup((R/'main.html').read_text(),'html.parser'))
for tag,attrs in [('link',{'rel':'stylesheet','href':'holiday-planner.css?v=20261025'}),('script',{'defer':'','src':'holiday-planner.js?v=20261025'})]:s.head.append(s.new_tag(tag,attrs=attrs))
for a in s.select('nav .nav-active'):a.attrs.pop('class',None)
a=s.new_tag('a',href='holiday-planner.html');a.string='Holiday planner';s.select_one('nav').append(a)
(F/'holiday-planner.html').write_text(str(s))
for name in ['index.html','explore-destinations.html','caravan-hire-faq.html']:
 p=BeautifulSoup(originals[name].decode().replace('@media(min-width:951px) and (max-width:1250px)','@media(min-width:951px) and (max-width:1700px)'),'html.parser')
 nav=p.select_one('nav')
 if nav:
  a=p.new_tag('a',href='holiday-planner.html');a.string='Holiday planner';nav.append(a)
 footer=p.select_one('.touring-footer-help')
 if footer:
  a=p.new_tag('a',href='/holiday-planner.html');a.string='Holiday planner';footer.insert(0,a)
 if name=='index.html':
  section=BeautifulSoup('<section class="touring-practical"><span class="eyebrow">YOUR NEXT ADVENTURE</span><h2>Your holiday, mapped out.</h2><p>Create your own itinerary, open the journey in Google Maps and work through your Travel Ready checklist. Keep it on screen or print a copy for the road.</p><a class="button" href="holiday-planner.html">Plan your holiday ↗</a></section>','html.parser')
  p.select_one('main').append(section)
 (F/name).write_text(str(p))
p=BeautifulSoup(originals['analytics-privacy.html'],'html.parser')
body=p.body
section=BeautifulSoup('<section><h2>Holiday planner privacy</h2><p>Your itinerary stays in this browser unless you choose to save it on this device, download it or open a map. Saved plans use browser storage and can be cleared with the planner’s “Clear saved plan” button. No account is required. Avoid including sensitive information, especially on shared devices.</p><p>Weather requests send only a selected forecast-area identifier to our server. Our server requests forecasts from MET Norway without forwarding your itinerary or browser IP address. Loading the optional Google map or opening Google Maps shares the selected map location or route with Google under its privacy terms.</p></section>','html.parser')
body.append(section);(F/'analytics-privacy.html').write_text(str(p))
xml=originals['sitemap.xml'].decode().replace('</urlset>','<url><loc>https://lakelandtouring.uk/holiday-planner.html</loc></url></urlset>');(F/'sitemap.xml').write_text(xml)
manifest={'site':'lakelandtouring.uk','base_url':'https://lakelandtouring.uk/','remote_root':'/public','files':{}}
for p in F.iterdir():
 manifest['files'][p.name]={'original_sha256':hashlib.sha256(originals[p.name]).hexdigest() if p.name in originals else None,'updated_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(R/'manifest.json').write_text(json.dumps(manifest,indent=2))
