import base64,datetime,os,re,socket,ssl
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
import paramiko
OLD='Assets/derwentwater-panorama.jpg';NEW='Assets/buttermere-4k.jpg'
CREDIT='''<p class="landscape-credit">Lake District photography: <a href="https://www.pexels.com/photo/calm-lake-amidst-green-hills-7244501/">Buttermere by Olga Lioncat / Pexels</a>. Displayed with a responsive crop and dark overlay.</p>'''
CSS='''\n/* Rich 4K landscape: preserve colour across the view and shade only the copy. */
.hero .hero-landscape{object-position:60% 52%;filter:none;opacity:1}
.hero:before{background:linear-gradient(90deg,#061216c9 0%,#06121670 38%,#0612160d 78%)}
.destination,.final-cta{background-image:linear-gradient(90deg,#071216c4,#07121630),url('Assets/buttermere-4k.jpg');background-position:center 56%}
@media(max-width:950px){.hero:before{background:linear-gradient(90deg,#061216bd,#06121624),linear-gradient(0deg,#06121644,transparent 70%)}}
@media(max-width:560px){.hero .hero-landscape{object-position:52% center}.destination,.final-cta{background-position:52% center}}
'''
parts=os.environ['SFTP_HOST_PUBLIC_KEY'].split()
if len(parts)==3:parts=parts[1:]
k=paramiko.PKey.from_type_string(parts[0],base64.b64decode(parts[1],validate=True))
t=paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25));t.start_client(timeout=25)
assert t.get_remote_server_key().asbytes()==k.asbytes()
t.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD']);s=paramiko.SFTPClient.from_transport(t);s.get_channel().settimeout(50)
def read(name):
 try:
  with s.open('/public/'+name,'rb') as f:return f.read()
 except FileNotFoundError:return None
def put(name,data):
 p='/public/'+name;stage=p+'.image-stage'
 with s.open(stage,'wb') as f:f.set_pipelined(True);f.write(data)
 s.chmod(stage,0o644);s.posix_rename(stage,p)
originals={};changed=[]
try:
 updates={NEW:Path('touring-images/buttermere-4k.jpg').read_bytes()}
 for name in ['index.html','booking.html','brand.css']:
  old=read(name);assert old;raw=old.decode()
  if name=='index.html':
   assert OLD in raw
   raw=raw.replace(OLD,NEW).replace('Derwentwater and the Lake District fells seen from Catbells','Buttermere and the surrounding Lake District fells').replace('width="3840" height="924"','width="4096" height="2731"')
   raw,n=re.subn(r'<p class="landscape-credit">.*?</p>',CREDIT,raw,count=1,flags=re.S);assert n==1
  if name.endswith('.html'):
   raw=raw.replace('brand.css?v=20261015-1','brand.css?v=20261015-4k2')
   assert 'noindex' not in raw.lower()
  else:
   assert OLD in raw
   raw=raw.replace(OLD,NEW)+CSS
  updates[name]=raw.encode();originals[name]=old
 originals[NEW]=read(NEW)
 for name,old in originals.items():
  if old is not None:
   p=Path('touring-images-rollback')/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old)
 for name,data in updates.items():
  assert read(name)==originals[name]
  put(name,data);changed.append(name)
 for name,data in updates.items():
  url='https://lakelandtouring.uk/'+name+'?image-check='+datetime.datetime.now().strftime('%Y%m%d%H%M%S')
  try:r=urlopen(url,timeout=45)
  except URLError as e:
   if not isinstance(e.reason,ssl.SSLError):raise
   r=urlopen(url.replace('https://','http://',1),timeout=45)
  with r:assert r.status==200 and r.read()==data,name
  print('VERIFIED',name,flush=True)
 print('4096px Buttermere photograph and reduced overlays published; existing HTTPS fault remains.')
except Exception:
 for name in reversed(changed):
  if originals[name] is None:s.remove('/public/'+name)
  else:put(name,originals[name])
 raise
finally:s.close();t.close()
