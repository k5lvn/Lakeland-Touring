const cal=document.getElementById('calendar'),monthLabel=document.getElementById('monthLabel'),startEl=document.getElementById('startDate'),endEl=document.getElementById('endDate'),hireEl=document.getElementById('hirePrice'),totalEl=document.getElementById('totalPrice'),balanceEl=document.getElementById('balancePrice'),balanceDueEl=document.getElementById('balanceDue'),continueBtn=document.getElementById('continueBtn'),modal=document.getElementById('bookingModal'),form=document.getElementById('bookingForm'),formMessage=document.getElementById('formMessage'),checkoutBtn=document.getElementById('checkoutBtn');
let cursor=new Date(); cursor.setDate(1); let start=null,end=null,booked=[],validQuote=null,availabilityReady=false,quoteVersion=0;
const iso=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
const fmt=d=>d?d.toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'short',year:'numeric'}):'Choose date';
const same=(a,b)=>a&&b&&iso(a)===iso(b); const atMidnight=d=>new Date(d.getFullYear(),d.getMonth(),d.getDate());
function isBooked(d){const s=iso(d);return booked.some(x=>s>=x.start&&s<x.end)}
function hasBookedBetween(a,b){let d=new Date(a);while(d<b){if(isBooked(d))return true;d.setDate(d.getDate()+1)}return false}
async function loadAvailability(){
 availabilityReady=false; validQuote=null; render();
 const notice=document.querySelector('.calendar-card .notice');
 const normal=notice ? notice.textContent : '';
 if(notice){notice.setAttribute('role','status');notice.textContent='Checking live availability…';}
 try{
  const r=await fetch('api/availability.php',{cache:'no-store',signal:AbortSignal.timeout(15000)});
  if(!r.ok)throw new Error('Availability unavailable');
  const j=await r.json();
  if(!Array.isArray(j.bookings)||!j.bookings.every(x=>x&&/^\\d{4}-\\d{2}-\\d{2}$/.test(x.start)&&/^\\d{4}-\\d{2}-\\d{2}$/.test(x.end)&&x.start<x.end))throw new Error('Invalid availability');
  booked=j.bookings;availabilityReady=true;
  if(notice)notice.textContent=normal;
 }catch(e){
  booked=[];start=null;end=null;
  if(notice){notice.textContent='Live availability could not be loaded. Dates cannot be selected. ';
   const retry=document.createElement('button');retry.type='button';retry.textContent='Retry availability';retry.onclick=()=>{notice.textContent=normal;loadAvailability();};notice.appendChild(retry);}
 }
 render();
}
async function refreshQuote(){const version=++quoteVersion;validQuote=null;startEl.textContent=fmt(start);endEl.textContent=fmt(end);hireEl.textContent=totalEl.textContent=balanceEl.textContent=balanceDueEl.textContent='—';continueBtn.disabled=true;if(!availabilityReady||!start||!end)return;try{const r=await fetch('api/quote.php',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({start:iso(start),end:iso(end)})});const q=await r.json();if(version!==quoteVersion)return;if(!r.ok)throw new Error(q.error||'Those dates cannot be booked.');validQuote=q;hireEl.textContent=`£${(q.hire_pence/100).toLocaleString('en-GB')} (${q.nights} nights)`;totalEl.textContent=`£${(q.pay_now_pence/100).toLocaleString('en-GB')}`;balanceEl.textContent=`£${(q.balance_pence/100).toLocaleString('en-GB')}`;balanceDueEl.textContent=q.balance_pence?new Date(q.balance_due_date+'T12:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}):'Paid in full at booking';continueBtn.disabled=false}catch(e){if(version!==quoteVersion)return;hireEl.textContent=e.message;hireEl.style.fontSize='.95rem'}}
function render(){monthLabel.textContent=cursor.toLocaleDateString('en-GB',{month:'long',year:'numeric'});cal.innerHTML='';const first=new Date(cursor.getFullYear(),cursor.getMonth(),1),offset=(first.getDay()+6)%7,gridStart=new Date(first);gridStart.setDate(1-offset);const today=atMidnight(new Date());for(let i=0;i<42;i++){const d=new Date(gridStart);d.setDate(gridStart.getDate()+i);const b=document.createElement('button');b.className='day';b.textContent=d.getDate();if(d.getMonth()!==cursor.getMonth())b.classList.add('muted');if(d<today)b.classList.add('past');if(isBooked(d))b.classList.add('booked');if(same(d,start)||same(d,end))b.classList.add('selected');if(start&&end&&d>start&&d<end)b.classList.add('in-range');b.setAttribute('aria-label',fmt(d));b.disabled=!availabilityReady||d<today||isBooked(d)||d.getMonth()!==cursor.getMonth();b.onclick=()=>selectDate(d);cal.appendChild(b)}refreshQuote()}
function selectDate(d){if(!availabilityReady)return;if(!start||(start&&end)||d<start){start=new Date(d);end=null}else if(hasBookedBetween(start,d)){alert('Those dates cross an existing booking. Please choose another return date.');return}else{end=new Date(d)}render()}
document.getElementById('prevMonth').setAttribute('aria-label','Previous month');document.getElementById('nextMonth').setAttribute('aria-label','Next month');document.getElementById('modalClose').setAttribute('aria-label','Close booking details');
document.getElementById('prevMonth').onclick=()=>{cursor.setMonth(cursor.getMonth()-1);render()};document.getElementById('nextMonth').onclick=()=>{cursor.setMonth(cursor.getMonth()+1);render()};continueBtn.onclick=()=>{if(validQuote){modal.classList.add('open');modal.setAttribute('aria-hidden','false')}};document.getElementById('modalClose').onclick=()=>{modal.classList.remove('open');modal.setAttribute('aria-hidden','true')};modal.addEventListener('click',e=>{if(e.target===modal){modal.classList.remove('open');modal.setAttribute('aria-hidden','true')}});
form.addEventListener('submit',async e=>{e.preventDefault();if(!validQuote)return;formMessage.textContent='';checkoutBtn.disabled=true;checkoutBtn.textContent='Preparing secure checkout…';const fd=new FormData(form),payload=Object.fromEntries(fd.entries());payload.start=iso(start);payload.end=iso(end);try{const r=await fetch('api/create-checkout-session.php',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await r.json();if(!r.ok)throw new Error(data.error||'Unable to start checkout');if(data.url)location.href=data.url;else throw new Error('Checkout URL missing')}catch(err){formMessage.textContent=err.message;checkoutBtn.disabled=false;checkoutBtn.textContent='Proceed to secure checkout'}});
loadAvailability();
