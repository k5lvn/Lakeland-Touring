"""Bounded destination navigation repair with current-byte guards and rollback."""
import base64, hashlib, json, os, re, socket, sys, time, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup
BASE='https://lakelandtouring.uk/'
HUB='explore-destinations.html'
GUIDE='scottish-borders-caravan-guide.html'
OUT=Path('navigation-qa'); OUT.mkdir(exist_ok=True)
CARD='<article class="guide-card"><span class="guide-kicker">A different kind of escape</span><h2>The Scottish Borders: Melrose &amp; beyond</h2><p>Explore Melrose, abbey towns and the Borders countryside, with practical touring campsite guidance to help plan your stay.</p><a href="scottish-borders-caravan-guide.html">Explore the guide →</a></article>'
def fetch(name):
    req=urllib.request.Request(BASE+name+'?navigation-check='+str(time.time_ns()),headers={'Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=45) as r:
        assert r.status==200
        assert 'noindex' not in r.headers.get('X-Robots-Tag','').lower(),name
        return r.read()
def transform(name,data):
    text=data.decode()
    def nav(match):
        return re.sub(r'(<a\b[^>]*href=[\"\'](?:/|https://lakelandtouring.uk/)?explore-destinations\.html[\"\'][^>]*>)\s*Destinations\s*(</a>)',r'\1Explore Destinations\2',match.group(),flags=re.I)
    text=re.sub(r'<nav\b.*?</nav>',nav,text,flags=re.S|re.I)
    if name==HUB:
        soup=BeautifulSoup(text,'html.parser')
        grid=soup.select_one('.guide-grid'); assert grid
        if not grid.select('a[href="'+GUIDE+'"]'):
            # Locate the existing grid without reserializing the surrounding page.
            start=text.index('<div class="guide-grid">'); end=text.index('</div>',start)
            text=text[:end]+CARD+text[end:]
        for old,new in [('10 Caravan Holiday Regions','11 Caravan Holiday Regions'),('nine more mainland','ten more mainland'),('among ten regions','among eleven regions')]: text=text.replace(old,new)
    return text.encode()
def verify(name,data):
    s=BeautifulSoup(data,'html.parser')
    assert not s.select('meta[name="robots"][content*="noindex"]'),name
    c=s.select_one('link[rel="canonical"]'); assert c and c.get('href')==BASE+name,name
    for a in s.select('nav a'):
        if a.get('href','').endswith(HUB): assert a.get_text(strip=True)=='Explore Destinations',name
    if name==HUB:
        assert len(s.select('.guide-card'))==11
        assert len(s.select('.guide-card a[href="'+GUIDE+'"]'))==1
        assert '11 Caravan Holiday Regions' in s.title.get_text()
    return s

def prepare():
    sitemap=fetch('sitemap.xml'); robots=fetch('robots.txt')
    assert not re.search(rb'^\s*Disallow:\s*/\s*$',robots,re.M|re.I)
    urls=[e.text for e in ET.fromstring(sitemap).iter() if e.tag.endswith('}loc')]
    assert BASE+GUIDE in urls and BASE+HUB in urls
    names=[u[len(BASE):] or 'index.html' for u in urls if u.startswith(BASE) and (u.endswith('.html') or u==BASE)]
    assert 'index.html' in names and HUB in names and GUIDE in names
    original={n:fetch(n) for n in names}
    release={n:transform(n,b) for n,b in original.items()}
    for n,b in release.items():
        # Home canonical deliberately uses the root URL.
        if n!='index.html': verify(n,b)
        (OUT/n).write_bytes(b)
    hub=BeautifulSoup(release[HUB],'html.parser')
    links=[a['href'] for a in hub.select('.guide-card a')]
    assert len(set(links))==11
    for n in links:
        assert n in original,n
        verify(n,release[n])
    plan={n:{'before':hashlib.sha256(original[n]).hexdigest(),'after':hashlib.sha256(b).hexdigest()} for n,b in release.items() if b!=original[n]}
    assert HUB in plan and 'index.html' in plan
    (OUT/'plan.json').write_text(json.dumps(plan,indent=2))
    print('PASS: 11 destination links, HTTP 200, canonicals, indexability, robots and sitemap; changed pages:',len(plan),flush=True)
    return original,{n:release[n] for n in plan},robots,sitemap

def deploy(original,release,robots,sitemap):
    import paramiko
    parts=os.environ['SFTP_HOST_PUBLIC_KEY'].strip().split(); i=next(i for i,p in enumerate(parts) if p.startswith(('ssh-','ecdsa-')))
    key=paramiko.PKey.from_type_string(parts[i],base64.b64decode(parts[i+1],validate=True))
    t=paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25)); t.start_client(timeout=25)
    assert t.get_remote_server_key().asbytes()==key.asbytes(),'SSH identity mismatch'
    t.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD']); s=paramiko.SFTPClient.from_transport(t);s.get_channel().settimeout(45)
    def read(n):
        with s.open('/public/'+n,'rb') as f:return f.read()
    def put(n,b):
        tmp='/public/'+n+'.navigation-stage'
        with s.open(tmp,'wb') as f:f.write(b)
        s.chmod(tmp,0o644);s.posix_rename(tmp,'/public/'+n)
    backup=Path('navigation-rollback');backup.mkdir(exist_ok=True);changed=[]
    try:
        assert read('robots.txt')==robots and read('sitemap.xml')==sitemap
        for n in release:
            assert read(n)==original[n],'Public/remote mismatch: '+n
            (backup/n).write_bytes(original[n])
        for n,b in release.items():
            assert read(n)==original[n],'Concurrent edit: '+n
            changed.append(n);put(n,b);assert read(n)==b
        for n,b in release.items():
            assert fetch(n)==b,'Public mismatch: '+n
            print('LIVE VERIFIED:',BASE+n,flush=True)
        assert read('robots.txt')==robots and read('sitemap.xml')==sitemap
        (OUT/'verified.json').write_text(json.dumps({'status':'verified','files':list(release),'destinationLinks':11},indent=2))
    except BaseException:
        errors=[]
        for n in reversed(changed):
            try:put(n,original[n]);assert read(n)==original[n]
            except Exception:errors.append(n)
        print('Rollback failures:',errors,flush=True);raise
    finally:s.close();t.close()
if __name__=='__main__':
    prepared=prepare()
    if '--publish' in sys.argv:deploy(*prepared)
