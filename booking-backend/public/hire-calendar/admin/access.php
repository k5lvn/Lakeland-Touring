<?php
declare(strict_types=1);
namespace HireCalendar;
use PDO;
use TouringBooking\Failure;
require_once dirname(__DIR__).'/calendar.php';

function operatorAccess(array $c,PDO $db): void {
    \TouringBooking\session();
    if (!empty($c['operator_user']) && hash_equals($c['operator_user'],(string)($_SERVER['REMOTE_USER']??''))) return;
    if (($_SESSION['operator_until']??0)>time()) {
        $_SESSION['operator_until']=time()+3600;
        return;
    }
    $message='';
    if ($_SERVER['REQUEST_METHOD']==='POST') {
        if (!is_string($_POST['csrf']??null) || !hash_equals($_SESSION['csrf'],$_POST['csrf'])) throw new Failure('Refresh the sign-in page.',403);
        if (($_POST['login']??'')==='send') {
            $db->exec('CREATE TABLE IF NOT EXISTS operator_login_mail (slot INTEGER PRIMARY KEY,sent INTEGER NOT NULL)');
            $allowed=transaction($db,function()use($db){
                $last=(int)$db->query('SELECT sent FROM operator_login_mail WHERE slot=1')->fetchColumn();
                if ($last>time()-120) return false;
                $db->prepare('INSERT OR REPLACE INTO operator_login_mail VALUES (1,?)')->execute([time()]);
                return true;
            });
            if (!$allowed) {
                $message='A sign-in code was recently requested. You can request another in two minutes.';
            } else {
                $code=(string)random_int(10000000,99999999);
                $_SESSION['operator_challenge']=['digest'=>password_hash($code,PASSWORD_DEFAULT),'expires'=>time()+600,'attempts'=>0];
                $ok=mail($c['office_email'],'Touring Admin sign-in code','Use '.$code.' on the sign-in page you opened. It expires in ten minutes.',['From'=>$c['office_email']]);
                $message=$ok?'Check the Touring office inbox for your sign-in code.':'Email is temporarily unavailable. Try again shortly.';
            }
        } elseif (($_POST['login']??'')==='verify') {
            $challenge=&$_SESSION['operator_challenge'];
            if (is_array($challenge) && $challenge['expires']>=time() && ++$challenge['attempts']<=5 &&
                is_string($_POST['code']??null) && preg_match('/^\d{8}$/D',$_POST['code']) && password_verify($_POST['code'],$challenge['digest'])) {
                session_regenerate_id(true);
                unset($_SESSION['operator_challenge']);
                $_SESSION['csrf']=bin2hex(random_bytes(32));
                $_SESSION['operator_until']=time()+3600;
                header('Location: ./',true,303); exit;
            }
            $message='Check the code or request a new one.';
        }
    }
    http_response_code(403);
    ?><!doctype html><html lang="en-GB"><head><meta name="viewport" content="width=device-width,initial-scale=1"><meta charset="utf-8"><title>Touring Admin sign-in</title><link rel="stylesheet" href="admin.css"></head><body><main class="operator"><p>Lakeland Touring Admin</p><h1>Bookings</h1><section class="request-card"><h2>Operator sign-in</h2><p>Use a single-use code sent to the Touring office inbox.</p>
    <?php if ($message): ?><p role="status"><?=h($message)?></p><?php endif; ?>
    <form method="post"><input type="hidden" name="csrf" value="<?=h($_SESSION['csrf'])?>"><button type="submit" name="login" value="send">Email a sign-in code</button></form>
    <?php if (!empty($_SESSION['operator_challenge'])): ?><form method="post"><input type="hidden" name="csrf" value="<?=h($_SESSION['csrf'])?>"><label>Sign-in code <input required name="code" pattern="[0-9]{8}" inputmode="numeric" autocomplete="one-time-code"></label><button name="login" value="verify">Sign in</button></form><?php endif; ?>
    </section></main></body></html><?php
    exit;
}
