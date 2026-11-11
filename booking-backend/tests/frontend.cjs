const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
function element(){return {textContent:'',innerHTML:'',style:{},disabled:false,classList:{add(){},remove(){}},setAttribute(){},addEventListener(){},before(){},append(){},appendChild(){}};}
const nodes=new Map(),requests=[];
const c=vm.createContext({document:{getElementById(id){if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);},createElement:element},
  fetch:(...args)=>new Promise(resolve=>requests.push({args,resolve})),Date,URL,console,alert(){},setInterval(){},window:{},location:{href:'https://lakelandtouring.uk/booking.html'},FormData:class{}});
vm.runInContext(fs.readFileSync(__dirname+'/../frontend/booking.js','utf8'),c);
assert.equal(nodes.get('continueBtn').disabled,true);
async function tick(){await new Promise(r=>setImmediate(r));}
function response(q){return {ok:true,json:async()=>q};}
const valid={hold_until:Math.floor(Date.now()/1000)+900,server_time:Math.floor(Date.now()/1000),hire_pence:59500,pay_now_pence:25000,balance_pence:34500,nights:7,balance_due_date:'2027-01-01'};
(async()=>{
 requests[0].resolve(response({bookings:[]}));await tick();
 assert.equal(nodes.get('continueBtn').disabled,true,'incomplete availability must fail closed');
 vm.runInContext("availabilityReady=true;csrfToken='fixture';start=new Date(2027,2,1);end=new Date(2027,2,8);refreshQuote();",c);
 const first=requests.at(-1);
 vm.runInContext("start=new Date(2027,2,8);end=new Date(2027,2,15);refreshQuote();",c);
 const second=requests.at(-1);second.resolve(response(valid));await tick();
 assert.equal(nodes.get('continueBtn').disabled,false);
 first.resolve(response({...valid,hire_pence:10000,balance_pence:0}));await tick();
 assert.match(nodes.get('hirePrice').textContent,/595/,'stale response must not overwrite current quote');
 vm.runInContext('refreshQuote()',c);requests.at(-1).resolve(response({...valid,pay_now_pence:'25000'}));await tick();
 assert.equal(nodes.get('continueBtn').disabled,true,'malformed monetary data must not enable checkout');
 assert.equal(JSON.parse(second.args[1].body).csrf,'fixture');
 vm.runInContext("holds=[{start:'2027-03-09',end:'2027-03-11',hold_until:9999999999}];cursor=new Date(2027,2,1);render(false);",c);
 assert.equal(vm.runInContext("isHeld(new Date(2027,2,10))",c),true);
 assert.equal(vm.runInContext("hasBookedBetween(new Date(2027,2,8),new Date(2027,2,12))",c),true);
 console.log('Passed frontend availability, stale-response, money validation and CSRF checks.');
})().catch(e=>{console.error(e);process.exit(1);});
