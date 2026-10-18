import base64,hashlib,json,os,re,socket,time,urllib.request
from pathlib import Path
import paramiko
ROOT=Path('seo-release');M=json.loads((ROOT/'manifest.json').read_text());files=M['files'];remote=M['remote_root'];site=M['site'];backup=Path('seo-rollback');backup.mkdir(exist_ok=True)
def digest(b):return hashlib.sha256(b).hexdigest()
parts=os.environ['SFTP_HOST_PUBLIC_KEY'].strip().split();ki=next(i for i,p in enumerate(parts) if p.startswith(('ssh-','ecdsa-')));key=paramiko.PKey.from_type_string(parts[ki],base64.b64decode(parts[ki+1],validate=True))
t=paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25));t.start_client(timeout=25)
assert t.get_remote_server_key().asbytes()==key.asbytes(),'SSH host identity mismatch'
t.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD']);s=paramiko.SFTPClient.from_transport(t);s.get_channel().settimeout(45)
def rp(name):return remote.rstrip('/')+'/'+name if remote!='.' else name
def read(name):
 with s.open(rp(name),'rb') as f:return f.read()
def put(name,data):
 tmp=rp(name)+'.seo-20261018-stage'
 with s.open(tmp,'wb') as f:f.write(data)
 s.chmod(tmp,0o644);s.posix_rename(tmp,rp(name))
changed=[];originals={}
try:
 # Confirm crawl configuration before any write.
 robots=read('robots.txt');assert not re.search(rb'^\s*Disallow:\s*/\s*$',robots,re.M|re.I),'Root robots block'
 for name,info in files.items():
  original=read(name);originals[name]=original
  dest=backup/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(original)
  assert digest(original)==info['original_sha256'],'Live file changed since review: '+name
  assert digest((ROOT/'files'/name).read_bytes())==info['updated_sha256'],'Release content mismatch: '+name
 print('All reviewed files match live originals; backup complete.',flush=True)
 try:
  config=read('.htaccess');(backup/'htaccess-before.txt').write_bytes(config)
  # Only routing directives are printed; authentication configuration is not logged.
  for line in config.decode(errors='replace').splitlines():
   if line.strip().lower().startswith(('rewriteengine','rewritecond','rewriterule')):print('ROUTING:',line,flush=True)
 except FileNotFoundError:print('ROUTING: no root .htaccess',flush=True)
 for name in files:
  assert read(name)==originals[name],'Concurrent live edit: '+name
 for name in files:
  data=(ROOT/'files'/name).read_bytes();changed.append(name);put(name,data)
  assert read(name)==data,'Remote verification mismatch: '+name
 for name in files:
  target=M['base_url']+('' if name=='index.html' else name)
  req=urllib.request.Request(target+'?seo-release=20261018-'+str(int(time.time())),headers={'Cache-Control':'no-cache'})
  with urllib.request.urlopen(req,timeout=40) as r:body=r.read();assert r.status==200
  expected=(ROOT/'files'/name).read_bytes()
  if name.endswith('.php'):
   title=re.search(rb'<title>(.*?)</title>',expected).group(1);assert b'<title>'+title+b'</title>' in body,'Rendered PHP title mismatch'
   assert b'<?php' not in body,'PHP source exposed'
  else:assert body==expected,'Public bytes mismatch: '+name
  print('LIVE VERIFIED:',target,flush=True)
 assert read('robots.txt')==robots,'robots changed unexpectedly'
 Path('SEO-DEPLOYED.json').write_text(json.dumps({'site':site,'files':list(files),'status':'verified'},indent=2))
except BaseException:
 print('Failure: restoring every modified file.',flush=True)
 for name in reversed(changed):put(name,originals[name]);assert read(name)==originals[name]
 raise
finally:s.close();t.close()
