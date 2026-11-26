<?php
declare(strict_types=1);
require __DIR__.'/calendar.php';
\TouringBooking\run(function(){
    $c=\HireCalendar\settings();$input=\TouringBooking\body($c);
    $id=$_SESSION['calendar_id']??null;
    if(!$id)throw new \TouringBooking\Failure('Refresh the calendar before submitting.',409);
    $attempt=$input['attempt']??null;
    if(!is_string($attempt) || !preg_match('/^[a-f0-9-]{36}$/D',$attempt))throw new \TouringBooking\Failure('Please reselect your dates.');
    $id=substr(hash_hmac('sha256',$attempt,$id),0,40);
    return \HireCalendar\requestStay(\HireCalendar\database($c),$c,$id,$input);
});
