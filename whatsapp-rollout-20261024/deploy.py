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
#worx365-whatsapp{position:fixed;top:calc(env(safe-area-inset-top,0px) + 136px);right:24px;z-index:900;display:inline-flex;align-items:center;justify-content:center;width:52px;height:52px;min-height:52px;padding:0;border:0;border-radius:0;background:transparent;color:#25D366;text-decoration:none;box-shadow:none;transition:transform .18s ease,filter .18s ease}
#worx365-whatsapp:hover{background:transparent;transform:translateY(-2px) scale(1.04);filter:drop-shadow(0 5px 12px rgba(26,210,113,.42))}#worx365-whatsapp:focus-visible{outline:3px solid rgba(255,255,255,.9);outline-offset:4px}
body #worx365-whatsapp{background:transparent!important;color:#25D366!important;border-color:transparent!important;box-shadow:none!important;-webkit-backdrop-filter:none!important;backdrop-filter:none!important}
body #worx365-whatsapp:hover{background:transparent!important;color:#25D366!important;border-color:transparent!important}
#worx365-whatsapp svg{display:block;width:48px;height:48px;flex-shrink:0;filter:drop-shadow(0 3px 8px rgba(3,26,20,.42));transition:filter .18s ease}
#worx365-whatsapp:hover svg{filter:drop-shadow(0 5px 10px rgba(26,210,113,.38))}
#worx365-whatsapp svg .wa-bubble{fill:url(#waGlass)!important;stroke:rgba(37,211,102,.96);stroke-width:.85}
#worx365-whatsapp svg .wa-phone{fill:#f8fffb!important}
#worx365-whatsapp svg .wa-reflection{fill:none;stroke:rgba(255,255,255,.64);stroke-width:.9;stroke-linecap:round;filter:drop-shadow(0 0 1px rgba(255,255,255,.42))}
#worx365-whatsapp span{display:none}
@media(max-width:760px){#worx365-whatsapp{top:calc(env(safe-area-inset-top,0px) + 124px);right:6%;width:48px;height:48px;min-height:48px}}
@media print{#worx365-whatsapp{display:none}}
</style>
<a id="worx365-whatsapp" href="HREF" target="_blank" rel="noopener noreferrer" aria-label="Message BRAND on WhatsApp">
<svg viewBox="0 0 48 48" role="img" aria-hidden="true"><defs><linearGradient id="waGlass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#25D366" stop-opacity=".52"/><stop offset=".48" stop-color="#25D366" stop-opacity=".4"/><stop offset="1" stop-color="#25D366" stop-opacity=".28"/></linearGradient></defs><path class="wa-bubble" d="M24 3.25a20.75 20.75 0 0 0-17.6 31.75L3.4 44.6l10.1-2.66A20.75 20.75 0 1 0 24 3.25z"/><path class="wa-phone" transform="translate(12 12)" d="M6.62 10.79a15.05 15.05 0 0 0 6.59 6.59l2.2-2.2a1 1 0 0 1 1.01-.24c1.12.37 2.33.57 3.58.57a1 1 0 0 1 1 1v3.5a1 1 0 0 1-1 1C10.61 21.01 2.99 13.39 2.99 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.46.57 3.58a1 1 0 0 1-.25 1.02L6.62 10.79z"/><path class="wa-reflection" d="M8 25c-2.3-7.8 1.6-16.1 8.9-19.8 5.3-2.7 11.6-2.3 16.5.8"/></svg>
<span>WhatsApp us</span></a>
<!-- worx365-whatsapp-end -->
'''.replace('HREF',html.escape(href,quote=True)).replace('BRAND',html.escape(brand,quote=True))
backup=Path('whatsapp-rollback');backup.mkdir(exist_ok=True)
parts=os.environ['SFTP_HOST_PUBLIC_KEY'].strip().split()
i=next(i for i,p in enumerate(parts) if p.startswith(('ssh-','ecdsa-')))
key=paramiko.PKey.from_type_string(parts[i],base64.b64decode(parts[i+1],validate=True))
t=paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25))
t.start_client(timeout=25)
assert t.get_remote_server_key().asbytes()==key.asbytes(),'SSH host identity mismatch'
t.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD'])
s=paramiko.SFTPClient.from_transport(t);s.get_channel().settimeout(45)
def rp(n): return str(PurePosixPath(root)/n)
def read(n):
 with s.open(rp(n),'rb') as f:return f.read()
def put(n,data):
 tmp=rp(n)+'.whatsapp-stage'
 with s.open(tmp,'wb') as f:f.write(data)
 s.chmod(tmp,0o644);s.posix_rename(tmp,rp(n))
def walk(folder='',depth=0):
 assert depth<=5,'Unexpected page depth'
 for a in s.listdir_attr(rp(folder)):
  if a.filename.startswith('.') or re.search(r'admin|backup|vendor|node_modules|private|upload|passport|certificate',a.filename,re.I):continue
  name=str(PurePosixPath(folder)/a.filename)
  if stat.S_ISDIR(a.st_mode):yield from walk(name,depth+1)
  elif stat.S_ISREG(a.st_mode) and name.endswith('.html') and a.st_size<2000000:yield name
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
  text=re.sub(r'<!-- worx365-whatsapp-start -->.*?<!-- worx365-whatsapp-end -->\s*','',text,flags=re.S)
  # Update existing WhatsApp anchors only; leave voice and other contact links intact.
  text=re.sub(r'https://wa\.me/\+?\d+(?:\?[^"\s<>]*)?',html.escape(href,quote=True),text)
  text=re.sub(r'https://api\.whatsapp\.com/send\?[^"\s<>]*',html.escape(href,quote=True),text)
  text=re.sub(r'</body\s*>',lambda m:block+'\n'+m.group(0),text,count=1,flags=re.I)
  assert text.count('id="worx365-whatsapp"')==1
  originals[name]=data;release[name]=text.encode('utf-8')
 assert 'index.html' in release,'No verified homepage'
 for name,data in originals.items():
  p=backup/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 Path('WHATSAPP-PLAN.json').write_text(json.dumps({'brand':brand,'number':'07383 660882','files':list(release)},indent=2))
 for name,data in release.items():
  assert read(name)==originals[name],'Concurrent live edit: '+name
  changed.append(name);put(name,data)
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
   put(name,originals[name]);assert read(name)==originals[name]
  except Exception:errors.append(name)
 if errors:print('ROLLBACK NEEDS ATTENTION:',errors,flush=True)
 raise
finally:
 s.close();t.close()
