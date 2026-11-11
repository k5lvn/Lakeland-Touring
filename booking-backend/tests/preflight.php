<?php
declare(strict_types=1);
require __DIR__.'/../preflight.php';
use function TouringPreflight\inspect;
$checks=0;
function check(bool $value):void{global $checks;if(!$value)throw new RuntimeException('Preflight assertion failed');$checks++;}
function status(array $report,string $id):string{return array_column($report['checks'],'status','id')[$id];}
$folder=sys_get_temp_dir().'/touring-preflight-'.bin2hex(random_bytes(8));
mkdir($folder,0700);mkdir($folder.'/public',0700);mkdir($folder.'/private',0700);mkdir($folder.'/public/api',0700);
$config=$folder.'/private/config.php';file_put_contents($config,'<?php return [];');
$cfg=['enabled'=>true,'policy_verified'=>true,'inventory_verified'=>true,'merchant_verified'=>true,
 'origin'=>'https://lakelandtouring.uk','private_dir'=>$folder.'/private','live_mode'=>false,
 'stripe_secret'=>'sk_test_fixtureOnly','stripe_webhook_secret'=>'whsec_fixtureOnly','stripe_account'=>'acct_fixtureOnly',
 'terms_version'=>'fixture-only','inventory_through'=>'2027-12-31','booking_deposit_pence'=>25000,'balance_weeks'=>12,
 'periods'=>[['start'=>'2027-03-01','end'=>'2027-04-01','prices'=>[7=>59500]],['start'=>'2027-04-01','end'=>'2027-05-01','prices'=>[7=>65000]]],'blocked'=>[]];
try{
 $run=fn($c)=>inspect($c,$config,$folder.'/public');
 $r=$run($cfg);check($r['configuration_checks_passed']);check($r['public_launch_verified']===false);
 check(!str_contains(json_encode($r),$cfg['stripe_secret']));check(!str_contains(json_encode($r),$cfg['stripe_webhook_secret']));
 check(glob($folder.'/private/*')===[$config]); // No database/storage mutation.
 $bad=$cfg;$bad['periods'][1]['start']='2027-03-31';check(status($run($bad),'season_calendar')==='blocked');
 $bad=$cfg;$bad['periods'][0]['start']='2027-02-29';check(status($run($bad),'season_calendar')==='blocked');
 $bad=$cfg;$bad['periods'][0]['end']='2028-01-01';check(status($run($bad),'season_calendar')==='blocked');
 $bad=$cfg;$bad['periods'][0]['prices'][7]=595.0;check(status($run($bad),'duration_prices')==='blocked');
 $bad=$cfg;$bad['periods'][0]['prices']=['seven'=>59500];check(status($run($bad),'duration_prices')==='blocked');
 $bad=$cfg;$bad['periods'][0]['prices']=[0=>59500];check(status($run($bad),'duration_prices')==='blocked');
 $bad=$cfg;$bad['blocked']=[['start'=>'2027-03-02','end'=>'2027-03-01']];check(status($run($bad),'inventory_blocks')==='blocked');
 $bad=$cfg;$bad['blocked']='unknown';check(status($run($bad),'inventory_blocks')==='blocked');
 $bad=$cfg;$bad['inventory_through']='';check(status($run($bad),'inventory_horizon')==='blocked');
 $bad=$cfg;$bad['stripe_secret']='sk_live_fixtureOnly';check(status($run($bad),'stripe_key_mode')==='blocked');
 $bad=$cfg;unset($bad['live_mode']);check(status($run($bad),'stripe_key_mode')==='blocked');
 $bad=$cfg;$bad['policy_verified']=false;check(status($run($bad),'policy_verified')==='blocked');
 $bad=$cfg;$bad['enabled']=false;check(status($run($bad),'enabled')==='blocked');
 $bad=$cfg;$bad['private_dir']=$folder.'/public';check(status($run($bad),'private_storage')==='blocked');
 $bad=$cfg;$bad['private_dir']=$folder.'/public/api';check(status($run($bad),'private_storage')==='blocked');
 file_put_contents($folder.'/public/config.php','<?php return [];');
 check(status(inspect($cfg,$folder.'/public/config.php',$folder.'/public'),'private_config')==='blocked');
 file_put_contents($folder.'/public/api/booking-disabled.php','<?php // fixture lock');
 $r=$run($cfg);check(!$r['configuration_checks_passed']);check($r['release_lock_present']);check(is_file($folder.'/public/api/booking-disabled.php'));
 // CLI output must not leak echoed config secrets; malformed configs fail closed.
 $command=escapeshellarg(PHP_BINARY).' '.escapeshellarg(__DIR__.'/../preflight.php').' --config '.escapeshellarg($config).' --document-root '.escapeshellarg($folder.'/public');
 file_put_contents($config,'<?php echo "SECRET_FIXTURE"; return [];');
 exec($command.' 2>&1',$output,$code);check($code===2);check(!str_contains(implode("\n",$output),'SECRET_FIXTURE'));
 file_put_contents($config,'<?php trigger_error("SECRET_WARNING_FIXTURE");return [];');
 $output=[];exec($command.' 2>&1',$output,$code);check($code===2);check(!str_contains(implode("\n",$output),'SECRET_WARNING_FIXTURE'));
 // A public config must be rejected before evaluation.
 file_put_contents($folder.'/public/config.php','<?php file_put_contents('.var_export($folder.'/executed',true).',"bad");return [];');
 $output=[];exec(escapeshellarg(PHP_BINARY).' '.escapeshellarg(__DIR__.'/../preflight.php').' --config '.escapeshellarg($folder.'/public/config.php').' --document-root '.escapeshellarg($folder.'/public').' 2>&1',$output,$code);
 check($code===2);check(!file_exists($folder.'/executed'));
}finally{
 foreach([$config,$folder.'/public/config.php',$folder.'/public/api/booking-disabled.php',$folder.'/executed'] as $p)if(is_file($p))unlink($p);
 rmdir($folder.'/public/api');rmdir($folder.'/public');rmdir($folder.'/private');rmdir($folder);
}
echo "Passed $checks offline launch-preflight checks; no network or production configuration used.\n";
