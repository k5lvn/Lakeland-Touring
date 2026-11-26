'use strict';
const el = id => document.getElementById(id);
const date = key => new Date(key + 'T12:00:00Z');
const iso = d => d.toISOString().slice(0, 10);
function add(key, count) {
  const d = date(key); d.setUTCDate(d.getUTCDate() + count); return iso(d);
}
const fmt = (key, options) => date(key).toLocaleDateString('en-GB', {...options, timeZone:'UTC'});
const money = p => new Intl.NumberFormat('en-GB', {style:'currency', currency:'GBP', minimumFractionDigits:p % 100 ? 2 : 0}).format(p / 100);
let diary, month, start, nights, issued;
let attempt = crypto.randomUUID();
const demo = window.calendarPreview;
const periodFor = key => diary.periods.find(p => p.start <= key && key < p.end);
const overlap = (start, end, b) => start < b.end && b.start < end;
function choices(key) {
  const p = periodFor(key);
  if (!p || key < diary.today) return [];
  const weekday = date(key).getUTCDay();
  return Object.keys(p.prices).map(Number).filter(n => {
    const end = add(key,n);
    if (p.season === 'peak' && (weekday !== 6 || n !== 7)) return false;
    if (p.season === 'low' && n === 3 && weekday !== 5) return false;
    return end <= p.end && !diary.blocks.some(b => overlap(key,end,b));
  }).sort((a,b)=>a-b);
}
function navigate(step) {
  const d = date(month); d.setUTCMonth(d.getUTCMonth()+step,1); month = iso(d); render();
}
function choose(key) {
  start = key; const opts = choices(key); nights = opts.includes(7) ? 7 : opts[0];
  issued = null; attempt=crypto.randomUUID(); el('notice').textContent = ''; render();
}
function render() {
  const first = date(month), final = date(month); final.setUTCMonth(first.getUTCMonth()+1,0);
  el('month').textContent = fmt(month,{month:'long',year:'numeric'});
  el('prev').disabled = month.slice(0,7) <= diary.today.slice(0,7);
  el('next').disabled = month.slice(0,7) >= diary.through.slice(0,7);
  const activePeriod = periodFor(month) || diary.periods.find(p=>p.start <= iso(final) && p.end > month);
  el('guide').textContent = activePeriod?.season === 'peak' ? 'Peak season · Choose a Saturday for seven nights.' : 'Choose a highlighted arrival date to see your stay options.';
  const grid = el('days'); grid.replaceChildren();
  for(let i=0;i<(first.getUTCDay()+6)%7;i++) grid.append(document.createElement('span'));
  for(let i=1;i<=final.getUTCDate();i++) {
    const key = add(month,i-1), p = periodFor(key), opts = choices(key);
    const block = diary.blocks.find(b=>b.start<=key && key<b.end);
    const state = key < diary.today || !p ? 'unreleased' : (block?.state || 'available');
    const b = document.createElement('button'); b.type='button'; b.className='day'; b.dataset.state = state;
    b.disabled = opts.length === 0; if(opts.length) b.classList.add('pick');
    const price = p && key >= diary.today && !block ? money(Math.round(p.prices['7']/7)) : '';
    const n = document.createElement('b'), amount = document.createElement('small'); n.textContent=String(i); amount.textContent=price;
    b.append(n,amount);
    const end = start && add(start,nights);
    if(start && key >= start && key < end) b.classList.add('range');
    if(key===start) b.classList.add('start');
    if(key===end){b.classList.add('end');amount.textContent='Return';}
    const description = opts.length ? 'available arrival' : state === 'available' ? 'stay night' : state;
    b.setAttribute('aria-label', [fmt(key,{weekday:'long',day:'numeric',month:'long'}),description,price,key===end?'return day':''].filter(Boolean).join(', '));
    if(!b.disabled)b.addEventListener('click',()=>choose(key));
    grid.append(b);
  }
  const length = el('length');
  if(start) {
    const p = periodFor(start); length.replaceChildren();
    choices(start).forEach(n=>length.add(new Option(n+' nights · '+money(p.prices[n]),String(n))));
    length.value=String(nights); length.disabled=length.options.length<=1;
    const label = fmt(start,{weekday:'short',day:'numeric',month:'short'})+' – '+fmt(add(start,nights),{weekday:'short',day:'numeric',month:'short',year:'numeric'});
    el('selection').textContent=label; el('total').textContent=money(p.prices[nights]);
    el('recap').textContent=label+' · '+nights+' nights · '+money(p.prices[nights])+' caravan hire';
  } else {length.replaceChildren(new Option('Select an arrival first',''));length.disabled=true;el('selection').textContent='Choose an available arrival date.';el('total').textContent='—';}
  el('continue').disabled=!start || Boolean(issued);
}
async function load() {
  try {
    const result=demo || await (await fetch('availability.php',{cache:'no-store'})).json();
    if(!result.periods?.length) throw Error(result.error || 'New dates are being prepared.');
    diary=result;
    if(!month) month=(diary.periods.find(p=>p.end>diary.today)?.start || diary.today).slice(0,7)+'-01';
    if(month.slice(0,7)<diary.today.slice(0,7)) month=diary.today.slice(0,7)+'-01';
    if(start && !choices(start).includes(nights)){start=null;issued=null;}
    render();
  } catch {
    start=null;diary=null;el('days').replaceChildren();el('continue').disabled=true;el('length').disabled=true;
    el('prev').disabled=true;el('next').disabled=true;el('total').textContent='—';el('selection').textContent='Contact us to check your dates.';
    el('guide').replaceChildren('The diary is temporarily unavailable. ');
    const link=document.createElement('a');link.href='/booking.html';link.textContent='Enquire about dates';el('guide').append(link);
  }
}
for(const name of ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']) {const s=document.createElement('span');s.textContent=name;el('week').append(s);}
el('prev').onclick=()=>navigate(-1);el('next').onclick=()=>navigate(1);
el('length').onchange=e=>{nights=Number(e.target.value);issued=null;render();};
el('continue').onclick=()=>{el('message').textContent='';el('details').showModal();};
document.querySelector('.close').onclick=()=>el('details').close();
el('request').onsubmit=async e=>{
  e.preventDefault();const button=e.submitter;button.disabled=true;
  try {
    if(demo){el('message').textContent='Design preview only. No request was sent.';return;}
    const data=Object.fromEntries(new FormData(e.target));
    if(!diary || !start)throw Error('Please select your stay again.');
    const request={...data,start,nights,attempt,expected:periodFor(start).prices[nights],csrf:diary.csrf};
    const response=await fetch('request.php',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request)});
    const result=await response.json();if(!response.ok)throw Error(result.error || 'Please try again.');
    issued=result.reference;el('details').close();el('notice').replaceChildren('Request '+issued+' is awaiting approval. ');
    const link=document.createElement('a');link.href='status.php?key='+encodeURIComponent(result.key);link.textContent='View your request and confirmation';el('notice').append(link);el('notice').scrollIntoView({block:'nearest'});render();
  } catch(error){el('message').textContent=error.message;await load();} finally{button.disabled=false;}
};
load();
