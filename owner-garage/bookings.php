<?php
declare(strict_types=1);
namespace TouringGarage;

use DateTimeImmutable;
use DateTimeZone;
use PDO;
use RuntimeException;
use Throwable;

require_once __DIR__.'/booking-policy.php';

function schema(PDO $db): void {
    $db->exec('CREATE TABLE IF NOT EXISTS garage_plan_acceptances (
        id INTEGER PRIMARY KEY, vehicle_id INTEGER NOT NULL REFERENCES vehicles(id), owner_id INTEGER NOT NULL REFERENCES owners(id),
        version TEXT NOT NULL, annual_pence INTEGER NOT NULL, booking_pence INTEGER NOT NULL, accepted_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS garage_restrictions (owner_id INTEGER PRIMARY KEY REFERENCES owners(id), reason TEXT NOT NULL, recorded_at TEXT NOT NULL, actor_id INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS garage_bookings (
        id TEXT PRIMARY KEY, vehicle_id INTEGER NOT NULL REFERENCES vehicles(id), owner_id INTEGER NOT NULL REFERENCES owners(id),
        plan_acceptance_id INTEGER NOT NULL REFERENCES garage_plan_acceptances(id), arrival TEXT NOT NULL, departure TEXT NOT NULL,
        hire_pence INTEGER NOT NULL, agreed_commission_pence INTEGER NOT NULL, customer_name TEXT NOT NULL, customer_email TEXT NOT NULL, customer_phone TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT "awaiting_deposit", deposit_confirmed_pence INTEGER NOT NULL DEFAULT 0,
        deposit_confirmed_at TEXT, deposit_reference TEXT, balance_confirmed_at TEXT, balance_reference TEXT,
        confirmed_at TEXT, cancelled_at TEXT, fee_paid_at TEXT, fee_reference TEXT,
        appointment_at TEXT, identity_at TEXT, identity_by INTEGER, identity_ref TEXT,
        licence_at TEXT, licence_by INTEGER, licence_ref TEXT, insurance_at TEXT, insurance_by INTEGER, insurance_ref TEXT,
        handover_at TEXT, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS garage_booking_audit (
        id INTEGER PRIMARY KEY, booking_id TEXT, vehicle_id INTEGER, actor_id INTEGER NOT NULL, event TEXT NOT NULL, recorded_at TEXT NOT NULL, detail TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS garage_audit_no_update BEFORE UPDATE ON garage_booking_audit BEGIN SELECT RAISE(ABORT,"Audit records are append-only"); END;
        CREATE TRIGGER IF NOT EXISTS garage_audit_no_delete BEFORE DELETE ON garage_booking_audit BEGIN SELECT RAISE(ABORT,"Audit records are append-only"); END;
        CREATE TRIGGER IF NOT EXISTS garage_plan_no_update BEFORE UPDATE ON garage_plan_acceptances BEGIN SELECT RAISE(ABORT,"Accepted terms are immutable"); END;
        CREATE TRIGGER IF NOT EXISTS garage_plan_no_delete BEFORE DELETE ON garage_plan_acceptances BEGIN SELECT RAISE(ABORT,"Accepted terms are immutable"); END;');
}
function query(PDO $db, string $sql, array $args=[]): \PDOStatement {
    $s=$db->prepare($sql);$s->execute($args);return $s;
}
function audit(PDO $db, int $actor, string $event, DateTimeImmutable $now, ?array $booking=null, array $detail=[]): void {
    query($db,'INSERT INTO garage_booking_audit(booking_id,vehicle_id,actor_id,event,recorded_at,detail) VALUES(?,?,?,?,?,?)',
        [$booking['id']??null,$booking['vehicle_id']??null,$actor,$event,$now->format(DATE_ATOM),json_encode($detail,JSON_THROW_ON_ERROR)]);
}
function text(array $input, string $key, int $max=200): string {
    $s=trim((string)($input[$key]??''));
    if($s===''||strlen($s)>$max||preg_match('/[\x00-\x1F\x7F]/',$s))throw new RuntimeException('Complete the required fields within their limits.');
    return $s;
}
function dateOnly(string $value): DateTimeImmutable {
    $date=DateTimeImmutable::createFromFormat('!Y-m-d',$value,new DateTimeZone('Europe/London'));
    if(!$date||$date->format('Y-m-d')!==$value)throw new RuntimeException('Enter a valid date.');return $date;
}
function fee(array $b, DateTimeImmutable $now): array {
    $result=\TouringOperations\commission($b,$now);
    // A cancelled booking cannot earn a fee later; already-earned fees remain due.
    $earned=$b['confirmed_at']!==null && (!$b['cancelled_at'] || new DateTimeImmutable($result['trigger_at'])<=new DateTimeImmutable($b['cancelled_at']));
    $result['payable']=$result['payable']&&$earned&&!$b['fee_paid_at'];
    $result['earned']=$earned&&$result['due'];return $result;
}
function visible(array $b, bool $admin, DateTimeImmutable $now): array {
    if(!$admin && !\TouringOperations\commission($b,$now)['customer_details_releasable']){
        unset($b['customer_name'],$b['customer_email'],$b['customer_phone']);
    }
    return $b;
}
function allowedHandover(array $b, array $closures): bool {
    if(!$b['appointment_at']||!$b['balance_confirmed_at']||$b['state']!=='confirmed')return false;
    $checks=['appointment_confirmed'=>true,'non_working_dates'=>$closures];
    foreach(['identity','licence','insurance'] as $kind)$checks[$kind]=['verified'=>!empty($b[$kind.'_at']),
        'verified_at'=>$b[$kind.'_at'],'verified_by'=>$b[$kind.'_by'],'evidence_reference'=>$b[$kind.'_ref']];
    return \TouringOperations\handoverAllowed($checks,new DateTimeImmutable($b['appointment_at']));
}
function act(PDO $db, int $actorId, string $action, array $input, array $config, ?DateTimeImmutable $now=null): void {
    $now??=new DateTimeImmutable('now',new DateTimeZone('Europe/London'));$stamp=$now->format(DATE_ATOM);
    $db->exec('BEGIN IMMEDIATE');
    try {
        $actor=query($db,'SELECT * FROM owners WHERE id=?',[$actorId])->fetch(PDO::FETCH_ASSOC);
        if(!$actor||!$actor['verified'])throw new RuntimeException('Verified account required.');
        $admin=strcasecmp($actor['email'],\GARAGE_EMAIL)===0;
        if($action==='accept-plan'){
            if(empty($input['accept_plan']))throw new RuntimeException('Accept the £49 annual and £25 booking admin terms first.');
            $v=query($db,'SELECT * FROM vehicles WHERE id=? AND owner_id=?',[(int)($input['vehicle_id']??0),$actorId])->fetch(PDO::FETCH_ASSOC);
            if(!$v)throw new RuntimeException('Vehicle not found in your garage.');
            if(query($db,'SELECT 1 FROM garage_restrictions WHERE owner_id=?',[$actorId])->fetchColumn())throw new RuntimeException('Advertising rights have ended. Contact Touring.');
            $plan=\TouringOperations\ownerPricingPlan();
            if(!query($db,'SELECT 1 FROM garage_plan_acceptances WHERE vehicle_id=? AND version=?',[$v['id'],$plan['version']])->fetchColumn()){
                query($db,'INSERT INTO garage_plan_acceptances(vehicle_id,owner_id,version,annual_pence,booking_pence,accepted_at) VALUES(?,?,?,?,?,?)',[$v['id'],$actorId,$plan['version'],$plan['annual_advertising_pence'],$plan['booking_admin_pence'],$stamp]);
                audit($db,$actorId,'plan_accepted',$now,['vehicle_id'=>$v['id']],$plan);
            }
        } elseif($action==='create-booking') {
            if(!$admin)throw new RuntimeException('Touring administrator access required.');
            $v=query($db,'SELECT * FROM vehicles WHERE id=?',[(int)($input['vehicle_id']??0)])->fetch(PDO::FETCH_ASSOC);
            if(!$v||$v['status']!=='live'||(int)$v['paid_until']<=$now->getTimestamp())throw new RuntimeException('An active paid listing is required.');
            if(query($db,'SELECT 1 FROM garage_restrictions WHERE owner_id=?',[$v['owner_id']])->fetchColumn())throw new RuntimeException('Advertising rights have ended.');
            $plan=query($db,'SELECT * FROM garage_plan_acceptances WHERE vehicle_id=? AND version=? ORDER BY id DESC LIMIT 1',[$v['id'],\TouringOperations\ownerPricingPlan()['version']])->fetch(PDO::FETCH_ASSOC);
            if(!$plan)throw new RuntimeException('The vehicle owner must accept the new pricing plan first.');
            $arrival=dateOnly(text($input,'arrival'));$departure=dateOnly(text($input,'departure'));
            if($arrival<$now->setTimezone(new DateTimeZone('Europe/London'))->setTime(0,0)||$departure<=$arrival)throw new RuntimeException('Choose a future arrival and a later return date.');
            $amount=text($input,'hire_amount');if(!preg_match('/^\d{1,6}(?:\.\d{1,2})?$/D',$amount))throw new RuntimeException('Enter the full hire price in pounds.');
            $parts=explode('.',$amount);$pence=((int)$parts[0])*100+(int)str_pad($parts[1]??'',2,'0');
            if($pence<25000)throw new RuntimeException('The hire price must cover the £250 booking deposit.');
            $email=text($input,'customer_email');if(!filter_var($email,FILTER_VALIDATE_EMAIL))throw new RuntimeException('Enter a valid customer email.');
            if(query($db,'SELECT 1 FROM garage_bookings WHERE vehicle_id=? AND state!="cancelled" AND arrival<? AND departure>?',[$v['id'],$departure->format('Y-m-d'),$arrival->format('Y-m-d')])->fetchColumn())throw new RuntimeException('These dates overlap another booking record.');
            $id=bin2hex(random_bytes(12));query($db,'INSERT INTO garage_bookings(id,vehicle_id,owner_id,plan_acceptance_id,arrival,departure,hire_pence,agreed_commission_pence,customer_name,customer_email,customer_phone,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                [$id,$v['id'],$v['owner_id'],$plan['id'],$arrival->format('Y-m-d'),$departure->format('Y-m-d'),$pence,$plan['booking_pence'],text($input,'customer_name'),$email,text($input,'customer_phone',50),$stamp]);
            audit($db,$actorId,'booking_recorded',$now,['id'=>$id,'vehicle_id'=>$v['id']]);
        } elseif($action==='terminate-advertising') {
            if(!$admin)throw new RuntimeException('Touring administrator access required.');
            $ownerId=(int)($input['owner_id']??0);$reason=text($input,'reason',1000);
            if(empty($input['reviewed'])||!query($db,'SELECT 1 FROM owners WHERE id=?',[$ownerId])->fetchColumn())throw new RuntimeException('Review the evidence and confirm termination first.');
            if(!query($db,'SELECT 1 FROM garage_restrictions WHERE owner_id=?',[$ownerId])->fetchColumn()){
                query($db,'INSERT INTO garage_restrictions VALUES(?,?,?,?)',[$ownerId,$reason,$stamp,$actorId]);
                query($db,'UPDATE vehicles SET status="draft" WHERE owner_id=?',[$ownerId]);
                audit($db,$actorId,'advertising_terminated',$now,null,['owner_id'=>$ownerId,'reason'=>$reason]);
            }
        } else {
            $b=query($db,'SELECT * FROM garage_bookings WHERE id=?',[(string)($input['booking_id']??'')])->fetch(PDO::FETCH_ASSOC);
            if(!$b||(!$admin&&(int)$b['owner_id']!==$actorId))throw new RuntimeException('Booking not found in your garage.');
            if($action==='record-fee'){
                if(!$admin)throw new RuntimeException('Touring administrator access required.');
                if(!$b['fee_paid_at']){
                    if(!fee($b,$now)['payable']||empty($input['received']))throw new RuntimeException('The admin fee must be due and actually received first.');
                    query($db,'UPDATE garage_bookings SET fee_paid_at=?,fee_reference=? WHERE id=?',[$stamp,text($input,'reference'),$b['id']]);audit($db,$actorId,'admin_fee_received',$now,$b,['amount_pence'=>$b['agreed_commission_pence']]);
                }
            } elseif($action==='cancel-booking') {
                if(!$admin)throw new RuntimeException('Touring administrator access required.');
                if($b['handover_at'])throw new RuntimeException('A handed-over booking cannot be cancelled here.');
                if($b['state']!=='cancelled'){
                    $reason=text($input,'reason',1000);query($db,'UPDATE garage_bookings SET state="cancelled",cancelled_at=? WHERE id=?',[$stamp,$b['id']]);audit($db,$actorId,'booking_cancelled',$now,$b,['reason'=>$reason,'refund'=>'manual_review']);
                }
            } else {
                if($b['state']==='cancelled'||$b['handover_at'])throw new RuntimeException('This booking is closed to changes.');
                if(in_array($action,['confirm-deposit','confirm-balance'],true)){
                    if((int)$b['owner_id']!==$actorId)throw new RuntimeException('Only the vehicle owner can confirm their receipt of hire payments.');
                    $kind=$action==='confirm-deposit'?'deposit':'balance';
                    if(!$b[$kind.'_confirmed_at']){
                        if(empty($input['received']))throw new RuntimeException('Confirm that the payment has actually reached you.');
                        if($kind==='balance'&&!$b['deposit_confirmed_at'])throw new RuntimeException('Confirm the booking deposit first.');
                        $ref=text($input,'reference');
                        if($kind==='deposit')query($db,'UPDATE garage_bookings SET deposit_confirmed_pence=25000,deposit_confirmed_at=?,deposit_reference=? WHERE id=?',[$stamp,$ref,$b['id']]);
                        else query($db,'UPDATE garage_bookings SET balance_confirmed_at=?,balance_reference=? WHERE id=?',[$stamp,$ref,$b['id']]);
                        audit($db,$actorId,$kind.'_received',$now,$b,['amount_pence'=>$kind==='deposit'?25000:$b['hire_pence']-25000]);
                    }
                } elseif($action==='confirm-booking') {
                    if(!$admin)throw new RuntimeException('Only Touring can confirm the booking.');
                    if(!$b['confirmed_at']){
                        if(!$b['deposit_confirmed_at'])throw new RuntimeException('The owner must confirm the deposit first.');
                        query($db,'UPDATE garage_bookings SET state="confirmed",confirmed_at=? WHERE id=?',[$stamp,$b['id']]);audit($db,$actorId,'booking_confirmed',$now,$b);
                    }
                } elseif($action==='appointment') {
                    $local=text($input,'appointment');$date=DateTimeImmutable::createFromFormat('!Y-m-d\TH:i',$local,new DateTimeZone('Europe/London'));
                    if(!$date||$date->format('Y-m-d\TH:i')!==$local||$date<=$now||$date->format('Y-m-d')!==$b['arrival']||(int)$date->format('N')>5||$date->format('H:i')<'09:00'||$date->format('H:i')>='16:00'||in_array($date->format('Y-m-d'),$config['non_working_dates'],true))throw new RuntimeException('Choose an arrival-day appointment, Monday–Friday 09:00–16:00, outside closure dates.');
                    if($b['appointment_at']!==$date->format(DATE_ATOM)){query($db,'UPDATE garage_bookings SET appointment_at=? WHERE id=?',[$date->format(DATE_ATOM),$b['id']]);audit($db,$actorId,'appointment_set',$now,$b,['appointment_at'=>$date->format(DATE_ATOM)]);}
                } elseif($action==='verify-evidence') {
                    $kind=text($input,'kind');if(!in_array($kind,['identity','licence','insurance'],true)||empty($input['verified']))throw new RuntimeException('Confirm the evidence check.');
                    if(!$b[$kind.'_at']){query($db,"UPDATE garage_bookings SET {$kind}_at=?,{$kind}_by=?,{$kind}_ref=? WHERE id=?",[$stamp,$actorId,text($input,'reference'),$b['id']]);audit($db,$actorId,$kind.'_verified',$now,$b);}
                } elseif($action==='authorise-handover') {
                    if(!allowedHandover($b,$config['non_working_dates']))throw new RuntimeException('Handover requires a confirmed booking, full balance, appointment and all evidence checked at least two working days beforehand.');
                    $appointment=new DateTimeImmutable($b['appointment_at']);
                    if($now->setTimezone(new DateTimeZone('Europe/London'))->format('Y-m-d')!==$appointment->format('Y-m-d')||$now<$appointment||$now->setTimezone(new DateTimeZone('Europe/London'))->format('H:i')>='16:00')throw new RuntimeException('Record handover at or after the appointment during that day’s office hours.');
                    if(empty($input['checked']))throw new RuntimeException('Confirm the handover check first.');
                    query($db,'UPDATE garage_bookings SET handover_at=? WHERE id=?',[$stamp,$b['id']]);audit($db,$actorId,'handover_authorised',$now,$b);
                } else throw new RuntimeException('Unknown booking action.');
            }
        }
        $db->exec('COMMIT');
    } catch(Throwable $e){$db->exec('ROLLBACK');throw $e;}
}
