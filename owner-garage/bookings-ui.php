<?php
declare(strict_types=1);
namespace TouringGarage;

use DateTimeImmutable;
use DateTimeZone;
use PDO;

function form(string $action, string $id, string $fields, string $button): string {
    return '<form method="post">'.\token().'<input type="hidden" name="action" value="'.$action.'"><input type="hidden" name="booking_id" value="'.\h($id).'">'.$fields.'<button class="button">'.\h($button).'</button></form>';
}
function check(string $name,string $label): string {
    return '<label class="garage-check"><input type="checkbox" name="'.$name.'" required><span>'.\h($label).'</span></label>';
}
function input(string $name,string $label,string $type='text'): string {
    // Booking cards repeat fields; wrap labels to avoid duplicate IDs.
    return '<label>'.\h($label).'<input name="'.$name.'" type="'.$type.'" maxlength="200" required></label>';
}
function render(PDO $db, array $actor, bool $admin, string $flash, array $config): string {
    $now=new DateTimeImmutable('now',new DateTimeZone('Europe/London'));
    $out='<h1>Bookings</h1>'.$flash.'<p>£49 per vehicle per year, plus a £25 admin fee per confirmed booking. Payment confirmations record what the owner has received; they do not collect money or verify a bank account.</p>';
    if($admin){
        $out.='<details><summary>Record a booking for an owner</summary><form method="post">'.\token().'<input type="hidden" name="action" value="create-booking"><label>Vehicle<select name="vehicle_id" required><option value="">Choose a vehicle</option>';
        foreach(query($db,'SELECT v.id,v.title FROM vehicles v JOIN garage_plan_acceptances p ON p.vehicle_id=v.id WHERE v.status="live" AND v.paid_until>? AND p.version=? AND NOT EXISTS(SELECT 1 FROM garage_restrictions r WHERE r.owner_id=v.owner_id) GROUP BY v.id',[time(),\TouringOperations\ownerPricingPlan()['version']])->fetchAll(PDO::FETCH_ASSOC) as $v)$out.='<option value="'.$v['id'].'">'.\h($v['title']).'</option>';
        $out.='</select></label>'.input('arrival','Arrival','date').input('departure','Return','date').input('hire_amount','Full hire price (£)').input('customer_name','Customer name').input('customer_email','Customer email','email').input('customer_phone','Customer phone','tel').'<button class="button">Record booking</button></form></details>';
    } else {
        foreach(query($db,'SELECT * FROM vehicles WHERE owner_id=?',[$actor['id']])->fetchAll(PDO::FETCH_ASSOC) as $v){
            $accepted=query($db,'SELECT accepted_at FROM garage_plan_acceptances WHERE vehicle_id=? AND version=?',[$v['id'],\TouringOperations\ownerPricingPlan()['version']])->fetchColumn();
            $out.='<section class="garage-box"><h2>'.\h($v['title']).'</h2>';
            if($accepted)$out.='<p>New booking plan accepted on '.\h($accepted).'. Existing annual expiry: '.($v['paid_until']?\h(date('j M Y',(int)$v['paid_until'])):'awaiting annual payment').'.</p>';
            else $out.='<p>Your existing advertising agreement stays in place until you accept this new booking plan. Acceptance does not renew your annual advert or take payment.</p><form method="post">'.\token().'<input type="hidden" name="action" value="accept-plan"><input type="hidden" name="vehicle_id" value="'.$v['id'].'">'.check('accept_plan','I accept £49 per vehicle for 12 months and a £25 admin fee per confirmed booking, under the owner booking terms.').'<p><a href="owner-booking-terms.html">Read the owner booking terms</a> · <a href="garage-booking-privacy.html">Booking privacy notice</a></p><button class="button">Accept booking plan</button></form>';
            $out.='</section>';
        }
    }
    $rows=query($db,'SELECT b.*,v.title FROM garage_bookings b JOIN vehicles v ON v.id=b.vehicle_id'.($admin?'':' WHERE b.owner_id=?').' ORDER BY b.arrival,b.created_at',$admin?[]:[$actor['id']])->fetchAll(PDO::FETCH_ASSOC);
    if(!$rows)$out.='<p>No bookings recorded yet.</p>';
    foreach($rows as $raw){$b=visible($raw,$admin,$now);$fee=fee($raw,$now);$id=$b['id'];
        $out.='<article class="garage-box booking-card"><h2>'.\h($b['title']).'</h2><p>Booking '.\h($id).' · '.\h($b['state']).'<br>'.\h($b['arrival']).' to '.\h($b['departure']).' · £'.number_format($b['hire_pence']/100,2).'</p>';
        if(isset($b['customer_name']))$out.='<section class="customer-details"><h3>Customer details</h3><p>'.\h($b['customer_name']).'<br>'.\h($b['customer_email']).'<br>'.\h($b['customer_phone']).'</p></section>';
        else $out.='<p class="customer-withheld">Customer details stay private until you confirm that the full balance has reached you. Use the booking reference when contacting Touring.</p>';
        $out.='<p>Booking deposit: '.($b['deposit_confirmed_at']?'£250 confirmed received':'awaiting owner confirmation').'<br>Full balance: '.($b['balance_confirmed_at']?'confirmed received':'awaiting owner confirmation').'</p>';
        $out.='<p>£25 admin fee: '.($b['fee_paid_at']?'received by Touring':($fee['payable']?'due from the owner’s booking deposit':($b['state']==='cancelled'&&!$fee['earned']?'not earned before cancellation; refund review required':'not yet due'))).'.<br>Due at the earlier of full balance confirmation or '.\h(dateOnly($b['arrival'])->modify('-12 weeks')->format('Y-m-d')).' (12 weeks before arrival). No money is moved by this screen.</p>';
        if($b['state']!=='cancelled'&&!$b['handover_at']){
            if((int)$actor['id']===(int)$b['owner_id'])foreach(['deposit','balance'] as $kind){
                if(!$b[$kind.'_confirmed_at']&&($kind==='deposit'||$b['deposit_confirmed_at']))$out.=form('confirm-'.$kind,$id,input('reference','Payment receipt / bank reference').check('received',$kind==='deposit'?'I have actually received the £250 booking deposit.':'I have actually received the full hire price, including the booking deposit.'),'Confirm '.$kind.' received');
            }
            if($admin&&!$b['confirmed_at'])$out.=form('confirm-booking',$id,'<p>Confirm only after the owner records receipt of the deposit.</p>','Confirm booking through Touring');
            $out.='<details><summary>Collection appointment and checks</summary><p>Collection must be Monday–Friday, 09:00–16:00, by appointment. Identity, licence and insurance evidence must be checked at least two working days beforehand.</p><p>Appointment: '.\h($b['appointment_at']??'not set').'</p>';
            $out.=form('appointment',$id,input('appointment','Collection appointment','datetime-local'),'Set appointment');
            foreach(['identity','licence','insurance'] as $kind){
                if($b[$kind.'_at']){
                    $out.='<p>'.\h(ucfirst($kind)).' checked: '.\h($b[$kind.'_at']).'</p>';
                    $out.='<details><summary>Withdraw '.\h($kind).' check</summary><p>Use this if the evidence is incorrect, expired or no longer valid. Handover will be blocked until new evidence is checked in time. The original check remains in the audit record.</p>'.form('invalidate-evidence',$id,'<input type="hidden" name="kind" value="'.$kind.'">'.input('reason','Reason for withdrawing the check').check('invalidated','I confirm this evidence check is no longer valid.'),'Withdraw '.$kind.' check').'</details>';
                }
                else $out.=form('verify-evidence',$id,'<input type="hidden" name="kind" value="'.$kind.'">'.input('reference',ucfirst($kind).' evidence reference (store documents securely)').check('verified','I checked the '.$kind.' evidence.'),'Record '.$kind.' check');
            }
            $out.='<p>Handover prerequisites: '.(allowedHandover($b,$config['non_working_dates'])?'complete':'incomplete').'.</p>'.form('authorise-handover',$id,check('checked','I checked the prerequisites and am handing the vehicle over at the agreed appointment.'),'Record handover').'</details>';
            if($admin)$out.='<details><summary>Cancel booking</summary><p>This records cancellation only. Refunds require a separate review; no refund is issued here.</p>'.form('cancel-booking',$id,input('reason','Cancellation reason'),'Record cancellation').'</details>';
        }
        if($b['handover_at'])$out.='<p>Handover recorded: '.\h($b['handover_at']).'</p>';
        if($admin&&$fee['payable'])$out.=form('record-fee',$id,input('reference','Admin fee receipt reference').check('received','Touring has actually received the £25 admin fee from the owner’s deposit.'),'Record admin fee received');
        $out.='<details><summary>Booking history</summary><ol>';
        foreach(query($db,'SELECT event,recorded_at,actor_id FROM garage_booking_audit WHERE booking_id=? ORDER BY id',[$id])->fetchAll(PDO::FETCH_ASSOC) as $event)$out.='<li>'.\h($event['recorded_at']).' · '.\h(str_replace('_',' ',$event['event'])).' · account '.(int)$event['actor_id'].'</li>';
        $out.='</ol></details></article>';
    }
    if($admin)$out.='<details><summary>End advertising rights after diversion review</summary><p>Review evidence before using this action. It removes all owner adverts from public view and prevents new bookings; existing booking records remain available.</p><form method="post">'.\token().'<input type="hidden" name="action" value="terminate-advertising">'.input('owner_id','Owner account number','number').input('reason','Reviewed evidence reference / reason').check('reviewed','I reviewed the diversion evidence and confirm that advertising rights must end.').'<button class="button">End advertising rights</button></form></details>';
    return $out.form('logout','','','Sign out');
}
