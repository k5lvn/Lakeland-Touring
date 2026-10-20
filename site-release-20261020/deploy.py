import base64, hashlib, json, os, socket, time, urllib.request, stat
from pathlib import Path, PurePosixPath
import paramiko
ROOT = Path('site-release-20261020')
M = json.loads((ROOT / 'manifest.json').read_text())
backup = Path('release-rollback'); backup.mkdir(exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
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
    return M['remote_root'].rstrip('/') + '/' + name
def read(name):
    try:
        with s.open(rp(name), 'rb') as f: return f.read()
    except FileNotFoundError: return None
def mkdirs(name):
    parent = str(PurePosixPath(rp(name)).parent)
    current = ''
    for part in parent.split('/'):
        if not part: continue
        current += '/' + part
        try: assert stat.S_ISDIR(s.stat(current).st_mode)
        except FileNotFoundError: s.mkdir(current)
def put(name, data):
    mkdirs(name)
    tmp = rp(name) + '.release-20261020-stage'
    with s.open(tmp, 'wb') as f: f.write(data)
    s.chmod(tmp, 0o644)
    s.posix_rename(tmp, rp(name))
def restore(name, data):
    if data is None:
        try: s.remove(rp(name))
        except FileNotFoundError: pass
    else: put(name, data)
originals = {}; release = {}; changed = []
try:
    robots = read('robots.txt')
    assert robots is not None and sha(robots) == M['robots_sha256'], 'Robots changed'
    for name, info in M['files'].items():
        data = (ROOT / 'files' / name).read_bytes()
        assert sha(data) == info['updated_sha256'], 'Release checksum mismatch'
        original = read(name)
        assert (sha(original) if original is not None else None) == info['original_sha256'], 'Live file changed: ' + name
        release[name] = data; originals[name] = original
        if original is not None:
            p = backup / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(original)
    (backup / 'manifest.json').write_text(json.dumps(M, indent=2))
    print('All live baselines match. Rollback saved before publication.', flush=True)
    # Publish new resources before the homepage and sitemap expose them.
    order = sorted(release, key=lambda n: (2 if n=='sitemap.xml' else 1 if n=='index.html' else 0, n))
    for name in order:
        assert read(name) == originals[name], 'Concurrent edit: ' + name
        changed.append(name); put(name, release[name])
        assert read(name) == release[name], 'Remote verification failed: ' + name
    results = []
    for name in order:
        url = M['base_url'] + ('' if name=='index.html' else name)
        req = urllib.request.Request(url+'?release-check='+str(time.time_ns()), headers={'Cache-Control':'no-cache'})
        with urllib.request.urlopen(req, timeout=60) as r:
            assert r.status == 200
            data = r.read()
        assert data == release[name], 'Public checksum mismatch: ' + name
        results.append({'url':url,'status':200,'sha256':sha(data)})
    assert read('robots.txt') == robots, 'Robots changed during deployment'
    Path('RELEASE-VERIFIED.json').write_text(json.dumps({'site':M['site'],'files':results,'status':'verified'}, indent=2))
    print('Verified public bytes for', M['site'], len(results), 'files.', flush=True)
except BaseException:
    print('Release failed; restoring modified targets.', flush=True)
    errors = []
    for name in reversed(changed):
        try:
            restore(name, originals[name]); assert read(name) == originals[name]
        except Exception as e: errors.append(name + ': ' + type(e).__name__)
    if errors: print('ROLLBACK NEEDS ATTENTION:', ', '.join(errors), flush=True)
    raise
finally:
    s.close(); t.close()
