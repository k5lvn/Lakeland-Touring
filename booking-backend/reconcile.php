<?php
// Private CLI entry point. Run every minute before activating booking.
declare(strict_types=1);
if (PHP_SAPI!=='cli') {http_response_code(404);exit;}
require __DIR__.'/public/api/common.php';
$_SERVER['DOCUMENT_ROOT']=getenv('TOURING_BOOKING_DOCUMENT_ROOT')?:'';
$cfg=\TouringBooking\config();
\TouringBooking\reconcileHolds(\TouringBooking\db($cfg),$cfg);
