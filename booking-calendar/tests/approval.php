<?php
declare(strict_types=1);
use function HireCalendar\{requestStay,decide,row,database,price};
use TouringBooking\Failure;
require dirname(__DIR__,2).'/booking-backend/public/hire-calendar/calendar.php';
$dir=sys_get_temp_dir().'/lt-'.bin2hex(random_bytes(8));mkdir($dir,0700);
$c=['private_dir'=>$dir,'receipt_secret'=>str_repeat('a',36),'periods'=>[['start'=>'2099-07-01','end'=>'2099-08-01','season'=>'peak','prices'=>[7=>98000]]],'blocked'=>[]];
$db=database($c);$sat=(new DateTimeImmutable('2099-07-01'))->modify('next Saturday')->format('Y-m-d');
$input=['name'=>'Test guest','email'=>'guest@example.com','details'=>'Fixture','mode'=>'self-tow','start'=>$sat,'nights'=>7,'expected'=>98000];
function must(bool $ok): void {if(!$ok)throw new RuntimeException('Assertion failed');}
function rejected(callable $fn): void {try{$fn();}catch(Failure){return;}throw new RuntimeException('Expected rejection');}
try {
    $a=bin2hex(random_bytes(20));$b=bin2hex(random_bytes(20));
    $one=requestStay($db,$c,$a,$input);must($one===requestStay($db,$c,$a,$input));
    requestStay($db,$c,$b,$input);must(row($db,$a)['state']==='requested');
    decide($db,$c,$a,'approved');decide($db,$c,$a,'approved');
    must(row($db,$a)['state']==='approved');rejected(fn()=>decide($db,$c,$b,'approved'));
    rejected(fn()=>\TouringBooking\available($db,$sat,row($db,$a)['end']));
    decide($db,$c,$b,'declined');must(row($db,$b)['state']==='declined');
    must((int)$db->query('SELECT COUNT(*) FROM calendar_mail')->fetchColumn()===4);
    rejected(fn()=>price($c,$sat,3));rejected(fn()=>price($c,(new DateTimeImmutable($sat))->modify('+1 day')->format('Y-m-d'),7));
    $next=row($db,$a)['end'];$input['start']=$next;$d=bin2hex(random_bytes(20));requestStay($db,$c,$d,$input);
    $c['blocked'][]=['start'=>$next,'end'=>(new DateTimeImmutable($next))->modify('+1 day')->format('Y-m-d')];
    rejected(fn()=>decide($db,$c,$d,'approved'));must(row($db,$d)['state']==='requested');
    echo "Passed request, retry, duplicate approval, overlap, changeover, outbox, and block-after-request checks.\n";
} finally {unset($db);foreach(glob($dir.'/*') as $f)unlink($f);rmdir($dir);}
