<?php
declare(strict_types=1);
namespace BookingSms;

function configured(string $dir): bool {
    return is_file($dir.'/clicksend-booking.json');
}

function credentials(string $dir): array {
    return json_decode(file_get_contents($dir.'/clicksend-booking.json'), true, 16, JSON_THROW_ON_ERROR);
}

function callApi(array $config, string $resource, ?array $payload = null): array {
    $ch = curl_init('https://rest.clicksend.com/v3/'.$resource);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true, CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_CONNECTTIMEOUT => 3, CURLOPT_TIMEOUT => 8, CURLOPT_HTTPAUTH => CURLAUTH_BASIC,
        CURLOPT_USERPWD => $config['username'].':'.$config['key'],
        CURLOPT_HTTPHEADER => ['Content-Type: application/json','Accept: application/json']
    ]);
    if ($payload !== null) curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload, JSON_THROW_ON_ERROR));
    $raw = curl_exec($ch);
    $result = [(int)curl_getinfo($ch,CURLINFO_RESPONSE_CODE), curl_errno($ch),
        is_string($raw) ? json_decode($raw,true) : null];
    curl_close($ch);
    return $result;
}

function save(string $dir, string $user, string $key, string $to): void {
    if ($user === '' || strlen($user)>255 || preg_match('/[:\x00-\x1f\x7f]/',$user)
        || $key === '' || strlen($key)>512 || preg_match('/[\x00-\x20\x7f]/',$key)
        || !preg_match('/^\+[1-9][0-9]{7,14}$/D',$to)) {
        throw new \InvalidArgumentException('Enter the ClickSend username, API key and mobile with country code.');
    }
    $config = ['username'=>$user,'key'=>$key,'to'=>$to];
    [$code,,$reply] = callApi($config,'account');
    if ($code !== 200 || ($reply['response_code'] ?? '') !== 'SUCCESS') {
        throw new \RuntimeException('ClickSend could not verify the login. Check the username and API key.');
    }
    $tmp = tempnam($dir,'booking-sms-');
    if (!$tmp || realpath(dirname($tmp)) !== realpath($dir)) throw new \RuntimeException('Private settings unavailable.');
    try {
        $json = json_encode($config,JSON_THROW_ON_ERROR);
        if (!chmod($tmp,0600) || file_put_contents($tmp,$json) !== strlen($json)
            || !rename($tmp,$dir.'/clicksend-booking.json')) throw new \RuntimeException('Could not save private settings.');
    } finally {if (is_file($tmp)) unlink($tmp);}
}

function send(array $config, string $body, string $reference): string {
    [$code,$error,$reply] = callApi($config,'sms/send',['messages'=>[[
        'to'=>$config['to'],'body'=>$body,'source'=>'php','custom_string'=>$reference
    ]]]);
    $message=$reply['data']['messages'][0] ?? [];
    if ($code>=200 && $code<300 && ($reply['response_code']??'')==='SUCCESS'
        && ($message['status']??'')==='SUCCESS' && !empty($message['message_id'])) return 'accepted';
    // Only retry when the request was definitely not accepted by the provider.
    if (in_array($error,[6,7],true) || $code===429) return 'retry';
    if (($code>=400 && $code<500) || (isset($message['status']) && $message['status']!=='SUCCESS')) return 'failed';
    return 'unknown';
}

function settingsPage(string $dir,string $csrf,string $site,string $back): void {
    header('Cache-Control: private, no-store');
    header('X-Robots-Tag: noindex, nofollow');
    header('Referrer-Policy: no-referrer');
    header("Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'");
    $notice='';
    if ($_SERVER['REQUEST_METHOD']==='POST') {
        if (!is_string($_POST['csrf']??null) || !hash_equals($csrf,$_POST['csrf'])) {http_response_code(403);exit('Refresh the settings page.');}
        try {
            save($dir,trim((string)($_POST['username']??'')),trim((string)($_POST['key']??'')),trim((string)($_POST['to']??'')));
            header('Location: '.basename($_SERVER['SCRIPT_NAME']),true,303);return;
        } catch (\Throwable $e) {
            $notice='Settings could not be saved. Check the ClickSend API username and key, the mobile number and the connection.';
        }
    }
    $h=static fn($s)=>htmlspecialchars($s,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');
    ?><!doctype html><html lang="en-GB"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>SMS booking alerts | <?=$h($site)?></title><style>body{font:1rem/1.55 system-ui;max-width:32rem;margin:3rem auto;padding:0 1.2rem}label,input,button{display:block}label{margin:1rem 0}input,button{box-sizing:border-box;width:100%;padding:.65rem;font:inherit}</style>
    <main><a href="<?=$h($back)?>">Back to diary</a><h1><?=$h($site)?> SMS alerts</h1>
    <p><?=configured($dir)?'ClickSend is connected. New booking requests trigger a text to the saved mobile.':'Connect ClickSend to receive a text when a new booking request is saved.'?></p>
    <?php if($notice):?><p role="alert"><?=$h($notice)?></p><?php endif;?>
    <form method="post" autocomplete="off"><input type="hidden" name="csrf" value="<?=$h($csrf)?>">
    <label>ClickSend API username<input name="username" required maxlength="255"></label>
    <label>ClickSend API key<input type="password" name="key" autocomplete="new-password" required maxlength="512"></label>
    <label>Alert mobile number including country code<input type="tel" name="to" placeholder="+44…" required></label>
    <button type="submit">Verify and save</button></form></main></html><?php
}
