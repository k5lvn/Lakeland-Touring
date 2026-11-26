<?php
declare(strict_types=1);
use function HireCalendar\{settings,database,receipt,row,reference,h,statusLabel,pounds};
require __DIR__.'/calendar.php';
header('Cache-Control: no-store');header('Referrer-Policy: no-referrer');header('X-Robots-Tag: noindex, nofollow');
try {
    $c=settings();$key=(string)($_GET['key']??'');$id=explode('.',$key,2)[0];
    if(!preg_match('/^[0-9a-f]{40}$/D',$id) || !hash_equals(receipt($c,$id),$key))throw new \TouringBooking\Failure('Request unavailable.',404);
    $r=row(database($c),$id);$q=json_decode($r['quote'],true);
}catch(Throwable $e){http_response_code($e instanceof \TouringBooking\Failure?$e->status:503);exit('Your request is unavailable. Please contact Lakeland Touring.');}
?><!doctype html><html lang="en-GB"><meta name="viewport" content="width=device-width,initial-scale=1"><meta charset="utf-8"><title>Your hire request | Lakeland Touring</title><link rel="stylesheet" href="calendar.css"><main class="diary"><p class="eyebrow">LAKELAND TOURING · <?=h(reference($id))?></p><h1><?=h(statusLabel($r['state']))?></h1><p id="selection"><?=h($r['start'])?> to <?=h($r['end'])?> · <?=h((string)$q['nights'])?> nights · <?=h(pounds($q['hire_pence']))?> caravan hire</p><p><?=h(['requested'=>'We have your request. Reopen this private link to see our decision.','approved'=>'Lakeland Touring has reserved these dates for you.','declined'=>'Please contact us if you would like to discuss other dates.'][$r['state']])?></p><p><a href="/booking.html">Contact Lakeland Touring</a></p></main></html>
