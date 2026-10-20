<?php
// Install privately OUTSIDE the document root. Never commit a populated copy.
return [
    'enabled' => false,
    'policy_verified' => false,
    'inventory_verified' => false,
    'merchant_verified' => false,
    'origin' => 'https://lakelandtouring.uk',
    'private_dir' => '/REPLACE_WITH_PRIVATE_DIRECTORY',
    'stripe_secret' => getenv('TOURING_STRIPE_SECRET') ?: '',
    'stripe_webhook_secret' => getenv('TOURING_STRIPE_WEBHOOK_SECRET') ?: '',
    'stripe_account' => '', // Expected acct_...; checked before creating sessions.
    'live_mode' => false,
    'terms_version' => '',
    'inventory_through' => '', // Verified last return date, never inferred from an empty DB.
    'booking_deposit_pence' => 25000,
    'balance_weeks' => 12,
    // Explicit, owner-approved collection/return windows. No inferred holiday dates,
    // winter availability, mixed-season calculation or extra-night pro-rating.
    // Example only: ['start'=>'2027-03-01','end'=>'2027-04-01',
    //               'prices'=>[3=>39500,4=>47500,5=>54500,7=>59500]]
    'periods' => [],
    // Import ALL existing bookings, maintenance and owner-use blocks before enabling.
    'blocked' => [], // Each ['start'=>'YYYY-MM-DD','end'=>'YYYY-MM-DD'] is end-exclusive.
];
