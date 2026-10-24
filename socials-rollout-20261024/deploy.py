"""Add verified brand social links to existing public footers, with rollback."""
import base64
import hashlib
import html
import json
import os
import re
import socket
import stat
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

CONFIG = json.loads(Path(__file__).with_name('config.json').read_text())
START = '<!-- worx365-socials-start -->'
END = '<!-- worx365-socials-end -->'
ICONS = {
    'Facebook': '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M14 21v-8h3l.5-3H14V8c0-.9.3-1.5 1.7-1.5H18V3.2c-.4-.1-1.8-.2-3-.2-3 0-5 1.8-5 5v2H7v3h3v8z"/></svg>',
    'Instagram': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".8" fill="currentColor" stroke="none"/></svg>',
}

def block(config):
    brand = html.escape(config['brand'], quote=True)
    anchors = ''.join(
        '<a href="'+html.escape(url, quote=True)+'" target="_blank" rel="noopener noreferrer" aria-label="Visit '+brand+' on '+network+' (opens in a new tab)">'+ICONS[network]+'<span>'+network+'</span></a>'
        for network, url in config['links']
    )
    return START+'''
<style id="worx365-socials-style">
#worx365-socials{box-sizing:border-box;clear:both;width:100%;max-width:1240px;margin:24px auto 0;padding:24px 20px;border-top:1px solid #ffffff29;color:#f6f6f6;text-align:center;font:400 14px/1.5 system-ui,sans-serif}
#worx365-socials h2{margin:0 0 6px;color:inherit;font:700 18px/1.3 system-ui,sans-serif;letter-spacing:.05em;text-transform:none}
#worx365-socials p{margin:0 0 16px;color:inherit;opacity:.8;font:400 14px/1.5 system-ui,sans-serif}
#worx365-socials .worx365-social-links{display:flex;flex-wrap:wrap;justify-content:center;align-items:center;gap:12px}
#worx365-socials .worx365-social-links a{box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;gap:9px;min-height:46px;padding:10px 18px;margin:0;border:1px solid ACCENT;border-radius:24px;background:#10151c;color:ACCENT;text-decoration:none;font:600 14px/1.4 system-ui,sans-serif;letter-spacing:0;transition:background .15s,color .15s}
#worx365-socials .worx365-social-links a:hover{background:ACCENT;color:#090d0e}
#worx365-socials .worx365-social-links a:focus-visible{outline:3px solid #fff;outline-offset:4px}
#worx365-socials svg{display:block;width:22px;height:22px;flex:none}
@media(max-width:400px){#worx365-socials{padding:20px 14px}#worx365-socials .worx365-social-links{gap:10px}}
@media(prefers-reduced-motion:reduce){#worx365-socials a{transition:none}}
@media print{#worx365-socials{display:none}}
</style>
<section id="worx365-socials" aria-label="Connect with BRAND">
<h2>Connect with us</h2><p>Follow BRAND for our latest updates.</p>
<div class="worx365-social-links">ANCHORS</div>
</section>
'''.replace('ACCENT', config['accent']).replace('BRAND', brand).replace('ANCHORS', anchors)+END

def transform(data, config):
    text = data.decode('utf-8')
    if not re.search(r'<footer\b', text, re.I):
        return None
    cleaned = re.sub(re.escape(START)+r'.*?'+re.escape(END), '', text, flags=re.S)
    ends = list(re.finditer(r'</footer\s*>', cleaned, re.I))
    if not ends:
        return None
    point = ends[-1].start()
    result = (cleaned[:point]+block(config)+'\n'+cleaned[point:]).encode('utf-8')
    assert result.count(b'id="worx365-socials"') == 1
    # The exact original document is retained around one insertion. No scripts,
    # forms, contact links, existing WhatsApp buttons or SEO content are edited.
    assert re.sub(re.escape(START)+r'.*?'+re.escape(END)+r'\n?', '', result.decode(), flags=re.S) == cleaned
    return result

def fetch(url):
    sep = '&' if '?' in url else '?'
    with urllib.request.urlopen(url+sep+'socials-check='+str(time.time_ns()), timeout=45) as response:
        assert response.status == 200
        return response.read()

def check(config):
    data = fetch(config['base'])
    result = transform(data, config)
    assert result and b'Connect with us' in result
    for _, url in config['links']:
        assert html.escape(url, quote=True).encode() in result
    Path('SOCIALS-PREVIEW.html').write_bytes(result)
    print('CHECK PASSED:', config['brand'], 'verified links:', len(config['links']), flush=True)

def deploy(config):
    import paramiko
    root, base = config['root'], config['base']
    backup = Path('socials-rollback')
    backup.mkdir(exist_ok=True)
    parts = os.environ['SFTP_HOST_PUBLIC_KEY'].strip().split()
    i = next(i for i, p in enumerate(parts) if p.startswith(('ssh-', 'ecdsa-')))
    key = paramiko.PKey.from_type_string(parts[i], base64.b64decode(parts[i+1], validate=True))
    transport = paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(), 22), timeout=25))
    transport.start_client(timeout=25)
    assert transport.get_remote_server_key().asbytes() == key.asbytes(), 'SSH host identity mismatch'
    transport.auth_password(os.environ['SFTP_USER'].strip(), os.environ['SFTP_PASSWORD'])
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.get_channel().settimeout(45)
    def remote(name): return str(PurePosixPath(root)/name)
    def read(name):
        with sftp.open(remote(name), 'rb') as f: return f.read()
    def put(name, data):
        tmp = remote(name)+'.socials-stage'
        with sftp.open(tmp, 'wb') as f: f.write(data)
        sftp.chmod(tmp, 0o644)
        sftp.posix_rename(tmp, remote(name))
    def walk(folder='', depth=0):
        assert depth <= 5, 'Unexpected page depth'
        for item in sftp.listdir_attr(remote(folder)):
            if item.filename.startswith('.') or re.search(r'admin|backup|vendor|node_modules|private|upload|passport|certificate', item.filename, re.I):
                continue
            name = str(PurePosixPath(folder)/item.filename)
            if stat.S_ISDIR(item.st_mode):
                yield from walk(name, depth+1)
            elif stat.S_ISREG(item.st_mode) and name.endswith('.html') and item.st_size < 2000000:
                yield name
    originals, release, changed, verified = {}, {}, [], []
    try:
        for name in walk():
            data = read(name)
            try:
                candidate = transform(data, config)
            except UnicodeDecodeError:
                continue
            if candidate is None: continue
            try:
                public = fetch(base+urllib.parse.quote(name))
            except Exception:
                if name == 'index.html': raise
                continue
            if public != data:
                if name == 'index.html': raise RuntimeError('Homepage public source differs')
                continue
            originals[name], release[name] = data, candidate
        assert 'index.html' in release, 'No verified homepage'
        for name, data in originals.items():
            p = backup/name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        Path('SOCIALS-PLAN.json').write_text(json.dumps({'brand': config['brand'], 'links': config['links'], 'files': list(release)}, indent=2))
        for name, data in release.items():
            assert read(name) == originals[name], 'Concurrent live edit: '+name
            changed.append(name)
            put(name, data)
            assert read(name) == data, 'SFTP verification failed: '+name
        for name, data in release.items():
            url = base+urllib.parse.quote(name)
            actual = fetch(url)
            assert actual == data, 'Public verification failed: '+name
            verified.append({'url': url, 'sha256': hashlib.sha256(actual).hexdigest()})
            print('LIVE VERIFIED:', url, flush=True)
        Path('SOCIALS-VERIFIED.json').write_text(json.dumps({'brand': config['brand'], 'links': config['links'], 'files': verified, 'status': 'verified'}, indent=2))
    except BaseException:
        errors = []
        for name in reversed(changed):
            try:
                put(name, originals[name])
                assert read(name) == originals[name]
            except Exception: errors.append(name)
        if errors: print('ROLLBACK NEEDS ATTENTION:', errors, flush=True)
        raise
    finally:
        sftp.close()
        transport.close()

if __name__ == '__main__':
    name = os.environ.get('GITHUB_REPOSITORY', '').split('/')[-1]
    if '--check' in sys.argv:
        if name in CONFIG: check(CONFIG[name])
        else:
            for config in CONFIG.values(): check(config)
    else:
        deploy(CONFIG[name])
