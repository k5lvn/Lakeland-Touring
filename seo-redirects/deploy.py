import base64,os,socket,re,urllib.request,urllib.error,json
from pathlib import Path
import paramiko
m=json.loads(Path('seo-redirects/config.json').read_text());host=m['host'];root=m['root'];site=m['site'];parts=os.environ['SFTP_HOST_PUBLIC_KEY'].split();i=next(i for i,x in enumerate(parts) if x.startswith(('ssh-','ecdsa-')));key=paramiko.PKey.from_type_string(parts[i],base64.b64decode(parts[i+1]))
t=paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25));t.start_client(timeout=25);assert t.get_remote_server_key().asbytes()==key.asbytes();t.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD']);s=paramiko.SFTPClient.from_transport(t);s.get_channel().settimeout(40);remote=root.rstrip('/')+'/.htaccess'
try:
 try:
  with s.open(remote,'rb') as f:old=f.read()
  raise RuntimeError('Existing .htaccess found; merge review required')
 except FileNotFoundError:old=None
 escaped=re.escape(host)
 rules=f'''# Worx365 approved canonical redirects 2026-10-18
RewriteEngine On
RewriteCond %{{THE_REQUEST}} \\s/+index\\.html[\\s?] [NC]
RewriteRule ^index\\.html$ https://{host}/ [R=301,L,NE]
RewriteCond %{{HTTPS}} !=on [OR]
RewriteCond %{{HTTP_HOST}} !^{escaped}$ [NC]
RewriteRule ^ https://{host}%{{REQUEST_URI}} [R=301,L,NE]
'''.encode()
 Path('REDIRECT-BACKUP.json').write_text(json.dumps({'previous_htaccess':'absent','host':host}))
 try:
  with s.open(remote+'.seo-stage','wb') as f:f.write(rules)
  s.chmod(remote+'.seo-stage',0o644);s.posix_rename(remote+'.seo-stage',remote)
  class NoRedirect(urllib.request.HTTPRedirectHandler):
   def redirect_request(self,*a):return None
  opener=urllib.request.build_opener(NoRedirect())
  alternate=site if host.startswith('www.') else 'www.'+site
  for url,want in [(f'http://{site}/',f'https://{host}/'),(f'https://{alternate}/',f'https://{host}/'),(f'https://{host}/index.html?keep=1',f'https://{host}/?keep=1')]:
   try:opener.open(url,timeout=40);raise RuntimeError('Missing redirect: '+url)
   except urllib.error.HTTPError as e:
    assert e.code==301,(url,e.code);assert e.headers['Location']==want,(url,e.headers.get('Location'));print('VERIFIED 301:',url,'->',want,flush=True)
  for path in ['','sitemap.xml','robots.txt']:
   with urllib.request.urlopen('https://'+host+'/'+path,timeout=40) as r:assert r.status==200
  Path('REDIRECT-DEPLOYED.json').write_text(json.dumps(m));print('Canonical redirect deployment verified.',flush=True)
 except BaseException:
  s.remove(remote);raise
finally:s.close();t.close()
