"""Patch current public HTML only; pinned SFTP, originals/rollback, exact readback."""
import base64, hashlib, json, os, re, socket, stat, time
from pathlib import Path
from urllib.request import Request, urlopen
import paramiko
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, unquote

ROOT=Path('analytics')
TAG=b'<script defer src="/analytics-consent.js?v=20261020-ga4"></script>'
def patch_html(data):
    if TAG in data:return data
    if re.search(rb'googletagmanager\.com/(?:gtag|gtm)|google-analytics\.com',data,re.I):
        raise ValueError('Existing tracking needs review')
    if not re.search(rb'</head\s*>',data,re.I):raise ValueError('HTML head required')
    return re.sub(rb'</head\s*>',lambda m:TAG+m.group(),data,count=1,flags=re.I)

def has_head(data):
    return bool(re.search(rb'</head\s*>',data,re.I))

def main():
    parts=os.environ['SFTP_HOST_PUBLIC_KEY'].strip().split()
    i=next(i for i,p in enumerate(parts) if p.startswith(('ssh-','ecdsa-')))
    key=paramiko.PKey.from_type_string(parts[i],base64.b64decode(parts[i+1],validate=True))
    backup=Path('analytics-rollback');backup.mkdir(exist_ok=True)
    with socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25) as sock:
        t=paramiko.Transport(sock);t.start_client(timeout=25)
        if t.get_remote_server_key().asbytes()!=key.asbytes():raise RuntimeError('SFTP host mismatch')
        t.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD'])
        s=paramiko.SFTPClient.from_transport(t);s.get_channel().settimeout(40)
        s.chdir('/public')
        def read(path):
            try:
                with s.open('./'+path,'rb') as f:return f.read()
            except FileNotFoundError:return None
        def put(path,data):
            stage='./'+path+'.analytics-stage'
            with s.open(stage,'wb') as f:f.write(data)
            s.chmod(stage,0o644)
            with s.open(stage,'rb') as f:
                if f.read()!=data:raise RuntimeError('Stage mismatch')
            s.posix_rename(stage,'./'+path)
        originals={};changed=[]
        try:
            robots=read('robots.txt');sitemap=read('sitemap.xml')
            if not robots or re.search(rb'^\s*Disallow:\s*/\s*$',robots,re.M|re.I):raise RuntimeError('Robots check failed')
            if not sitemap or b'lakelandtouring.uk' not in sitemap:raise RuntimeError('Sitemap check failed')
            home=read('index.html')
            if not home or b'lakeland touring' not in home.lower():raise RuntimeError('Wrong hosting root')
            updates={'analytics-consent.js':(ROOT/'analytics-consent.js').read_bytes(),
                     'analytics-privacy.html':(ROOT/'analytics-privacy.html').read_bytes()}
            page_names=set()
            def is_public(name):
                return not any(part.lower().startswith(('admin','account','login','register','rider-hub','owner-garage','passport','verify','verification','performance365')) for part in name.split('/'))
            for entry in s.listdir_attr('.'):
                name=entry.filename
                if not stat.S_ISREG(entry.st_mode) or not name.endswith(('.html','.htm')) or name.startswith('google'):continue
                
                if is_public(name):page_names.add(name)
            for element in ET.fromstring(sitemap).iter():
                if element.tag.split('}')[-1]!='loc' or not element.text:continue
                parsed=urlparse(element.text);name=unquote(parsed.path).lstrip('/')
                if parsed.hostname not in ('lakelandtouring.uk','www.lakelandtouring.uk'):raise RuntimeError('Unexpected sitemap host')
                if not name.endswith(('.html','.htm')):continue
                if '..' in name.split('/') or name.startswith(('admin/','media/','assets/')) or '\\' in name:raise RuntimeError('Invalid sitemap page')
                
                if is_public(name):page_names.add(name)
            for name in sorted(page_names):
                data=read(name)
                if data is None:raise RuntimeError('Sitemap page missing: '+name)
                if not has_head(data):continue
                updates.setdefault(name,patch_html(data))
            if TAG not in updates.get('index.html',b''):raise RuntimeError('Homepage must be tagged')
            if len(updates)<3:raise RuntimeError('Unexpected public page coverage')
            updates['sitemap.xml']=sitemap
            if b'https://lakelandtouring.uk/analytics-privacy.html' not in sitemap:
                updates['sitemap.xml']=sitemap.replace(b'</urlset>',b'<url><loc>https://lakelandtouring.uk/analytics-privacy.html</loc><lastmod>2026-10-20</lastmod></url>\n</urlset>')
            for name in updates:
                original=read(name);originals[name]=original
                if original is not None:
                    dest=backup/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(original)
            (backup/'original-presence.json').write_text(json.dumps({k:v is not None for k,v in originals.items()}))
            for name,data in updates.items():
                if data==originals[name]:continue
                if read(name)!=originals[name]:raise RuntimeError('Concurrent public change')
                changed.append(name);put(name,data)
                if read(name)!=data:raise RuntimeError('Remote readback failed')
            for name in ['index.html','analytics-consent.js','analytics-privacy.html','sitemap.xml']:
                url='https://lakelandtouring.uk/'+('' if name=='index.html' else name)+'?analytics-release='+str(int(time.time()))
                with urlopen(Request(url,headers={'Cache-Control':'no-cache'}),timeout=35) as r:
                    if r.status!=200 or r.read()!=updates[name]:raise RuntimeError('Public verification failed: '+name)
            if read('robots.txt')!=robots:raise RuntimeError('Robots changed')
            Path('ANALYTICS-DEPLOYED.json').write_text(json.dumps({'site':'lakelandtouring.uk','propertyId':'559721087','measurementId':'G-5W12LPB0KK','files':list(updates),'sha256':{k:hashlib.sha256(v).hexdigest() for k,v in updates.items()}},indent=2))
            print('LIVE VERIFIED: Lakeland Touring consent-gated Analytics installed; '+str(len(updates))+' public files checked. Previous pages preserved in rollback artifact.')
        except BaseException:
            for name in reversed(changed):
                if originals[name] is None:s.remove('./'+name)
                else:put(name,originals[name])
            raise
        finally:s.close();t.close()

if __name__=='__main__':main()
