<?php
declare(strict_types=1);
require __DIR__.'/common.php';
\TouringBooking\run(function() {
    $cfg=\TouringBooking\config(); \TouringBooking\body($cfg);
    if (!\TouringBooking\releaseHold(\TouringBooking\db($cfg),$cfg,$_SESSION['booking_id'])) throw new \TouringBooking\Failure('Payment is being checked. Please contact us before selecting different dates.',409);
    $_SESSION['booking_id']=bin2hex(random_bytes(24));
    return ['released'=>true];
});
