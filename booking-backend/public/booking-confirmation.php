<?php
declare(strict_types=1);
require __DIR__.'/api/common.php';
header('Cache-Control: no-store'); header('Referrer-Policy: no-referrer');
$message='We are awaiting payment confirmation. Please contact us if you need help with your booking.';
try {
    $cfg=\TouringBooking\config(); \TouringBooking\session();
    $find=\TouringBooking\db($cfg)->prepare('SELECT state,quote FROM bookings WHERE id=?');
    $find->execute([$_SESSION['booking_id']]); $row=$find->fetch(PDO::FETCH_ASSOC);
    if($row && $row['state']==='paid') {
        $q=json_decode($row['quote'],true);
        $message='Your payment of £'.number_format($q['pay_now_pence']/100,2).' has been confirmed for '.$q['start'].' to '.$q['end'].'. ';
        $message.=$q['balance_pence']>0?'The remaining hire balance is £'.number_format($q['balance_pence']/100,2).', due '.$q['balance_due_date'].'.':'Your hire charge is paid in full.';
        $message.=' The refundable security deposit and towing-suitability checks remain separate. Contact us to arrange collection.';
    }
} catch(Throwable $e) { http_response_code(503); $message='Online booking is not open yet. Please contact us to discuss your dates.'; }
?><!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Booking payment status | Lakeland Touring</title><link rel="stylesheet" href="styles.css"><main class="section"><h1>Booking payment status</h1><p><?=htmlspecialchars($message,ENT_QUOTES,'UTF-8')?></p><p><a href="tel:+441228307953">01228 307953</a> · <a href="mailto:LakelandTouring@Worx365Group.uk">Email Lakeland Touring</a></p><a href="booking.html">Return to availability</a></main></html>
