"""Change only the destination count wording in current live homepage bytes."""
import importlib.util,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('release','navigation-fix-20261030/release.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
before=release.fetch('index.html')
old=b'Start with the Lake District, then explore nine more regions'
new=b'Start with the Lake District, then explore more destinations'
assert before.count(old)==1,'Expected homepage wording changed; stop for review'
after=before.replace(old,new,1)
assert len(after)>0 and after!=before
assert after.count(new)==1 and old not in after
assert b'Explore Destinations' in after,'Preserve live navigation'
release.OUT.joinpath('index.html').write_bytes(after)
print('PASS: exactly one count phrase replaced; all other homepage bytes preserved',flush=True)
if '--publish' in sys.argv:
    release.deploy({'index.html':before},{'index.html':after},release.fetch('robots.txt'),release.fetch('sitemap.xml'))
