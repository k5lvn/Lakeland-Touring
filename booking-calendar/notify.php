<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli') exit(1);
require dirname(__DIR__).'/booking-backend/public/hire-calendar/mail.php';
$_SERVER['DOCUMENT_ROOT']=getenv('TOURING_DOCUMENT_ROOT')?:'';
$c=\HireCalendar\settings();
\HireCalendar\deliverMail(\HireCalendar\database($c),$c);
