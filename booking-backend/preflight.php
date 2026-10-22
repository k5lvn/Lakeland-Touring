<?php
declare(strict_types=1);
namespace TouringPreflight;

// Private CLI only. No database connections, network calls, writes or lock removal.
function inside(string $path, string $root): bool {
    return $path === $root || str_starts_with($path, $root.DIRECTORY_SEPARATOR);
}
function validDate(mixed $value): bool {
    if (!is_string($value)) return false;
    $date=\DateTimeImmutable::createFromFormat('!Y-m-d',$value,new \DateTimeZone('Europe/London'));
    return $date && $date->format('Y-m-d')===$value;
}
function inspect(array $cfg, string $configPath, string $documentRoot): array {
    $checks=[];
    $add=function(string $id,bool $pass,string $message) use (&$checks):void {
        $checks[]=['id'=>$id,'status'=>$pass?'pass':'blocked','message'=>$message];
    };
    $root=realpath($documentRoot);$config=realpath($configPath);
    $add('private_config',$root!==false && is_dir($root) && $config!==false && is_file($config) && !inside($config,$root),
        'Configuration must be a private file outside the document root.');
    $private=is_string($cfg['private_dir']??null)?realpath($cfg['private_dir']):false;
    $add('private_storage',$root!==false && $private!==false && is_dir($private) && !inside($private,$root) && is_writable($private),
        'Booking storage must be a writable private directory outside the document root. No database is opened by this check.');
    $add('origin',($cfg['origin']??null)==='https://lakelandtouring.uk','The configured origin must match the production booking host.');
    $mode=$cfg['live_mode']??null;$secret=$cfg['stripe_secret']??null;
    $add('stripe_key_mode',is_bool($mode) && is_string($secret) &&
        preg_match($mode?'/^sk_live_[A-Za-z0-9]+$/D':'/^sk_test_[A-Za-z0-9]+$/D',$secret)===1,
        'A correctly shaped Stripe key must match the explicit payment mode. Key validity is not verified offline.');
    $add('stripe_account',is_string($cfg['stripe_account']??null) && preg_match('/^acct_[A-Za-z0-9]+$/D',$cfg['stripe_account'])===1,
        'An expected merchant account must be set. Merchant identity and enabled charges still need a provider check.');
    $add('webhook_secret',is_string($cfg['stripe_webhook_secret']??null) && preg_match('/^whsec_[A-Za-z0-9]+$/D',$cfg['stripe_webhook_secret'])===1,
        'A webhook signing secret must be present. Actual delivery and signature handling still need a test-mode roundtrip.');
    $add('terms_version',is_string($cfg['terms_version']??null) && trim($cfg['terms_version'])!=='',
        'A versioned hire agreement must be identified; its legal adequacy is not checked here.');
    $add('deposit',is_int($cfg['booking_deposit_pence']??null) && $cfg['booking_deposit_pence']>0,
        'The booking deposit must be a positive whole number of pence. This is separate from the damage deposit.');
    $add('balance_deadline',is_int($cfg['balance_weeks']??null) && $cfg['balance_weeks']>=0 && $cfg['balance_weeks']<=52,
        'The balance deadline must be an explicit number of weeks from 0 to 52.');
    $horizon=$cfg['inventory_through']??null;
    $add('inventory_horizon',validDate($horizon),'The last verified return date must be explicitly configured.');
    $periods=$cfg['periods']??null;$calendar=is_array($periods)&&count($periods)>0;$prices=$calendar;$ranges=[];
    if(is_array($periods))foreach($periods as $p){
        if(!is_array($p)||!validDate($p['start']??null)||!validDate($p['end']??null)||$p['start']>=$p['end']){
            $calendar=false;$prices=false;continue;
        }
        if(validDate($horizon)&&$p['end']>$horizon)$calendar=false;
        $ranges[]=[$p['start'],$p['end']];
        if(!is_array($p['prices']??null)||!$p['prices']){$prices=false;continue;}
        foreach($p['prices'] as $nights=>$pence){
            if(!is_int($nights)||$nights<1||$nights>365||!is_int($pence)||$pence<=0)$prices=false;
        }
    }
    usort($ranges,fn($a,$b)=>strcmp($a[0],$b[0]));
    for($i=1;$i<count($ranges);$i++)if($ranges[$i][0]<$ranges[$i-1][1])$calendar=false;
    $add('season_calendar',$calendar,'Configure valid, non-overlapping seasonal windows within the verified horizon. Uncovered dates and cross-season stays require a manual quote.');
    $add('duration_prices',$prices,'Each supported duration needs an explicit positive whole-pence price; no short-break or extra-night price is inferred.');
    $blocks=$cfg['blocked']??null;$validBlocks=is_array($blocks);
    if(is_array($blocks))foreach($blocks as $b){
        if(!is_array($b)||!validDate($b['start']??null)||!validDate($b['end']??null)||$b['start']>=$b['end'])$validBlocks=false;
    }
    $add('inventory_blocks',$validBlocks,'Blocks must be explicit valid date ranges. An empty list does not prove availability or that existing bookings were imported.');
    foreach(['policy_verified','inventory_verified','merchant_verified'] as $flag){
        $add($flag,($cfg[$flag]??false)===true,'Operator verification flag: '.$flag.'. A true flag records an assertion, not independently verified evidence.');
    }
    $add('enabled',($cfg['enabled']??false)===true,'The private enable flag is off until operator review. This tool never changes it.');
    $locked=$root!==false&&is_file($root.'/api/booking-disabled.php');
    $add('release_lock',!$locked,'An installed release lock keeps checkout unavailable even when private flags are true. This tool never removes it.');
    return ['scope'=>'offline_configuration_only','configuration_checks_passed'=>!array_filter($checks,fn($c)=>$c['status']==='blocked'),
        'public_launch_verified'=>false,'release_lock_present'=>$locked,'checks'=>$checks,
        'still_requires'=>['Operator-approved hire prices, season dates, durations and existing booking/maintenance/owner-use reconciliation.',
            'Actual vehicle/towing/insurance facts and reviewed hire, cancellation, refund and damage-deposit terms.',
            'Stripe test-mode checkout and signed webhook replay, expected merchant and hosting validation.',
            'Private scheduler operation, overdue reconciliation monitoring, backups, retention and secure administration.',
            'Reviewed deployment, frontend integration and explicit activation approval.']];
}
function main(array $args): int {
    if(PHP_SAPI!=='cli')return 2;
    $options=getopt('',['config:','document-root:']);
    $path=$options['config']??'';$root=$options['document-root']??'';
    $config=is_string($path)?realpath($path):false;$document=is_string($root)?realpath($root):false;
    // Reject public config before executing any PHP from it; do not print paths/secrets/errors.
    if(!$config||!is_file($config)||!is_readable($config)||!$document||!is_dir($document)||inside($config,$document)){
        fwrite(STDERR,"Provide --config pointing to a readable private PHP config and --document-root pointing to the public directory.\n");return 2;
    }
    ob_start();
    set_error_handler(function(int $severity,string $message):never {throw new \ErrorException('Private config warning',0,$severity);});
    try{$cfg=require $config;}catch(\Throwable $e){ob_end_clean();fwrite(STDERR,"Private configuration could not be loaded.\n");return 2;}
    finally{restore_error_handler();}
    $unexpected=ob_get_clean();
    if(!is_array($cfg)||$unexpected!==''){fwrite(STDERR,"Private configuration must return an array without output.\n");return 2;}
    $result=inspect($cfg,$config,$document);
    foreach(['pdo_sqlite','curl'] as $extension)$result['checks'][]=['id'=>'extension_'.$extension,
        'status'=>extension_loaded($extension)?'pass':'blocked','message'=>'Required PHP extension: '.$extension.'.'];
    $result['checks'][]=['id'=>'php_version','status'=>PHP_VERSION_ID>=80200?'pass':'blocked','message'=>'PHP 8.2 or newer is required.'];
    $result['configuration_checks_passed']=!array_filter($result['checks'],fn($c)=>$c['status']==='blocked');
    echo json_encode($result,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n";
    return $result['configuration_checks_passed']?0:2;
}
if(PHP_SAPI!=='cli') {http_response_code(404);exit;}
if(realpath($_SERVER['SCRIPT_FILENAME']??'')===__FILE__)exit(main($argv));
