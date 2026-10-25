<?php
declare(strict_types=1);
// Public fixed-area forecast proxy: no itinerary, arbitrary URL or credential input.
header('Content-Type: application/json; charset=utf-8');header('Cache-Control: no-store');header('X-Content-Type-Options: nosniff');
function fail(int $code): never {http_response_code($code);echo json_encode(['error'=>'Forecast temporarily unavailable']);exit;}
if(($_SERVER['REQUEST_METHOD']??'GET')!=='GET')fail(405);
$areas=['braithwaite'=>['Braithwaite / Keswick',54.604,-3.191],'dalston'=>['Dalston / Carlisle',54.842,-2.985],'penrith'=>['Penrith / Ullswater',54.665,-2.755],'windermere'=>['Windermere / Bowness',54.379,-2.906],'ambleside'=>['Ambleside',54.432,-2.963],'coniston'=>['Coniston',54.369,-3.076],'buttermere'=>['Buttermere',54.541,-3.277],'eskdale'=>['Eskdale',54.390,-3.278],'kirkby'=>['Kirkby Lonsdale',54.202,-2.597],'gretna'=>['Gretna',54.993,-3.065]];
$id=$_GET['area']??'';if(!is_string($id)||!isset($areas[$id]))fail(400);
$dir=sys_get_temp_dir().'/lakeland-touring-weather-v1';if(!is_dir($dir)&&!@mkdir($dir,0700,true)&&!is_dir($dir))fail(503);
$file=$dir.'/'.$id.'.json';$lock=@fopen($dir.'/'.$id.'.lock','c');if(!$lock||!flock($lock,LOCK_EX))fail(503);
$cache=is_file($file)?json_decode((string)file_get_contents($file),true):null;$now=time();
if(!$cache||$now>max((int)($cache['next_check']??0),(int)($cache['expires']??0))){
 $headers=['User-Agent: LakelandTouring/1.0 https://lakelandtouring.uk/ LakelandTouring@Worx365Group.uk','Accept: application/json','Accept-Encoding: gzip, deflate'];
 if(!empty($cache['last_modified']))$headers[]='If-Modified-Since: '.$cache['last_modified'];
 $url='https://api.met.no/weatherapi/locationforecast/2.0/compact?'.http_build_query(['lat'=>$areas[$id][1],'lon'=>$areas[$id][2]]);
 $context=stream_context_create(['http'=>['method'=>'GET','header'=>implode("\r\n",$headers),'timeout'=>12,'ignore_errors'=>true],'ssl'=>['verify_peer'=>true,'verify_peer_name'=>true]]);
 $raw=@file_get_contents($url,false,$context);$response=$http_response_header??[];$status=0;$expires=0;$modified='';$encoding='';
 foreach($response as $header){if(preg_match('~^HTTP/\S+\s+(\d+)~',$header,$m))$status=(int)$m[1];if(stripos($header,'Expires:')===0)$expires=(int)strtotime(trim(substr($header,8)));if(stripos($header,'Last-Modified:')===0)$modified=trim(substr($header,14));if(stripos($header,'Content-Encoding:')===0)$encoding=trim(substr($header,17));}
 if(is_string($raw)&&$encoding==='gzip')$raw=@gzdecode($raw);elseif(is_string($raw)&&$encoding==='deflate')$raw=@gzuncompress($raw);
 if($status===304&&$cache){$cache['next_check']=$now+6*3600;$cache['expires']=$expires;$cache['fetched_at']=gmdate('c');}
 elseif($status===200&&is_string($raw)&&strlen($raw)<1000000){$payload=json_decode($raw,true);$hours=[];foreach(($payload['properties']['timeseries']??[]) as $item){$d=$item['data']['instant']['details']??[];if(!isset($item['time'],$d['air_temperature'],$d['wind_speed']))continue;$hours[]=['time'=>$item['time'],'temperature'=>$d['air_temperature'],'wind'=>$d['wind_speed'],'gust'=>$d['wind_speed_of_gust']??null,'symbol'=>$item['data']['next_1_hours']['summary']['symbol_code']??$item['data']['next_6_hours']['summary']['symbol_code']??''];}
 if($hours&&isset($payload['properties']['meta']['updated_at']))$cache=['area'=>$areas[$id][0],'fetched_at'=>gmdate('c'),'updated_at'=>$payload['properties']['meta']['updated_at'],'hours'=>$hours,'next_check'=>$now+6*3600,'expires'=>$expires,'last_modified'=>$modified];else $cache=null;
 }elseif($cache){$cache['next_check']=$now+1800;}
 if($cache){$temp=$file.'.tmp';if(file_put_contents($temp,json_encode($cache),LOCK_EX)!==false){@chmod($temp,0600);rename($temp,$file);}}
}
flock($lock,LOCK_UN);fclose($lock);
if(!$cache||empty($cache['hours'])||$now-strtotime($cache['fetched_at'])>12*3600)fail(503);
echo json_encode(['area'=>$cache['area'],'fetched_at'=>$cache['fetched_at'],'updated_at'=>$cache['updated_at'],'stale'=>false,'hours'=>$cache['hours']],JSON_UNESCAPED_SLASHES);
