<?php
declare(strict_types=1);
namespace HireCalendar;
use PDO;
require_once __DIR__.'/calendar.php';
require_once __DIR__.'/booking-sms.php';

function deliverSms(PDO $db,array $c,?string $only=null,?callable $send=null): void {
    if (!\BookingSms\configured($c['private_dir'])) return;
    $cfg=\BookingSms\credentials($c['private_dir']);
    $job=transaction($db,static function() use ($db,$only) {
        $q=$db->prepare("SELECT s.booking,s.attempts,b.start,b.end FROM calendar_sms s JOIN bookings b ON b.id=s.booking
            WHERE s.status IN ('pending','retry') AND s.due<=? AND b.state='requested' ".($only===null?'':' AND s.booking=?')." ORDER BY s.rowid LIMIT 1");
        $q->execute($only===null?[time()]:[time(),$only]);
        $job=$q->fetch(PDO::FETCH_ASSOC);
        if ($job) $db->prepare("UPDATE calendar_sms SET status='sending', attempts=attempts+1 WHERE booking=?")->execute([$job['booking']]);
        return $job;
    });
    if (!$job) return;
    $ref=reference($job['booking']);
    $start=(new \DateTimeImmutable($job['start']))->format('j M Y');
    $end=(new \DateTimeImmutable($job['end']))->format('j M Y');
    $body="Lakeland Touring: New hire request $ref, $start to $end. Check your booking diary.";
    try { $status=($send??'BookingSms\\send')($cfg,$body,$ref); }
    catch(\Throwable $e) { $status='unknown'; }
    $due=$status==='retry'?time()+min(7200,60*(2**min(7,(int)$job['attempts']))):0;
    $db->prepare('UPDATE calendar_sms SET status=?,due=? WHERE booking=?')->execute([$status,$due,$job['booking']]);
    if ($status!=='accepted') error_log('Touring booking SMS '.$status.' for '.$ref);
}
