"""Read-only hosting readiness check. Print only allowlisted booleans; never credentials/data."""
import base64,json,os,re,socket,stat
from pathlib import Path
import paramiko
parts=os.environ['SFTP_HOST_PUBLIC_KEY'].split()
i=next(i for i,p in enumerate(parts) if p.startswith(('ssh-','ecdsa-')))
key=paramiko.PKey.from_type_string(parts[i],base64.b64decode(parts[i+1],validate=True))
t=paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(),22),timeout=25));t.start_client(timeout=25)
assert t.get_remote_server_key().asbytes()==key.asbytes(),'Host identity mismatch'
t.auth_password(os.environ['SFTP_USER'].strip(),os.environ['SFTP_PASSWORD'])
s=paramiko.SFTPClient.from_transport(t);s.get_channel().settimeout(35)
def read(path):
 try:
  with s.open(path,'rb') as f:return f.read(1024*1024).decode('utf-8',errors='replace')
 except FileNotFoundError:return None
def exists(path):
 try:return stat.S_ISREG(s.stat(path).st_mode)
 except FileNotFoundError:return False
def literal(source,name):
 m=re.search(r"['\"]"+re.escape(name)+r"['\"]\s*=>\s*['\"]([^'\"]*)['\"]",source or '')
 return m.group(1) if m else None
def flag(source,name):
 m=re.search(r"['\"]"+re.escape(name)+r"['\"]\s*=>\s*(true|false)\b",source or '',re.I)
 return m.group(1).lower()=='true' if m else None
try:
 result={'readOnly':True,'releaseLockPresent':exists('/public/api/booking-disabled.php'),'bookingApiPresent':exists('/public/api/common.php')}
 htaccess=read('/public/.htaccess') or ''
 match=re.search(r'^\s*SetEnv\s+TOURING_BOOKING_CONFIG\s+["\x27]?([^\s"\x27]+)',htaccess,re.M)
 path=match.group(1) if match else None
 result['bookingConfigSetInHtaccess']=bool(path)
 result['bookingConfigOutsidePublic']=bool(path and path.startswith('/') and not path.startswith('/public/'))
 config=read(path) if result['bookingConfigOutsidePublic'] else None
 result['configuredBookingFileExists']=config is not None
 result['bookingVerificationFlags']={k:flag(config,k) for k in ['enabled','policy_verified','inventory_verified','merchant_verified']}
 result['bookingTermsVersionConfigured']=bool(literal(config,'terms_version'))
 result['inventoryHorizonConfigured']=bool(literal(config,'inventory_through'))
 result['calendarPeriodsConfigured']=bool(re.search(r"['\"]periods['\"]\s*=>\s*\[\s*\[",config or '',re.S))
 result['bookingStorageConfigured']=bool(literal(config,'private_dir'))
 result['stripeKeyLiteralPresent']=bool(re.search(r'sk_(?:live|test)_[A-Za-z0-9]+',config or ''))
 result['stripeWebhookLiteralPresent']=bool(re.search(r'whsec_[A-Za-z0-9]+',config or ''))
 result['stripeAccountConfigured']=bool(re.fullmatch(r'acct_[A-Za-z0-9]+',literal(config,'stripe_account') or ''))
 legacy=read('/public/config.php')
 result['legacyPublicConfigExists']=legacy is not None
 result['legacyStripeKeyPresent']=bool(re.search(r'sk_(?:live|test)_[A-Za-z0-9]+',legacy or ''))
 result['legacyStripeWebhookPresent']=bool(re.search(r'whsec_[A-Za-z0-9]+',legacy or ''))
 garage=read('/.touring-garage/booking-config.php')
 result['ownerDatabaseExists']=exists('/.touring-garage/garage.sqlite')
 result['ownerBookingModulePresent']=exists('/public/garage-bookings.php')
 result['ownerBookingConfigExists']=garage is not None
 result['ownerBookingEnabledLiteral']=flag(garage,'enabled')
 result['ownerClosureDatesConfigured']=bool(re.search(r"['\"]non_working_dates['\"]\s*=>",garage or ''))
 result['scopeLimit']='Environment settings outside .htaccess and dynamically computed PHP settings are not inferred. No private database read or payment/provider request.'
 # Verify the actual web-process environment through a short-lived authenticated probe.
 # No existing file is overwritten; cleanup runs even when HTTP validation fails.
 import secrets,urllib.request,urllib.error,hashlib
 token=secrets.token_hex(32);probe_name='_touring_runtime_'+secrets.token_hex(12)+'.php';probe='/public/'+probe_name
 php='''<?php
ini_set('display_errors','0');
if(!hash_equals('TOKEN_HASH',hash('sha256',$_SERVER['HTTP_X_TOURING_DIAGNOSTIC']??''))){http_response_code(404);exit;}
header('Content-Type: application/json');header('Cache-Control: no-store');
$path=getenv('TOURING_BOOKING_CONFIG')?:'';$real=$path?realpath($path):false;$doc=realpath($_SERVER['DOCUMENT_ROOT']??'');
$outside=$real&&$doc&&$real!==$doc&&!str_starts_with($real,$doc.DIRECTORY_SEPARATOR);
$out=['webConfigEnvironmentSet'=>$path!=='','webConfigFileExists'=>(bool)$real,'webConfigOutsideDocumentRoot'=>(bool)$outside];
$cfg=[];if($outside){ob_start();try{$value=require $real;if(is_array($value))$cfg=$value;}catch(Throwable $e){$out['configLoadFailed']=true;}finally{ob_end_clean();}}
foreach(['enabled','policy_verified','inventory_verified','merchant_verified'] as $flag)$out[$flag]=isset($cfg[$flag])&&$cfg[$flag]===true;
$out['calendarPeriodCount']=isset($cfg['periods'])&&is_array($cfg['periods'])?count($cfg['periods']):0;
$out['inventoryHorizonConfigured']=!empty($cfg['inventory_through']);
$out['stripeSecretConfigured']=isset($cfg['stripe_secret'])&&(bool)preg_match('/^sk_(live|test)_/',$cfg['stripe_secret']);
$out['stripeAccountConfigured']=isset($cfg['stripe_account'])&&(bool)preg_match('/^acct_[A-Za-z0-9]+$/',$cfg['stripe_account']);
$out['stripeWebhookConfigured']=isset($cfg['stripe_webhook_secret'])&&str_starts_with($cfg['stripe_webhook_secret'],'whsec_');
echo json_encode($out);
'''.replace('TOKEN_HASH',hashlib.sha256(token.encode()).hexdigest())
 assert not exists(probe),'Probe path collision'
 try:
  with s.open(probe,'wb') as f:f.write(php.encode())
  s.chmod(probe,0o644)
  url='https://lakelandtouring.uk/'+probe_name
  try:
   with urllib.request.urlopen(url,timeout=35) as r:raise RuntimeError('Unauthenticated probe unexpectedly accessible')
  except urllib.error.HTTPError as e:assert e.code==404,'Probe authentication gate failed'
  req=urllib.request.Request(url,headers={'X-Touring-Diagnostic':token,'Cache-Control':'no-cache'})
  with urllib.request.urlopen(req,timeout=35) as r:
   assert r.status==200
   web=json.loads(r.read())
  allowed={'webConfigEnvironmentSet','webConfigFileExists','webConfigOutsideDocumentRoot','configLoadFailed','enabled','policy_verified','inventory_verified','merchant_verified','calendarPeriodCount','inventoryHorizonConfigured','stripeSecretConfigured','stripeAccountConfigured','stripeWebhookConfigured'}
  assert set(web)<=allowed and all(isinstance(v,(bool,int)) for v in web.values())
  result['webRuntime']=web
 finally:
  if exists(probe):s.remove(probe)
  result['temporaryProbeRemoved']=not exists(probe)
  assert result['temporaryProbeRemoved'],'Probe cleanup failed'
 result['readOnly']=False
 result['scopeLimit']='Existing hosting files and private databases unchanged. One temporary header-authenticated web-process probe was created and removed. No credential values or provider/payment requests.'
 Path('touring-readiness-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
finally:s.close();t.close()
