<?php
declare(strict_types=1);
require __DIR__.'/calendar.php';
\TouringBooking\run(function(){
    $c=\HireCalendar\settings();$db=\HireCalendar\database($c);\TouringBooking\session();
    $_SESSION['calendar_id']??=bin2hex(random_bytes(20));
    $blocks=$db->query("SELECT start,end,CASE WHEN state IN ('creating','pending','goodwill') THEN 'held' ELSE 'booked' END AS state FROM bookings WHERE state IN ('creating','pending','paid','approved','goodwill','owner_block')")->fetchAll(PDO::FETCH_ASSOC);
    foreach($c['blocked'] as $b)$blocks[]=['start'=>$b['start'],'end'=>$b['end'],'state'=>'booked'];
    return ['today'=>\HireCalendar\today(),'through'=>$c['request_through'],'allowEnquiries'=>!empty($c['allow_enquiries']),'periods'=>array_map(fn($p)=>array_intersect_key($p,array_flip(['start','end','season','prices'])),$c['periods']),'blocks'=>$blocks,'csrf'=>$_SESSION['csrf']];
});
