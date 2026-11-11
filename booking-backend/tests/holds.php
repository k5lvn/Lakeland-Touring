<?php
declare(strict_types=1);
require __DIR__.'/../public/api/common.php';
require __DIR__.'/../operations.php';
use function TouringBooking\{db,hold,claimHold,releaseHold,reconcileHolds,available,quote,dateValue};
use TouringBooking\Failure;
$checks=0;function ok($v){global $checks;if(!$v)throw new RuntimeException('Assertion failed at '.$checks);$checks++;}
function rejects($fn){try{$fn();}catch(Failure $e){ok(true);return;}throw new RuntimeException('Expected rejection');}
$private=sys_get_temp_dir().'/holds-'.bin2hex(random_bytes(8));mkdir($private,0700);
$_SERVER['DOCUMENT_ROOT']=__DIR__.'/../public';
$cfg=['private_dir'=>$private,'inventory_through'=>'2030-04-01','periods'=>[['start'=>'2030-03-01','end'=>'2030-04-01','prices'=>[7=>59500]]],'blocked'=>[],'booking_deposit_pence'=>25000,'balance_weeks'=>12,'terms_version'=>'fixture','live_mode'=>false];
$db=db($cfg);$q=quote($cfg,'2030-03-01','2030-03-08',dateValue('2026-10-21'));$now=time();
$one=hold($db,$cfg,'one',$q,$now);ok($one['hold_until']===$now+900);
ok((int)hold($db,$cfg,'one',$q,$now+60)['hold_until']===$now+900);
rejects(fn()=>hold($db,$cfg,'two',$q));
ok(releaseHold($db,$cfg,'one'));hold($db,$cfg,'two',$q);
claimHold($db,'two',$q,['name'=>'Fixture']);ok(!releaseHold($db,$cfg,'two'));
$db->exec("UPDATE bookings SET hold_until=1 WHERE id='two'");reconcileHolds($db,$cfg);rejects(fn()=>available($db,$q['start'],$q['end']));
$db->exec("UPDATE bookings SET session_id='cs_fixture',state='pending' WHERE id='two'");
$gateway=fn($method,$path)=>['id'=>'cs_fixture','client_reference_id'=>'two','livemode'=>false,'status'=>$method==='POST'?'expired':'open','payment_status'=>'unpaid'];
ok(releaseHold($db,$cfg,'two',$gateway));available($db,$q['start'],$q['end']);ok(true);
hold($db,$cfg,'three',$q);$db->exec("UPDATE bookings SET hold_until=1 WHERE id='three'");reconcileHolds($db,$cfg);available($db,$q['start'],$q['end']);ok(true);
hold($db,$cfg,'four',$q);$db->exec("UPDATE bookings SET state='paid' WHERE id='four'");ok(!releaseHold($db,$cfg,'four'));rejects(fn()=>available($db,$q['start'],$q['end']));
$plan=\TouringOperations\ownerPricingPlan();
ok($plan['annual_advertising_pence']===4900&&$plan['annual_unit']==='vehicle'&&$plan['annual_months']===12);
ok($plan['booking_admin_pence']===2500&&$plan['booking_unit']==='confirmed_booking'&&$plan['automatic_renewal']===false);
$b=['arrival'=>'2027-03-01','deposit_confirmed_pence'=>25000,'agreed_commission_pence'=>$plan['booking_admin_pence']];
$c=\TouringOperations\commission($b,new DateTimeImmutable('2026-12-07',new DateTimeZone('Europe/London')));ok($c['payable']&&$c['source']==='owner_booking_deposit');
ok($c['amount_pence']===2500&&$b['deposit_confirmed_pence']-$c['amount_pence']===22500);
ok(!\TouringOperations\commission($b,new DateTimeImmutable('2026-12-06'))['payable']);
$b['balance_confirmed_at']='2026-11-01T10:00:00+00:00';$c=\TouringOperations\commission($b,new DateTimeImmutable('2026-11-02'));ok($c['payable']&&$c['customer_details_releasable']&&$c['trigger']==='full_balance_received');
$b['agreed_commission_pence']=null;ok(!\TouringOperations\commission($b,new DateTimeImmutable('2026-12-08'))['payable']);
$v=['verified'=>true,'verified_at'=>'2026-10-22T12:00:00+01:00','verified_by'=>'fixture','evidence_reference'=>'fixture-only'];
$checksForHandover=['appointment_confirmed'=>true,'non_working_dates'=>[],'identity'=>$v,'licence'=>$v,'insurance'=>$v];
ok(\TouringOperations\handoverAllowed($checksForHandover,new DateTimeImmutable('2026-10-27T10:00:00+00:00')));
$checksForHandover['insurance']['verified']=false;ok(!\TouringOperations\handoverAllowed($checksForHandover,new DateTimeImmutable('2026-10-27T10:00:00+00:00')));
$db=null;foreach(glob($private.'/*')as$f)unlink($f);rmdir($private);echo "Passed $checks hold, cancellation, payment exclusion and operational-policy checks.\n";
