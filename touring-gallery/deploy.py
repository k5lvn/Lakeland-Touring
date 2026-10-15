import base64,datetime,os,re,socket,ssl,hashlib
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
import paramiko
from build import build,PHOTOS
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
 p='/public/'+name;stage=p+'.gallery-stage'
 with s.open(stage,'wb') as f:f.set_pipelined(True);f.write(data)
 s.chmod(stage,0o644);s.posix_rename(stage,p)
originals={};changed=[]
try:
 robots=read('robots.txt');sitemap=read('sitemap.xml');assert robots and sitemap
 assert not re.search(rb'^\s*Disallow:\s*/\s*$',robots,re.M|re.I)
 raw=read('index.html');assert raw
 updates={f'Assets/touring-{n}.jpg':Path(f'site/Assets/touring-{n}.jpg').read_bytes() for n,_ in PHOTOS}
 updates.update({name:Path('touring-gallery/'+name).read_bytes() for name in ['gallery.css','gallery.js']})
 updates['index.html']=build(raw.decode()).encode()
 for name in updates:
  old=read(name);originals[name]=old
  if old is not None:
   p=Path('touring-gallery-rollback')/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old)
 for name,data in updates.items():
  if data==originals[name]:continue
  assert read(name)==originals[name]
  put(name,data);changed.append(name)
 for name,data in updates.items():
  url='https://lakelandtouring.uk/'+name+'?gallery-check='+datetime.datetime.now().strftime('%Y%m%d%H%M%S')
  try:r=urlopen(url,timeout=45)
  except URLError as e:
   if not isinstance(e.reason,ssl.SSLError):raise
   r=urlopen(url.replace('https://','http://',1),timeout=45)
  with r:assert r.status==200 and hashlib.sha256(r.read()).digest()==hashlib.sha256(data).digest(),name
  print('VERIFIED',name,flush=True)
 assert read('robots.txt')==robots and read('sitemap.xml')==sitemap
 print('Ten clean original photos and accessible full-screen gallery verified; existing HTTPS fault remains.')
except Exception:
 for name in reversed(changed):
  if originals[name] is None:s.remove('/public/'+name)
  else:put(name,originals[name])
 raise
finally:s.close();t.close()
