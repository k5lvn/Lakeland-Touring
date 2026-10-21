<?php
declare(strict_types=1);
ini_set('display_errors','0');
const GARAGE_URL='https://lakelandtouring.uk/garage.php';
const GARAGE_EMAIL='LakelandTouring@Worx365Group.uk';
function h($s):string{return htmlspecialchars((string)$s,ENT_QUOTES,'UTF-8');}
function secure():bool{return !empty($_SERVER['HTTPS'])&&$_SERVER['HTTPS']!=='off';}
function page(string $title,string $content):never{
 header('Content-Type: text/html; charset=UTF-8');header('X-Content-Type-Options: nosniff');header('Referrer-Policy: strict-origin-when-cross-origin');header('X-Frame-Options: DENY');header('Cache-Control: no-store');
 $public=in_array($_GET['view']??'',['browse','vehicle'],true);
 echo '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'.h($title).' | Lakeland Touring</title><meta name="description" content="Explore independently owned caravans, campervans and motorhomes advertised through Lakeland Touring Owner’s Garage. Contact owners directly."><link rel="canonical" href="'.GARAGE_URL.($public?'?view='.h($_GET['view']).(isset($_GET['id'])?'&amp;id='.(int)$_GET['id']:''):'').'"><link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="brand.css?v=20261015-centre3"><link rel="stylesheet" href="garage.css?v=1"></head><body>';
 readfile(__DIR__.'/garage-header.html');echo '<main class="garage-main">'.$content.'</main>';readfile(__DIR__.'/garage-footer.html');echo '</body></html>';exit;
}
function notice():string{return '<aside class="garage-notice"><h2>Independent owner advertisements</h2><p>Owner’s Garage provides advertising space only. Enquiries, hire agreements, bookings and payments are arranged directly with the vehicle owner. Owners are responsible for vehicle condition, safety, insurance, listing accuracy, cancellations, refunds and booking disputes. Lakeland Touring does not inspect or guarantee these vehicles and is not a party to their hire agreements.</p><p>This does not affect your statutory rights or our responsibility for our own advertising service. We do not exclude liability that cannot lawfully be excluded. This notice applies to independent owner listings; our own Elddis hire service has its separate booking terms.</p></aside>';}
function q(string $sql,array $args=[]):PDOStatement{global $db;$s=$db->prepare($sql);$s->execute($args);return $s;}
function go(string $to=''):never{header('Location: '.GARAGE_URL.$to, true,303);exit;}
function token():string{return '<input type="hidden" name="csrf" value="'.h($_SESSION['csrf']).'">';}
function field(string $name,string $label,string $type='text',string $value='',bool $required=true):string{return '<label for="'.h($name).'">'.h($label).'</label><input id="'.h($name).'" name="'.h($name).'" type="'.h($type).'" value="'.h($value).'" '.($required?'required':'').' maxlength="'.($type==='password'?'200':'200').'">';}
function mailtoken(string $email,string $kind):void{
 $raw=bin2hex(random_bytes(32));q('UPDATE owners SET token=?,token_kind=?,token_until=? WHERE email=?',[hash('sha256',$raw),$kind,time()+3600,$email]);
 $url=GARAGE_URL.'?view='.$kind.'&token='.$raw;
 if(!mail($email,'Your Lakeland Touring Garage link',"Open this link within one hour:\n".$url."\nIf you did not request it, ignore this email.",'From: '.GARAGE_EMAIL))throw new RuntimeException('We could not send your email. Please contact our team.');
}
// HTTP never accepts credentials, cookies, uploads or account actions.
if(!secure()){
 if($_SERVER['REQUEST_METHOD']==='POST'){http_response_code(403);page('Secure access required','<h1>Secure access required</h1><p>Please use our secure website before entering account details.</p><a class="button" href="'.GARAGE_URL.'">Open secure Owner’s Garage →</a>');}
 page('Owner’s Garage','<span class="eyebrow">FOR VEHICLE OWNERS</span><h1>Your vehicle.<br>Your own garage.</h1><p>Advertise your caravan, motorhome or campervan for £49 per vehicle for 12 months. No booking commission. Manage photos and details, and receive enquiries directly.</p><div class="garage-notice"><p>Owner registration is temporarily unavailable while we restore secure access. Please contact us to register your interest; no payment is taken here.</p><a class="button" href="mailto:'.GARAGE_EMAIL.'?subject=Owner%27s%20Garage%20enquiry">Enquire about advertising →</a></div>'.notice());
}
$storage=dirname(__DIR__).'/.touring-garage';
if(!is_dir($storage))mkdir($storage,0700,true);
try{
 $db=new PDO('sqlite:'.$storage.'/garage.sqlite',null,null,[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC]);
 $db->exec('PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000; CREATE TABLE IF NOT EXISTS owners(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,name TEXT NOT NULL,verified INTEGER DEFAULT 0,token TEXT,token_kind TEXT,token_until INTEGER); CREATE TABLE IF NOT EXISTS vehicles(id INTEGER PRIMARY KEY,owner_id INTEGER NOT NULL REFERENCES owners(id),title TEXT NOT NULL,type TEXT NOT NULL,location TEXT NOT NULL,description TEXT NOT NULL,price TEXT NOT NULL,contact TEXT NOT NULL,status TEXT DEFAULT "draft",paid_until INTEGER DEFAULT 0,created INTEGER NOT NULL); CREATE TABLE IF NOT EXISTS photos(id INTEGER PRIMARY KEY,vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,file TEXT NOT NULL); CREATE TABLE IF NOT EXISTS attempts(key TEXT PRIMARY KEY,count INTEGER NOT NULL,until INTEGER NOT NULL);');chmod($storage.'/garage.sqlite',0600);
}catch(Throwable $e){error_log('Touring garage storage unavailable');http_response_code(503);page('Owner’s Garage','<h1>Owner’s Garage</h1><p>Account access is temporarily unavailable. Please contact our team.</p><a class="button" href="mailto:'.GARAGE_EMAIL.'">Contact us →</a>'.notice());}
// New booking service is opt-in through a private config, never a request parameter.
$bookingConfig=['enabled'=>false,'non_working_dates'=>null];
if(is_file($storage.'/booking-config.php')){
 $candidate=require $storage.'/booking-config.php';
 if(is_array($candidate))$bookingConfig=array_replace($bookingConfig,$candidate);
}
$bookingEnabled=($bookingConfig['enabled']??false)===true && is_array($bookingConfig['non_working_dates']);
if($bookingEnabled){
 foreach($bookingConfig['non_working_dates'] as $closed)if(!is_string($closed)||!preg_match('/^\d{4}-\d{2}-\d{2}$/D',$closed))$bookingEnabled=false;
}
if($bookingEnabled){require_once __DIR__.'/garage-bookings.php';require_once __DIR__.'/garage-bookings-ui.php';\TouringGarage\schema($db);}
ini_set('session.use_strict_mode','1');ini_set('session.use_only_cookies','1');session_name('touringgarage');session_set_cookie_params(['lifetime'=>0,'path'=>'/','secure'=>true,'httponly'=>true,'samesite'=>'Lax']);session_start();$_SESSION['csrf']??=bin2hex(random_bytes(32));
$owner=isset($_SESSION['owner'])?q('SELECT * FROM owners WHERE id=?',[$_SESSION['owner']])->fetch():false;
if($owner&&((time()-(int)($_SESSION['last']??0)>3600)||!hash_equals($owner['password'],(string)($_SESSION['password_stamp']??'')))){$_SESSION=[];go();}
if($owner)$_SESSION['last']=time();
$isAdmin=$owner&&strtolower($owner['email'])===strtolower(GARAGE_EMAIL);
$view=(string)($_GET['view']??($owner?'dashboard':'welcome'));$error='';$message='';
try{
 if($_SERVER['REQUEST_METHOD']==='POST'){
  if(!hash_equals($_SESSION['csrf'],(string)($_POST['csrf']??'')))throw new RuntimeException('Your session expired. Refresh the page and try again.');
  $action=(string)($_POST['action']??'');
  if(in_array($action,['login','register','forgot','resend'],true)){
   $key=hash('sha256',($_SERVER['REMOTE_ADDR']??'').'|'.$action);$attempt=q('SELECT * FROM attempts WHERE key=?',[$key])->fetch();
   if($attempt&&$attempt['until']>time()&&$attempt['count']>=8)throw new RuntimeException('Too many attempts. Please try again in 15 minutes.');
   q('INSERT INTO attempts VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN until<? THEN 1 ELSE count+1 END,until=CASE WHEN until<? THEN excluded.until ELSE until END',[$key,time()+900,time(),time()]);
   $email=strtolower(trim((string)($_POST['email']??'')));
   if(!filter_var($email,FILTER_VALIDATE_EMAIL)||strlen($email)>200)throw new RuntimeException('Enter a valid email address.');
   $account=q('SELECT * FROM owners WHERE email=?',[$email])->fetch();
   if($action==='register'){
    $pw=(string)($_POST['password']??'');$name=trim((string)($_POST['name']??''));
    if(strlen($pw)<12||strlen($pw)>200||!$name||strlen($name)>100||empty($_POST['terms']))throw new RuntimeException('Enter your name, a password of at least 12 characters, and accept the owner terms.');
    if(!$account){q('INSERT INTO owners(email,password,name) VALUES(?,?,?)',[$email,password_hash($pw,PASSWORD_DEFAULT),$name]);mailtoken($email,'verify');}
    $message='If this address can be registered, a verification link has been sent. Already registered? Sign in or reset your password.';
   }elseif($action==='login'){
    $valid=password_verify((string)($_POST['password']??''),$account['password']??'$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uheWG/igi.');
    if(!$account||!$valid)throw new RuntimeException('Email or password not recognised.');
    if(!$account['verified'])throw new RuntimeException('Please verify your email first. You can request another link below.');
    session_regenerate_id(true);$_SESSION['owner']=$account['id'];$_SESSION['password_stamp']=$account['password'];$_SESSION['last']=time();go();
   }else{if($account&&($action==='forgot'||!$account['verified']))mailtoken($email,$action==='forgot'?'reset':'verify');$message='If the address is eligible, we have sent an email link.';}
  }elseif($action==='reset'){
   $pw=(string)($_POST['password']??'');if(strlen($pw)<12||strlen($pw)>200)throw new RuntimeException('Use a password of at least 12 characters.');
   $a=q('SELECT id FROM owners WHERE token=? AND token_kind="reset" AND token_until>?',[hash('sha256',(string)($_POST['token']??'')),time()])->fetch();
   if(!$a)throw new RuntimeException('This link has expired. Request a new one.');
   q('UPDATE owners SET password=?,token=NULL,token_until=NULL WHERE id=?',[password_hash($pw,PASSWORD_DEFAULT),$a['id']]);unset($_SESSION['owner']);$owner=false;$view='welcome';$message='Password updated. You can now sign in.';
  }else{
   if(!$owner)throw new RuntimeException('Please sign in first.');
   if($action==='logout'){$_SESSION=[];session_regenerate_id(true);go();}
   if($action==='approve'||$action==='reject'){
    if(!$isAdmin)throw new RuntimeException('Administrator access required.');
    $listing=(int)($_POST['listing']??0);$record=q('SELECT * FROM vehicles WHERE id=?',[$listing])->fetch();if(!$record)throw new RuntimeException('Listing not found.');
    if($action==='approve'){
     if(empty($_POST['checked']))throw new RuntimeException('Confirm the listing review and annual payment first.');
     $until=strtotime((string)($_POST['paid_until']??''));if(!$until||$until<time()||$until>strtotime('+2 years'))throw new RuntimeException('Enter a valid paid expiry date within two years.');
     if(!q('SELECT COUNT(*) FROM photos WHERE vehicle_id=?',[$listing])->fetchColumn())throw new RuntimeException('Listing requires a photo.');
     if($bookingEnabled&&\TouringGarage\query($db,'SELECT 1 FROM garage_restrictions WHERE owner_id=?',[$record['owner_id']])->fetchColumn())throw new RuntimeException('Advertising rights have ended.');
     q('UPDATE vehicles SET status="live",paid_until=? WHERE id=?',[$until,$listing]);
    }else q('UPDATE vehicles SET status="draft" WHERE id=?',[$listing]);
    go('?view=admin');
   }
   if(in_array($action,['accept-plan','create-booking','confirm-deposit','confirm-balance','confirm-booking','record-fee','cancel-booking','appointment','verify-evidence','authorise-handover','terminate-advertising'],true)){
    if(!$bookingEnabled)throw new RuntimeException('The new owner booking service is not active.');
    \TouringGarage\act($db,(int)$owner['id'],$action,$_POST,$bookingConfig);
    go('?view=bookings');
   }
   $id=(int)($_POST['id']??0);$v=$id?q('SELECT * FROM vehicles WHERE id=? AND owner_id=?',[$id,$owner['id']])->fetch():false;
   if($id&&!$v)throw new RuntimeException('Vehicle not found in your garage.');
   if($action==='save'){
    $values=[];foreach(['title','type','location','description','price','contact'] as $f){$values[$f]=trim((string)($_POST[$f]??''));if(!$values[$f]||strlen($values[$f])>($f==='description'?5000:200))throw new RuntimeException('Complete every field within the stated limits.');}
    if(!in_array($values['type'],['Touring caravan','Motorhome','Campervan','Static caravan'],true)||!filter_var($values['contact'],FILTER_VALIDATE_EMAIL)||empty($_POST['responsibility']))throw new RuntimeException('Check your vehicle type, contact email and owner responsibility confirmation.');
    if($v)q('UPDATE vehicles SET title=?,type=?,location=?,description=?,price=?,contact=?,status="draft" WHERE id=? AND owner_id=?',[...array_values($values),$id,$owner['id']]);
    else{if(q('SELECT COUNT(*) FROM vehicles WHERE owner_id=?',[$owner['id']])->fetchColumn()>=20)throw new RuntimeException('Please contact us to add more than 20 vehicles.');q('INSERT INTO vehicles(owner_id,title,type,location,description,price,contact,created) VALUES(?,?,?,?,?,?,?,?)',[$owner['id'],...array_values($values),time()]);$id=(int)$db->lastInsertId();}
    $message='Vehicle saved as a draft. Add photos, then request review.';$view='edit';$_GET['id']=$id;
   }elseif($action==='upload'){
    if(!$v)throw new RuntimeException('Save your vehicle first.');
    if(q('SELECT COUNT(*) FROM photos WHERE vehicle_id=?',[$id])->fetchColumn()>=12)throw new RuntimeException('You can add up to 12 photos.');
    $f=$_FILES['photo']??null;if(!$f||$f['error']!==UPLOAD_ERR_OK||$f['size']>8*1024*1024||!is_uploaded_file($f['tmp_name']))throw new RuntimeException('Choose a JPEG or PNG photo under 8 MB.');
    $info=getimagesize($f['tmp_name']);if(!$info||!in_array($info[2],[IMAGETYPE_JPEG,IMAGETYPE_PNG],true)||$info[0]*$info[1]>24000000)throw new RuntimeException('Choose a JPEG or PNG image under 24 megapixels.');
    $img=$info[2]===IMAGETYPE_JPEG?imagecreatefromjpeg($f['tmp_name']):imagecreatefrompng($f['tmp_name']);if(!$img)throw new RuntimeException('Could not read that image.');
    $ratio=min(1,1800/max($info[0],$info[1]));$dest=imagecreatetruecolor((int)($info[0]*$ratio),(int)($info[1]*$ratio));imagecopyresampled($dest,$img,0,0,0,0,imagesx($dest),imagesy($dest),$info[0],$info[1]);
    $file=bin2hex(random_bytes(20)).'.jpg';imagejpeg($dest,$storage.'/'.$file,88);chmod($storage.'/'.$file,0600);imagedestroy($img);imagedestroy($dest);q('INSERT INTO photos(vehicle_id,file) VALUES(?,?)',[$id,$file]);q('UPDATE vehicles SET status="draft" WHERE id=?',[$id]);go('?view=edit&id='.$id);
   }elseif($action==='remove-photo'){
    $photo=q('SELECT p.* FROM photos p JOIN vehicles v ON v.id=p.vehicle_id WHERE p.id=? AND v.owner_id=?',[(int)($_POST['photo_id']??0),$owner['id']])->fetch();if(!$photo)throw new RuntimeException('Photo not found.');q('DELETE FROM photos WHERE id=?',[$photo['id']]);@unlink($storage.'/'.$photo['file']);q('UPDATE vehicles SET status="draft" WHERE id=?',[$photo['vehicle_id']]);go('?view=edit&id='.$photo['vehicle_id']);
   }elseif($action==='review'){
    if(!$v||!q('SELECT COUNT(*) FROM photos WHERE vehicle_id=?',[$id])->fetchColumn())throw new RuntimeException('Add at least one photo before requesting review.');
    if(!mail(GARAGE_EMAIL,'Garage listing review #'.$id,"Owner: ".$owner['email']."\nVehicle: ".$v['title']."\nAnnual advertising: £49 per vehicle for 12 months. Review and arrange invoicing before activation.",'From: '.GARAGE_EMAIL))throw new RuntimeException('We could not send the request. Please contact us.');
    q('UPDATE vehicles SET status="pending" WHERE id=?',[$id]);go('?sent=1');
   }elseif($action==='unpublish'){q('UPDATE vehicles SET status="draft" WHERE id=? AND owner_id=?',[$id,$owner['id']]);go();}
  }
 }
 if($view==='verify'){
  $a=q('SELECT id FROM owners WHERE token=? AND token_kind="verify" AND token_until>?',[hash('sha256',(string)($_GET['token']??'')),time()])->fetch();if(!$a)throw new RuntimeException('This verification link has expired. Request another link.');q('UPDATE owners SET verified=1,token=NULL,token_until=NULL WHERE id=?',[$a['id']]);$view='welcome';$message='Email verified. You can now sign in.';
 }
}catch(RuntimeException $e){$error=$e->getMessage();}
$flash=($error?'<p role="alert" class="garage-error">'.h($error).'</p>':'').($message?'<p role="status" class="garage-success">'.h($message).'</p>':'');
$nav='<div class="garage-tabs"><a href="owners-garage.html">How it works</a><a href="?view=browse">Browse vehicles</a><a href="garage.php">'.($owner?'My garage':'Owner sign in').'</a></div>';
if($owner&&isset($_SESSION['last'])&&time()-$_SESSION['last']>3600){$_SESSION=[];go();}if($owner)$_SESSION['last']=time();
if($bookingEnabled&&$owner)$nav.='<p><a class="button" href="?view=bookings">Bookings and payment confirmations</a></p>';
if($view==='bookings'){
 if(!$owner){http_response_code(403);page('Sign in required','<h1>Sign in to view your bookings</h1>');}
 if(!$bookingEnabled){http_response_code(503);page('Bookings unavailable','<h1>Owner bookings are not active yet</h1>');}
 page('Bookings',$nav.\TouringGarage\render($db,$owner,(bool)$isAdmin,$flash,$bookingConfig));
}
if($view==='photo'){
 $p=q('SELECT p.file,v.owner_id,v.status,v.paid_until FROM photos p JOIN vehicles v ON v.id=p.vehicle_id WHERE p.id=?',[(int)($_GET['id']??0)])->fetch();
 if(!$p||!(($p['status']==='live'&&$p['paid_until']>time())||($owner&&(int)$owner['id']===(int)$p['owner_id'])||$isAdmin)){http_response_code(404);exit;}
 header('Content-Type: image/jpeg');header('X-Content-Type-Options: nosniff');header('Cache-Control: private, max-age=300');readfile($storage.'/'.$p['file']);exit;
}
if($view==='admin'){
 if(!$isAdmin){http_response_code(403);page('Access restricted','<h1>Administrator access required</h1>');}
 $body=$nav.'<h1>Owner listing reviews</h1>'.$flash.'<p>Review the photos, owner details and advert before publication. Confirm payment separately; this screen does not take or verify payments.</p>';
 foreach(q('SELECT v.*,o.email AS owner_email,o.name AS owner_name FROM vehicles v JOIN owners o ON o.id=v.owner_id ORDER BY created DESC')->fetchAll() as $v){
  $body.='<article class="garage-box" style="margin:25px 0"><h2>'.h($v['title']).'</h2><p>'.h($v['owner_name']).' · '.h($v['owner_email']).'</p><p>'.h($v['type']).' · '.h($v['location']).' · '.h($v['price']).'</p><p>'.nl2br(h($v['description'])).'</p><p>Public contact: '.h($v['contact']).' · Status: '.h($v['status']).'</p><div class="garage-gallery">';
  foreach(q('SELECT id FROM photos WHERE vehicle_id=?',[$v['id']])->fetchAll() as $p)$body.='<a href="?view=photo&amp;id='.$p['id'].'" target="_blank" rel="noopener"><img src="?view=photo&amp;id='.$p['id'].'" alt="Listing review photo"></a>';
  $body.='</div><form method="post">'.token().'<input type="hidden" name="listing" value="'.$v['id'].'">'.field('paid_until','Paid advertising expiry date','date',date('Y-m-d',$v['paid_until']>time()?(int)$v['paid_until']:strtotime('+1 year'))).'<label class="garage-check"><input type="checkbox" name="checked"><span>I reviewed this advert and confirmed the £49 annual payment, or the listing already has an active paid term.</span></label><button class="button" name="action" value="approve">Approve and publish</button> <button class="button ghost" name="action" value="reject">Return to draft / unpublish</button></form></article>';
 }
 page('Listing reviews',$body);
}
if($view==='reset')page('Reset password',$nav.'<h1>Reset your password</h1>'.$flash.'<form method="post">'.token().'<input type="hidden" name="action" value="reset"><input type="hidden" name="token" value="'.h($_GET['token']??'').'">'.field('password','New password (12 characters minimum)','password').'<button class="button">Set password →</button></form>');
if(in_array($view,['browse','vehicle'],true)){
 $rows=q('SELECT v.* FROM vehicles v WHERE status="live" AND paid_until>?'.($view==='vehicle'?' AND id=?':''),$view==='vehicle'?[time(),(int)($_GET['id']??0)]:[time()])->fetchAll();
 if($view==='vehicle'&&!$rows){http_response_code(404);page('Vehicle not found',$nav.'<h1>Listing unavailable</h1><p>This listing is not currently available.</p>');}
 $body=$nav.'<span class="eyebrow">INDEPENDENT OWNER LISTINGS</span><h1>'.($view==='vehicle'?h($rows[0]['title']):'Find your next escape.').'</h1>';
 if(!$rows)$body.='<p>Independent owner listings are coming soon. Own a vehicle? <a href="owners-garage.html">Create your own garage →</a></p>';
 $body.='<div class="garage-grid">';foreach($rows as $v){$photos=q('SELECT id FROM photos WHERE vehicle_id=?',[$v['id']])->fetchAll();$body.='<article class="garage-box">';
 if($view==='vehicle'){$body.='<div class="garage-gallery">';foreach($photos as $p)$body.='<a href="?view=photo&amp;id='.$p['id'].'" target="_blank" rel="noopener"><img src="?view=photo&amp;id='.$p['id'].'" alt="'.h($v['title']).' photo" loading="lazy"></a>';$body.='</div>';}
 elseif($photos)$body.='<img class="garage-photo" src="?view=photo&amp;id='.$photos[0]['id'].'" alt="'.h($v['title']).'" loading="lazy">';
 $body.='<h2>'.h($v['title']).'</h2><p>'.h($v['type']).' · '.h($v['location']).'</p><p>'.h($v['price']).'</p>';
 if($view==='vehicle')$body.='<p>'.nl2br(h($v['description'])).'</p><p>Advertised by an independent owner. Please confirm availability, insurance and all hire terms directly with them.</p><a class="button" href="mailto:'.h($v['contact']).'?subject='.rawurlencode('Enquiry: '.$v['title']).'">Enquire with the owner →</a>';
 else $body.='<a class="button" href="?view=vehicle&amp;id='.$v['id'].'">View vehicle →</a>';$body.='</article>';}
 page($view==='vehicle'?$rows[0]['title']:'Owner vehicles',$body.'</div>'.notice());
}
if(!$owner){
 $body=$nav.'<h1>Owner’s Garage</h1><p>Your email address is your username. '.($bookingEnabled?'£49 per vehicle annually, plus a £25 admin fee per confirmed booking.':'One annual advertising fee. No booking commission.').'</p>'.$flash.'<div class="garage-layout"><section class="garage-box"><h2>Sign in</h2><form method="post">'.token().'<input type="hidden" name="action" value="login">'.field('email','Email address','email').field('password','Password','password').'<button class="button">Open my garage →</button></form></section><section class="garage-box"><h2>Create your garage</h2><p>£49 per vehicle for 12 months. Create your account and prepare a draft free. We review your listing and arrange payment by invoice before it goes live. No automatic renewal.</p><form method="post">'.token().'<input type="hidden" name="action" value="register">'.field('name','Your name').field('email','Email address','email').field('password','Password (12 characters minimum)','password').'<label class="garage-check"><input type="checkbox" name="terms" required> <span>I accept the <a href="owner-terms.html">owner advertising terms</a> and <a href="garage-privacy.html">privacy notice</a>.</span></label><button class="button">Create my garage →</button></form></section></div><details><summary>Forgotten password or need a verification link?</summary><form method="post">'.token().field('email','Account email','email').'<button class="button" name="action" value="forgot">Reset password</button> <button class="button ghost" name="action" value="resend">Resend verification</button></form></details>';page('Owner sign in',$body.notice());
}
if($view==='edit'){
 $id=(int)($_GET['id']??0);$v=$id?q('SELECT * FROM vehicles WHERE id=? AND owner_id=?',[$id,$owner['id']])->fetch():[];if($id&&!$v){http_response_code(404);page('Not found','<h1>Vehicle not found</h1>');}
 $body=$nav.'<h1>'.($id?'Edit your vehicle':'Add a vehicle').'</h1>'.$flash.'<p>Changes return a listing to draft for review. Your annual expiry date stays the same.</p><form method="post">'.token().'<input type="hidden" name="action" value="save"><input type="hidden" name="id" value="'.$id.'">';
 foreach(['title'=>'Listing title','location'=>'Town / county','price'=>'Hire price and period (e.g. from £650 per week)','contact'=>'Public enquiry email'] as $f=>$label)$body.=field($f,$label,$f==='contact'?'email':'text',$v[$f]??'');
 $body.='<label for="type">Vehicle type</label><select id="type" name="type">';foreach(['Touring caravan','Motorhome','Campervan','Static caravan'] as $t)$body.='<option'.(($v['type']??'')===$t?' selected':'').'>'.h($t).'</option>';
 $body.='</select><label for="description">Description, facilities and hire requirements (maximum 5,000 characters)</label><textarea id="description" name="description" maxlength="5000" required>'.h($v['description']??'').'</textarea><label class="garage-check"><input type="checkbox" name="responsibility" required><span>I own this vehicle or am authorised to advertise it. I am responsible for accuracy, safety, insurance and all bookings under the <a href="owner-terms.html">owner terms</a>.</span></label><button class="button">Save vehicle →</button></form>';
 if($id){$body.='<h2>Your photos</h2><p>Up to 12 JPEG or PNG photos, 8 MB each. Use clear original images without promotional text.</p><div class="garage-grid">';foreach(q('SELECT id FROM photos WHERE vehicle_id=?',[$id])->fetchAll() as $p)$body.='<div><img class="garage-photo" src="?view=photo&amp;id='.$p['id'].'" alt="Your vehicle photo"><form method="post">'.token().'<input type="hidden" name="action" value="remove-photo"><input type="hidden" name="photo_id" value="'.$p['id'].'"><button class="button ghost">Remove photo</button></form></div>';
 $body.='</div><form method="post" enctype="multipart/form-data">'.token().'<input type="hidden" name="action" value="upload"><input type="hidden" name="id" value="'.$id.'"><label for="photo">Add a photo</label><input id="photo" type="file" name="photo" accept="image/jpeg,image/png" required><button class="button">Upload photo →</button></form><form method="post">'.token().'<input type="hidden" name="action" value="review"><input type="hidden" name="id" value="'.$id.'"><p>Ready? We will review your listing and arrange the £49 annual payment before publication. For an existing paid listing, we review your changes without charging again.</p><button class="button">Request review / renewal →</button></form>';}
 page('Edit vehicle',$body.notice());
}
$body=$nav.($isAdmin?'<p><a class="button" href="?view=admin">Review owner listings →</a></p>':'').'<h1>Hello, '.h($owner['name']).'.</h1><p>Welcome to your garage. '.($bookingEnabled?'The new booking plan is £49 per vehicle annually plus £25 per confirmed booking. Accept it for each vehicle under Bookings. Existing agreements keep their recorded terms.':'£49 per vehicle for 12 months, with no booking commission or automatic renewal.').'</p>'.$flash.(isset($_GET['sent'])?'<p class="garage-success">Review requested. We will contact you about approval and invoicing.</p>':'').'<a class="button" href="?view=edit">Add a vehicle →</a><div class="garage-grid" style="margin-top:30px">';
foreach(q('SELECT * FROM vehicles WHERE owner_id=? ORDER BY created DESC',[$owner['id']])->fetchAll() as $v){$body.='<article class="garage-box"><h2>'.h($v['title']).'</h2><p class="garage-status">'.h(ucfirst($v['status'])).($v['paid_until']?' · Annual expiry '.date('j M Y',(int)$v['paid_until']):' · Payment pending').'</p><a class="button" href="?view=edit&amp;id='.$v['id'].'">Manage vehicle →</a><form method="post">'.token().'<input type="hidden" name="id" value="'.$v['id'].'"><button class="button ghost" name="action" value="unpublish">Keep offline</button></form></article>';}
$body.='</div><form method="post">'.token().'<button class="button ghost" name="action" value="logout">Sign out</button></form>';page('My garage',$body.notice());
