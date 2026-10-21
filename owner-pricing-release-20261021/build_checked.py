from pathlib import Path
import hashlib,json,re,subprocess,sys
root=Path(__file__).parent
expected=json.loads((root/'manifest.json').read_text())
(root/'files').mkdir(exist_ok=True);(root/'originals').mkdir(exist_ok=True)
subprocess.run([sys.executable,str(root/'prepare.py')],check=True)
assert json.loads((root/'manifest.json').read_text())==expected,'Rebuilt release differs from approved hashes'
for n,info in expected['files'].items():
 b=(root/'files'/n).read_bytes();assert hashlib.sha256(b).hexdigest()==info['updated_sha256']
 assert len(re.findall(rb'<h1[\s>]',b))==1 and b'noindex' not in b.lower()
print('Exact approved page hashes rebuilt; public baselines and guarded files unchanged.')
