<?php
declare(strict_types=1);
namespace HireCalendar;
use PDO;
use TouringBooking\Failure;
use function TouringBooking\{available,dateValue,db,overlaps};
require_once dirname(__DIR__).'/api/common.php';
require_once __DIR__.'/booking-sms.php';

function seasonalHirePeriods(string $from, string $through): array {
    // Each change starts a new hire week. The last date is checkout only.
    $changes = [
        '2026-11-21' => 'low',
        '2026-12-19' => 'peak',
        '2027-01-02' => 'low',
        '2027-02-13' => 'peak',
        '2027-02-20' => 'low',
        '2027-03-20' => 'peak',
        '2027-04-10' => 'low',
        '2027-05-01' => 'peak',
        '2027-05-08' => 'mid',
        '2027-05-29' => 'peak',
        '2027-06-05' => 'mid',
        '2027-06-26' => 'peak',
        '2027-09-04' => 'mid',
        '2027-10-02' => 'low',
        '2027-10-23' => 'peak',
        '2027-10-30' => 'low',
        '2027-12-18' => 'peak',
        '2028-01-08' => 'low',
        '2028-02-12' => 'peak',
        '2028-02-19' => 'low',
        '2028-04-01' => 'peak',
        '2028-04-22' => 'low',
        '2028-04-29' => 'peak',
        '2028-05-06' => 'mid',
        '2028-05-27' => 'peak',
        '2028-06-03' => 'mid',
        '2028-07-01' => 'peak',
        '2028-09-02' => 'mid',
        '2028-09-30' => null,
    ];
    $prices = [
        'low' => [3 => 37500, 5 => 57500, 7 => 69500],
        'mid' => [7 => 79500],
        'peak' => [7 => 95000],
    ];
    $boundaries = array_keys($changes);
    $periods = [];
    for ($i = 0; $i < count($boundaries) - 1; $i++) {
        $start = max($from, $boundaries[$i]);
        $end = min($through, $boundaries[$i + 1]);
        if ($start < $end) {
            $season = $changes[$boundaries[$i]];
            $periods[] = ['start' => $start, 'end' => $end, 'season' => $season, 'prices' => $prices[$season]];
        }
    }
    return $periods;
}

function settings(): array {
    $root = realpath($_SERVER['DOCUMENT_ROOT'] ?? '');
    if (!$root) throw new Failure('Diary storage is unavailable.',503);
    $path = getenv('TOURING_CALENDAR_CONFIG') ?: dirname($root).'/.touring-calendar/config.php';
    $file = realpath($path);
    if (!$file || str_starts_with($file,$root.'/')) throw new Failure('Diary configuration is unavailable.',503);
    $c = require $file;
    $holdPath=dirname($root).'/.touring-calendar/opening-hold.json';
    if (empty($c['initial_hold']) && is_file($holdPath)) $c['initial_hold']=json_decode(file_get_contents($holdPath),true,512,JSON_THROW_ON_ERROR);
    if (strlen($c['receipt_secret'] ?? '') < 32 || !filter_var($c['office_email'] ?? '', FILTER_VALIDATE_EMAIL)
        || ($c['origin'] ?? '') !== 'https://lakelandtouring.uk') throw new Failure('Diary configuration is incomplete.',503);
    $c['request_through'] = dateValue(today())->modify('+12 months')->format('Y-m-d');
    if (empty($c['inventory_verified'])) $c['periods'] = [];
    $c['inventory_through'] = $c['inventory_through'] ?: $c['request_through'];
    $last = ''; dateValue($c['inventory_through']);
    foreach ($c['periods'] as $p) {
        if (dateValue($p['end']) <= dateValue($p['start']) || $p['start'] < $last || $p['end'] > $c['inventory_through']) throw new Failure('Check the diary periods.',503);
        $last = $p['end'];
        $season = $p['season'] ?? '';
        if (!in_array($season,['peak','mid','low'],true) || empty($p['prices'][7])) throw new Failure('Check the hire tariff.',503);
        foreach ($p['prices'] as $n=>$price) {
            if (!is_int($n) || !is_int($price) || $price <= 0 || $n > 366 || ($season === 'low' && !in_array($n,[3,5,7],true))
                || ($season === 'peak' && $n !== 7) || ($season === 'mid' && $n<7)) throw new Failure('Check the hire tariff.',503);
        }
    }
    foreach ($c['blocked'] as $b) if(dateValue($b['end']) <= dateValue($b['start'])) throw new Failure('Check blocked dates.',503);
    // A guest can request a priced stay before the operator confirms availability.
    if (empty($c['inventory_verified']) && !empty($c['allow_enquiries'])) {
        $c['periods'] = seasonalHirePeriods(today(), $c['request_through']);
    }
    return $c;
}
function today(): string {return (new \DateTimeImmutable('today',new \DateTimeZone('Europe/London')))->format('Y-m-d');}
function price(array $c,string $start,int $n): array {
    if ($n<1 || $n>366 || $start<today()) throw new Failure('Choose a future stay.');
    $a=dateValue($start);$end=$a->modify("+$n days")->format('Y-m-d');
    if (isset($c['request_through']) && $end > $c['request_through']) throw new Failure('Choose dates within the next twelve months.');
    foreach ($c['blocked'] as $block) {
        if (overlaps($start,$end,$block['start'],$block['end'])) throw new Failure('Those dates are unavailable.',409);
    }
    foreach ($c['periods'] as $p) {
        if ($p['start']>$start || $p['end']<$end || !isset($p['prices'][$n])) continue;
        if ($p['season']==='peak' && ((int)$a->format('N')!==6 || $n!==7)) continue;
        if ($p['season']==='mid' && (int)$a->format('N')!==6) continue;
        if ($p['season']==='low' && $n===3 && (int)$a->format('N')!==5) continue;
        foreach ($c['blocked'] as $b) if(overlaps($start,$end,$b['start'],$b['end'])) throw new Failure('Those dates are unavailable.',409);
        return ['start'=>$start,'end'=>$end,'nights'=>$n,'hire_pence'=>$p['prices'][$n]];
    }
    if (!empty($c['allow_enquiries']) && in_array($n,[3,5,7],true) && ($n !== 3 || (int)$a->format('N') === 5)) {
        foreach ($c['periods'] as $p) {
            if (overlaps($start,$end,$p['start'],$p['end'])) throw new Failure('Choose a stay within the advertised season.',409);
        }
        return ['start'=>$start,'end'=>$end,'nights'=>$n,'hire_pence'=>null];
    }
    throw new Failure('Please choose an available stay from the calendar.',409);
}
function database(array $c): PDO {
    $db=db($c);
    $db->exec('CREATE TABLE IF NOT EXISTS calendar_mail (booking TEXT NOT NULL, status TEXT NOT NULL, sent INTEGER, PRIMARY KEY(booking,status))');
    $db->exec("CREATE TABLE IF NOT EXISTS calendar_sms (booking TEXT PRIMARY KEY, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, due INTEGER NOT NULL DEFAULT 0)");
    if (!empty($c['initial_hold'])) installInitialHold($db,$c);
    return $db;
}
function installInitialHold(PDO $db,array $c): void {
    $hold = $c['initial_hold'];
    $id = $hold['id'];
    // Older installations keep the original return date in their private seed file or config.
    $openingWeek = $id === 'a8b5f06d1bb5469e0d523d9c472d472fa02db3e7'
        && $hold['start'] === '2027-08-14' && in_array($hold['end'],['2027-08-20','2027-08-21'],true);
    if ($openingWeek) $hold['end'] = '2027-08-21';
    $lookup = $db->prepare('SELECT state,start,end,terms_version,quote FROM bookings WHERE id=?');
    $read = static function() use ($lookup,$id) {
        $lookup->execute([$id]);
        $row = $lookup->fetch(PDO::FETCH_ASSOC);
        $lookup->closeCursor();
        return $row;
    };
    $needsExtension = static fn(array $row): bool => $openingWeek && $row['state'] === 'goodwill'
        && $row['terms_version'] === 'operator-hold-v1' && $row['start'] === $hold['start']
        && $row['end'] === '2027-08-20';
    $existing = $read();
    if ($existing && !$needsExtension($existing)) return;
    transaction($db,function() use ($db,$c,$hold,$id,$openingWeek,$read,$needsExtension) {
        $existing = $read();
        if ($existing && !$needsExtension($existing)) return;
        $start = $hold['start'];
        $end = $hold['end'];
        $checkFrom = $existing ? $existing['end'] : $start;
        try {
            foreach ($c['blocked'] as $block) {
                if (overlaps($checkFrom,$end,$block['start'],$block['end'])) throw new Failure('Operator review required for overlapping dates.',409);
            }
            available($db,$checkFrom,$end);
        } catch (Failure $e) {
            if ($openingWeek && $e->status === 409) return;
            throw $e;
        }
        if ($existing) {
            $quote = json_decode($existing['quote'],true,512,JSON_THROW_ON_ERROR);
            $quote['end'] = $end;
            $quote['nights'] = 7;
            $db->prepare("UPDATE bookings SET end=?, quote=?, terms_version='operator-hold-v2' WHERE id=?")
                ->execute([$end,json_encode($quote,JSON_THROW_ON_ERROR),$id]);
            return;
        }
        $quote=['start'=>$start,'end'=>$end,'nights'=>dateValue($start)->diff(dateValue($end))->days,'hire_pence'=>null];
        $guest=['name'=>'Guest hold','mode'=>'undecided','email'=>'','details'=>'Hire option and booking deposit to be confirmed.'];
        $insert=$db->prepare("INSERT INTO bookings (id,start,end,state,quote,customer,created,terms_version) VALUES (?,?,?,'goodwill',?,?,?,?)");
        $insert->execute([$id,$start,$end,json_encode($quote),json_encode($guest),time(),$openingWeek ? 'operator-hold-v2' : 'operator-hold-v1']);
    });
}
function receipt(array $c,string $id): string {return $id.'.'.hash_hmac('sha256',$id,$c['receipt_secret']);}
function reference(string $id): string {return 'LT-'.strtoupper(substr($id,0,12));}
function transaction(PDO $db,callable $fn): mixed {
    $db->exec('BEGIN IMMEDIATE');try {$out=$fn();$db->exec('COMMIT');return $out;}catch(\Throwable $e){$db->exec('ROLLBACK');throw $e;}
}
function row(PDO $db,string $id): array {
    $q=$db->prepare("SELECT * FROM bookings WHERE id=? AND state IN ('requested','approved','declined','goodwill','released')");
    $q->execute([$id]);return $q->fetch(PDO::FETCH_ASSOC) ?: throw new Failure('Request unavailable.',404);
}
function scheduleMail(PDO $db,string $id,string $state): void {
    $db->prepare('INSERT OR IGNORE INTO calendar_mail(booking,status) VALUES (?,?)')->execute([$id,$state]);
}
function requestStay(PDO $db,array $c,string $id,array $input): array {
    foreach(['name'=>100,'email'=>254,'details'=>600] as $field=>$max){
        $v=$input[$field]??null;
        if(!is_string($v) || trim($v)==='' || strlen($v)>$max || preg_match('/[\x00-\x08\x0b\x0c\x0e-\x1f]/',$v))throw new Failure('Please check your contact and hire details.');
        $customer[$field]=trim($v);
    }
    if(!filter_var($customer['email'],FILTER_VALIDATE_EMAIL) || !in_array($input['mode']??'',['self-tow','delivery'],true))throw new Failure('Please check your email and hire option.');
    $customer['mode']=$input['mode'];
    if(!is_int($input['nights']??null) || !is_string($input['start']??null))throw new Failure('Invalid stay.');
    $q=price($c,$input['start'],$input['nights']);
    if($q['hire_pence']!==($input['expected']??null))throw new Failure('The tariff has changed. Please select your dates again.',409);
    return transaction($db,function()use($db,$id,$q,$customer,$c){
        $prior=$db->prepare('SELECT quote,customer FROM bookings WHERE id=?');$prior->execute([$id]);
        if($existing=$prior->fetch(PDO::FETCH_ASSOC)){
            if($existing['quote']!==json_encode($q) || $existing['customer']!==json_encode($customer))throw new Failure('A request was already sent. Refresh to start another.',409);
        }else{
            available($db,$q['start'],$q['end']);
            $db->prepare("INSERT INTO bookings(id,start,end,state,quote,customer,created,terms_version) VALUES(?,?,?,'requested',?,?,?,'operator-request-v1')")
               ->execute([$id,$q['start'],$q['end'],json_encode($q),json_encode($customer),time()]);
            scheduleMail($db,$id,'requested');
            if (\BookingSms\configured($c['private_dir'])) {
                $db->prepare("INSERT INTO calendar_sms(booking,status) VALUES (?,'pending')")->execute([$id]);
            }
        }
        return ['reference'=>reference($id),'key'=>receipt($c,$id)];
    });
}
function changeHoldReturn(PDO $db, array $c, string $id, string $expectedEnd, string $newEnd): void {
    $return = dateValue($newEnd);
    transaction($db, function () use ($db, $c, $id, $expectedEnd, $newEnd, $return) {
        $entry = row($db, $id);
        if ($entry['state'] !== 'goodwill') throw new Failure('Only an active hold can be edited.', 409);
        if ($entry['end'] === $newEnd) return;
        if ($entry['end'] !== $expectedEnd) throw new Failure('The return date has changed. Review the current dates and try again.', 409);

        $arrival = dateValue($entry['start']);
        if ($return <= $arrival || $newEnd < today() || $entry['end'] < today()) {
            throw new Failure('Choose a return date after arrival for a current or future hold.');
        }
        if ($newEnd > $entry['end']) {
            if ($newEnd > $c['request_through']) throw new Failure('Choose a return date within the booking window.');
            // Test only the added nights, starting on the old return day, so the hold cannot conflict with itself.
            foreach ($c['blocked'] as $block) {
                if (overlaps($entry['end'], $newEnd, $block['start'], $block['end'])) {
                    throw new Failure('The additional nights include a blocked date.', 409);
                }
            }
            available($db, $entry['end'], $newEnd);
        }
        $quote = json_decode($entry['quote'], true, 512, JSON_THROW_ON_ERROR);
        $quote['end'] = $newEnd;
        $quote['nights'] = $arrival->diff($return)->days;
        $update = $db->prepare("UPDATE bookings SET end=?, quote=?,
            terms_version=CASE WHEN terms_version='operator-hold-v1' THEN 'operator-hold-v2' ELSE terms_version END WHERE id=?");
        $update->execute([$newEnd, json_encode($quote, JSON_THROW_ON_ERROR), $id]);
    });
}
function decide(PDO $db,array $c,string $id,string $action,?int $agreedPrice=null,?string $expectedEnd=null): void {
    if (!in_array($action,['approved','declined','released'],true)) throw new Failure('Unknown decision.');
    transaction($db,function()use($db,$c,$id,$action,$agreedPrice,$expectedEnd){
        $r=row($db,$id);
        if ($r['state']===$action) return;
        $hold=$r['state']==='goodwill';
        if ($hold && $expectedEnd !== null && $r['end'] !== $expectedEnd) {
            throw new Failure('The held dates changed. Review them before confirming your decision.', 409);
        }
        if (($hold && $action==='declined') || (!$hold && ($r['state']!=='requested' || $action==='released'))) throw new Failure('This entry already has a decision.',409);
        $q=json_decode($r['quote'],true);
        if ($action==='approved') {
            if (!$hold) {
                // An existing unpriced enquiry may still have a bespoke price agreed by the operator.
                $reviewConfig = $c;
                if ($q['hire_pence'] === null && !empty($c['allow_enquiries'])) $reviewConfig['periods'] = [];
                $fresh=price($reviewConfig,$r['start'],$q['nights']);
                if ($fresh['hire_pence']!==$q['hire_pence']) throw new Failure('The price changed. Agree a new request with the customer.',409);
                available($db,$r['start'],$r['end']);
            }
            if ($q['hire_pence']===null) {
                if ($agreedPrice===null || $agreedPrice<=0) throw new Failure('Enter the hire price agreed with the guest.');
                $q['hire_pence']=$agreedPrice;
            }
        }
        $db->prepare('UPDATE bookings SET state=?,quote=? WHERE id=?')->execute([$action,json_encode($q),$id]);
        if (json_decode($r['customer'],true)['email']!=='') scheduleMail($db,$id,$action);
    });
}
function h(string $s): string {return htmlspecialchars($s,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');}
function pounds(int $v): string {return '£'.number_format($v/100,2);}
function statusLabel(string $state): string {return ['requested'=>'Awaiting approval','approved'=>'Approved · dates reserved','declined'=>'Declined','goodwill'=>'Your dates are held · Payment pending','released'=>'Hold released'][$state];}
