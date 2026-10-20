<?php
declare(strict_types=1);
require __DIR__.'/api/common.php';
\TouringBooking\run(function() {
    if (($_SERVER['REQUEST_METHOD']??'')!=='POST') throw new \TouringBooking\Failure('Method not allowed.',405);
    $cfg=\TouringBooking\config();
    $raw=file_get_contents('php://input',false,null,0,1048577);
    if(strlen($raw)>1048576) throw new \TouringBooking\Failure('Request too large.',413);
    $event=\TouringBooking\verifyEvent($raw,$_SERVER['HTTP_STRIPE_SIGNATURE']??'',$cfg['stripe_webhook_secret']);
    \TouringBooking\processEvent(\TouringBooking\db($cfg),$event,$cfg['live_mode']); return ['received'=>true];
});
