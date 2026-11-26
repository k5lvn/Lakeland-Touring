<?php
declare(strict_types=1);

use function HireCalendar\{changeHoldReturn,decide,receipt,row};
use function TouringBooking\available;

// Called by diary.php using the same disposable diary database.
function checkHoldReturnEditing(PDO $db, array $c): void {
    $id = bin2hex(random_bytes(20));
    $start = '2099-09-01';
    $oldEnd = '2099-09-07';
    $newEnd = '2099-09-08';
    $quote = ['start'=>$start,'end'=>$oldEnd,'nights'=>6,'hire_pence'=>null,'handover'=>'15:00'];
    $guest = ['name'=>'Return date fixture','email'=>'return@example.invalid','mode'=>'undecided'];
    $insert = $db->prepare("INSERT INTO bookings(id,start,end,state,quote,customer,created,terms_version)
                             VALUES(?,?,?,'goodwill',?,?,?,'operator-hold-v1')");
    $insert->execute([$id,$start,$oldEnd,json_encode($quote),json_encode($guest),time()]);
    $key = receipt($c, $id);
    $mailCount = $db->query('SELECT count(*) FROM calendar_mail')->fetchColumn();

    $blocked = $c;
    $blocked['blocked'][] = ['start'=>$oldEnd,'end'=>$newEnd];
    refuses(fn()=>changeHoldReturn($db, $blocked, $id, $oldEnd, $newEnd));
    $other = bin2hex(random_bytes(20));
    $db->prepare("INSERT INTO bookings(id,start,end,state,quote,customer,created,terms_version)
                  VALUES(?,?,?,'owner_block','{}','{}',?,'owner-use')")->execute([$other,$oldEnd,$newEnd,time()]);
    refuses(fn()=>changeHoldReturn($db, $c, $id, $oldEnd, $newEnd));
    check(row($db,$id)['end'] === $oldEnd);
    $db->prepare('UPDATE bookings SET start=?,end=? WHERE id=?')->execute([$newEnd,'2099-09-09',$other]);

    changeHoldReturn($db, $c, $id, $oldEnd, $newEnd);
    changeHoldReturn($db, $c, $id, $oldEnd, $newEnd); // Retry after the save succeeded.
    $entry = row($db, $id);
    $saved = json_decode($entry['quote'],true);
    check($entry['state'] === 'goodwill' && $entry['start'] === $start && $entry['end'] === $newEnd);
    check($saved['nights'] === 7 && $saved['end'] === $newEnd && $saved['hire_pence'] === null && $saved['handover'] === '15:00');
    check(json_decode($entry['customer'],true) === $guest && receipt($c,$id) === $key);
    check($db->query('SELECT count(*) FROM calendar_mail')->fetchColumn() === $mailCount);
    refuses(fn()=>available($db, $oldEnd, $newEnd));
    refuses(fn()=>changeHoldReturn($db, $c, $id, $oldEnd, '2099-09-06'));
    refuses(fn()=>changeHoldReturn($db, $c, $id, $newEnd, $start));
    refuses(fn()=>decide($db, $c, $id, 'approved', 85000, $oldEnd));
    check(row($db,$id)['state'] === 'goodwill');
    changeHoldReturn($db, $c, $id, $newEnd, $oldEnd);
    available($db, $oldEnd, $newEnd);
    decide($db, $c, $id, 'released', null, $oldEnd);
    refuses(fn()=>changeHoldReturn($db, $c, $id, $oldEnd, $newEnd));
}
