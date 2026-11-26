<?php
declare(strict_types=1);
use function HireCalendar\{database,requestStay,decide,row,price};
use function TouringBooking\available;
use TouringBooking\Failure;
require dirname(__DIR__,2).'/booking-backend/public/hire-calendar/calendar.php';
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
    echo "Diary hold, release, changeover, horizon, quote confirmation and mail checks passed.\n";
} finally {unset($db);foreach(glob($dir.'/*') as $f) unlink($f);rmdir($dir);}
