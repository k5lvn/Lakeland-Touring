<?php
declare(strict_types=1);
require __DIR__.'/common.php';
\TouringBooking\run(function() {
    $cfg=\TouringBooking\config(); $data=\TouringBooking\body($cfg);
    $customer=\TouringBooking\customer($data);
    $q=\TouringBooking\quote($cfg,$data['start']??'',$data['end']??'');
    $account=\TouringBooking\stripe($cfg,'GET','account');
    if (($account['id']??'')!==$cfg['stripe_account'] || ($account['charges_enabled']??false)!==true) throw new \TouringBooking\Failure('Merchant setup is unavailable.',503);
    $db=\TouringBooking\db($cfg); $id=$_SESSION['booking_id'];
    if (($_SESSION['checkout_attempts']??0)>=10) throw new \TouringBooking\Failure('Please contact us to complete your booking.',429);
    $_SESSION['checkout_attempts']=($_SESSION['checkout_attempts']??0)+1;
    $row=\TouringBooking\claimHold($db,$id,$q,$customer);
    if ($row['checkout_url']) return ['url'=>$row['checkout_url']];
    // Fixed parameters and an idempotency key make uncertain retries safe.
    // Do not release this reservation on a timeout: Stripe may have created a session.
    // Stripe requires >=30 minutes; the server reconciliation job expires it
    // at the earlier selection-hold deadline before reopening the dates.
    $expires=(int)$row['created']+3600;
    if ($expires<time()+1801) throw new \TouringBooking\Failure('Please contact us to reconcile your checkout before retrying.',409);
    $s=\TouringBooking\stripe($cfg,'POST','checkout/sessions',[
        'mode'=>'payment','payment_method_types'=>['card'],'locale'=>'en-GB',
        'client_reference_id'=>$id,'customer_email'=>$customer['email'],'expires_at'=>$expires,
        'success_url'=>$cfg['origin'].'/booking-confirmation.php',
        'cancel_url'=>$cfg['origin'].'/booking.html?checkout=cancelled',
        'line_items'=>[['price_data'=>['currency'=>'gbp','unit_amount'=>$q['pay_now_pence'],
            'product_data'=>['name'=>'Elddis caravan hire '.$q['start'].' to '.$q['end'],
                'description'=>$q['balance_pence']>0?'Booking deposit; remaining hire balance due '.$q['balance_due_date'].'. Security deposit separate.':'Full hire payment. Security deposit separate.']], 'quantity'=>1]]
    ],'touring-booking-'.$id);
    $url=$s['url']??'';
    if (!is_string($s['id']??null) || !is_string($url) || parse_url($url,PHP_URL_SCHEME)!=='https' || parse_url($url,PHP_URL_HOST)!=='checkout.stripe.com' || ($s['livemode']??null)!==$cfg['live_mode']) throw new \TouringBooking\Failure('Checkout reconciliation required. Please contact us.',503);
    // The webhook can arrive first; never move a paid/expired row back to pending.
    $db->prepare("UPDATE bookings SET session_id=?,checkout_url=?,state=CASE WHEN state='creating' THEN 'pending' ELSE state END WHERE id=? AND (session_id IS NULL OR session_id=?)")
        ->execute([$s['id'],$url,$id,$s['id']]);
    return ['url'=>$url];
});
