import base64,hashlib,json,os,socket,time,urllib.request
from pathlib import Path
from datetime import datetime,timezone
import xml.etree.ElementTree as ET
import paramiko
from build import build,BASE
def sha(b):return hashlib.sha256(b).hexdigest()
def deploy():
 data=json.loads(Path('reviews-sync-20261102/reviews.json').read_text())
 checked=datetime.fromisoformat(data['checked_at'].replace('Z','+00:00'))
 assert 0 <= (datetime.now(timezone.utc)-checked).total_seconds()<172800,'Stale snapshot'
 parts=os.environ['SFTP_HOST_PUBLIC_KEY'].strip().split();i=next(i for i,p in enumerate(parts) if p.startswith(('ssh-','ecdsa-')))
 key=paramiko.PKey.from_type_string(parts[i],base64.b64decode(parts[i+1],validate=True))
 transport=paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25));transport.start_client(timeout=25)
 assert transport.get_remote_server_key().asbytes()==key.asbytes(),'SSH identity mismatch'
 transport.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD'])
 sftp=paramiko.SFTPClient.from_transport(transport);sftp.get_channel().settimeout(45)
 def read(n):
  try:
   with sftp.open('/public/'+n,'rb') as f:return f.read()
  except FileNotFoundError:return None
 def put(n,b):
  stage='/public/'+n+'.reviews-stage'
  with sftp.open(stage,'wb') as f:f.write(b)
  sftp.chmod(stage,0o644);sftp.posix_rename(stage,'/public/'+n)
 originals={};changed=[]
 backup=Path('review-rollback');backup.mkdir(exist_ok=True)
 try:
  names=['index.html','sitemap.xml','reviews/index.html']
  for n in names:
   originals[n]=read(n)
   if originals[n] is not None:
    p=backup/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(originals[n])
  assert originals['index.html'] and originals['sitemap.xml']
  protected={n:read(n) for n in ['robots.txt','.htaccess','send.php']}
  home,page=build(originals['index.html'],data)
  root=ET.fromstring(originals['sitemap.xml']);ns='{http://www.sitemaps.org/schemas/sitemap/0.9}';ET.register_namespace('',ns[1:-1])
  if not any(t.text==BASE+'reviews/' for t in root.iter(ns+'loc')):
   item=ET.SubElement(root,ns+'url');ET.SubElement(item,ns+'loc').text=BASE+'reviews/'
  sitemap=ET.tostring(root,encoding='utf-8',xml_declaration=True)
  release={'index.html':home,'sitemap.xml':sitemap,'reviews/index.html':page}
  try:sftp.stat('/public/reviews')
  except FileNotFoundError:sftp.mkdir('/public/reviews',0o755)
  for n,b in release.items():
   if b==originals[n]:continue
   assert read(n)==originals[n],'Concurrent edit: '+n
   changed.append(n);put(n,b);assert read(n)==b
  for n,b in release.items():
   url=BASE+('reviews/' if n=='reviews/index.html' else n)
   req=urllib.request.Request(url+'?review-check='+str(time.time_ns()),headers={'Cache-Control':'no-cache'})
   with urllib.request.urlopen(req,timeout=60) as r:assert r.status==200 and r.read()==b,'Public verification failed: '+n
  for n,b in protected.items():assert read(n)==b
  Path('REVIEWS-VERIFIED.json').write_text(json.dumps({'status':'verified','url':BASE+'reviews/','checked_at':data['checked_at'],'count':data['total_count'],'files':{n:sha(b) for n,b in release.items()}},indent=2))
  print('Review page, homepage links and sitemap published and verified.')
 except BaseException:
  for n in reversed(changed):
   if originals[n] is None:sftp.remove('/public/'+n)
   else:put(n,originals[n])
  raise
 finally:sftp.close();transport.close()
if __name__=='__main__':deploy()
