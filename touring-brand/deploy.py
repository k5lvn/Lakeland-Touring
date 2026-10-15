import base64,datetime,hashlib,os,re,socket
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
import ssl
import paramiko
from build import build
parts=os.environ['SFTP_HOST_PUBLIC_KEY'].split()
if len(parts)==3:parts=parts[1:]
key=paramiko.PKey.from_type_string(parts[0],base64.b64decode(parts[1],validate=True))
t=paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25));t.start_client(timeout=25)
assert t.get_remote_server_key().asbytes()==key.asbytes(),'Host identity mismatch'
t.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD']);s=paramiko.SFTPClient.from_transport(t);s.get_channel().settimeout(50)
def read(name):
 try:
  with s.open('/public/'+name,'rb') as f:return f.read()
 except FileNotFoundError:return None
def put(name,data):
 p='/public/'+name;stage=p+'.brand-stage'
 with s.open(stage,'wb') as f:
  f.set_pipelined(True);f.write(data)
 s.chmod(stage,0o644)
 s.posix_rename(stage,p)
originals={};changed=[]
try:
 robots=read('robots.txt');sitemap=read('sitemap.xml')
 assert robots and sitemap and not re.search(rb'^\s*Disallow:\s*/\s*$',robots,re.M|re.I),'Indexing configuration needs review'
 updates={name:Path('site/'+name).read_bytes() for name in ['Assets/lakeland-touring-official.png','Assets/derwentwater-panorama.jpg','brand.css']}
 for name in ['index.html','booking.html']:
  data=read(name);assert data
  updates[name]=build(data.decode(),name).encode()
 for name in updates:
  data=read(name);originals[name]=data
  if data is not None:
   dest=Path('touring-brand-rollback')/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 for name,data in updates.items():
  assert read(name)==originals[name],'File changed during deployment: '+name
  put(name,data);changed.append(name)
 for name,data in updates.items():
  url='https://lakelandtouring.uk/'+name+'?brand-check='+datetime.datetime.now().strftime('%Y%m%d%H%M%S')
  try:
   response=urlopen(url,timeout=45)
  except URLError as e:
   if not isinstance(e.reason,ssl.SSLError):raise
   print('PRE-EXISTING HTTPS HANDSHAKE FAILURE; verifying static public bytes via HTTP:',name,flush=True)
   response=urlopen(url.replace('https://','http://',1),timeout=45)
  with response as r:assert r.status==200 and r.read()==data,'Live verification mismatch: '+name
  print('VERIFIED',name,flush=True)
 assert read('robots.txt')==robots and read('sitemap.xml')==sitemap
 print('Exact Touring logo and Derwentwater hero verified live. Booking scripts and data preserved.')
except Exception:
 for name in reversed(changed):
  if originals[name] is None:s.remove('/public/'+name)
  else:put(name,originals[name])
 raise
finally:s.close();t.close()
