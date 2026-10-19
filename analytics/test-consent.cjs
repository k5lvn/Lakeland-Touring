const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('analytics/analytics-consent.js','utf8');
function boot(saved){
 const store={};if(saved)store['lt-analytics-consent-v1']=JSON.stringify(saved);
 const head=[],body=[],cookies=[],handlers={};
 const node=()=>({hidden:false,setAttribute(){},append(){},focus(){},querySelector(key){return this.children[key]??=(node());},children:{}});
 const document={readyState:'complete',title:'Bathrooms',referrer:'https://example.test/private?email=person@example.test',head:{append:n=>head.push(n)},body:{append:n=>body.push(n)},createElement:()=>node()};
 Object.defineProperty(document,'cookie',{get:()=> '_ga=old; _ga_5W12LPB0KK=old; essential=yes',set:v=>cookies.push(v)});
 const context={document,location:{hostname:'www.lakelandtouring.uk',origin:'https://lakelandtouring.uk',pathname:'/bathrooms.html',search:'?email=private',hash:'#private'},localStorage:{getItem:k=>store[k]??null,setItem:(k,v)=>store[k]=v},URL,Date,addEventListener:(n,h)=>handlers[n]=h};context.window=context;
 vm.runInNewContext(source,context);return {context,head,body,cookies,store,handlers};
}
let p=boot();assert.equal(p.head.filter(n=>n.src).length,0);assert.equal(p.body[0].hidden,false);
p.body[0].querySelector('[data-lt-reject]').onclick();assert.equal(p.head.filter(n=>n.src).length,0);assert.equal(p.context['ga-disable-G-5W12LPB0KK'],true);
p.body[1].onclick();p.body[0].querySelector('[data-lt-accept]').onclick();assert.equal(p.head.filter(n=>n.src).length,1);
const events=p.context.dataLayer.map(v=>Array.from(v));const event=events.find(v=>v[0]==='event');assert.equal(event[2].page_location,'https://lakelandtouring.uk/bathrooms.html');assert.equal(event[2].page_referrer,'https://example.test');assert(!JSON.stringify(events).includes('person@example.test'));
p.body[0].querySelector('[data-lt-reject]').onclick();assert.equal(p.context['ga-disable-G-5W12LPB0KK'],true);assert(p.cookies.every(v=>!v.startsWith('essential=')));
p=boot({allowed:true,at:Date.now()});assert.equal(p.head.filter(n=>n.src).length,1);assert.equal(p.body[0].hidden,true);
p=boot({allowed:true,at:Date.now()-181*86400000});assert.equal(p.head.filter(n=>n.src).length,0);assert.equal(p.body[0].hidden,false);
console.log('Consent: no requests before opt-in/rejection, returning consent, expiry, withdrawal and URL redaction passed.');
