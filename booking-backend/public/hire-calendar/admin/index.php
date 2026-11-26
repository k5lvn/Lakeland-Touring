<?php
declare(strict_types=1);

use function HireCalendar\{settings,database,decide,h,pounds,reference,today};
use TouringBooking\Failure;

require __DIR__.'/access.php';
require dirname(__DIR__).'/mail.php';
header('Cache-Control: no-store');
header('Referrer-Policy: no-referrer');
header('X-Robots-Tag: noindex, nofollow');

try {
    $c = settings();
    $db = database($c);
    \HireCalendar\operatorAccess($c,$db);
    try { \HireCalendar\deliverMail($db,$c); } catch (Throwable $e) {error_log('Calendar notification queued for retry.');}
    $error = '';
    $today = today();
    $monthKey = $_GET['month'] ?? substr($today, 0, 7);
    if (!is_string($monthKey) || !preg_match('/\A(?:19|20|21)[0-9]{2}-(?:0[1-9]|1[0-2])\z/', $monthKey)) {
        throw new Failure('Choose a valid diary month.', 400);
    }
    $month = new DateTimeImmutable($monthKey.'-01', new DateTimeZone('Europe/London'));
    $next = $month->modify('+1 month');
    $previous = $month->modify('-1 month');
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        if (!is_string($_POST['csrf'] ?? null) || !hash_equals($_SESSION['csrf'], $_POST['csrf'])) {
            throw new Failure('Refresh the review page.', 403);
        }
        try {
            if (isset($_POST['signout'])) {
                unset($_SESSION['operator_until'],$_SESSION['operator_challenge']); session_regenerate_id(true);
                header('Location: ./',true,303); exit;
            }
            if (isset($_POST['block'])) {
                $from=\TouringBooking\dateValue((string)($_POST['start']??''))->format('Y-m-d');
                $until=\TouringBooking\dateValue((string)($_POST['end']??''))->format('Y-m-d');
                if ($from<today() || $until<=$from) throw new Failure('Choose a future start and a later return date.');
                \HireCalendar\transaction($db,function()use($db,$from,$until){
                    \TouringBooking\available($db,$from,$until);
                    $db->prepare("INSERT INTO bookings(id,start,end,state,quote,customer,created,terms_version) VALUES(?,?,?,'owner_block','{}','{}',?,'owner-use')")->execute([bin2hex(random_bytes(20)),$from,$until,time()]);
                });
                header('Location: ./?month='.substr($from,0,7),true,303); exit;
            }
            if (isset($_POST['unblock'])) {
                $db->prepare("UPDATE bookings SET state='unblocked' WHERE id=? AND state='owner_block'")->execute([(string)$_POST['unblock']]);
                header('Location: ./?month='.rawurlencode($monthKey),true,303); exit;
            }
            $id = (string)($_POST['id'] ?? '');
            if (isset($_POST['save_time'])) {
                $time=(string)($_POST['handover']??'');
                if (!preg_match('/^(?:[01][0-9]|2[0-3]):[0-5][0-9]$/D',$time)) throw new Failure('Enter a valid handover time.');
                \HireCalendar\transaction($db,function()use($db,$id,$time){
                    $entry=\HireCalendar\row($db,$id);
                    if (!in_array($entry['state'],['approved','goodwill'],true)) throw new Failure('Choose a held or confirmed stay.');
                    $quote=json_decode($entry['quote'],true); $quote['handover']=$time;
                    $db->prepare('UPDATE bookings SET quote=? WHERE id=?')->execute([json_encode($quote),$id]);
                });
                header('Location: ./?month='.rawurlencode($monthKey).'#request-'.rawurlencode(reference($id)),true,303); exit;
            }
            $decision = (string)($_POST['decision'] ?? '');
            $entry = \HireCalendar\row($db, $id);
            if ($decision === 'approved' && empty($_POST['delivery_agreed']) && json_decode($entry['customer'], true)['mode'] === 'delivery') {
                throw new Failure('Agree the delivery price with the customer before approving.');
            }
            $amount=trim((string)($_POST['agreed_price']??''));
            $pence=null;
            if ($decision==='approved') {
                if (empty($_POST['agreed'])) throw new Failure('Confirm availability, the agreed price and deposit before booking.');
                if ($amount!=='') {
                    if (!preg_match('/^([0-9]{1,6})(?:\.([0-9]{1,2}))?$/D',$amount,$parts)) throw new Failure('Enter a valid price in pounds.');
                    $pence=(int)$parts[1]*100+(int)str_pad($parts[2]??'',2,'0');
                }
            }
            decide($db,$c,$id,$decision,$pence);
            try { \HireCalendar\deliverMail($db,$c); } catch (Throwable $e) {error_log('Calendar notification queued for retry.');}
            header('Location: ./?month='.rawurlencode(substr($entry['start'], 0, 7)).'#request-'.rawurlencode(reference($id)), true, 303);
            exit;
        } catch (Failure $e) {
            $error = $e->getMessage();
        }
    }

    $start = $month->format('Y-m-d');
    $end = $next->format('Y-m-d');
    // Every pending request remains reachable; decided stays belong to the months they occupy.
    $review = $db->prepare("SELECT id,start,end,state,quote,customer FROM bookings
        WHERE state='requested' OR (state IN ('approved','declined','goodwill','released') AND start < ? AND end > ?)
        ORDER BY CASE state WHEN 'requested' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END, start, created");
    $review->execute([$end, $start]);
    $requests = $review->fetchAll(PDO::FETCH_ASSOC);
    $monthsNights = [];
    for ($night = $month; $night < $next; $night = $night->modify('+1 day')) {
        $monthsNights[$night->format('Y-m-d')] = ['booked'=>false, 'hold'=>false, 'blocked'=>false, 'requests'=>0, 'link'=>''];
    }
    $occupied = $db->prepare("SELECT id,start,end,state FROM bookings WHERE state IN ('creating','pending','paid','owner_block') AND start < ? AND end > ?");
    $occupied->execute([$end, $start]);
    $intervals = $occupied->fetchAll(PDO::FETCH_ASSOC);
    foreach ($c['blocked'] as $block) {
        $intervals[] = ['start'=>$block['start'], 'end'=>$block['end'], 'state'=>'blocked'];
    }
    $pendingCount = 0;
    foreach ($requests as $r) {
        if ($r['state'] === 'requested') {
            $pendingCount++;
        }
        if (!in_array($r['state'],['declined','released'],true) && $r['start'] < $end && $r['end'] > $start) {
            $intervals[] = $r;
        }
    }
    foreach ($intervals as $interval) {
        foreach ($monthsNights as $date => &$info) {
            if ($date < $interval['start'] || $date >= $interval['end']) {
                continue; // A returning guest releases the night starting on the return date.
            }
            switch ($interval['state']) {
                case 'requested':
                    $info['requests']++;
                    $info['link'] = $info['link'] ?: reference($interval['id']);
                    break;
                case 'approved':
                    $info['link'] = reference($interval['id']);
                    $info['booked'] = true;
                    break;
                case 'paid': $info['booked'] = true; break;
                case 'goodwill': $info['link']=reference($interval['id']); $info['hold']=true; break;
                case 'owner_block': case 'blocked': $info['blocked'] = true; break;
                default: $info['hold'] = true;
            }
        }
        unset($info);
    }
} catch (Throwable $e) {
    http_response_code($e instanceof Failure ? $e->status : 503);
    exit($e instanceof Failure ? h($e->getMessage()) : 'Diary temporarily unavailable.');
}
?>
<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Operator diary | Lakeland Touring</title>
<link rel="stylesheet" href="admin.css">
</head>
<body><main class="operator">
<header class="mast">
  <div class="wordmark"><span aria-hidden="true">LT</span> Lakeland Touring</div>
  <form method="post"><input type="hidden" name="csrf" value="<?=h($_SESSION['csrf'])?>"><button class="private" name="signout" value="1">Sign out</button></form>
</header>
<p>Touring Admin</p><h1>Bookings</h1>
<?php if ($error !== ''): ?><p class="error" role="alert"><?=h($error)?></p><?php endif; ?>
<div class="workspace">
<section class="calendar" aria-labelledby="month-title">
  <div class="month-bar">
    <h2 id="month-title"><?=h($month->format('F Y'))?></h2>
    <nav aria-label="Calendar month">
      <?php if ($monthKey > '1900-01'): ?><a href="?month=<?=h($previous->format('Y-m'))?>" aria-label="Previous month">&#8249;</a><?php endif; ?>
      <a class="current" href="?month=<?=h(substr($today, 0, 7))?>">Today</a>
      <?php if ($monthKey < '2199-12'): ?><a href="?month=<?=h($next->format('Y-m'))?>" aria-label="Next month">&#8250;</a><?php endif; ?>
    </nav>
  </div>
  <p class="vehicle">Elddis Avanté 866</p>
  <div class="month-grid">
    <?php foreach (['Mon','Tue','Wed','Thu','Fri','Sat','Sun'] as $weekday): ?><span class="weekday"><?=h($weekday)?></span><?php endforeach; ?>
    <?php for ($blank=1; $blank<(int)$month->format('N'); $blank++): ?><span aria-hidden="true"></span><?php endfor; ?>
    <?php foreach ($monthsNights as $date => $info):
        $status = $info['booked'] ? 'Reserved' : ($info['blocked'] ? 'Blocked' : ($info['hold'] ? 'Held' : ''));
        $short = $info['requests'] > 0 ? (string)$info['requests'].($info['requests'] === 1 ? ' request' : ' requests') : '';
        $label = (new DateTimeImmutable($date))->format('j F Y').($status ? ', '.$status : '').($short ? ', '.$short : '');
        $classes = 'night'.($status ? ' '.strtolower($status) : '').($info['requests'] ? ' requested' : '').($date === $today ? ' today' : '');
        $target = $info['link']; ?>
    <?php if ($target): ?><a class="<?=h($classes)?>" href="#request-<?=h($target)?>" aria-label="<?=h($label)?>"><?php else: ?><span class="<?=h($classes)?>" aria-label="<?=h($label)?>"><?php endif; ?>
      <b><?=h((string)(int)substr($date, -2))?></b>
      <?php if ($status): ?><span class="flag <?=h(strtolower($status))?>"><i aria-hidden="true"></i><span><?=h($status)?></span></span><?php endif; ?>
      <?php if ($short): ?><span class="flag requested"><i aria-hidden="true"></i><span><?=h($short)?></span></span><?php endif; ?>
    <?php if ($target): ?></a><?php else: ?></span><?php endif; ?>
    <?php endforeach; ?>
  </div>
  <div class="legend">
    <?php foreach (['requested'=>'Request','reserved'=>'Reserved','held'=>'Held','blocked'=>'Blocked'] as $style=>$title): ?><span class="flag <?=h($style)?>"><i aria-hidden="true"></i><?=h($title)?></span><?php endforeach; ?>
  </div>
  <p class="caption">Each date represents that night. Pending requests leave the dates open.</p>
</section>
<section class="queue" aria-labelledby="queue-title">
  <div class="queue-head"><h2 id="queue-title">Hire requests</h2><span class="count"><?=h((string)$pendingCount)?> pending</span></div>
  <?php if (!$requests): ?><p class="empty">No pending requests or recorded decisions for this month.</p><?php endif; ?>
  <?php foreach ($requests as $r):
    $guest = json_decode($r['customer'], true);
    $quote = json_decode($r['quote'], true);
    $state = $r['state'];
    $stateLabels = ['requested'=>'Awaiting approval', 'approved'=>'Approved', 'declined'=>'Declined','goodwill'=>'Held · Payment pending','released'=>'Hold released'];
    $ref = reference($r['id']);
    $arrival = new DateTimeImmutable($r['start']); $return = new DateTimeImmutable($r['end']); ?>
  <article class="request-card <?=h($state)?>" id="request-<?=h($ref)?>">
    <div class="card-meta"><span class="tag"><?=h($stateLabels[$state])?></span><small><?=h($ref)?></small></div>
    <h3><?=h($guest['name'])?></h3>
    <p class="stay"><?=h($arrival->format('j M Y'))?> to <?=h($return->format('j M Y'))?></p>
    <p class="hire"><?=h((string)$quote['nights'])?> nights · <?= $quote['hire_pence']===null?'Price to agree':h(pounds($quote['hire_pence'])).' hire' ?> · <?=h(['delivery'=>'Delivered','self-tow'=>'Self-tow','undecided'=>'Hire option to confirm'][$guest['mode']])?></p>
    <p class="contact"><a href="mailto:<?=h($guest['email'])?>"><?=h($guest['email'])?></a></p>
    <p class="notes"><?=h($guest['details'])?></p>
    <?php if (in_array($state,['goodwill','approved'],true)): ?><p><a href="../status.php?key=<?=h(\HireCalendar\receipt($c,$r['id']))?>">Open guest’s private holiday page</a></p>
    <form method="post"><input type="hidden" name="csrf" value="<?=h($_SESSION['csrf'])?>"><input type="hidden" name="id" value="<?=h($r['id'])?>"><label>Agreed handover (UK time) <input required type="time" name="handover" value="<?=h($quote['handover']??'')?>"></label><button name="save_time" value="1">Save handover time</button></form><?php endif; ?>
    <?php if (in_array($state,['requested','goodwill'],true)): ?>
    <form method="post">
      <input type="hidden" name="csrf" value="<?=h($_SESSION['csrf'])?>">
      <input type="hidden" name="id" value="<?=h($r['id'])?>">
      <?php if ($guest['mode'] === 'delivery'): ?><label class="agree"><input type="checkbox" name="delivery_agreed" value="1"> Customer has agreed the delivery price separately.</label><?php endif; ?>
      <?php if ($quote['hire_pence']===null): ?><label>Agreed hire price (£) <input name="agreed_price" inputmode="decimal" placeholder="0.00"></label><?php endif; ?>
      <label class="agree"><input type="checkbox" name="agreed" value="1"> I have checked availability, agreed the price with the guest and received the booking deposit.</label>
      <div class="actions"><button type="submit" name="decision" value="approved">Approve &amp; reserve dates</button><button class="secondary" type="submit" name="decision" value="<?=$state==='goodwill'?'released':'declined'?>"><?=$state==='goodwill'?'Release hold':'Decline'?></button></div>
    </form>
    <?php endif; ?>
  </article>
  <?php endforeach; ?>
</section>
</div>
<section class="request-card"><h2>Owner and maintenance dates</h2>
<form method="post"><input type="hidden" name="csrf" value="<?=h($_SESSION['csrf'])?>">
<label>First night <input type="date" name="start" required min="<?=h($today)?>"></label>
<label>Available again <input type="date" name="end" required min="<?=h($today)?>"></label>
<button name="block" value="1">Block dates</button></form>
<?php foreach ($intervals as $block): if ($block['state']!=='owner_block') continue; ?>
<form method="post"><input type="hidden" name="csrf" value="<?=h($_SESSION['csrf'])?>"><p><?=h($block['start'])?> to <?=h($block['end'])?> <button name="unblock" value="<?=h($block['id'])?>">Reopen dates</button></p></form><?php endforeach; ?>
</section></main></body></html>
