"""Current-live, URL-preserving luxury release with exact rollback and no backend writes."""
import concurrent.futures, hashlib, importlib.util, json, re, sys
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup, NavigableString
ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('prior','navigation-fix-20261030/release.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
BASE=prior.BASE
OUT=Path('luxury-qa');OUT.mkdir(exist_ok=True)
ORIGINAL=Path('luxury-backup');ORIGINAL.mkdir(exist_ok=True)
CSS=(ROOT/'luxury.css').read_text()
NOTE='<aside class="lt-service-note"><strong>Delivered caravan stays, personally arranged.</strong> You book and pay for your campsite separately. We deliver, set up and collect the caravan. All stays and longer-distance deliveries are individually quoted, subject to availability, access and campsite approval. <a href="/#contact">Request your bespoke quotation →</a></aside>'
CONTACT='<section class="lt-section lt-enquiry-main"><p class="lt-kicker">YOUR DESTINATION. OUR PLEASURE.</p><h1>Let’s plan your luxury caravan escape.</h1><p>Our Elddis Avanté 866 accommodates up to six guests. Tell us your preferred dates, guest numbers and campsite or destination. We’ll check availability and delivery feasibility and provide a bespoke quotation for hire, delivery, setup and collection.</p><p>You book and pay for your campsite pitch separately, after confirming suitability and delivery arrangements with us. Your quotation will confirm inclusions, payment terms and any deposit. An enquiry does not reserve dates or confirm a booking.</p><div class="lt-actions"><a class="lt-button" href="mailto:LakelandTouring@Worx365Group.uk?subject=Delivered%20caravan%20stay%20quotation">Email Your Plans</a><a class="lt-button lt-outline" href="tel:+441228307953">Call 01228 307953</a><a class="lt-button lt-outline" href="/#contact">Quotation Details</a></div></section>'
FAQ='''<section class="lt-section"><p class="lt-kicker">GOOD TO KNOW</p><h1>Luxury caravan hire FAQs</h1><h2>Do we tow or collect the caravan?</h2><p>We handle delivery, setup and collection. You arrive at the agreed campsite and enjoy your stay.</p><h2>Who books the campsite?</h2><p>You book and pay the campsite directly. First confirm with us and the campsite that the pitch fits the caravan and that delivery, access and collection can be arranged.</p><h2>How much does a stay cost?</h2><p>All stays are individually quoted around dates, duration, guests and destination. We confirm hire, delivery, setup, collection, inclusions, payment terms and any deposit before booking. Campsite fees are separate.</p><h2>What is included?</h2><p>The delivered and prepared caravan, beds made for your stay, bedding, towels, toiletries and a welcome hamper. Your quotation confirms the full inclusions and any personal requests.</p><h2>How many guests can stay?</h2><p>Our Elddis Avanté 866 is a six-berth caravan, suitable for up to six guests. We can explain the sleeping layout before you book.</p><h2>Can you deliver further afield?</h2><p>Tell us your destination. Longer-distance delivery is considered individually, subject to logistics, suitable access and availability, with a bespoke quotation.</p><h2>How do we book?</h2><p>Send your dates, guests and destination. We confirm availability, practical arrangements and your quote personally. Online instant booking is not available.</p><a class="lt-button" href="/#contact">Request Your Bespoke Quote</a></section>'''
def replace_words(t):
    t=re.sub(r'self[\s‐‑–-]*tow', 'delivered and set-up',t,flags=re.I)
    t=re.sub(r'collect in Carlisle', 'delivery from Carlisle', t, flags=re.I)
    t=re.sub(r'collection arrangements', 'delivery arrangements', t, flags=re.I)
    t=t.replace('Carlisle collection','delivery arrangements')
    if re.search(r'\btowing\b',t,re.I):
        sentences=re.split(r'(?<=[.!?])\s+',t)
        t=' '.join('We confirm campsite access and delivery arrangements before your stay.' if re.search(r'\btowing\b',part,re.I) else part for part in sentences)
    t=t.replace('collection and return dates','arrival and departure dates').replace('towing journey','delivery journey')
    t=t.replace('Collect in Carlisle and make it your home for the week.','We deliver, set up and collect at your agreed campsite.').replace('collect from Carlisle','arrange delivery from Carlisle').replace('collection from Carlisle','delivery from Carlisle')
    return t

def transform(name,data):
    s=BeautifulSoup(data,'html.parser')
    assert s.head and s.body,name
    if name=='index.html':
        gallery=s.select_one('#caravan');assert gallery and gallery.select('.touring-gallery img')
        gallery['class']=['lt-section','lt-gallery']
        gallery.select_one('h2').string='Your home from home.'
        layout=(ROOT/'home.html').read_text().replace('<!-- CARAVAN_GALLERY -->',str(gallery))
        oldmain=s.find('main'); assert oldmain
        # Keep footer, analytics consent, gallery/lightbox, social links and all runtime scripts.
        if s.find('header'):s.find('header').decompose()
        oldmain.replace_with(BeautifulSoup(layout,'html.parser'))
        for x in s.select('div#contact'):x.decompose()
        s.title.string='Luxury Caravan Hire Carlisle & Lake District | Delivered | Lakeland Touring'
        s.select_one('meta[name="description"]')['content']='Luxury six-berth caravan hire from Carlisle for Lake District stays and beyond. Delivered, set up and collected. Request your bespoke quotation; campsite fees separate.'
        for q,value in [('meta[property="og:title"]','Lakeland Touring — Boutique Luxury on Tour'),('meta[property="og:description"]','Luxury caravan stays, delivered, beautifully prepared and collected. Bespoke quotations. You book your campsite separately.')]:
            if s.select_one(q):s.select_one(q)['content']=value
    elif name in ['booking.html','caravan-hire-faq.html','holiday-planner.html']:
        main=s.find('main')
        if main:main.clear()
        else:
            for child in list(s.body.find_all(recursive=False)):
                if (child.name=='section' and 'w365-review' not in child.get('class',[])) or child.get('id')=='bookingModal':child.decompose()
            main=s.new_tag('main');s.find('header').insert_after(main)
        main.append(BeautifulSoup(FAQ if name=='caravan-hire-faq.html' else CONTACT,'html.parser'))
        s.title.string=('Bespoke Delivered Caravan Quotations' if name=='booking.html' else 'Luxury Caravan Stay Planning' if name=='holiday-planner.html' else 'Delivered Caravan Hire FAQs')+' | Lakeland Touring'
        desc=s.select_one('meta[name="description"]')
        if desc:desc['content']='Delivered caravan stays from Carlisle. We deliver, set up and collect; you book your campsite separately. Contact Lakeland Touring for a bespoke quotation.'
        for prop,value in [('og:title',s.title.get_text()),('og:description',desc.get('content','') if desc else 'Personally arranged delivered caravan stays.'),('og:url',BASE+name)]:
            tag=s.select_one('meta[property="'+prop+'"]')
            if tag:tag['content']=value
        for script in s.select('script[type="application/ld+json"]'):
            script.string=json.dumps({'@context':'https://schema.org','@type':'WebPage','name':s.title.get_text(),'url':BASE+name,'description':'Delivered caravan stays with bespoke quotations. Campsite booked and paid separately.'})
        # These scripts power retired public instant-booking interactions, not backend infrastructure.
        for script in s.select('script[src]'):
            if re.search(r'booking(?:-standby)?\.js',script['src']):script.decompose()
    else:
        main=s.find('main')
        if main:main.insert(0,BeautifulSoup(NOTE,'html.parser'))
    if name!='index.html':
        layout=BeautifulSoup((ROOT/'home.html').read_text(),'html.parser')
        header=layout.find('header')
        for a in header.select('a[href^="#"]'):a['href']='/'+a['href']
        old=s.find('header')
        if old:old.replace_with(header)
        else:s.body.insert(0,header)
        s.body.append(layout.find('script'))
    for x in list(s.select('#gg-widget,#gg-open,#gg-panel,script[src*="gigi.js"]')):x.decompose()
    for tag in list(s.find_all(string=True)):
        if tag.parent.name in ['script','style']:continue
        new=replace_words(str(tag))
        if new!=str(tag):tag.replace_with(new)
    for tag in s.select('meta[content],img[alt]'):
        key='content' if tag.has_attr('content') else 'alt';tag[key]=replace_words(tag[key])
    for script in s.select('script[type="application/ld+json"]'):
        if script.string:
            # Preserve structured-data identity; remove obsolete service description only.
            script.string=replace_words(script.string)
    # All marketing CTAs lead to personal quotation; preserve backend routes/files.
    for a in list(s.select('a[href]')):
        href=a['href'];label=a.get_text(' ',strip=True)
        if href in ['garage.php?view=browse','owners-garage.html','owner-terms.html','holiday-planner.html'] and (a.find_parent('nav') or a.find_parent('footer')):
            a.decompose();continue
        if 'booking.html' in href and re.search('availability|booking|book|dates',label,re.I):
            a.string='Request a Bespoke Quote'
        elif href.endswith('#pricing') and label in ['Pricing','Prices']:a.string='Quotations'
    for node in list(s.find_all(string=True)):
        if node.parent.name in ['script','style']:continue
        # Remove obsolete customer-towing sales promises in destination guide copy.
        if re.search(r'\bunlimited mileage\b',str(node),re.I):node.replace_with(re.sub(r'\bunlimited mileage\b','delivery agreed in your quotation',str(node),flags=re.I))
    style=s.new_tag('style',id='lakeland-touring-luxury-20261031');style.string=CSS;s.head.append(style)
    return str(s).encode()

def validate(name,before,after):
    a=BeautifulSoup(before,'html.parser');b=BeautifulSoup(after,'html.parser')
    assert b.select_one('link[rel="canonical"]')['href']==a.select_one('link[rel="canonical"]')['href'],name
    assert not b.select('meta[name="robots"][content*="noindex"]'),name
    assert len(b.select('h1'))==1,(name,'h1')
    assert not re.search(r'self[\s‐‑–-]*tow',b.get_text(' ',strip=True),re.I),name
    assert b.select_one('#lakeland-touring-luxury-20261031'),name
    for script in a.select('script[src]'):
        if re.search('analytics-consent|gallery',script['src']):assert b.select(f'script[src="{script["src"]}"]'),name
    if name=='index.html':
        assert len(b.select('.touring-gallery img'))==len(a.select('.touring-gallery img'))
        assert '£595' not in b.get_text() and '£795' not in b.get_text()
        assert b.select_one('#contact') and b.select_one('#lt-navigation')
        assert b.select_one('dialog#touring-photo-viewer')
    return True

def prepare():
    sitemap=prior.fetch('sitemap.xml');robots=prior.fetch('robots.txt')
    names=set()
    for el in ET.fromstring(sitemap).iter():
        if el.tag.endswith('}loc') and el.text.startswith(BASE):
            n=el.text[len(BASE):] or 'index.html'
            if n.endswith('.html') and not n.startswith(('owner','garage-privacy','analytics-privacy')):names.add(n)
    names.update(['index.html','booking.html','caravan-hire-faq.html'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        originals=dict(zip(sorted(names),pool.map(prior.fetch,sorted(names))))
    changes={}
    for n,b in originals.items():
        out=transform(n,b);validate(n,b,out)
        (ORIGINAL/n).write_bytes(b);(OUT/n).write_bytes(out);changes[n]=out
    (ORIGINAL/'robots.txt').write_bytes(robots);(ORIGINAL/'sitemap.xml').write_bytes(sitemap)
    manifest={n:{'before':hashlib.sha256(originals[n]).hexdigest(),'after':hashlib.sha256(b).hexdigest()} for n,b in changes.items()}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('PASS: prepared',len(changes),'pages; URLs, canonicals, gallery, analytics, robots and sitemap preserved',flush=True)

def deploy():
    manifest=json.loads((OUT/'manifest.json').read_text())
    original={n:(ORIGINAL/n).read_bytes() for n in manifest};release={n:(OUT/n).read_bytes() for n in manifest}
    for n in manifest:
        assert hashlib.sha256(original[n]).hexdigest()==manifest[n]['before']
        assert hashlib.sha256(release[n]).hexdigest()==manifest[n]['after']
        validate(n,original[n],release[n])
    prior.deploy(original,release,(ORIGINAL/'robots.txt').read_bytes(),(ORIGINAL/'sitemap.xml').read_bytes())
if __name__=='__main__':
    if '--publish' in sys.argv:deploy()
    else:prepare()
