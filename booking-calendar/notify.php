<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli')exit(1);
use function HireCalendar\{settings,database,row,receipt,reference,statusLabel};
require dirname(__DIR__).'/booking-backend/public/hire-calendar/calendar.php';
// Run by hosting cron outside the web root. A retry never changes the reservation.
$_SERVER['DOCUMENT_ROOT']=getenv('TOURING_DOCUMENT_ROOT')?:'';
if(!$_SERVER['DOCUMENT_ROOT'])exit(1);
$c=settings();$db=database($c);$lock=fopen($c['private_dir'].'/calendar-notify.lock','c');
if(!$lock || !flock($lock,LOCK_EX|LOCK_NB))exit;
$jobs=$db->query('SELECT booking,status FROM calendar_mail WHERE sent IS NULL ORDER BY rowid LIMIT 100')->fetchAll(PDO::FETCH_ASSOC);
foreach($jobs as $job){
    $r=row($db,$job['booking']);$guest=json_decode($r['customer'],true);$ref=reference($r['id']);
    $isNew=$job['status']==='requested';
    $to=$isNew?$c['office_email']:$guest['email'];
    $message=$isNew?'A hire request needs review. Open the operator diary: '.$c['origin'].'/hire-calendar/admin/':
        'Your hire request is now '.statusLabel($job['status']).'. Your private confirmation: '.$c['origin'].'/hire-calendar/status.php?key='.receipt($c,$r['id']);
    if(mail($to,'Lakeland Touring hire request '.$ref,$message."\n".$r['start'].' to '.$r['end'],['From'=>$c['office_email'],'Content-Type'=>'text/plain; charset=UTF-8'])){
        $db->prepare('UPDATE calendar_mail SET sent=? WHERE booking=? AND status=?')->execute([time(),$r['id'],$job['status']]);
    }
}
