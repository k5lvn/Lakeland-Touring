<?php
declare(strict_types=1);
require __DIR__.'/common.php';
\TouringBooking\run(function() {
    $cfg=\TouringBooking\config(); $data=\TouringBooking\body($cfg);
    $q=\TouringBooking\quote($cfg,$data['start']??'',$data['end']??'');
    $db=\TouringBooking\db($cfg); \TouringBooking\reconcileHolds($db,$cfg);
    $row=\TouringBooking\hold($db,$cfg,$_SESSION['booking_id'],$q);
    return $q+['hold_until'=>(int)$row['hold_until'],'server_time'=>time()];
});
