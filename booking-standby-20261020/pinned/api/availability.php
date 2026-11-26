<?php
declare(strict_types=1);
require __DIR__.'/common.php';
\TouringBooking\run(function() {
    if (($_SERVER['REQUEST_METHOD']??'')!=='GET') throw new \TouringBooking\Failure('Method not allowed.',405);
    $cfg=\TouringBooking\config(); $db=\TouringBooking\db($cfg); \TouringBooking\session();
    $bookings=$db->query("SELECT start,end FROM bookings WHERE state IN ('creating','pending','paid')")->fetchAll(PDO::FETCH_ASSOC);
    return ['bookings'=>array_merge($cfg['blocked'],$bookings),'csrf'=>$_SESSION['csrf'],
        'available_through'=>$cfg['inventory_through'],'periods'=>array_map(fn($p)=>['start'=>$p['start'],'end'=>$p['end']],$cfg['periods'])];
});
