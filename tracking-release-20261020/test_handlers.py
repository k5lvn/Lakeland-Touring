from pathlib import Path
import subprocess,json,base64,uuid
root=Path('tracking-release-20261020')
path=root/'files/send.php'
if not path.exists():
 print('No mail handler in this release');raise SystemExit(0)
subprocess.run(['php','-l',str(path)],check=True)
sid=json.loads((root/'manifest.json').read_text())['site']
def run(method,fields,transport='/bin/true'):
 encoded=base64.b64encode(json.dumps(fields).encode()).decode()
 code="$_SERVER=['REQUEST_METHOD'=>'"+method+"','REMOTE_ADDR'=>'qa-"+uuid.uuid4().hex+"','CONTENT_LENGTH'=>1000];$_POST=json_decode(base64_decode('"+encoded+"'),true);require $argv[1];"
 # PHP's mail transport is replaced with a local success/failure executable.
 # No message can be sent by these tests.
 p=subprocess.run(['php','-d','sendmail_path='+transport,'-r',code,str(path)],capture_output=True,text=True,check=True)
 return p.stdout
fields={'form_type':'Contact enquiry' if sid=='ld' else 'Group enquiry','name':'Example Test','email':'qa@example.invalid','phone':'000000','message':'Local-only handler verification','website':''}
success=run('POST',fields)
expected='contact' if sid=='ld' else 'group'
assert '<meta name="worx-lead" content="'+expected+'">' in success and 'analytics-consent.js?v=20261020-conversions' in success
if sid=='ld':
 q=run('POST',{**fields,'form_type':'Quote request'})
 assert '<meta name="worx-lead" content="quote">' in q
for page in [run('GET',{}),run('POST',{**fields,'email':'invalid'}),run('POST',fields,'/bin/false')]:
 assert 'worx-lead' not in page and 'analytics-consent.js' not in page
print('Mail handler: accepted contact/quote responses track; errors never track. All mail transports stubbed.')
