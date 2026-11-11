"""Exercise real PHP JSON handlers without calling Stripe or sending messages."""
import json, os, socket, subprocess, tempfile, time, urllib.request, urllib.error, shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1] / 'public'
with tempfile.TemporaryDirectory(prefix='touring-http-') as td:
    private = Path(td)
    fixture_root = private / 'webroot'
    shutil.copytree(root, fixture_root)
    config = private / 'config.php'
    config.write_text("<?php return " + "[" + ",".join([
        "'enabled'=>true", "'policy_verified'=>true", "'inventory_verified'=>true", "'merchant_verified'=>true",
        "'origin'=>'https://lakelandtouring.uk'", "'private_dir'=>" + repr(td),
        "'stripe_secret'=>'sk_test_fixture'", "'stripe_webhook_secret'=>'whsec_fixture'", "'stripe_account'=>'acct_fixture'",
        "'live_mode'=>false", "'terms_version'=>'fixture'", "'inventory_through'=>'2030-12-31'",
        "'booking_deposit_pence'=>25000", "'balance_weeks'=>12", "'blocked'=>[]",
        "'periods'=>[['start'=>'2030-03-01','end'=>'2030-04-01','prices'=>[7=>59500]]]"
    ]) + "];" )
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    env=dict(os.environ,TOURING_BOOKING_CONFIG=str(config))
    server=subprocess.Popen(['php','-S',f'127.0.0.1:{port}','-t',str(fixture_root)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    base=f'http://127.0.0.1:{port}'
    def call(path,data=None,cookie=None,origin=None,kind='application/json'):
        headers={'Content-Type':kind}
        if cookie: headers['Cookie']=cookie
        if origin: headers['Origin']=origin
        req=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=headers)
        try:r=urllib.request.urlopen(req,timeout=5)
        except urllib.error.HTTPError as e:r=e
        return r.status, dict(r.headers),json.loads(r.read())
    try:
        for _ in range(50):
            try:
                with socket.create_connection(('127.0.0.1',port),timeout=.1):break
            except OSError:time.sleep(.1)
        # The shipped release lock wins even over an otherwise enabled private config.
        for route,data in [('/api/availability.php',None),('/api/quote.php',{}),('/api/release-hold.php',{}),('/api/create-checkout-session.php',{}),('/booking-webhook.php',{})]:
            status,headers,response=call(route,data)
            assert status==503 and 'contact us' in response['error'] and 'Set-Cookie' not in headers
        assert not (private/'touring-bookings.sqlite').exists()
        (fixture_root/'api/booking-disabled.php').unlink()
        status,headers,availability=call('/api/availability.php')
        assert status==200 and availability['bookings']==[]
        cookie=headers['Set-Cookie'].split(';')[0]
        assert 'HttpOnly' in headers['Set-Cookie'] and 'secure' in headers['Set-Cookie'].lower()
        body={'start':'2030-03-01','end':'2030-03-08','csrf':availability['csrf']}
        status,_,q=call('/api/quote.php',body,cookie)
        assert status==200 and q['hire_pence']==59500 and q['pay_now_pence']==25000
        assert 899 <= q['hold_until']-q['server_time'] <= 900
        status,_,again=call('/api/quote.php',body,cookie)
        assert status==200 and again['hold_until']==q['hold_until']
        _,_,mine=call('/api/availability.php',cookie=cookie)
        assert mine['own_hold']['start']==body['start'] and mine['holds']==[]
        _,headers2,other=call('/api/availability.php')
        cookie2=headers2['Set-Cookie'].split(';')[0]
        assert len(other['holds'])==1 and other['own_hold'] is None
        assert not any(k in other['holds'][0] for k in ['id','email','name','customer','quote'])
        assert call('/api/quote.php',{**body,'csrf':other['csrf']},cookie2)[0]==409
        assert call('/api/release-hold.php',{'csrf':'wrong'},cookie)[0]==403
        assert call('/api/release-hold.php',{'csrf':availability['csrf']},cookie)[0]==200
        assert call('/api/quote.php',{**body,'csrf':other['csrf']},cookie2)[0]==200
        assert call('/api/quote.php',{**body,'csrf':'bad'},cookie)[0]==403
        assert call('/api/quote.php',body,cookie,'https://attacker.invalid')[0]==403
        assert call('/api/quote.php',body,cookie,kind='text/plain')[0]==415
        assert call('/api/quote.php',{**body,'end':'2030-03-07'},cookie)[0]==422
        assert call('/api/quote.php')[0]==405
        assert call('/api/create-checkout-session.php',body,cookie)[0]==422
        assert call('/booking-webhook.php',{},cookie)[0]==400
        config.write_text("<?php return ['enabled'=>false];")
        assert call('/api/availability.php')[0]==503
        print('Passed HTTP release-lock, fixed 15-minute hold, two-session exclusivity, privacy, release, CSRF, origin, method and pricing checks; no external requests.')
    finally:
        server.terminate();server.wait(timeout=5)
