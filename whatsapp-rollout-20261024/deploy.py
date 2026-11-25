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
#worx365-whatsapp{position:fixed;top:calc(env(safe-area-inset-top,0px) + 136px);right:24px;z-index:900;display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;min-height:44px;padding:0;border:0;border-radius:0;background:transparent;color:#25D366;text-decoration:none;box-shadow:none;transition:transform .18s ease}
#worx365-whatsapp:hover{background:transparent;transform:scale(1.04)}#worx365-whatsapp:focus-visible{outline:3px solid #111;outline-offset:4px}
body #worx365-whatsapp{background:transparent!important;color:#25D366!important;border-color:transparent!important;box-shadow:none!important}
body #worx365-whatsapp:hover{background:transparent!important;color:#25D366!important;border-color:transparent!important}
#worx365-whatsapp svg{width:44px;height:44px;flex-shrink:0}#worx365-whatsapp span{display:none}
@media(max-width:760px){#worx365-whatsapp{top:calc(env(safe-area-inset-top,0px) + 124px);right:6%;width:44px;height:44px;min-height:44px}}
@media print{#worx365-whatsapp{display:none}}
</style>
<a id="worx365-whatsapp" href="HREF" target="_blank" rel="noopener noreferrer" aria-label="Message BRAND on WhatsApp">
<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#25D366" d="M12 1.5a10.3 10.3 0 0 0-8.9 15.5L2 22l5.2-1.4A10.5 10.5 0 1 0 12 1.5Zm0 18.9a8.4 8.4 0 0 1-4.3-1.2l-.3-.2-3.1.8.8-3-.2-.3A8.3 8.3 0 1 1 12 20.4Z"/><path fill="#fff" d="M8.2 6.8c-.3-.6-.6-.6-.9-.6h-.7c-.2 0-.6.1-.9.5-.3.3-1.2 1.2-1.2 2.8s1.2 3.2 1.4 3.4c.2.2 2.4 3.8 5.9 5.2 2.9 1.2 3.5 1 4.1.9.6-.1 1.9-.8 2.1-1.5.3-.7.3-1.3.2-1.5-.1-.1-.3-.2-.7-.4l-2.1-1c-.3-.1-.5-.2-.7.2-.2.3-.8 1-1-1-.2-.2-.4-.2-.7-.1-.3.2-1.1.7-1.3.9-.2.2-.4.2-.7.1-.3-.1-1.4-.5-2.6-1.6-1-.9-1.6-2-1.8-2.3-.2-.3 0-.5.1-.6l.5-.6.3-.5c.1-.2 0-.4 0-.6l-1-2.3Z"/></svg>
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
