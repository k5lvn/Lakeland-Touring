<?php
// Installed outside the public site. The release creates the stable receipt key there.
$legacyPath=getenv('TOURING_BOOKING_CONFIG');
$legacy=$legacyPath && is_file($legacyPath) ? require $legacyPath : [];
return [
    'origin'=>'https://lakelandtouring.uk',
    'private_dir'=>$legacy['private_dir']??__DIR__,
    'receipt_secret'=>trim(file_get_contents(__DIR__.'/receipt.key')),
    'office_email'=>'LakelandTouring@Worx365Group.uk',
    'inventory_verified'=>false,'periods'=>[],'inventory_through'=>'',
    'blocked'=>$legacy['blocked']??[],
    'allow_enquiries'=>true,
    'initial_hold'=>json_decode(file_get_contents(__DIR__.'/opening-hold.json'),true,512,JSON_THROW_ON_ERROR),
];
