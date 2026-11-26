<?php
declare(strict_types=1);
namespace HireCalendar;
use PDO;
use function TouringBooking\dateValue;
require_once __DIR__.'/calendar.php';

function deliverMail(PDO $db,array $c): void {
    $lock=fopen($c['private_dir'].'/calendar-notify.lock','c');
    if (!$lock) return;
    try {
        if (!flock($lock,LOCK_EX|LOCK_NB)) return;
        $jobs=$db->query('SELECT booking,status FROM calendar_mail WHERE sent IS NULL ORDER BY rowid LIMIT 12')->fetchAll(PDO::FETCH_ASSOC);
        foreach ($jobs as $job) {
            $r=row($db,$job['booking']); $guest=json_decode($r['customer'],true);
            $ref=reference($r['id']); $state=$job['status'];
            $new=$state==='requested';
            $to=$new?$c['office_email']:$guest['email'];
            if (!filter_var($to,FILTER_VALIDATE_EMAIL)) continue;
            $link=$new ? $c['origin'].'/hire-calendar/admin/?month='.substr($r['start'],0,7).'#request-'.$ref :
                $c['origin'].'/hire-calendar/status.php?key='.receipt($c,$r['id']);
            $headers=['From'=>$c['office_email'],'MIME-Version'=>'1.0','Content-Type'=>'text/html; charset=UTF-8'];
            if ($state==='approved') $headers['Bcc']=$c['office_email'];
            $arrival=dateValue($r['start']); $now=dateValue(today());
            $dateText=$arrival->format('j F Y').' to '.dateValue($r['end'])->format('j F Y');
            $subject=$new?'A hire request needs review':($state==='approved'?'Your holiday countdown starts here':'Your hire request');
            $title=$new?'New hire request':($state==='approved'?'Your holiday is booked.':statusLabel($state));
            $message='<div style="max-width:560px;font:16px/1.55 Arial;color:#14383a"><div style="background:#12323b url('.$c['origin'].'/hire-calendar/lake.webp) center/cover;padding:32px;color:white"><p>Lakeland Touring</p><h1>'.h($title).'</h1></div><div style="padding:22px"><p>'.h($dateText).' · Elddis Avanté 866</p>';
            if ($state==='approved') {
                $days=max(0,(int)$now->diff($arrival)->format('%r%a'));
                $message.='<h2>'.$days.' days to go</h2><p>As of '.h($now->format('j F Y')).'.</p>';
            }
            $message.='<p><a href="'.h($link).'">'.($new?'Review the request':($state==='approved'?'View my live countdown':'View my request')).'</a></p></div></div>';
            if (mail($to,$subject.' | '.$ref,$message,$headers)) {
                $db->prepare('UPDATE calendar_mail SET sent=? WHERE booking=? AND status=?')->execute([time(),$r['id'],$state]);
            }
        }
    } finally {fclose($lock);}
}
