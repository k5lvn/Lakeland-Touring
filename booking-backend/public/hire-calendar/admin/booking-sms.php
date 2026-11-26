<?php
declare(strict_types=1);
require_once __DIR__.'/access.php';
require_once dirname(__DIR__).'/booking-sms.php';
$c=\HireCalendar\settings();
$db=\HireCalendar\database($c);
\HireCalendar\operatorAccess($c,$db);
\BookingSms\settingsPage($c['private_dir'],$_SESSION['csrf'],'Lakeland Touring','./');
