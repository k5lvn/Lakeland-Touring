<?php
declare(strict_types=1);
require __DIR__.'/../public/api/common.php';
use function TouringBooking\{quote,dateValue,db,reserve,available,verifyEvent,processEvent};
use TouringBooking\Failure;
$checks=0;
function ok(bool $v):void{global $checks;if(!$v)throw new RuntimeException('Assertion failed');$checks++;}
function fails(callable $fn):void{try{$fn();}catch(Failure $e){ok(true);return;}throw new RuntimeException('Expected rejection');}
$today=dateValue('2026-10-20');
$cfg=['inventory_through'=>'2027-10-31','periods'=>[['start'=>'2027-03-01','end'=>'2027-04-01','prices'=>[3=>39500,4=>47500,5=>54500,7=>59500]]],
 'blocked'=>[],'booking_deposit_pence'=>25000,'balance_weeks'=>12,'terms_version'=>'fixture-only'];
$q=quote($cfg,'2027-03-01','2027-03-08',$today);
ok($q['pay_now_pence']===25000&&$q['balance_pence']===34500&&$q['nights']===7);
ok(quote($cfg,'2027-03-01','2027-03-04',$today)['hire_pence']===39500);
ok(quote($cfg,'2027-03-01','2027-03-08',dateValue('2026-12-07'))['pay_now_pence']===59500);
ok(quote($cfg,'2027-03-01','2027-03-08',dateValue('2026-12-06'))['pay_now_pence']===25000);
fails(fn()=>dateValue('2027-02-29'));
fails(fn()=>quote($cfg,'2027-03-01','2027-03-01',$today));
fails(fn()=>quote($cfg,'2027-03-01','2027-03-07',$today));
fails(fn()=>quote($cfg,'2027-03-29','2027-04-05',$today));
$blocked=$cfg;$blocked['blocked']=[['start'=>'2027-03-03','end'=>'2027-03-04']];
fails(fn()=>quote($blocked,'2027-03-01','2027-03-08',$today));
$private=sys_get_temp_dir().'/touring-fixture-'.bin2hex(random_bytes(8));mkdir($private,0700);
$_SERVER['DOCUMENT_ROOT']=__DIR__.'/../public';$cfg['private_dir']=$private;$db=db($cfg);
$customer=['name'=>'Fixture Customer','email'=>'test@example.invalid'];
reserve($db,$cfg,'fixture',$q,$customer);reserve($db,$cfg,'fixture',$q,$customer);
ok((int)$db->query('SELECT COUNT(*) FROM bookings')->fetchColumn()===1);
fails(fn()=>reserve($db,$cfg,'other',$q,$customer));
available($db,'2027-03-08','2027-03-15');ok(true);
$e=['id'=>'evt_fixture','type'=>'checkout.session.completed','livemode'=>false,'data'=>['object'=>['id'=>'cs_test_fixture','client_reference_id'=>'fixture','payment_status'=>'paid','currency'=>'gbp','amount_total'=>25000,'livemode'=>false]]];
$raw=json_encode($e);$stamp=1000;$sig='t=1000,v1='.hash_hmac('sha256','1000.'.$raw,'fixture_secret');
ok(verifyEvent($raw,$sig,'fixture_secret',$stamp)===$e);
fails(fn()=>verifyEvent($raw,$sig,'fixture_secret',1301));
fails(fn()=>verifyEvent($raw.' ',$sig,'fixture_secret',$stamp));
fails(fn()=>verifyEvent($raw,$sig,'wrong',$stamp));
$bad=$e;$bad['data']['object']['amount_total']=1;fails(fn()=>processEvent($db,$bad,false));
fails(fn()=>processEvent($db,$e,true));
processEvent($db,$e,false);processEvent($db,$e,false);
ok($db->query("SELECT state FROM bookings WHERE id='fixture'")->fetchColumn()==='paid');
ok((int)$db->query('SELECT COUNT(*) FROM events')->fetchColumn()===1);
$expired=$e;$expired['id']='evt_expired';$expired['type']='checkout.session.expired';processEvent($db,$expired,false);
ok($db->query("SELECT state FROM bookings WHERE id='fixture'")->fetchColumn()==='paid');
$q2=quote($cfg,'2027-03-08','2027-03-15',$today);reserve($db,$cfg,'second',$q2,$customer);
$expired['id']='evt_expired_second';$expired['data']['object']['client_reference_id']='second';$expired['data']['object']['id']='cs_test_second';processEvent($db,$expired,false);
available($db,'2027-03-08','2027-03-15');ok(true);
$db=null;foreach(glob($private.'/*') as $f)unlink($f);rmdir($private);
echo "Passed $checks booking integrity checks; no external requests.\n";
