<?php
declare(strict_types=1);
require __DIR__.'/common.php';
\TouringBooking\run(function() {
    if (($_SERVER['REQUEST_METHOD']??'')!=='GET') throw new \TouringBooking\Failure('Method not allowed.',405);
    $cfg=\TouringBooking\config(); $db=\TouringBooking\db($cfg); \TouringBooking\session();
    \TouringBooking\reconcileHolds($db,$cfg);
    $bookings=$db->query("SELECT start,end FROM bookings WHERE state='paid'")->fetchAll(PDO::FETCH_ASSOC);
    $held=$db->prepare("SELECT start,end,hold_until FROM bookings WHERE state IN ('held','creating','pending') AND id<>?");
    $held->execute([$_SESSION['booking_id']]);
    $own=$db->prepare("SELECT start,end,hold_until,state FROM bookings WHERE id=? AND state IN ('held','creating','pending','paid')");$own->execute([$_SESSION['booking_id']]);
    return ['bookings'=>array_merge($cfg['blocked'],$bookings),'csrf'=>$_SESSION['csrf'],
        'holds'=>$held->fetchAll(PDO::FETCH_ASSOC),'own_hold'=>$own->fetch(PDO::FETCH_ASSOC)?:null,'server_time'=>time(),
        'available_through'=>$cfg['inventory_through'],'periods'=>array_map(fn($p)=>['start'=>$p['start'],'end'=>$p['end'],'peak'=>($p['peak']??false)===true],$cfg['periods'])];
});
