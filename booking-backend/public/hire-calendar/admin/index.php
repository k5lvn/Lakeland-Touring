<?php
declare(strict_types=1);
use function HireCalendar\{settings,database,decide,h,pounds,reference,statusLabel};
use TouringBooking\Failure;
require dirname(__DIR__).'/calendar.php';
header('Cache-Control: no-store');header('Referrer-Policy: no-referrer');header('X-Robots-Tag: noindex, nofollow');
try {
    $c=settings();
    // Only the account authenticated by the host's password-protected directory may review requests.
    if(!hash_equals($c['operator_user'],(string)($_SERVER['REMOTE_USER']??'')))throw new Failure('Operator sign-in required.',403);
    \TouringBooking\session();$db=database($c);$error='';
    if($_SERVER['REQUEST_METHOD']==='POST'){
        if(!hash_equals($_SESSION['csrf'],(string)($_POST['csrf']??'')))throw new Failure('Refresh the review page.',403);
        try{
            $id=(string)($_POST['id']??'');
            if(($_POST['decision']??'')==='approved' && empty($_POST['delivery_agreed'])){
                $entry=\HireCalendar\row($db,$id);
                if(json_decode($entry['customer'],true)['mode']==='delivery')throw new Failure('Agree the delivery price with the customer before approving.');
            }
            decide($db,$c,(string)($_POST['id']??''),(string)($_POST['decision']??''));header('Location: ./',true,303);exit;}
        catch(Failure $e){$error=$e->getMessage();}
    }
    $requests=$db->query("SELECT * FROM bookings WHERE state IN ('requested','approved','declined') ORDER BY (state='requested') DESC,created DESC");
}catch(Throwable $e){http_response_code($e instanceof Failure?$e->status:503);exit($e instanceof Failure?h($e->getMessage()):'Diary temporarily unavailable.');}
?><!doctype html><html lang="en-GB"><meta name="viewport" content="width=device-width,initial-scale=1"><meta charset="utf-8"><title>Hire requests | Lakeland Touring</title><link rel="stylesheet" href="../calendar.css"><main class="diary"><p class="eyebrow">LAKELAND TOURING</p><h1>Hire requests</h1><p role="alert"><?=h($error)?></p>
<?php $count=0;foreach($requests as $r):$count++;$guest=json_decode($r['customer'],true);$quote=json_decode($r['quote'],true);?>
<article class="review"><p class="eyebrow"><?=h(reference($r['id']))?> · <?=h(statusLabel($r['state']))?></p><h2><?=h($guest['name'])?></h2><p><?=h($r['start'])?> to <?=h($r['end'])?> · <?=h((string)$quote['nights'])?> nights · <?=h(pounds($quote['hire_pence']))?> hire</p><p><?=h($guest['email'])?> · <?=h($guest['mode'])?></p><p><?=h($guest['details'])?></p>
<?php if($r['state']==='requested'):?><form method="post"><input type="hidden" name="csrf" value="<?=h($_SESSION['csrf'])?>"><input type="hidden" name="id" value="<?=h($r['id'])?>"><?php if($guest['mode']==='delivery'):?><label class="agree"><input type="checkbox" name="delivery_agreed" value="1">Customer has agreed the delivery price separately.</label><?php endif;?><button class="approve" name="decision" value="approved">Approve &amp; reserve dates</button><button class="decline" name="decision" value="declined">Decline</button></form><?php endif;?></article>
<?php endforeach;if(!$count):?><p>No requests yet.</p><?php endif;?></main></html>
