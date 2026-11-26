<?php
declare(strict_types=1);
use function HireCalendar\{settings,database,receipt,row,h,statusLabel,pounds};
use function TouringBooking\dateValue;
require __DIR__.'/calendar.php';
header('Cache-Control: private, no-store');
header('Referrer-Policy: no-referrer');
header('X-Robots-Tag: noindex, nofollow');
try {
    $c=settings();
    $key=$_GET['key']??'';
    $id=is_string($key)?explode('.',$key,2)[0]:'';
    $invite=$_GET['invite']??'';
    if (is_string($invite) && preg_match('/^[0-9a-f]{64}$/D',$invite)
        && hash_equals($c['initial_hold']['id']??'',substr(hash('sha256',$invite),0,40))) {
        $id=$c['initial_hold']['id'];
    } elseif (!preg_match('/^[0-9a-f]{40}$/D',$id) || !hash_equals(receipt($c,$id),$key)) {
        throw new \TouringBooking\Failure('Private holiday link required.',404);
    }
    $r=row(database($c),$id);
    $q=json_decode($r['quote'],true,512,JSON_THROW_ON_ERROR);
    $arrival=dateValue($r['start']); $departure=dateValue($r['end']);
    $time=$q['handover']??null;
    $target=$time ? new DateTimeImmutable($r['start'].' '.$time,$arrival->getTimezone()) : $arrival;
    $active=in_array($r['state'],['approved','goodwill'],true);
} catch(Throwable $e) {
    http_response_code($e instanceof \TouringBooking\Failure?$e->status:503);
    exit('This private holiday link is unavailable. Please contact Lakeland Touring.');
}
?><!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="My holiday">
<link rel="apple-touch-icon" href="/Assets/lakeland-touring-official.png"><meta name="theme-color" content="#13363b">
<title>My holiday | Lakeland Touring</title><link rel="stylesheet" href="holiday.css"><script src="holiday.js" defer></script></head>
<body class="holiday-page"><main class="holiday-shell">
<header class="holiday-mast"><a href="/"><img src="brochure-logo.webp" alt="Lakeland Touring" width="155" height="58"></a><span>My holiday</span></header>
<section class="holiday-intro"><p><?=h(statusLabel($r['state']))?></p><h1><?= $active?'Your Cumbrian <em>getaway.</em>':'Your hire request' ?></h1></section>
<section class="holiday-card">
<?php if($active): ?><h2 id="clock-label"><?=$time?'Time until handover':'Time until your arrival day'?></h2>
<div class="rings" data-target="<?=h($target->format(DATE_ATOM))?>" data-arrival="<?=h($r['start'])?>" data-end="<?=h($r['end'])?>" role="timer" aria-labelledby="clock-label">
<?php foreach(['Days','Hours','Mins','Secs'] as $unit): ?><div class="ring-unit"><div class="ring"><span>–</span></div><small><?=$unit?></small></div><?php endforeach; ?>
</div><?php endif; ?>
<div class="holiday-dates"><div><small>Arrival</small><strong><?=h($arrival->format('D j M Y'))?></strong></div>
<div><small>Departure</small><strong><?=h($departure->format('D j M Y'))?></strong></div></div>
<p><?=h((string)$q['nights'])?> nights · Elddis Avanté 866</p>
<?php if($active): ?><p><?= $time?'Handover at '.h($time).' UK time.':'We’ll agree your handover time with you.' ?></p><?php endif; ?>
<?php if($q['hire_pence']!==null): ?><p>Caravan hire <?=h(pounds($q['hire_pence']))?></p><?php endif; ?>
<?php if ($r['state']==='requested'): ?><p>We’ve received your request. We’ll check availability and get back to you.</p><?php endif; ?>
<?php if ($r['state']==='goodwill'): ?><p>We’re holding these dates for you. Your booking deposit is still due.</p><?php endif; ?>
<a href="/booking.html">Contact Lakeland Touring</a></section>
</main></body></html>
