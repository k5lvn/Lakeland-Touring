"""Insert the calendar in the current booking page without replacing unrelated edits."""
from pathlib import Path
import re
import sys

page = Path(sys.argv[1])
html = page.read_bytes()
if b'href="/hire-calendar/"' not in html:
    marker = re.compile(rb'(<h1\b[^>]*>Get a touring caravan hire quote</h1>)', re.I)
    html, count = marker.subn(rb'\1<p><a class="lt-button" href="/hire-calendar/">Check dates and hire prices</a></p>', html)
    if count != 1:
        raise SystemExit("Current booking page heading could not be identified.")
    page.write_bytes(html)
