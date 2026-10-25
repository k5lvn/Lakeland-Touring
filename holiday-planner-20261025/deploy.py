"""Publish the exact audited release with pinned host, baseline guards and rollback."""
import base64,hashlib,json,os,re,socket,time,urllib.request
from pathlib import Path
import paramiko
R=Path('holiday-planner-20261025');M=json.loads((R/'manifest.json').read_text());B=Path('holiday-planner-rollback');B.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
parts=os.environ['SFTP_HOST_PUBLIC_KEY'].strip().split();i=next(i for i,p in enumerate(parts) if p.startswith(('ssh-','ecdsa-')));key=paramiko.PKey.from_type_string(parts[i],base64.b64decode(parts[i+1],validate=True))
t=paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25));t.start_client(timeout=25);assert t.get_remote_server_key().asbytes()==key.asbytes(),'SSH identity mismatch';t.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD']);s=paramiko.SFTPClient.from_transport(t);s.get_channel().settimeout(45)
def read(n):
 try:
  with s.open('/public/'+n,'rb') as f:return f.read()
 except FileNotFoundError:return None
def put(n,b):
 tmp='/public/'+n+'.upgrade-stage'
 with s.open(tmp,'wb') as f:f.write(b)
 s.chmod(tmp,0o644);s.posix_rename(tmp,'/public/'+n)
originals={};changed=[]
try:
 robots=read('robots.txt');assert robots and not re.search(rb'^\s*Disallow:\s*/\s*$',robots,re.M|re.I)
 lock=read('api/booking-disabled.php');assert lock is not None,'Booking lock missing'
 for n,v in M['files'].items():
  b=read(n);originals[n]=b
  assert (sha(b) if b is not None else None)==v['original_sha256'],'Concurrent edit: '+n
  assert sha((R/'files'/n).read_bytes())==v['updated_sha256']
  if b is not None:(B/n).write_bytes(b)
 # Complete preflight before any live replacement.
 for n in M['files']:assert read(n)==originals[n],'Live content changed: '+n
 for n in M['files']:
  changed.append(n);put(n,(R/'files'/n).read_bytes());assert read(n)==(R/'files'/n).read_bytes()
 verified=[]
 for n in M['files']:
  url=M['base_url']+('' if n=='index.html' else n)
  if n.endswith('.php'):
   assert sha(read(n))==M['files'][n]['updated_sha256'];continue
  request=urllib.request.Request(url+'?touring-upgrade='+str(time.time_ns()),headers={'Cache-Control':'no-cache'})
  with urllib.request.urlopen(request,timeout=45) as r:b=r.read();assert r.status==200
  assert sha(b)==M['files'][n]['updated_sha256'],'Public bytes differ: '+n
  verified.append({'url':url,'sha256':sha(b)});print('LIVE VERIFIED:',url,flush=True)
 assert read('robots.txt')==robots;assert read('api/booking-disabled.php')==lock
 with urllib.request.urlopen(M['base_url']+'holiday-weather.php?area=braithwaite',timeout=40) as response:weather=json.load(response)
 assert weather.get('hours') and weather.get('updated_at') and not weather.get('stale'),'Live forecast integration failed'
 print('LIVE VERIFIED: weather endpoint returned current forecast',flush=True)
 Path('HOLIDAY-PLANNER-VERIFIED.json').write_text(json.dumps({'status':'verified','bookingLockPreserved':True,'robotsPreserved':True,'files':verified},indent=2))
except BaseException:
 errors=[]
 for n in reversed(changed):
  try:
   if originals[n] is None:s.remove('/public/'+n)
   else:put(n,originals[n])
   assert read(n)==originals[n]
  except Exception:errors.append(n)
 print('Rollback failures:',errors,flush=True);raise
finally:s.close();t.close()
