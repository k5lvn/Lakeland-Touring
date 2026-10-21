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
 Path('touring-readiness-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
finally:s.close();t.close()
