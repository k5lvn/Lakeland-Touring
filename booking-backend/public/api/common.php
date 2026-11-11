<?php
declare(strict_types=1);
namespace TouringBooking;

use DateTimeImmutable;
use DateTimeZone;
use PDO;
use RuntimeException;
use Throwable;

final class Failure extends RuntimeException {
    public function __construct(string $message, public int $status = 422) { parent::__construct($message); }
}
function dateValue(string $value): DateTimeImmutable {
    $d = DateTimeImmutable::createFromFormat('!Y-m-d', $value, new DateTimeZone('Europe/London'));
    if (!$d || $d->format('Y-m-d') !== $value) throw new Failure('Invalid date.');
    return $d;
}
function overlaps(string $a, string $b, string $c, string $d): bool { return $a < $d && $c < $b; }
function quote(array $cfg, string $start, string $end, ?DateTimeImmutable $today = null): array {
    $a = dateValue($start); $b = dateValue($end);
    $today ??= new DateTimeImmutable('today', new DateTimeZone('Europe/London'));
    if ($a < $today || $b <= $a) throw new Failure('Choose valid future collection and return dates.');
    if (empty($cfg['inventory_through']) || $end > $cfg['inventory_through']) throw new Failure('Please contact us to confirm those dates.');
    $nights = (int)$a->diff($b)->days;
    $matches = array_values(array_filter($cfg['periods'], fn($p) => $start >= $p['start'] && $end <= $p['end']));
    if (count($matches) !== 1 || !isset($matches[0]['prices'][$nights])) throw new Failure('Please contact us for a quote for this duration or seasonal changeover.');
    foreach ($cfg['blocked'] as $block) if (overlaps($start, $end, $block['start'], $block['end'])) throw new Failure('Those dates are unavailable.', 409);
    $hire = $matches[0]['prices'][$nights];
    if (!is_int($hire) || $hire <= 0) throw new Failure('Pricing is unavailable.', 503);
    $due = $a->modify('-' . $cfg['balance_weeks'] . ' weeks');
    $now = $due <= $today ? $hire : min($hire, $cfg['booking_deposit_pence']);
    return ['start'=>$start,'end'=>$end,'nights'=>$nights,'hire_pence'=>$hire,
        'pay_now_pence'=>$now,'balance_pence'=>$hire-$now,'balance_due_date'=>$due->format('Y-m-d')];
}
function config(): array {
    if (is_file(__DIR__.'/booking-disabled.php')) throw new Failure('Online booking is unavailable. Please contact us.', 503);
    $path = getenv('TOURING_BOOKING_CONFIG') ?: '';
    $real = realpath($path); $doc = realpath($_SERVER['DOCUMENT_ROOT'] ?? '') ?: '';
    if (!$real || !$doc || str_starts_with($real, $doc . DIRECTORY_SEPARATOR)) throw new Failure('Online booking is unavailable. Please contact us.', 503);
    $cfg = require $real;
    foreach (['enabled','policy_verified','inventory_verified','merchant_verified'] as $flag) {
        if (($cfg[$flag] ?? false) !== true) throw new Failure('Online booking is unavailable. Please contact us.', 503);
    }
    if (($cfg['origin'] ?? '') !== 'https://lakelandtouring.uk' || empty($cfg['terms_version']) ||
        !preg_match('/^acct_[A-Za-z0-9]+$/', $cfg['stripe_account'] ?? '') ||
        !preg_match('/^sk_(test|live)_/', $cfg['stripe_secret'] ?? '') ||
        !str_starts_with($cfg['stripe_webhook_secret'] ?? '', 'whsec_') ||
        !is_int($cfg['booking_deposit_pence'] ?? null) || $cfg['booking_deposit_pence'] <= 0 ||
        !is_int($cfg['balance_weeks'] ?? null) || $cfg['balance_weeks'] < 0 || $cfg['balance_weeks'] > 52) {
        throw new Failure('Online booking configuration is incomplete.', 503);
    }
    if (str_starts_with($cfg['stripe_secret'], 'sk_live_') !== ($cfg['live_mode'] === true)) throw new Failure('Payment mode mismatch.', 503);
    dateValue($cfg['inventory_through']);
    if (!is_array($cfg['periods']) || !$cfg['periods'] || !is_array($cfg['blocked'])) throw new Failure('Availability has not been configured.', 503);
    foreach (array_merge($cfg['periods'], $cfg['blocked']) as $period) {
        if (dateValue($period['end']) <= dateValue($period['start'])) throw new Failure('Invalid calendar configuration.', 503);
    }
    return $cfg;
}
function db(array $cfg): PDO {
    $dir = realpath($cfg['private_dir']); $doc = realpath($_SERVER['DOCUMENT_ROOT'] ?? '') ?: '';
    if (!$dir || !$doc || $dir === $doc || str_starts_with($dir, $doc . DIRECTORY_SEPARATOR) || !is_writable($dir)) throw new Failure('Booking storage is unavailable.', 503);
    umask(0077);
    $db = new PDO('sqlite:' . $dir . '/touring-bookings.sqlite', null, null, [PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION]);
    $db->exec('PRAGMA busy_timeout=10000');
    $db->exec('CREATE TABLE IF NOT EXISTS bookings (id TEXT PRIMARY KEY, start TEXT NOT NULL, end TEXT NOT NULL, state TEXT NOT NULL, quote TEXT NOT NULL, customer TEXT NOT NULL, session_id TEXT UNIQUE, checkout_url TEXT, created INTEGER NOT NULL, terms_version TEXT NOT NULL)');
    $db->exec('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, processed INTEGER NOT NULL)');
    $db->exec('BEGIN IMMEDIATE');
    try {
        $columns=$db->query('PRAGMA table_info(bookings)')->fetchAll(PDO::FETCH_COLUMN,1);
        if (!in_array('hold_until',$columns,true)) $db->exec('ALTER TABLE bookings ADD COLUMN hold_until INTEGER');
        $db->exec('COMMIT');
    } catch(Throwable $e) {$db->exec('ROLLBACK');throw $e;}
    return $db;
}
function available(PDO $db, string $start, string $end): void {
    $q = $db->prepare("SELECT COUNT(*) FROM bookings WHERE (state IN ('creating','pending','paid') OR (state='held' AND hold_until > strftime('%s','now'))) AND start < ? AND end > ?");
    $q->execute([$end,$start]);
    if ($q->fetchColumn()) throw new Failure('Those dates are no longer available. Please choose again.',409);
}
// A selection hold lasts exactly 900 seconds; polling never extends it.
function hold(PDO $db, array $cfg, string $id, array $q, ?int $now=null): array {
    $now ??= time();
    $db->exec('BEGIN IMMEDIATE');
    try {
        $db->prepare("UPDATE bookings SET state='expired' WHERE state='held' AND hold_until<=?")->execute([$now]);
        $find=$db->prepare('SELECT * FROM bookings WHERE id=?');$find->execute([$id]);$row=$find->fetch(PDO::FETCH_ASSOC);
        if ($row) {
            if ($row['state']!=='held' || $row['quote']!==json_encode($q)) throw new Failure('Release your current dates before selecting another stay.',409);
            $db->exec('COMMIT');return $row;
        }
        available($db,$q['start'],$q['end']);
        $until=$now+900;
        $db->prepare('INSERT INTO bookings (id,start,end,state,quote,customer,created,terms_version,hold_until) VALUES (?,?,?,?,?,?,?,?,?)')
            ->execute([$id,$q['start'],$q['end'],'held',json_encode($q),'{}',$now,$cfg['terms_version'],$until]);
        $db->exec('COMMIT');return ['hold_until'=>$until,'state'=>'held'];
    } catch(Throwable $e) {$db->exec('ROLLBACK');throw $e;}
}
function claimHold(PDO $db, string $id, array $q, array $customer): array {
    $db->exec('BEGIN IMMEDIATE');
    try {
        $find=$db->prepare('SELECT * FROM bookings WHERE id=?');$find->execute([$id]);$row=$find->fetch(PDO::FETCH_ASSOC);
        if (!$row || $row['quote']!==json_encode($q) || (int)$row['hold_until']<=time() || !in_array($row['state'],['held','creating','pending'],true)) throw new Failure('Your hold has expired. Please choose your dates again.',409);
        if ($row['state']==='held') {
            $db->prepare("UPDATE bookings SET state='creating',customer=? WHERE id=?")->execute([json_encode($customer),$id]);
            $row['customer']=json_encode($customer);$row['state']='creating';
        } elseif ($row['customer']!==json_encode($customer)) throw new Failure('Checkout details have changed. Please contact us.',409);
        $db->exec('COMMIT');return $row;
    } catch(Throwable $e) {$db->exec('ROLLBACK');throw $e;}
}
// Release only after a Stripe session is demonstrably unable to take payment.
// A creating row without its Stripe ID stays blocked for manual reconciliation.
function releaseHold(PDO $db, array $cfg, string $id, ?callable $gateway=null): bool {
    $find=$db->prepare('SELECT * FROM bookings WHERE id=?');$find->execute([$id]);$row=$find->fetch(PDO::FETCH_ASSOC);
    if (!$row || in_array($row['state'],['expired','cancelled'],true)) return true;
    if ($row['state']==='held') {
        $db->prepare("UPDATE bookings SET state='cancelled' WHERE id=? AND state='held'")->execute([$id]);
        $find->execute([$id]);$current=$find->fetch(PDO::FETCH_ASSOC);
        return in_array($current['state'],['cancelled','expired'],true);
    }
    if ($row['state']==='paid' || !$row['session_id']) return false;
    $gateway ??= fn($method,$path)=>stripe($cfg,$method,$path);
    $path='checkout/sessions/'.rawurlencode($row['session_id']);
    $s=$gateway('GET',$path);
    if (($s['id']??null)!==$row['session_id'] || ($s['client_reference_id']??null)!==$id || ($s['livemode']??null)!==$cfg['live_mode']) throw new Failure('Checkout reconciliation required.',409);
    if (($s['status']??'')==='open') $s=$gateway('POST',$path.'/expire');
    if (($s['id']??null)!==$row['session_id'] || ($s['client_reference_id']??null)!==$id || ($s['livemode']??null)!==$cfg['live_mode']) throw new Failure('Checkout reconciliation required.',409);
    if (($s['status']??'')!=='expired' || ($s['payment_status']??'')!=='unpaid') return false;
    $db->prepare("UPDATE bookings SET state='expired' WHERE id=? AND state IN ('creating','pending') AND session_id=?")->execute([$id,$row['session_id']]);
    $find->execute([$id]);return $find->fetch(PDO::FETCH_ASSOC)['state']==='expired';
}
function reconcileHolds(PDO $db, array $cfg, ?callable $gateway=null): void {
    $db->exec("UPDATE bookings SET state='expired' WHERE state='held' AND hold_until<=strftime('%s','now')");
    $rows=$db->query("SELECT id FROM bookings WHERE state IN ('creating','pending') AND hold_until<=strftime('%s','now') ORDER BY hold_until LIMIT 20")->fetchAll(PDO::FETCH_COLUMN);
    foreach($rows as $id) releaseHold($db,$cfg,$id,$gateway);
}
function session(): void {
    if (session_status() === PHP_SESSION_NONE) {
        session_name('touring_booking');
        session_start(['use_strict_mode'=>1,'cookie_secure'=>true,'cookie_httponly'=>true,'cookie_samesite'=>'Lax']);
    }
    $_SESSION['csrf'] ??= bin2hex(random_bytes(32));
    $_SESSION['booking_id'] ??= bin2hex(random_bytes(24));
}
function body(array $cfg): array {
    if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') throw new Failure('Method not allowed.',405);
    if (strtolower(trim(explode(';', $_SERVER['CONTENT_TYPE'] ?? '')[0])) !== 'application/json') throw new Failure('JSON required.',415);
    if (isset($_SERVER['HTTP_ORIGIN']) && $_SERVER['HTTP_ORIGIN'] !== $cfg['origin']) throw new Failure('Invalid origin.',403);
    $raw = file_get_contents('php://input', false, null, 0, 16385);
    if (strlen($raw) > 16384) throw new Failure('Request too large.',413);
    $data = json_decode($raw,true);
    if (!is_array($data)) throw new Failure('Invalid request.');
    session();
    if (!is_string($data['csrf'] ?? null) || !hash_equals($_SESSION['csrf'],$data['csrf'])) throw new Failure('Please refresh availability and try again.',403);
    return $data;
}
function customer(array $data): array {
    $out=[];
    foreach (['name'=>160,'email'=>254,'phone'=>40,'vehicle'=>160,'registration'=>30,'experience'=>30,'region'=>20,'destination'=>300] as $field=>$max) {
        if (!is_string($data[$field] ?? null)) throw new Failure('Please complete all booking details.');
        $out[$field]=trim($data[$field]);
        if ($out[$field]==='' || strlen($out[$field])>$max || preg_match('/[\x00-\x1F\x7F]/',$out[$field])) throw new Failure('Please check your booking details.');
    }
    if (!filter_var($out['email'],FILTER_VALIDATE_EMAIL) || !in_array($out['region'],['England','Scotland','Wales'],true) ||
        !in_array($out['experience'],['Experienced','Some experience','First time'],true) ||
        ($data['terms']??'')!=='accepted' || ($data['travel_policy']??'')!=='accepted') throw new Failure('Please check your details and accept the booking rules.');
    return $out;
}
function stripe(array $cfg, string $method, string $path, array $params=[], ?string $idempotency=null): array {
    $ch=curl_init('https://api.stripe.com/v1/'.$path);
    $headers=['Authorization: Bearer '.$cfg['stripe_secret']];
    if ($idempotency) $headers[]='Idempotency-Key: '.$idempotency;
    curl_setopt_array($ch,[CURLOPT_RETURNTRANSFER=>true,CURLOPT_CONNECTTIMEOUT=>10,CURLOPT_TIMEOUT=>25,
        CURLOPT_CUSTOMREQUEST=>$method,CURLOPT_HTTPHEADER=>$headers,CURLOPT_FOLLOWLOCATION=>false]);
    if ($method==='POST') curl_setopt($ch,CURLOPT_POSTFIELDS,http_build_query($params));
    $raw=curl_exec($ch); $status=curl_getinfo($ch,CURLINFO_RESPONSE_CODE); curl_close($ch);
    $obj=is_string($raw)?json_decode($raw,true):null;
    if ($status<200 || $status>=300 || !is_array($obj)) throw new Failure('Secure checkout is temporarily unavailable. Please contact us.',503);
    return $obj;
}
function reserve(PDO $db, array $cfg, string $id, array $q, array $customer): array {
    $db->exec('BEGIN IMMEDIATE');
    try {
        $find=$db->prepare('SELECT * FROM bookings WHERE id=?'); $find->execute([$id]); $existing=$find->fetch(PDO::FETCH_ASSOC);
        if ($existing) {
            if ($existing['quote']!==json_encode($q) || $existing['customer']!==json_encode($customer) || !in_array($existing['state'],['creating','pending'],true)) throw new Failure('Refresh the page before starting another booking.',409);
            $db->exec('COMMIT'); return $existing;
        }
        available($db,$q['start'],$q['end']);
        $created=time();
        $db->prepare('INSERT INTO bookings (id,start,end,state,quote,customer,created,terms_version) VALUES (?,?,?,?,?,?,?,?)')
            ->execute([$id,$q['start'],$q['end'],'creating',json_encode($q),json_encode($customer),$created,$cfg['terms_version']]);
        $db->exec('COMMIT'); return ['state'=>'creating','checkout_url'=>null,'created'=>$created];
    } catch (Throwable $e) { $db->exec('ROLLBACK'); throw $e; }
}
function verifyEvent(string $raw, string $signature, string $secret, ?int $now=null): array {
    $parts=[]; foreach (explode(',',$signature) as $part) { $pair=explode('=',$part,2); if(count($pair)===2)$parts[$pair[0]][]=$pair[1]; }
    $ts=$parts['t'][0]??'';
    if (!ctype_digit($ts) || abs(($now??time())-(int)$ts)>300) throw new Failure('Invalid signature.',400);
    $expected=hash_hmac('sha256',$ts.'.'.$raw,$secret);
    $ok=false; foreach ($parts['v1']??[] as $value) $ok=hash_equals($expected,$value)||$ok;
    $event=json_decode($raw,true);
    if (!$ok || !is_array($event) || !is_string($event['id']??null)) throw new Failure('Invalid signature.',400);
    return $event;
}
function processEvent(PDO $db, array $event, bool $live): void {
    if (($event['livemode']??null)!==$live) throw new Failure('Payment mode mismatch.',400);
    $db->exec('BEGIN IMMEDIATE');
    try {
        $seen=$db->prepare('SELECT id FROM events WHERE id=?'); $seen->execute([$event['id']]);
        if ($seen->fetchColumn()) { $db->exec('COMMIT'); return; }
        if (in_array($event['type']??'', ['checkout.session.completed','checkout.session.expired'],true)) {
            $s=$event['data']['object']??[]; $id=$s['client_reference_id']??'';
            $q=$db->prepare('SELECT * FROM bookings WHERE id=?'); $q->execute([$id]); $row=$q->fetch(PDO::FETCH_ASSOC);
            if (!$row || ($row['session_id'] && $row['session_id']!==($s['id']??null))) throw new Failure('Booking reconciliation required.',409);
            if ($event['type']==='checkout.session.completed') {
                $price=json_decode($row['quote'],true);
                if (($s['payment_status']??'')!=='paid' || ($s['currency']??'')!=='gbp' || ($s['amount_total']??null)!==$price['pay_now_pence'] || ($s['livemode']??null)!==$live) throw new Failure('Payment reconciliation required.',409);
                if (!in_array($row['state'],['creating','pending','paid'],true)) throw new Failure('Booking reconciliation required.',409);
                $db->prepare("UPDATE bookings SET state='paid',session_id=? WHERE id=?")->execute([$s['id'],$id]);
            } else {
                $db->prepare("UPDATE bookings SET state='expired',session_id=? WHERE id=? AND state IN ('creating','pending')")->execute([$s['id'],$id]);
            }
        }
        $db->prepare('INSERT INTO events VALUES (?,?)')->execute([$event['id'],time()]); $db->exec('COMMIT');
    } catch(Throwable $e) { $db->exec('ROLLBACK'); throw $e; }
}
function run(callable $action): void {
    header('Content-Type: application/json'); header('Cache-Control: no-store'); header('X-Content-Type-Options: nosniff');
    try { echo json_encode($action(),JSON_THROW_ON_ERROR); }
    catch(Failure $e) { http_response_code($e->status); if($e->status===405)header('Allow: GET, POST'); echo json_encode(['error'=>$e->getMessage()]); }
    catch(Throwable $e) { http_response_code(503); echo json_encode(['error'=>'Online booking is unavailable. Please contact us.']); }
}
