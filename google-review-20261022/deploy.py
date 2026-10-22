import base64, hashlib, json, os, socket, stat, time, urllib.request
from pathlib import Path, PurePosixPath
import paramiko

ROOT = Path('google-review-20261022')
M = json.loads((ROOT / 'manifest.json').read_text())
backup = Path('review-rollback'); backup.mkdir(exist_ok=True)
sha = lambda data: hashlib.sha256(data).hexdigest()
parts = os.environ['SFTP_HOST_PUBLIC_KEY'].strip().split()
ki = next(i for i, p in enumerate(parts) if p.startswith(('ssh-', 'ecdsa-')))
key = paramiko.PKey.from_type_string(parts[ki], base64.b64decode(parts[ki+1], validate=True))
t = paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(), 22), timeout=25))
t.start_client(timeout=25)
assert t.get_remote_server_key().asbytes() == key.asbytes(), 'SSH host identity mismatch'
t.auth_password(os.environ['SFTP_USER'].strip(), os.environ['SFTP_PASSWORD'])
s = paramiko.SFTPClient.from_transport(t); s.get_channel().settimeout(45)
def rp(name):
    assert not name.startswith('/') and '..' not in PurePosixPath(name).parts
    return str(PurePosixPath(M['remote_root']) / name)
def read(name):
    try:
        with s.open(rp(name), 'rb') as f: return f.read()
    except FileNotFoundError: return None
def put(name, data):
    parent = PurePosixPath(rp(name)).parent
    for path in reversed([parent, *parent.parents]):
        if str(path) in ('.', '/'): continue
        try: assert stat.S_ISDIR(s.stat(str(path)).st_mode)
        except FileNotFoundError: s.mkdir(str(path))
    temporary = rp(name) + '.review-20261022-stage'
    with s.open(temporary, 'wb') as f: f.write(data)
    s.chmod(temporary, 0o644); s.posix_rename(temporary, rp(name))
originals = {}; release = {}; changed = []
try:
    for name in ('robots.txt', 'sitemap.xml'):
        data = read(name)
        assert data and sha(data) == M[name+'_sha256'], name+' changed since review'
        originals[name] = data
    for name, info in M['files'].items():
        data = (ROOT / 'files' / name).read_bytes()
        assert sha(data) == info['updated_sha256'], 'Release checksum mismatch: '+name
        original = read(name)
        assert (sha(original) if original is not None else None) == info['original_sha256'], 'Live file changed: '+name
        originals[name] = original; release[name] = data
        if original is not None:
            p = backup / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(original)
    (backup/'manifest.json').write_text(json.dumps(M, indent=2))
    # Assets first, HTML only once both assets are installed.
    order = sorted(release, key=lambda n: (n.endswith('.html'), n))
    for name in order:
        assert read(name) == originals[name], 'Concurrent live edit: '+name
        changed.append(name); put(name, release[name])
        assert read(name) == release[name], 'Remote verification failed: '+name
    results = []
    for name in order:
        url = M['base_url'] + ('' if name == 'index.html' else name)
        req = urllib.request.Request(url+'?review-check='+str(time.time_ns()), headers={'Cache-Control':'no-cache'})
        with urllib.request.urlopen(req, timeout=45) as r:
            assert r.status == 200
            actual = r.read()
        assert actual == release[name], 'Public bytes mismatch: '+name
        results.append({'url':url,'sha256':sha(actual),'status':200})
        print('LIVE VERIFIED:', url, flush=True)
    for name in ('robots.txt', 'sitemap.xml'):
        assert read(name) == originals[name], 'Crawl configuration changed: '+name
    Path('REVIEWS-VERIFIED.json').write_text(json.dumps({'site':M['site'],'status':'verified','files':results}, indent=2))
except BaseException:
    print('Deployment failed; restoring modified targets.', flush=True)
    errors = []
    for name in reversed(changed):
        try:
            if originals[name] is None: s.remove(rp(name))
            else: put(name, originals[name])
            assert read(name) == originals[name]
        except Exception as e: errors.append(name+': '+type(e).__name__)
    if errors: print('ROLLBACK NEEDS ATTENTION:', ', '.join(errors), flush=True)
    raise
finally:
    s.close(); t.close()
