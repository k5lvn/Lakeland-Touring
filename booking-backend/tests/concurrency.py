"""Two independent PHP processes race for overlapping dates in the same SQLite DB."""
import os, pathlib, subprocess, tempfile
common=pathlib.Path(__file__).resolve().parents[1]/'public/api/common.php'
with tempfile.TemporaryDirectory(prefix='touring-race-') as folder:
    code='''<?php
require $argv[1];
$_SERVER['DOCUMENT_ROOT']=__DIR__;
$cfg=['private_dir'=>$argv[2],'terms_version'=>'fixture'];
$db=\\TouringBooking\\db($cfg);
$q=['start'=>'2030-01-01','end'=>'2030-01-08'];
while(!is_file($argv[2].'/go'))usleep(1000);
try{\\TouringBooking\\hold($db,$cfg,$argv[3],$q);echo 'held';}
catch(\\TouringBooking\\Failure $e){if($e->status!==409)throw $e;echo 'conflict';}
'''
    script=pathlib.Path(folder)/'race.php';script.write_text(code)
    # Document root is outside private_dir, as on production; don't use __DIR__.
    script.write_text(code.replace("$_SERVER['DOCUMENT_ROOT']=__DIR__;","$_SERVER['DOCUMENT_ROOT']=$argv[4];"))
    jobs=[subprocess.Popen(['php',str(script),str(common),folder,str(i),str(common.parent)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for i in range(2)]
    (pathlib.Path(folder)/'go').touch()
    results=[p.communicate(timeout=20) for p in jobs]
    assert all(p.returncode==0 for p in jobs),results
    assert sorted(o.strip() for o,e in results)==['conflict','held'],results
    print('Passed simultaneous independent-process overlap rejection and first-open schema migration.')
