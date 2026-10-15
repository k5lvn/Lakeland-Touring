import base64,datetime,os,re,socket,ssl,hashlib
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
import paramiko
from build import build
parts=os.environ['SFTP_HOST_PUBLIC_KEY'].split()
if len(parts)==3:parts=parts[1:]
key=paramiko.PKey.from_type_string(parts[0],base64.b64decode(parts[1],validate=True))
t=paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25));t.start_client(timeout=25)
assert t.get_remote_server_key().asbytes()==key.asbytes()
t.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD']);s=paramiko.SFTPClient.from_transport(t);s.get_channel().settimeout(50)
def read(name):
 try:
  with s.open('/public/'+name,'rb') as f:return f.read()
 except FileNotFoundError:return None
def put(name,data):
 p='/public/'+name;stage=p+'.garage-stage'
 with s.open(stage,'wb') as f:f.set_pipelined(True);f.write(data)
 s.chmod(stage,0o644);s.posix_rename(stage,p)
originals={};changed=[]
try:
 index=read('index.html');booking=read('booking.html');robots=read('robots.txt');sitemap=read('sitemap.xml')
 assert index and booking and robots and sitemap
 assert not re.search(rb'^\s*Disallow:\s*/\s*$',robots,re.M|re.I)
 updates={name:data.encode() for name,data in build(index.decode(),booking.decode()).items()}
 assert not any(b'noindex' in d.lower() for n,d in updates.items() if n.endswith('.html'))
 # Keep the latest live source in the artifact for future maintenance.
 for name in updates:
  old=read(name);originals[name]=old
  if old is not None:
   p=Path('garage-rollback')/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old)
 for name,data in updates.items():
  if data==originals[name]:continue
  assert read(name)==originals[name]
  put(name,data);changed.append(name)
 for name in ['index.html','booking.html','owners-garage.html','owner-terms.html','garage-privacy.html','garage.css','robots.txt','sitemap.xml']:
  url='https://lakelandtouring.uk/'+name+'?garage-check='+datetime.datetime.now().strftime('%Y%m%d%H%M%S')
  try:r=urlopen(url,timeout=35)
  except URLError as e:
   if not isinstance(e.reason,ssl.SSLError):raise
   r=urlopen(url.replace('https://','http://',1),timeout=35)
  with r:assert r.status==200 and r.read()==updates[name],name
  print('VERIFIED',name,flush=True)
 # Check PHP execution and HTTPS gate without submitting credentials over HTTP.
 with urlopen('http://lakelandtouring.uk/garage.php',timeout=35) as r:
  result=r.read();assert b'Owner registration is temporarily unavailable' in result and b'<?php' not in result
 print('VERIFIED PHP execution and HTTP registration lock; HTTPS activation remains blocked by existing certificate fault.',flush=True)
 Path('garage-published').mkdir(exist_ok=True)
 for name,data in updates.items():Path('garage-published/'+name).write_bytes(data)
except Exception:
 for name in reversed(changed):
  if originals[name] is None:s.remove('/public/'+name)
  else:put(name,originals[name])
 raise
finally:s.close();t.close()
