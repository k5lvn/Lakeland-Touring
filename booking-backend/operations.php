<?php
declare(strict_types=1);
namespace TouringOperations;

use DateTimeImmutable;
use DateTimeZone;
use InvalidArgumentException;

// Persist these amounts with an explicitly accepted new-plan agreement.
// Do not infer acceptance or reprice existing advertising agreements.
function ownerPricingPlan(): array {
    return ['version'=>'owner-admin-20261021','annual_advertising_pence'=>4900,
        'annual_unit'=>'vehicle','annual_months'=>12,'booking_admin_pence'=>2500,
        'booking_unit'=>'confirmed_booking','automatic_renewal'=>false];
}

// Owner confirmations are evidence of receipt, not automatic bank verification.
// Integration must enforce owner/listing permissions before calling these rules.
function commission(array $booking, DateTimeImmutable $now): array {
    $zone=new DateTimeZone('Europe/London');
    $arrival=DateTimeImmutable::createFromFormat('!Y-m-d',$booking['arrival']??'', $zone);
    if (!$arrival || $arrival->format('Y-m-d')!==($booking['arrival']??'')) throw new InvalidArgumentException('Invalid arrival date.');
    $threshold=$arrival->modify('-12 weeks');
    $balance=isset($booking['balance_confirmed_at'])?new DateTimeImmutable($booking['balance_confirmed_at']):null;
    $trigger=$balance&&$balance<$threshold?$balance:$threshold;
    $deposit=$booking['deposit_confirmed_pence']??null;
    $fee=$booking['agreed_commission_pence']??null;
    if (!is_int($deposit)||$deposit<0||($fee!==null&&(!is_int($fee)||$fee<0))) throw new InvalidArgumentException('Invalid confirmed amounts.');
    $due=$now>=$trigger;
    return ['trigger_at'=>$trigger->format(DATE_ATOM),'trigger'=>$balance&&$balance<$threshold?'full_balance_received':'12_weeks_before_arrival',
        'due'=>$due,'source'=>'owner_booking_deposit','amount_pence'=>$fee,
        'payable'=>$due&&$fee!==null&&$deposit>=$fee&&$deposit>0,
        'shortfall_pence'=>$fee===null?null:max(0,$fee-$deposit),
        'customer_details_releasable'=>$balance!==null&&$now>=$balance];
}
function handoverAllowed(array $checks, DateTimeImmutable $collection): bool {
    $zone=new DateTimeZone('Europe/London');$collection=$collection->setTimezone($zone);
    // Office hours agreed Mon–Fri 09:00–16:00. Holiday/insurer closures are
    // explicit private dates; no statutory calendar is guessed here.
    if (($checks['appointment_confirmed']??false)!==true || (int)$collection->format('N')>5 || $collection->format('H:i')<'09:00' || $collection->format('H:i')>='16:00') return false;
    if (!isset($checks['non_working_dates'])||!is_array($checks['non_working_dates'])||in_array($collection->format('Y-m-d'),$checks['non_working_dates'],true)) return false;
    $deadline=$collection;$days=0;
    while($days<2){$deadline=$deadline->modify('-1 day');if((int)$deadline->format('N')<=5&&!in_array($deadline->format('Y-m-d'),$checks['non_working_dates'],true))$days++;}
    // Evidence must be complete at least two working days before collection.
    foreach(['identity','licence','insurance'] as $type){
        $check=$checks[$type]??[];
        if(($check['verified']??false)!==true || empty($check['verified_at']) || empty($check['verified_by']) || empty($check['evidence_reference']))return false;
        $at=new DateTimeImmutable($check['verified_at']);if($at>$deadline)return false;
    }
    return true;
}
