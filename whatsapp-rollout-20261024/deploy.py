import base64, hashlib, html, json, os, re, socket, stat, time, urllib.parse, urllib.request
from pathlib import Path, PurePosixPath
import paramiko
CONFIG = {
 'Digital-Kinetics': ('Digital Kinetics','/public','https://www.digitalkinetics.uk/'),
 'Lakeland-Developments': ('Lakeland Developments','/','https://www.lakelanddevelopments.uk/'),
 'Lakeland-Touring': ('Lakeland Touring','/public','https://lakelandtouring.uk/'),
 'Worx365Group': ('Worx365 Group','/public','https://worx365group.uk/'),
 'CrankHub': ('CrankHub','.','https://crankhub.uk/')
}
brand, root, base = CONFIG[os.environ['GITHUB_REPOSITORY'].split('/')[1]]
href = 'https://wa.me/447383660882?text=' + urllib.parse.quote('Hi '+brand+', I have an enquiry from your website. ')
block = '''
<!-- worx365-whatsapp-start -->
<style id="worx365-whatsapp-style">
#worx365-whatsapp{position:relative;z-index:900;display:inline-flex;align-items:center;justify-content:center;width:52px;height:52px;min-height:52px;padding:0;border:0;border-radius:0;background:transparent;color:#25D366;text-decoration:none;box-shadow:none;transition:transform .18s ease,filter .18s ease}
#worx365-whatsapp:hover{background:transparent;transform:translateY(-2px);filter:drop-shadow(0 4px 8px rgba(26,210,113,.22))}
#worx365-whatsapp::before {
  content: "";
  position: absolute;
  width: 48px;
  height: 48px;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  -webkit-clip-path: path("M24 3.25a20.75 20.75 0 0 0-17.6 31.75L3.4 44.6l10.1-2.66A20.75 20.75 0 1 0 24 3.25z");
  clip-path: path("M24 3.25a20.75 20.75 0 0 0-17.6 31.75L3.4 44.6l10.1-2.66A20.75 20.75 0 1 0 24 3.25z");
}
@supports ((clip-path: path("M24 3.25a20.75 20.75 0 0 0-17.6 31.75L3.4 44.6l10.1-2.66A20.75 20.75 0 1 0 24 3.25z")) or (-webkit-clip-path: path("M24 3.25a20.75 20.75 0 0 0-17.6 31.75L3.4 44.6l10.1-2.66A20.75 20.75 0 1 0 24 3.25z"))) {
  #worx365-whatsapp::before {
    -webkit-backdrop-filter: blur(1.6px) saturate(145%);
    backdrop-filter: blur(1.6px) saturate(145%);
  }
}
#worx365-whatsapp:focus-visible{outline:3px solid rgba(255,255,255,.9);outline-offset:4px}
body #worx365-whatsapp{background:transparent!important;color:#25D366!important;border-color:transparent!important;box-shadow:none!important;-webkit-backdrop-filter:none!important;backdrop-filter:none!important}
body #worx365-whatsapp:hover{background:transparent!important;color:#25D366!important;border-color:transparent!important}
#worx365-whatsapp svg{position:relative;z-index:1;display:block;width:48px;height:48px;flex-shrink:0;filter:drop-shadow(0 2px 4px rgba(3,26,20,.24));transition:filter .18s ease}
#worx365-whatsapp:hover svg{filter:drop-shadow(0 5px 10px rgba(26,210,113,.38))}
#worx365-whatsapp svg .wa-bubble{fill:url(#waGlass)!important;stroke:#41eb8b;stroke-opacity:.56;stroke-width:.9}
#worx365-whatsapp svg .wa-phone{fill:#fff!important;filter:drop-shadow(0 1px 1px rgba(0,55,28,.7))}
#worx365-whatsapp svg .wa-reflection{display:none}
#worx365-whatsapp span{display:none}
@media(max-width:760px){#worx365-whatsapp{width:48px;height:48px;min-height:48px}}
@media print{#worx365-whatsapp{display:none}}
#w365-contact-rail{position:fixed;inset:auto;top:var(--rail-top,88px);right:var(--rail-right,14px);display:flex;align-items:center;flex-direction:column;gap:2px;z-index:900;background:transparent}
#w365-contact-rail[hidden]{display:none}
#w365-contact-rail #worx365-whatsapp{position:relative!important;inset:auto!important;margin:0!important}
#w365-contact-rail .glass-social{display:grid;place-items:center;position:relative;width:46px;height:46px;padding:0;margin:0;color:white;background:none;border:0;box-shadow:none}
#w365-contact-rail .glass-social::before{content:"";position:absolute;inset:4px;border-radius:24%;background:var(--social-tint);-webkit-backdrop-filter:blur(1.6px) saturate(145%);backdrop-filter:blur(1.6px) saturate(145%);box-shadow:inset 0 0 0 1px #ffffff59,0 2px 4px #00132536}
#w365-contact-rail .facebook{--social-tint:linear-gradient(145deg,#2784ffad,#165ac78a)}
#w365-contact-rail .instagram{--social-tint:linear-gradient(145deg,#8248c4b8,#bf357ca6 55%,#e38c45ac)}
#w365-contact-rail .glass-social svg{display:block;width:27px;height:27px;position:relative;color:#fff}
#w365-contact-rail .glass-social:focus-visible{outline:2px solid white;outline-offset:2px}
@media print{#w365-contact-rail{display:none}}
</style>
<div id="w365-contact-rail" role="group" aria-label="Contact BRAND">
<a id="worx365-whatsapp" href="HREF" target="_blank" rel="noopener noreferrer" aria-label="Message BRAND on WhatsApp">
<svg viewBox="0 0 48 48" role="img" aria-hidden="true"><defs><linearGradient id="waGlass" x1="0%" y1="0%" x2="70%" y2="100%"><stop offset="0" stop-color="#25D366" stop-opacity=".64"/><stop offset=".45" stop-color="#25D366" stop-opacity=".39"/><stop offset="1" stop-color="#08763f" stop-opacity=".60"/></linearGradient></defs><path class="wa-bubble" d="M24 3.25a20.75 20.75 0 0 0-17.6 31.75L3.4 44.6l10.1-2.66A20.75 20.75 0 1 0 24 3.25z"/><path class="wa-phone" transform="translate(12 12)" d="M6.62 10.79a15.05 15.05 0 0 0 6.59 6.59l2.2-2.2a1 1 0 0 1 1.01-.24c1.12.37 2.33.57 3.58.57a1 1 0 0 1 1 1v3.5a1 1 0 0 1-1 1C10.61 21.01 2.99 13.39 2.99 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.46.57 3.58a1 1 0 0 1-.25 1.02L6.62 10.79z"/><path class="wa-reflection" d="M8 25c-2.3-7.8 1.6-16.1 8.9-19.8 5.3-2.7 11.6-2.3 16.5.8"/></svg>
<span>WhatsApp us</span></a>
<a class="glass-social facebook" href="https://www.facebook.com/61595660185063/" target="_blank" rel="noopener noreferrer" aria-label="Visit BRAND on Facebook"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M14 21v-8h3l.5-3H14V8c0-.9.3-1.5 1.7-1.5H18V3.2c-.4-.1-1.8-.2-3-.2-3 0-5 1.8-5 5v2H7v3h3v8z"/></svg></a>
</div>
<script>
(() => {
  const rail = document.getElementById("w365-contact-rail");
  const header = document.querySelector("header, [role=banner]");
  const controls = [...document.querySelectorAll('.lt-menu,.hamburger,.menu-toggle,.menu-btn,.nav-toggle,button[aria-label*="menu" i],button[aria-controls*="nav" i]')];
  let pending = false;
  function place() {
    pending = false;
    const menu = controls.find(el => el.getBoundingClientRect().width && el.getBoundingClientRect().height);
    const box = menu?.getBoundingClientRect();
    const top = box ? box.bottom : header?.getBoundingClientRect().bottom;
    const width = document.documentElement.clientWidth;
    const buttonSize = matchMedia("(max-width:760px)").matches ? 48 : 52;
    rail.hidden = menu?.getAttribute("aria-expanded") === "true";
    rail.style.setProperty("--rail-top", Math.max(8, Math.round((top ?? 72) + 6)) + "px");
    rail.style.setProperty("--rail-right", (box ? Math.max(4, Math.min(width-buttonSize-4, Math.round(width-box.left-box.width/2-buttonSize/2))) : 14) + "px");
  }
  function schedule() { if (!pending) { pending = true; requestAnimationFrame(place); } }
  place();
  addEventListener("resize", schedule, {passive:true});
  addEventListener("scroll", schedule, {passive:true});
  addEventListener("load", schedule, {once:true});
  if (header && "ResizeObserver" in window) new ResizeObserver(schedule).observe(header);
  const changes = new MutationObserver(schedule);
  for (const menu of controls) changes.observe(menu,{attributes:true,attributeFilter:["aria-expanded","class","hidden"]});
})();
</script>
<!-- worx365-whatsapp-end -->
'''.replace('HREF',html.escape(href,quote=True)).replace('BRAND',html.escape(brand,quote=True))
backup=Path('whatsapp-rollback');backup.mkdir(exist_ok=True)
parts=os.environ['SFTP_HOST_PUBLIC_KEY'].strip().split()
i=next(i for i,p in enumerate(parts) if p.startswith(('ssh-','ecdsa-')))
key=paramiko.PKey.from_type_string(parts[i],base64.b64decode(parts[i+1],validate=True))
s = t = None
opened = 0
def connect():
 global s, t, opened
 if t is not None:
  t.close()
 t = paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25))
 t.start_client(timeout=25)
 assert t.get_remote_server_key().asbytes()==key.asbytes(),'SSH host identity mismatch'
 t.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD'])
 t.set_keepalive(12)
 s=paramiko.SFTPClient.from_transport(t)
 s.get_channel().settimeout(45)
 opened=time.monotonic()
def with_session(operation):
 for attempt in range(3):
  try:
   if t is None or not t.is_active() or time.monotonic()-opened>45:
    connect()
   return operation()
  except (EOFError, ConnectionError, socket.timeout, paramiko.SSHException) as exc:
   if attempt==2 or isinstance(exc,paramiko.AuthenticationException):
    raise
   if t is not None:t.close()
   time.sleep(attempt+1)
def rp(n): return str(PurePosixPath(root)/n)
def read(n):
 def get():
  with s.open(rp(n),'rb') as f:return f.read()
 return with_session(get)
def put(n,data,expected):
 def replace():
  with s.open(rp(n),'rb') as f: current=f.read()
  if current==data:return
  assert current==expected,'Concurrent live edit: '+n
  tmp=rp(n)+'.whatsapp-stage'
  with s.open(tmp,'wb') as f:f.write(data)
  s.chmod(tmp,0o644)
  s.posix_rename(tmp,rp(n))
 return with_session(replace)
def walk(folder='',depth=0):
 assert depth<=5,'Unexpected page depth'
 for a in with_session(lambda:s.listdir_attr(rp(folder))):
  if a.filename.startswith('.') or re.search(r'admin|backup|vendor|node_modules|private|upload|passport|certificate',a.filename,re.I):continue
  name=str(PurePosixPath(folder)/a.filename)
  if stat.S_ISDIR(a.st_mode):yield from walk(name,depth+1)
  elif stat.S_ISREG(a.st_mode) and name.endswith('.html') and a.st_size<2000000:yield name

from html.parser import HTMLParser

ACTION_OUTLINES = '''<style id="lt-action-outlines">
html body :is(.lt-button, .w365-review .w365-review-action a, #w365-review .w365-review-button, .page-reviews .btn, .lt-cta, a.btn-primary, a.btn-secondary) {
  background: transparent !important;
  border: 1.5px solid #65c7bb !important;
  color: inherit !important;
  box-shadow: none !important;
}
html body :is(.lt-button,.w365-review-action a,.page-reviews .btn,.lt-cta,a.btn-primary,a.btn-secondary):hover {
  text-decoration: underline;
  text-underline-offset: .22em;
}
html body :is(.lt-button,.w365-review-action a,.page-reviews .btn,.lt-cta,a.btn-primary,a.btn-secondary):focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 3px;
}
</style>'''

# Preserve page markup and URLs; edit only user-facing control labels.
ARROW = re.compile(r'[ \t\u00a0]*(?:[↗→←↖➜➝➞➔]|&(?:nearr|nearrow|rarr|rightarrow|larr|leftarrow);|&#(?:x(?:219[0279]|279[cd4e])|859[24]|8599|1014[24]);)[\ufe0e\ufe0f]?', re.I)
LABEL_ATTR = re.compile(r'''(\b(?:aria-label|title)\s*=\s*)(["'])(.*?)\2''', re.I|re.S)

class ButtonLabels(HTMLParser):
 def __init__(self, page):
  super().__init__(convert_charrefs=False)
  self.page = page
  self.lines = [0] + [match.end() for match in re.finditer('\n', page)]
  self.controls = []
  self.changes = []
 def source_offset(self):
  row, column = self.getpos()
  return self.lines[row-1] + column
 def handle_starttag(self, tag, attrs):
  if tag not in ('a','button'):return
  start = self.source_offset()
  self.controls.append((tag,start,self.get_starttag_text(),dict(attrs)))
 def handle_endtag(self, tag):
  if not self.controls or self.controls[-1][0] != tag:return
  _,start,opening,attrs = self.controls.pop()
  stop = self.source_offset()
  inner = self.page[start+len(opening):stop]
  if not ARROW.search(inner+opening):return
  def strip_attr(match):
   return match[1]+match[2]+ARROW.sub('',match[3]).strip()+match[2]
  new_opening = LABEL_ATTR.sub(strip_attr,opening)
  # Split markup from text so SVG paths and non-label attributes stay intact.
  pieces = re.split(r'(<!--.*?-->|<[^>]+>)',inner,flags=re.S)
  cleaned = ''.join(bit if i%2 else ARROW.sub('',bit) for i,bit in enumerate(pieces))
  if ARROW.search(inner) and not html.unescape(re.sub(r'<[^>]*>','',cleaned)).strip() and '<svg' not in cleaned and '<img' not in cleaned:
   label = ARROW.sub('',attrs.get('aria-label','') or attrs.get('title','')).strip()
   if not label:label = 'Previous' if '←' in html.unescape(inner) else 'Continue'
   cleaned = html.escape(label)
  updated = new_opening+cleaned
  if updated!=opening+inner:self.changes.append((start,stop,updated))

def remove_button_arrows(page):
 parser=ButtonLabels(page)
 parser.feed(page)
 parser.close()
 for start,stop,value in reversed(parser.changes):
  page=page[:start]+value+page[stop:]
 return page,len(parser.changes)


# Use the same artwork and glass styling in both contact placements.
def footer_contacts():
 css = block.split('<style id="worx365-whatsapp-style">',1)[1].split('</style>',1)[0]
 wa_css = css.split('#w365-contact-rail{',1)[0].replace('#worx365-whatsapp','#lt-footer-whatsapp').replace('waGlass','waFooterGlass')
 fb_css = css[css.index('#w365-contact-rail .glass-social{'):css.index('@media print{#w365-contact-rail')].replace('#w365-contact-rail','#lt-footer-social')
 anchors = block.split('<div id="w365-contact-rail"',1)[1].split('>\n',1)[1].split('</div>',1)[0]
 anchors = anchors.replace('id="worx365-whatsapp"','id="lt-footer-whatsapp"').replace('waGlass','waFooterGlass')
 return ('<!-- worx365-socials-start -->\n<style>'+wa_css+fb_css+
  '\n#lt-footer-social{display:flex;align-items:center;justify-content:center;gap:6px;padding:18px 0;margin:12px auto 0}'
  '\n#lt-footer-social a{flex:none} #lt-footer-whatsapp{position:relative!important;inset:auto!important}'
  '\n@media print{#lt-footer-social{display:none}}</style>\n'
  '<nav id="lt-footer-social" aria-label="Lakeland Touring social links">'+anchors+'</nav>\n<!-- worx365-socials-end -->')

FOOTER_SOCIAL = footer_contacts()
SOCIAL_BLOCK = re.compile(r'<!-- worx365-socials-start -->.*?<!-- worx365-socials-end -->', re.S)
REVIEW_BLOCK = re.compile(r'<section\b(?=[^>]*\bclass=["\']w365-review["\'])[^>]*>.*?</section>',re.I|re.S)
REVIEW_STYLE = '''<style id="lt-review-layout">
html body #lt-google-review{display:grid!important;grid-template-columns:auto minmax(0,1fr);align-items:center;gap:clamp(15px,3vw,32px);max-width:840px;margin:32px auto;padding:clamp(20px,4vw,38px);border:1px solid #375d5a;border-radius:14px;background:#14292b;color:#edf5ef;text-align:left;box-sizing:border-box}
#lt-google-review h2{margin:0 0 7px;font-size:clamp(1.35rem,3vw,2rem);line-height:1.15}
#lt-google-review p{max-width:56ch;margin:0;line-height:1.55}
#lt-google-review .lt-review-links{display:flex;flex-wrap:wrap;align-items:center;gap:0 22px;margin-top:6px}
html body #lt-google-review a.lt-review-text{display:inline-flex!important;align-items:center;min-height:44px;background:none!important;border:0!important;border-radius:0!important;box-shadow:none!important;padding:0!important;color:#a2e1d8!important;text-decoration:underline;text-underline-offset:.22em;font:inherit;font-weight:600}
html body #lt-google-review a.lt-review-g{display:grid!important;place-items:center;box-sizing:border-box;width:58px;height:58px;min-width:58px;padding:12px!important;background:#fff!important;border:0!important;border-radius:50%!important;box-shadow:none!important}
#lt-google-review .lt-review-g img{display:block;width:34px;height:34px;object-fit:contain;background:transparent;border:0;padding:0}
#lt-google-review a:focus-visible{outline:2px solid #baf9ec;outline-offset:4px}
@media(max-width:620px){html body #lt-google-review{margin:24px 16px;padding:18px;align-items:start;gap:14px}#lt-google-review .lt-review-links{gap:0 16px}}
@media(max-width:380px){html body #lt-google-review{grid-template-columns:1fr}}
</style>'''

class ReviewTargets(HTMLParser):
 def __init__(self):
  super().__init__()
  self.read_url = self.write_url = self.logo = None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  href=a.get('href','')
  if tag=='a' and href.rstrip('/')=='/reviews':self.read_url=href
  if tag=='a' and href.startswith('https://g.page/'):self.write_url=href
  if tag=='img' and 'google-g-official' in a.get('src',''):self.logo=a['src']

def tidy_review(match):
 card = match.group()
 target=ReviewTargets()
 target.feed(card)
 assert target.write_url and target.logo,'Unrecognised Google review target'
 dest=html.escape(target.write_url,quote=True)
 read=html.escape(target.read_url or '/reviews/',quote=True)
 logo=html.escape(target.logo,quote=True)
 heading=re.search(r'<h2\b[^>]*>.*?</h2>',card,re.S).group()
 description=re.search(r'<p\b[^>]*>.*?</p>',card,re.S).group()
 return ('<section id="lt-google-review" class="w365-review" aria-labelledby="w365-review-title">'
  '<a class="lt-review-g" href="'+dest+'" target="_blank" rel="noopener noreferrer" aria-label="Write a Lakeland Touring review on Google"><img loading="lazy" alt="" src="'+logo+'" width="34" height="34"></a>'
  '<div>'+heading+description+'<div class="lt-review-links"><a class="lt-review-text" href="'+read+'">Read our Google reviews</a>'
  '<a class="lt-review-text" href="'+dest+'" target="_blank" rel="noopener noreferrer">Leave a Google review</a></div></div></section>')

def tidy_footer(page):
 page=REVIEW_BLOCK.sub(tidy_review,page)
 if SOCIAL_BLOCK.search(page):
  page=SOCIAL_BLOCK.sub(lambda _:FOOTER_SOCIAL,page,count=1)
 elif '</footer>' in page.lower():
  page=re.sub(r'</footer>',lambda m:FOOTER_SOCIAL+m[0],page,count=1,flags=re.I)
 page=re.sub(r'<style id="lt-review-layout">.*?</style>','',page,flags=re.S)
 if 'id="lt-google-review"' in page:
  page=re.sub(r'</head\s*>',lambda m:REVIEW_STYLE+m[0],page,count=1,flags=re.I)
 return page

originals={};release={};changed=[];results=[]
try:
 for name in walk():
  data=read(name)
  try: text=data.decode('utf-8')
  except UnicodeDecodeError:continue
  if not re.search(r'</body\s*>',text,re.I):continue
  # Verify each target is publicly served and matches before editing.
  url=base+urllib.parse.quote(name)
  try:
   with urllib.request.urlopen(url+'?wa-baseline='+str(time.time_ns()),timeout=40) as r: public=r.read()
  except Exception:
   if name=='index.html':raise
   continue
  if public!=data:
   if name=='index.html':raise RuntimeError('Homepage public source differs')
   continue
  text=re.sub(r'\n?<!-- worx365-whatsapp-start -->.*?<!-- worx365-whatsapp-end -->\s*','',text,flags=re.S)
  text=re.sub(r'</body\s*>',lambda m:block+'\n'+m.group(0),text,count=1,flags=re.I)
  assert text.count('id="worx365-whatsapp"')==1
  text=re.sub(r'<style id="lt-action-outlines">.*?</style>','',text,flags=re.S)
  text=re.sub(r'</head\s*>',lambda m:ACTION_OUTLINES+m[0],text,count=1,flags=re.I)
  text = tidy_footer(text)
  text, count = remove_button_arrows(text)
  if count:print('Touring control labels updated:',name,count,flush=True)
  originals[name]=data;release[name]=text.encode('utf-8')
 assert 'index.html' in release,'No verified homepage'
 for name,data in originals.items():
  p=backup/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 Path('WHATSAPP-PLAN.json').write_text(json.dumps({'brand':brand,'number':'07383 660882','files':list(release)},indent=2))
 for name,data in release.items():
  assert read(name)==originals[name],'Concurrent live edit: '+name
  if data==originals[name]:continue
  changed.append(name);put(name,data,originals[name])
  assert read(name)==data,'SFTP verification failed'
 for name,data in release.items():
  url=base+urllib.parse.quote(name)
  with urllib.request.urlopen(url+'?wa-verify='+str(time.time_ns()),timeout=45) as r:actual=r.read()
  assert actual==data,'Public verification failed: '+name
  results.append({'url':url,'sha256':hashlib.sha256(actual).hexdigest()})
  print('LIVE VERIFIED:',url,flush=True)
 Path('WHATSAPP-VERIFIED.json').write_text(json.dumps({'brand':brand,'number':'447383660882','status':'verified','files':results},indent=2))
except BaseException:
 errors=[]
 for name in reversed(changed):
  try:
   put(name,originals[name],release[name]);assert read(name)==originals[name]
  except Exception:errors.append(name)
 if errors:print('ROLLBACK NEEDS ATTENTION:',errors,flush=True)
 raise
finally:
 if t is not None:t.close()
