import urllib.request,urllib.parse,http.cookiejar,re,sqlite3,time,json
BASE='http://127.0.0.1:8767/garage.php'
class Client:
 def __init__(self):self.cookie=''
 def get(self,path=''):
  r=urllib.request.urlopen(urllib.request.Request(BASE+path,headers={'Cookie':self.cookie}));self.cookies(r);return r.read().decode()
 def cookies(self,r):
  for val in r.headers.get_all('Set-Cookie',[]):
   if val.startswith('touringgarage='):self.cookie=val.split(';')[0]
 def post(self,fields,path=''):
  body=urllib.parse.urlencode(fields).encode();req=urllib.request.Request(BASE+path,data=body,headers={'Cookie':self.cookie,'Content-Type':'application/x-www-form-urlencoded'})
  # Preserve session cookies on redirect, including regenerated login session IDs.
  class Stop(urllib.request.HTTPRedirectHandler):
   def redirect_request(self,*args):return None
  op=urllib.request.build_opener(Stop)
  try:r=op.open(req)
  except urllib.error.HTTPError as e:r=e
  self.cookies(r);status=r.code;text=r.read().decode()
  if status==303:return self.get(r.headers['Location'].replace('https://lakelandtouring.uk/garage.php',''))
  return text
 def csrf(self,html):return re.search('name="csrf" value="([a-f0-9]+)"',html)[1]
a=Client();s=a.get();csrf=a.csrf(s)
assert 'Sign in' in s
assert 'session expired' in a.post({'action':'register','email':'a@example.test','password':'long-test-password','name':'Owner A','terms':'1','csrf':'invalid'})
s=a.post({'action':'register','email':'a@example.test','password':'long-test-password','name':'Owner A','terms':'1','csrf':csrf});assert 'verification link has been sent' in s
conn=sqlite3.connect('garage-test/.touring-garage/garage.sqlite');conn.execute('UPDATE owners SET verified=1');conn.commit()
s=a.post({'action':'login','email':'a@example.test','password':'wrong','csrf':csrf});assert 'not recognised' in s
s=a.post({'action':'login','email':'a@example.test','password':'long-test-password','csrf':csrf});assert 'Hello, Owner A' in s
csrf=a.csrf(s)
s=a.post({'action':'save','id':'0','title':'Test caravan','type':'Touring caravan','location':'Carlisle','price':'£650 per week','contact':'owner@example.test','description':'A genuine test caravan','responsibility':'1','csrf':csrf});assert 'Vehicle saved as a draft' in s
vid=conn.execute('SELECT id FROM vehicles').fetchone()[0]
assert 'Test caravan' not in a.get('?view=browse')
s=a.post({'action':'approve','listing':str(vid),'checked':'1','paid_until':'2027-10-15','csrf':csrf});assert 'Administrator access required' in s
assert conn.execute('SELECT status FROM vehicles WHERE id=?',(vid,)).fetchone()[0]=='draft'
b=Client();s=b.get();csrf2=b.csrf(s);s=b.post({'action':'register','email':'b@example.test','password':'long-test-password','name':'Owner B','terms':'1','csrf':csrf2});conn.execute('UPDATE owners SET verified=1');conn.commit()
s=b.post({'action':'login','email':'b@example.test','password':'long-test-password','csrf':csrf2});assert 'Owner B' in s
try:b.get('?view=edit&id='+str(vid));raise AssertionError('Cross owner access succeeded')
except urllib.error.HTTPError as e:assert e.code==404
s=b.post({'action':'unpublish','id':str(vid),'csrf':b.csrf(s)});assert 'not found in your garage' in s
# Expired paid listings remain hidden.
conn.execute('UPDATE vehicles SET status="live",paid_until=? WHERE id=?',(int(time.time())-1,vid));conn.commit();assert 'Test caravan' not in a.get('?view=browse')
conn.execute('UPDATE vehicles SET status="live",paid_until=? WHERE id=?',(int(time.time())+86400,vid));conn.commit();assert 'Test caravan' in a.get('?view=browse')
s=a.get('?view=vehicle&id='+str(vid));assert 'Enquire with the owner' in s and 'Independent owner advertisements' in s
print('PASS: CSRF, registration, login, owner isolation, payment moderation restriction, expiry and public responsibility notice.')
