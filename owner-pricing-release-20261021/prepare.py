from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request,re,json,hashlib
root=Path(__file__).parent;base='https://lakelandtouring.uk/'
def get(name):return name,urllib.request.urlopen(base+name,timeout=45).read()
raw=dict(ThreadPoolExecutor(6).map(get,['index.html','booking.html','owners-garage.html','owner-terms.html','robots.txt','sitemap.xml','booking.js']))
for n in ['index.html','booking.html','owners-garage.html']:(root/'originals'/n).write_bytes(raw[n])
index=raw['index.html'].decode()
a='Book online with secure payment. The rates below apply to our Elddis Avanté 866.'
assert a in index;index=index.replace(a,'The rates below apply to our Elddis Avanté 866. Contact us to confirm availability and arrange your booking while online checkout is unavailable.')
a='Check live availability and pricing.';assert a in index;index=index.replace(a,'Send your preferred dates so we can confirm availability and pricing.')
a='Enter your details and pay securely.';assert a in index;index=index.replace(a,'Confirm your hire arrangements and payment instructions with our team.')
a='Advertise your caravan, motorhome or campervan for £49 per vehicle per year. Upload photos, manage your listing and receive enquiries directly. No booking commission.';assert a in index
index=index.replace(a,'Our new owner booking plan is £49 per vehicle per year, plus a £25 admin fee per confirmed booking. Existing advertising agreements keep their recorded terms until the owner accepts the new plan. Contact us to discuss joining.')
booking=raw['booking.html'].decode()
a='Green dates are available. Pick your collection date and return date to see the exact hire price and payment schedule.';assert a in booking
booking=booking.replace(a,'Online checkout is currently unavailable. Contact our team with your collection and return dates to confirm availability, your hire price and payment arrangements.')
# Put the contact route above the calendar; its existing script also supplies the fallback.
marker='<div class="booking-layout">'
if marker not in booking:
 matches=re.findall(r'<[^>]+class="[^"]*booking[^>]+>',booking)
 print('BOOKING CLASSES',matches[:10])
# Preserve the published prices and insurance qualification unchanged.
owner=raw['owners-garage.html'].decode()
start=owner.index('<main class="garage-main">');end=owner.index('</main>',start)
body='''<main class="garage-main"><span class="eyebrow">OWNER’S GARAGE · NEW BOOKING PLAN</span><h1>£49 a year.<br><em>£25 per booking.</em></h1><p>Our new plan for independently owned caravans, motorhomes and campervans combines annual advertising with a small admin fee for each confirmed booking.</p><div class="garage-layout"><section class="garage-box"><h2>Clear, affordable fees.</h2><strong class="price">£49</strong><p>Per vehicle · 12 months from activation<br>Plus £25 per confirmed booking · No automatic renewal</p><p>Enquiries and temporary date holds do not incur the booking fee. The £25 comes from the owner’s £250 booking deposit, leaving £225 with the owner. It becomes due at the earlier of confirmed full-balance payment or 12 weeks before arrival.</p><a class="button" href="mailto:LakelandTouring@Worx365Group.uk?subject=New%20owner%20booking%20plan">Discuss joining the new plan →</a><p>The new booking service is being introduced. Contact us to discuss enrolment and the applicable terms; no payment or plan acceptance is taken on this page.</p></section><section class="garage-box"><h2>Your existing agreement stays yours.</h2><p>Existing owners keep their recorded advertising terms until they explicitly accept the new booking plan. The new £25 fee is not applied automatically to existing agreements.</p><p><a class="button" href="garage.php">Manage your existing garage →</a></p><p><a href="owner-terms.html">Existing advertising terms</a> · <a href="garage-privacy.html">Garage privacy notice</a></p><h3>How the new plan works</h3><p>Bookings are arranged and confirmed through Lakeland Touring. The independent owner receives the customer’s hire payments and confirms receipt. The £25 admin fee is an owner charge; it is not added to the customer’s hire price.</p><p>The owner remains responsible for the vehicle, accurate listing, hire agreement, maintenance, insurance and handover requirements. The new plan and hire terms must be agreed before a booking is confirmed.</p></section></div><h2>Speak to our team.</h2><p><a href="mailto:LakelandTouring@Worx365Group.uk">LakelandTouring@Worx365Group.uk</a> · <a href="tel:+441228307953">01228 307953</a></p></main>'''
owner=owner[:start]+body+owner[end+len('</main>'):]
desc='New owner booking plan: £49 per vehicle per year plus £25 per confirmed booking. Existing advertising agreements stay unchanged until you accept the new plan.'
for key in ['description','og:description','twitter:description']:
 owner=re.sub(r'(<meta (?:name|property)="'+key+r'" content=")[^"]*',lambda m:m[1]+desc,owner)
owner=re.sub(r'(<title>).*?(</title>)',r'\g<1>Owner Booking Plan — £49 Annual + £25 Per Booking | Lakeland Touring\g<2>',owner)
def schema(m):
 d=json.loads(m[1]);d['description']=desc;d['name']='Owner Booking Plan — £49 Annual + £25 Per Booking';return '<script type="application/ld+json">'+json.dumps(d)+'</script>'
owner=re.sub(r'<script type="application/ld\+json">(.*?)</script>',schema,owner,flags=re.S)
for key in ['og:title','twitter:title']:
 owner=re.sub(r'(<meta (?:name|property)="'+key+r'" content=")[^"]*',lambda m:m[1]+'Owner Booking Plan — £49 Annual + £25 Per Booking',owner)
files={'index.html':index,'booking.html':booking,'owners-garage.html':owner};manifest={'site':'touring','base_url':base,'remote_root':'/public','files':{},'robots_sha256':hashlib.sha256(raw['robots.txt']).hexdigest(),'guards':{n:hashlib.sha256(raw[n]).hexdigest() for n in ['sitemap.xml','owner-terms.html','booking.js']}}
for n,s in files.items():
 assert len(re.findall('<h1[\\s>]',s))==1 and 'noindex' not in s.lower()
 for payload in re.findall(r'<script type="application/ld\+json">(.*?)</script>',s,re.S):json.loads(payload)
 (root/'files'/n).write_text(s)
 manifest['files'][n]={'original_sha256':hashlib.sha256(raw[n]).hexdigest(),'updated_sha256':hashlib.sha256(s.encode()).hexdigest()}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2));print('Prepared three public-copy updates. No payment, calendar, legacy terms or account change.')
