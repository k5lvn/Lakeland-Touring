"""Real HTTP owner/admin journeys against disposable private SQLite storage."""
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
checks = 0


def check(value):
    global checks
    assert value, f'Failed check {checks + 1}'
    checks += 1


class Client:
    def __init__(self, base):
        self.base, self.cookie = base, ''
    def request(self, path='', fields=None):
        class Stop(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args):
                return None
        req = urllib.request.Request(self.base + path,
            data=None if fields is None else urllib.parse.urlencode(fields).encode(),
            headers={'Cookie': self.cookie})
        try:
            response = urllib.request.build_opener(Stop).open(req, timeout=10)
        except urllib.error.HTTPError as error:
            response = error
        for value in response.headers.get_all('Set-Cookie', []):
            if value.startswith('touringgarage='):
                self.cookie = value.split(';')[0]
        body = response.read().decode()
        if response.status == 303:
            return self.request(response.headers['Location'].replace('https://lakelandtouring.uk/garage.php', ''))
        return response.status, body
    def post(self, action, **fields):
        _, page = self.request('?view=bookings')
        token = re.search(r'name="csrf" value="([a-f0-9]+)"', page)[1]
        return self.request('?view=bookings', dict(csrf=token, action=action, **fields))[1]
    def login(self, email):
        _, page = self.request()
        token = re.search(r'name="csrf" value="([a-f0-9]+)"', page)[1]
        return self.request('', dict(action='login', csrf=token, email=email, password='fixture-password-123'))[1]


with tempfile.TemporaryDirectory(prefix='garage-bookings-') as folder:
    root = Path(folder)
    public, private = root / 'public', root / '.touring-garage'
    public.mkdir()
    private.mkdir(mode=0o700)
    for source, target in [('garage.php', 'garage.php'), ('bookings.php', 'garage-bookings.php'), ('bookings-ui.php', 'garage-bookings-ui.php'), ('router.php', 'router.php'), ('garage.css', 'garage.css')]:
        shutil.copyfile(ROOT / source, public / target)
    shutil.copyfile(ROOT.parent / 'booking-backend/operations.php', public / 'booking-policy.php')
    subprocess.run(['php', str(ROOT/'test_policy.php'), str(public)], check=True)
    for name in ['garage-header.html', 'garage-footer.html']:
        (public / name).write_text('<header></header>')
    (public / 'styles.css').write_text('body{background:#091317;color:white;font:16px Arial;margin:0}*{box-sizing:border-box}a{color:#64e9e2}.button{display:inline-block;background:#125b59;color:white;padding:12px;border:0;border-radius:6px;font:inherit}')
    (public / 'brand.css').write_text('')
    for name in ['owner-booking-terms.html', 'garage-booking-privacy.html']:
        (public / name).write_text('<h1>Fixture review terms</h1>')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    with (root / 'server.log').open('w+') as log:
        server = subprocess.Popen(['php', '-d', 'sendmail_path=/bin/false', '-S', f'127.0.0.1:{port}', '-t', str(public), str(public / 'router.php')], stdout=log, stderr=log)
        try:
            base = f'http://127.0.0.1:{port}/garage.php'
            for _ in range(50):
                try:
                    Client(base).request()
                    break
                except OSError:
                    time.sleep(.1)
            db = sqlite3.connect(private / 'garage.sqlite')
            password = subprocess.check_output(['php', '-r', 'echo password_hash("fixture-password-123",PASSWORD_DEFAULT);'], text=True)
            for index, email in enumerate(['a@example.test', 'b@example.test', 'LakelandTouring@Worx365Group.uk'], 1):
                db.execute('INSERT INTO owners(id,email,password,name,verified) VALUES(?,?,?,?,1)', (index, email.lower(), password, f'Owner {index}'))
            for index in [1, 2]:
                db.execute('INSERT INTO vehicles(id,owner_id,title,type,location,description,price,contact,status,paid_until,created) VALUES(?,?,?,?,?,?,?,?,?,?,?)', (index, index, f'Caravan {index}', 'Touring caravan', 'Carlisle', 'Fixture only', '£650 per week', 'owner@example.test', 'live', int(time.time())+86400*365, int(time.time())))
            db.commit()
            a, b, admin, anon = [Client(base) for _ in range(4)]
            check('Hello' in a.login('a@example.test'))
            check(a.request('?view=bookings')[0] == 503)
            check(db.execute("SELECT count(*) FROM sqlite_master WHERE name='garage_bookings'").fetchone()[0] == 0)
            # A request cannot activate the private feature flag.
            check(a.request('?view=bookings&enabled=1')[0] == 503)
            (private / 'booking-config.php').write_text("<?php return ['enabled'=>true,'non_working_dates'=>[]];")
            check('Hello' in b.login('b@example.test'))
            check('Hello' in admin.login('LakelandTouring@Worx365Group.uk'))
            check(anon.request('?view=bookings')[0] == 403)
            check('Accept booking plan' in a.request('?view=bookings')[1])
            check('session expired' in a.request('?view=bookings', dict(action='accept-plan', vehicle_id=1, accept_plan=1, csrf='wrong'))[1])
            check('not found' in b.post('accept-plan', vehicle_id=1, accept_plan=1))
            check('Accept the £49' in a.post('accept-plan', vehicle_id=1))
            a.post('accept-plan', vehicle_id=1, accept_plan=1)
            a.post('accept-plan', vehicle_id=1, accept_plan=1)
            check(db.execute('SELECT count(*) FROM garage_plan_acceptances').fetchone()[0] == 1)
            check(db.execute('SELECT annual_pence,booking_pence FROM garage_plan_acceptances').fetchone() == (4900, 2500))
            original_expiry = db.execute('SELECT paid_until FROM vehicles WHERE id=1').fetchone()[0]
            check(original_expiry > time.time())
            arrival = dt.date.today() + dt.timedelta(days=140)
            while arrival.weekday() > 4:
                arrival += dt.timedelta(days=1)
            booking = dict(vehicle_id=1, arrival=arrival.isoformat(), departure=(arrival+dt.timedelta(days=7)).isoformat(), hire_amount='650.00', customer_name='PRIVATE-CUSTOMER <script>', customer_email='private-customer@example.test', customer_phone='PRIVATE-PHONE')
            check('administrator access' in a.post('create-booking', **booking))
            check('owner must accept' in admin.post('create-booking', **{**booking, 'vehicle_id':2}))
            admin.post('create-booking', **booking)
            bid = db.execute('SELECT id FROM garage_bookings').fetchone()[0]
            check(db.execute('SELECT hire_pence,agreed_commission_pence FROM garage_bookings').fetchone() == (65000,2500))
            check('overlap' in admin.post('create-booking', **booking))
            page = a.request('?view=bookings')[1]
            check(all(secret not in page for secret in ['PRIVATE-CUSTOMER', 'private-customer@example.test', 'PRIVATE-PHONE']))
            check(bid not in b.request('?view=bookings')[1])
            check('not found' in b.post('confirm-deposit', booking_id=bid, received=1, reference='receipt'))
            check('Only the vehicle owner' in admin.post('confirm-deposit', booking_id=bid, received=1, reference='receipt'))
            check('owner must confirm' in admin.post('confirm-booking', booking_id=bid))
            check('actually reached you' in a.post('confirm-deposit', booking_id=bid, reference='receipt'))
            check(db.execute('SELECT deposit_confirmed_pence FROM garage_bookings').fetchone()[0] == 0)
            check('deposit first' in a.post('confirm-balance', booking_id=bid, received=1, reference='receipt'))
            a.post('confirm-deposit', booking_id=bid, received=1, reference='receipt-deposit')
            count = db.execute('SELECT count(*) FROM garage_booking_audit').fetchone()[0]
            a.post('confirm-deposit', booking_id=bid, received=1, reference='duplicate')
            check(db.execute('SELECT count(*) FROM garage_booking_audit').fetchone()[0] == count)
            check('Only Touring' in a.post('confirm-booking', booking_id=bid))
            admin.post('confirm-booking', booking_id=bid)
            check(db.execute('SELECT state FROM garage_bookings').fetchone()[0] == 'confirmed')
            check('PRIVATE-CUSTOMER' not in a.request('?view=bookings')[1])
            check('must be due' in admin.post('record-fee', booking_id=bid, received=1, reference='fee'))
            page = a.post('confirm-balance', booking_id=bid, received=1, reference='receipt-balance')
            check('PRIVATE-CUSTOMER &lt;script&gt;' in page and '<script>' not in page)
            check('private-customer@example.test' in page and 'PRIVATE-PHONE' in page)
            check('administrator access' in a.post('record-fee', booking_id=bid, received=1, reference='fee'))
            check('actually received' in admin.post('record-fee', booking_id=bid, reference='fee'))
            admin.post('record-fee', booking_id=bid, received=1, reference='fee')
            admin.post('record-fee', booking_id=bid, received=1, reference='duplicate')
            check(db.execute("SELECT count(*) FROM garage_booking_audit WHERE event='admin_fee_received'").fetchone()[0] == 1)
            check('Handover requires' in a.post('authorise-handover', booking_id=bid, checked=1))
            check('evidence check' in a.post('verify-evidence', booking_id=bid, kind='insurance', reference='fixture'))
            a.post('verify-evidence', booking_id=bid, kind='insurance', verified=1, reference='insurance-ref')
            check(db.execute('SELECT insurance_by FROM garage_bookings').fetchone()[0] == 1)
            check('arrival-day appointment' in a.post('appointment', booking_id=bid, appointment=arrival.isoformat()+'T18:00'))
            check('administrator access' in a.post('cancel-booking', booking_id=bid, reason='fixture'))
            admin.post('cancel-booking', booking_id=bid, reason='Fixture cancellation')
            check('closed to changes' in a.post('confirm-balance', booking_id=bid, received=1, reference='late'))
            check('administrator access' in a.post('terminate-advertising', owner_id=1, reason='fixture', reviewed=1))
            admin.post('terminate-advertising', owner_id=1, reason='Reviewed diversion evidence reference', reviewed=1)
            check(db.execute('SELECT status FROM vehicles WHERE id=1').fetchone()[0] == 'draft')
            check('Advertising rights have ended' in a.post('accept-plan', vehicle_id=1, accept_plan=1))
            check('PRIVATE-CUSTOMER' not in anon.request('?view=browse')[1])
            for sql in ['DELETE FROM garage_booking_audit', 'UPDATE garage_booking_audit SET event="changed"', 'UPDATE garage_plan_acceptances SET booking_pence=1']:
                try:
                    db.execute(sql)
                    raise AssertionError('Immutable records changed')
                except sqlite3.IntegrityError:
                    check(True)
                    db.rollback()
            check(db.execute('SELECT paid_until FROM vehicles WHERE id=1').fetchone()[0] == original_expiry)
            if '--browser' in __import__('sys').argv:
                subprocess.run(['node', str(ROOT/'test_bookings.cjs'), base], check=True, env=os.environ)
            print(f'Passed {checks} owner/admin HTTP checks: private feature flag, CSRF, isolation, acceptance, payment evidence, fee receipt, redaction, cancellation, restriction and immutable audit.')
        finally:
            server.terminate()
            server.wait(timeout=10)
            log.seek(0)
            output = log.read()
            assert 'Fatal error' not in output, output
