<?php
declare(strict_types=1);
// Run from a disposable directory containing the publication-shaped module files.
const GARAGE_EMAIL='LakelandTouring@Worx365Group.uk';
require $argv[1].'/garage-bookings.php';
use function TouringGarage\{schema,act,query,fee,allowedHandover};
use DateTimeImmutable as Clock;
$db=new PDO('sqlite::memory:',null,null,[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC]);
$db->exec('PRAGMA foreign_keys=ON; CREATE TABLE owners(id INTEGER PRIMARY KEY,email TEXT,verified INTEGER); CREATE TABLE vehicles(id INTEGER PRIMARY KEY,owner_id INTEGER,title TEXT,status TEXT,paid_until INTEGER); INSERT INTO owners VALUES(1,"owner@example.test",1),(2,"LakelandTouring@Worx365Group.uk",1); INSERT INTO vehicles VALUES(1,1,"Fixture","live",2000000000);');schema($db);
$cfg=['non_working_dates'=>[]];$checks=0;
function ok(bool $v):void{global $checks;if(!$v)throw new RuntimeException('Failed policy check '.$checks);$checks++;}
function refuses(callable $fn):void{try{$fn();}catch(RuntimeException $e){ok(true);return;}throw new RuntimeException('Expected refusal');}
$at=fn($s)=>new Clock($s,new DateTimeZone('Europe/London'));
act($db,1,'accept-plan',['vehicle_id'=>1,'accept_plan'=>1],$cfg,$at('2026-10-01'));
$create=['vehicle_id'=>1,'arrival'=>'2027-03-01','departure'=>'2027-03-08','hire_amount'=>'650','customer_name'=>'Fixture','customer_email'=>'fixture@example.test','customer_phone'=>'fixture'];
act($db,2,'create-booking',$create,$cfg,$at('2026-10-01'));
$b=query($db,'SELECT * FROM garage_bookings')->fetch();$id=$b['id'];$fields=['booking_id'=>$id,'received'=>1,'reference'=>'fixture'];
act($db,1,'confirm-deposit',$fields,$cfg,$at('2026-10-01'));
act($db,2,'confirm-booking',$fields,$cfg,$at('2026-10-01'));
$b=query($db,'SELECT * FROM garage_bookings')->fetch();
ok(!fee($b,$at('2026-12-06 23:59:59'))['payable']);ok(fee($b,$at('2026-12-07'))['payable']);
ok(fee($b,$at('2026-12-07'))['amount_pence']===2500);
act($db,1,'confirm-balance',$fields,$cfg,$at('2026-11-01'));
$b=query($db,'SELECT * FROM garage_bookings')->fetch();ok(fee($b,$at('2026-11-01'))['payable']);
act($db,1,'appointment',['booking_id'=>$id,'appointment'=>'2027-03-01T10:00'],$cfg,$at('2027-02-20'));
foreach(['identity','licence','insurance'] as $kind)act($db,1,'verify-evidence',['booking_id'=>$id,'kind'=>$kind,'verified'=>1,'reference'=>'fixture'],$cfg,$at('2027-02-25 10:00'));
$b=query($db,'SELECT * FROM garage_bookings')->fetch();ok(allowedHandover($b,[]));ok(!allowedHandover($b,['2027-02-26']));
// Withdrawn evidence must block handover; a recheck gets a new server time.
$withdraw=['booking_id'=>$id,'kind'=>'insurance','invalidated'=>1,'reason'=>'Policy withdrawn'];
act($db,2,'invalidate-evidence',$withdraw,$cfg,$at('2027-02-25 10:30'));
$b=query($db,'SELECT * FROM garage_bookings')->fetch();ok($b['insurance_at']===null&&$b['insurance_by']===null&&$b['insurance_ref']===null);ok(!allowedHandover($b,[]));
$history=query($db,'SELECT actor_id,detail FROM garage_booking_audit WHERE event="insurance_invalidated"')->fetch();$detail=json_decode($history['detail'],true);
ok((int)$history['actor_id']===2&&$detail['previous']['evidence_reference']==='fixture'&&$detail['previous']['verified_by']===1&&$detail['reason']==='Policy withdrawn');
$count=query($db,'SELECT count(*) FROM garage_booking_audit')->fetchColumn();act($db,2,'invalidate-evidence',$withdraw,$cfg,$at('2027-02-25 10:31'));ok(query($db,'SELECT count(*) FROM garage_booking_audit')->fetchColumn()===$count);
act($db,1,'verify-evidence',['booking_id'=>$id,'kind'=>'insurance','verified'=>1,'reference'=>'replacement-policy'],$cfg,$at('2027-02-25 10:40'));
$b=query($db,'SELECT * FROM garage_bookings')->fetch();ok($b['insurance_ref']==='replacement-policy'&&$b['insurance_at']==='2027-02-25T10:40:00+00:00');ok(!allowedHandover($b,[]));
// A later collection slot restores the required two-working-day interval.
act($db,1,'appointment',['booking_id'=>$id,'appointment'=>'2027-03-01T11:00'],$cfg,$at('2027-02-25 10:45'));
$b=query($db,'SELECT * FROM garage_bookings')->fetch();ok(allowedHandover($b,[]));
refuses(fn()=>act($db,1,'authorise-handover',['booking_id'=>$id,'checked'=>1],$cfg,$at('2027-02-26 10:00')));
act($db,1,'authorise-handover',['booking_id'=>$id,'checked'=>1],$cfg,$at('2027-03-01 11:00'));
ok(query($db,'SELECT handover_at FROM garage_bookings')->fetchColumn()!==false);
refuses(fn()=>act($db,2,'cancel-booking',['booking_id'=>$id,'reason'=>'fixture'],$cfg,$at('2027-03-01 11:00')));
// Cancellation before the threshold earns no later fee; earned fees survive cancellation.
$b['handover_at']=null;$b['balance_confirmed_at']=null;$b['cancelled_at']='2026-11-01T00:00:00+00:00';
ok(!fee($b,$at('2027-01-01'))['payable']);$b['cancelled_at']='2026-12-08T00:00:00+00:00';ok(fee($b,$at('2027-01-01'))['payable']);
$b['fee_paid_at']='2026-12-08T00:00:00+00:00';ok(!fee($b,$at('2027-01-01'))['payable']);
// Missing and late evidence cannot authorise handover, including a weekend.
$b['state']='confirmed';$b['balance_confirmed_at']='2027-02-01T00:00:00+00:00';$b['insurance_at']=null;ok(!allowedHandover($b,[]));
$b['insurance_at']='2027-02-26T10:00:00+00:00';ok(!allowedHandover($b,[]));
$b['appointment_at']='2027-02-28T10:00:00+00:00';ok(!allowedHandover($b,[]));
echo "Passed $checks booking fee timing, cancellation and handover policy checks.\n";
