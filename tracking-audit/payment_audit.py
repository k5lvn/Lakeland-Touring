import os,socket,base64,json,hashlib,re
from pathlib import Path
import paramiko
parts=os.environ['SFTP_HOST_PUBLIC_KEY'].strip().split();ki=next(i for i,p in enumerate(parts) if p.startswith(('ssh-','ecdsa-')))
key=paramiko.PKey.from_type_string(parts[ki],base64.b64decode(parts[ki+1],validate=True))
t=paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25));t.start_client(timeout=25)
assert t.get_remote_server_key().asbytes()==key.asbytes()
t.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD']);s=paramiko.SFTPClient.from_transport(t);s.get_channel().settimeout(30)
root='/public';out={};paths=['api/create-checkout-session.php']
# List only public route filenames relevant to checkout completion, never configs.
for directory in ['', '/api']:
 try:names=s.listdir(root+directory)
 except FileNotFoundError:
  out[directory or '/']={'exists':False};continue
 for name in names:
  if re.fullmatch(r'[a-zA-Z0-9_-]*(?:success|thank|confirm|webhook)[a-zA-Z0-9_-]*\.php',name):paths.append((directory+'/'+name).lstrip('/'))
try:
 for path in paths:
  try:
   with s.open(root+'/'+path,'rb') as f:b=f.read()
  except FileNotFoundError:out[path]={'exists':False};continue
  text=b.decode(errors='replace')
  # Output only structural booleans and public PHP/HTML route names. No source,
  # credentials, session IDs, form values, keys, URLs or query strings leave SFTP.
  out[path]={'exists':True,'sha256':hashlib.sha256(b).hexdigest(),'has_purchase_event':bool(re.search(r"(?:gtag|track)[\s\S]{0,40}['\"]purchase['\"]",text)),
   'checks_payment_status':'payment_status' in text,'checks_paid_value':bool(re.search(r"['\"]paid['\"]",text)),
   'has_success_url':'success_url' in text,'public_routes':sorted(set(re.findall(r'(?:/|[\'\"])([a-zA-Z0-9_/-]+\.(?:php|html))',text))),
   'mentions_analytics':'analytics' in text.lower(),'verifies_stripe_webhook':'constructEvent' in text}
 Path('checkout-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
finally:s.close();t.close()
