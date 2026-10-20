<?php
declare(strict_types=1);
require __DIR__.'/common.php';
\TouringBooking\run(function() {
    $cfg=\TouringBooking\config(); $data=\TouringBooking\body($cfg);
    $q=\TouringBooking\quote($cfg,$data['start']??'',$data['end']??'');
    \TouringBooking\available(\TouringBooking\db($cfg),$q['start'],$q['end']); return $q;
});
