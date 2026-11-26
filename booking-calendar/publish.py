"""Publish the diary using the site's established guarded IONOS transfer."""
from contextlib import closing
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import secrets
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'search-enquiries-20261125'))
from transfer import Host, backup, guarded_replace, read

WEB = PurePosixPath('/public')
PRIVATE = PurePosixPath('/.touring-calendar')
PUBLIC = ROOT / 'booking-backend/public'
BASE = 'https://lakelandtouring.uk/'
HOLD = json.loads((HERE / 'opening-hold.json').read_text())


def page(path):
    request = Request(BASE + path + ('&' if '?' in path else '?') + 'diary-check=' + str(time.time_ns()),
                      headers={'Cache-Control':'no-cache','Accept-Encoding':'identity'})
    try:
        with urlopen(request, timeout=25) as response:
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()


def patch_page(name, data):
    if data is None:
        raise RuntimeError('Missing website entry point: ' + name)
    if b'/hire-calendar/' in data:
        return data
    if name == 'index.html':
        pattern = rb'(<section\b[^>]*class="lt-hero"[^>]*>.*?<div class="lt-actions">)'
        addition = b'<a class="lt-button" href="/hire-calendar/">Check availability</a>'
    elif name == 'booking.html':
        pattern = rb'(<h1\b[^>]*>Get a touring caravan hire quote</h1>)'
        addition = b'<p><a class="lt-button" href="/hire-calendar/">Check availability</a></p>'
    else:
        # This is an admin navigation link. The destination authenticates every request.
        # Using no quotes in the fixed href preserves surrounding PHP string literals.
        pattern = rb'(<h2>Diary login</h2>)'
        addition = b'<p><a href=/hire-calendar/admin/>Bookings</a></p>'
    updated, count = re.subn(pattern, lambda match: match[0]+addition, data, count=1, flags=re.I|re.S)
    if count != 1:
        raise RuntimeError('Cannot locate navigation in '+name)
    return updated


def private_setup(sftp):
    try:
        sftp.stat(str(PRIVATE))
    except FileNotFoundError:
        sftp.mkdir(str(PRIVATE),0o700)
    def create(name, value):
        path=str(PRIVATE/name)
        try:
            sftp.stat(path)
            return
        except FileNotFoundError:
            pass
        stage=path+'.'+secrets.token_hex(8)
        with sftp.open(stage,'wb') as output:
            output.write(value)
        sftp.chmod(stage,0o600)
        try:
            sftp.rename(stage,path)
        except OSError:
            sftp.remove(stage)
            sftp.stat(path)
    create('receipt.key',secrets.token_hex(48).encode())
    create('opening-hold.json',(HERE/'opening-hold.json').read_bytes())
    create('config.php',(HERE/'default-config.php').read_bytes())


def verify_diary():
    status, body=page('hire-calendar/availability.php')
    if status != 200:
        raise RuntimeError('Diary availability returned HTTP '+str(status))
    result=json.loads(body)
    if not isinstance(result.get('blocks'),list) or not result.get('csrf'):
        raise RuntimeError('Diary did not return its live inventory')
    for block in result['blocks']:
        if set(block) != {'start','end','state'}:
            raise RuntimeError('Unexpected public inventory fields')
    if page('hire-calendar/admin/')[0] != 403:
        raise RuntimeError('Operator sign-in check failed')
    if page('hire-calendar/status.php')[0] != 404:
        raise RuntimeError('Guest privacy check failed')
    status, public=page('hire-calendar/')
    if status!=200 or b'Find your dates' not in public:
        raise RuntimeError('Missing public diary')
    expected = {'start': HOLD['start'], 'end': HOLD['end'], 'state': 'held'}
    occupied = [block for block in result['blocks']
                if block['start'] < expected['end'] and block['end'] > expected['start']]
    return occupied == [expected]


def run():
    with closing(Host()) as host:
        def current(name):
            return host.run(lambda s:read(s,WEB/name))
        def replace(name,old,new):
            host.run(lambda s:guarded_replace(s,WEB/name,old,new))
        public_source=PUBLIC/'hire-calendar'
        updates={'hire-calendar/'+str(p.relative_to(public_source)):p.read_bytes()
                 for p in sorted(public_source.rglob('*'), key=lambda p: (
                     p.parent != public_source or p.name not in ('booking-sms.php','sms.php'),
                     p.name != 'booking-sms.php', str(p))) if p.is_file()}
        updates['hire-calendar/lake.webp']=(ROOT/'luxury-release-20261031/luxury-lake-dusk-20261031.webp').read_bytes()
        for name in ['api/common.php','api/availability.php']:
            actual=current(name)
            allowed=[None,(ROOT/'booking-standby-20261020/pinned'/name).read_bytes(),(PUBLIC/name).read_bytes()]
            if actual not in allowed:
                raise RuntimeError('Review existing hosting change before updating '+name)
            updates[name]=(PUBLIC/name).read_bytes()
        entries=['Admin/index.php','booking.html','index.html']
        old={name:current(name) for name in [*updates,*entries]}
        for name in entries:
            updates[name]=patch_page(name,old[name])
        archive=BytesIO()
        with ZipFile(archive,'w',ZIP_DEFLATED) as z:
            for name,content in old.items():
                if content is not None and content!=updates[name]:
                    z.writestr(name,content)
        host.run(lambda s:backup(s,'/.touring-diary-'+str(time.time_ns())+'.zip',archive.getvalue()))
        # Never replace an existing private config, key, booking database or hold.
        host.run(private_setup)
        changed=[]
        try:
            for name,data in updates.items():
                if name in entries or old[name]==data: continue
                changed.append(name)
                replace(name,old[name],data)
            held=verify_diary()
            for name in entries:
                if old[name]!=updates[name]:
                    changed.append(name)
                    replace(name,old[name],updates[name])
            for name in ['','booking.html','Admin/']:
                status,content=page(name)
                if status!=200 or b'/hire-calendar/' not in content:
                    raise RuntimeError('Missing published navigation on '+(name or 'homepage'))
            print('Verified guest calendar, operator sign-in, private receipt boundary and three live entry points.')
            print(f"Public calendar shows one hold from {HOLD['start']} to checkout {HOLD['end']}: {held}")
        except BaseException:
            for name in reversed(changed):
                if current(name)==updates[name]:
                    replace(name,updates[name],old[name])
            raise

if __name__=='__main__':
    run()
