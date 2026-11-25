"""Apply the audited text and tracking changes to the latest public files."""
import argparse
from contextlib import closing
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'design-standard-20261125'))
from transfer import Host, read, backup, guarded_replace

CONF = json.loads((HERE / 'site.json').read_text())

def public(name):
    url = CONF['base'] + ('' if name == 'index.html' else name)
    req = Request(url + '?audit-release=' + str(time.time_ns()), headers={'Accept-Encoding':'identity','Cache-Control':'no-cache'})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=35) as res:
                return res.read()
        except HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code < 500 or attempt == 2:
                raise
        except (TimeoutError, OSError):
            if attempt == 2:
                raise
        time.sleep(attempt + 1)

def updated(name, current, changes):
    text = current.decode('utf-8')
    for edit in changes:
        seen = text.count(edit['old'])
        completed = text.count(edit['new'])
        if completed >= edit['count'] and seen == completed * edit['new'].count(edit['old']):
            continue
        if seen != edit['count']:
            raise ValueError('Unexpected source in ' + name + ': ' + edit['old'][:50])
        text = text.replace(edit['old'], edit['new'])
    return text.encode('utf-8')

def run(write):
    originals, result = {}, {}
    brochure = 'downloads/lakeland-touring-brochure.pdf'
    if CONF.get('brochure'):
        originals[brochure] = public(brochure)
        result[brochure] = (HERE / Path(brochure).name).read_bytes()
        if not result[brochure].startswith(b'%PDF-'):
            raise ValueError('Invalid brochure')
        if originals[brochure] not in (None, result[brochure]):
            raise ValueError('A different brochure exists at the target URL')
    for name, changes in json.loads((HERE / 'edits.json').read_text()).items():
        originals[name] = public(name)
        if originals[name] is None:
            raise ValueError('Missing existing page ' + name)
        result[name] = updated(name, originals[name], changes)
    if not write:
        return
    root = PurePosixPath('/public')
    with closing(Host()) as host:
        def hosting_read(name):
            return host.run(lambda s:read(s,root/name))
        def replace(name, old, new):
            host.run(lambda s:guarded_replace(s,root/name,old,new))
        for name,original in originals.items():
            if hosting_read(name) != original:
                raise RuntimeError('Live and hosted source differ for '+name)
        memory = BytesIO()
        with ZipFile(memory,'w',ZIP_DEFLATED) as archive:
            for name,original in originals.items():
                if original is not None:
                    archive.writestr(name,original)
        host.run(lambda s:backup(s,'/.search-enquiries-'+str(time.time_ns())+'.zip',memory.getvalue()))
        changed = []
        try:
            for name, data in result.items():
                if data != originals[name]:
                    changed.append(name)
                    replace(name, originals[name], data)
            for name,data in result.items():
                if public(name) != data:
                    raise RuntimeError('Public verification failed: '+name)
                print('Verified', name, flush=True)
        except BaseException:
            for name in reversed(changed):
                if hosting_read(name) == result[name]:
                    replace(name, result[name], originals[name])
            raise

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--publish', action='store_true')
    run(ap.parse_args().publish)
