<?php
// Private configuration outside the document root. Use the existing booking database directory.
return [
    'origin'=>'https://lakelandtouring.uk',
    'private_dir'=>'',
    'receipt_secret'=>'', // A private random secret of at least 32 bytes, stable across releases.
    'operator_user'=>'', // Exact hosting-authenticated username allowed to review requests.
    'office_email'=>'',
    'inventory_verified'=>false,
    'inventory_through'=>'',
    'periods'=>[], // Ordered, non-overlapping {start,end,season,prices}; dates ISO, end exclusive, total prices in integer pence keyed by nights.
    'blocked'=>[], // Existing bookings, owner use, maintenance and any required turnaround nights.
];
