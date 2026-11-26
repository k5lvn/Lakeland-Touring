<?php
declare(strict_types=1);
use function HireCalendar\{database,requestStay,decide,row,price};
use function TouringBooking\available;
use TouringBooking\Failure;
require dirname(__DIR__,2).'/booking-backend/public/hire-calendar/calendar.php';
require_once __DIR__.'/hold-return.php';
$_SERVER['DOCUMENT_ROOT']=dirname(__DIR__,2).'/booking-backend/public';
$dir=sys_get_temp_dir().'/touring-diary-'.bin2hex(random_bytes(10));
mkdir($dir,0700);
$id=bin2hex(random_bytes(20));
$c=['private_dir'=>$dir,'receipt_secret'=>bin2hex(random_bytes(32)),'periods'=>[],'allow_enquiries'=>true,
    'request_through'=>'2099-12-31','blocked'=>[],'initial_hold'=>['id'=>$id,'start'=>'2099-08-14','end'=>'2099-08-20']];
function check(bool $condition): void {if (!$condition) throw new RuntimeException('Diary assertion failed');}
function refuses(callable $operation): void {try {$operation();}catch(Failure){return;}throw new RuntimeException('Expected rejection');}
try {
    $db=database($c);
    check(row($db,$id)['state']==='goodwill');
    check((int)$db->query('SELECT count(*) FROM bookings')->fetchColumn()===1);
    database($c);
    refuses(fn()=>available($db,'2099-08-13','2099-08-15'));
    available($db,'2099-08-20','2099-08-27');
    $guest=['name'=>'Fixture','email'=>'test@example.invalid','details'=>'Test caravan','mode'=>'self-tow','start'=>'2099-08-20','nights'=>7,'expected'=>null];
    $request=bin2hex(random_bytes(20));
    requestStay($db,$c,$request,$guest);
    refuses(fn()=>decide($db,$c,$request,'approved'));
    decide($db,$c,$request,'approved',85000);
    check(json_decode(row($db,$request)['quote'],true)['hire_pence']===85000);
    refuses(fn()=>available($db,'2099-08-20','2099-08-21'));
    check(!price($c,'2099-08-01',7)['hire_pence']);
    refuses(fn()=>price($c,'2099-12-27',7));
    decide($db,$c,$id,'released');
    database($c);
    check(row($db,$id)['state']==='released');
    available($db,'2099-08-14','2099-08-20');
    check((int)$db->query('SELECT count(*) FROM calendar_mail')->fetchColumn()===2);
    $opening = json_decode(file_get_contents(dirname(__DIR__).'/opening-hold.json'),true,512,JSON_THROW_ON_ERROR);
    check($opening['end'] === '2027-08-21');
    $c['initial_hold'] = $opening;
    $openingId = $opening['id'];
    database($c);
    $fresh = row($db,$openingId);
    check($fresh['end'] === '2027-08-21' && json_decode($fresh['quote'],true)['nights'] === 7);

    // Simulate a deployed six-night row with a preserved private seed and extra quote data.
    $c['initial_hold']['end'] = '2027-08-20';
    $oldQuote = ['start'=>'2027-08-14','end'=>'2027-08-20','nights'=>6,'hire_pence'=>87500,'handover'=>'12:00'];
    $restore = $db->prepare("UPDATE bookings SET end='2027-08-20',terms_version='operator-hold-v1',quote=?,state=? WHERE id=?");
    foreach (['released','approved'] as $state) {
        $restore->execute([json_encode($oldQuote),$state,$openingId]);
        database($c);
        $untouched = row($db,$openingId);
        check($untouched['end'] === '2027-08-20' && $untouched['state'] === $state);
    }
    $restore->execute([json_encode($oldQuote),'goodwill',$openingId]);
    $c['blocked'][] = ['start'=>'2027-08-20','end'=>'2027-08-21'];
    database($c);
    check(row($db,$openingId)['end'] === '2027-08-20');
    $c['blocked'] = [];
    $db->exec("INSERT INTO bookings(id,start,end,state,quote,customer,created,terms_version)
        VALUES('friday-block','2027-08-20','2027-08-21','owner_block','{}','{}',0,'fixture')");
    database($c);
    check(row($db,$openingId)['end'] === '2027-08-20');
    $db->exec("DELETE FROM bookings WHERE id='friday-block'");
    database($c);
    database($c);
    $corrected = row($db,$openingId);
    check($corrected['start'] === $opening['start'] && $corrected['end'] === $opening['end']);
    check($corrected['state'] === 'goodwill' && $corrected['customer'] === $fresh['customer']
        && $corrected['created'] === $fresh['created'] && $corrected['terms_version'] === 'operator-hold-v2');
    check(json_decode($corrected['quote'],true) === array_replace($oldQuote,['end'=>'2027-08-21','nights'=>7]));
    refuses(fn()=>available($db,'2027-08-20','2027-08-21'));
    available($db,'2027-08-21','2027-08-22');
    // A later explicit change or release wins, including a return to the original date.
    $db->prepare("UPDATE bookings SET end='2027-08-20',quote=? WHERE id=?")->execute([json_encode($oldQuote),$openingId]);
    database($c);
    check(row($db,$openingId)['end'] === '2027-08-20');
    $db->prepare("DELETE FROM bookings WHERE id=?")->execute([$openingId]);
    database($c);
    check(row($db,$openingId)['end'] === '2027-08-21');
    checkHoldReturnEditing($db,$c);
    echo "Diary hold, seven-night correction, return date edits, release, changeover, horizon, quote confirmation and mail checks passed.\n";
} finally {unset($db);foreach(glob($dir.'/*') as $f) unlink($f);rmdir($dir);}
