/* Lakeland Touring: basic consent mode. No Google request before opt-in. */
(()=>{'use strict';
 const id='G-5W12LPB0KK',key='lt-analytics-consent-v1',age=180*86400000;
 if(!['lakelandtouring.uk','www.lakelandtouring.uk'].includes(location.hostname))return;
 let loaded=false,banner;
 const read=()=>{try{const v=JSON.parse(localStorage.getItem(key));return v&&typeof v.allowed==='boolean'&&Date.now()-v.at<age&&Date.now()>=v.at?v.allowed:null;}catch{return null;}};
 const save=allowed=>{try{localStorage.setItem(key,JSON.stringify({allowed,at:Date.now()}));}catch{}};
 const clear=()=>{for(const c of document.cookie.split(';')){const name=c.trim().split('=')[0];if(!/^_ga(?:_|$)/.test(name))continue;for(const domain of ['',location.hostname,'.lakelandtouring.uk'])document.cookie=name+'=; Max-Age=0; Path=/; SameSite=Lax'+(domain?'; Domain='+domain:'');}};
 const load=()=>{
  window['ga-disable-'+id]=false;if(loaded)return;loaded=true;
  window.dataLayer=window.dataLayer||[];
  window.gtag=window.gtag||function(){window.dataLayer.push(arguments);};
  gtag('consent','default',{analytics_storage:'denied',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});
  gtag('consent','update',{analytics_storage:'granted'});
  gtag('js',new Date());
  let referrer='';try{referrer=new URL(document.referrer).origin;}catch{}
  gtag('config',id,{send_page_view:false,allow_google_signals:false,allow_ad_personalization_signals:false,cookie_expires:15552000,page_location:location.origin+location.pathname,page_referrer:referrer});
  gtag('event','page_view',{page_location:location.origin+location.pathname,page_referrer:referrer,page_title:document.title});
  const lead=document.querySelector('meta[name="worx-lead"]')?.content;if(['contact','quote','group'].includes(lead))gtag('event','generate_lead',{form_name:lead,lead_source:'website_form'});
  const script=document.createElement('script');script.async=true;script.src='https://www.googletagmanager.com/gtag/js?id='+id;document.head.append(script);
 };
 const events=Object.freeze({contact_phone_click:{contact_method:'telephone'},contact_email_click:{contact_method:'email'},email_enquiry_start:{form_name:'project'},booking_checkout_start:{booking_stage:'secure_checkout'}});
 const track=name=>{if(!Object.prototype.hasOwnProperty.call(events,name)||read()!==true||!loaded||window['ga-disable-'+id])return false;gtag('event',name,events[name]);return true;};
 window.WorxAnalytics=Object.freeze({track});
 document.addEventListener('click',event=>{const link=event.target.closest?.('a[href]');if(!link)return;const href=link.getAttribute('href')||'';if(/^tel:/i.test(href))track('contact_phone_click');else if(/^mailto:/i.test(href))track('contact_email_click');});
 const choose=allowed=>{save(allowed);if(allowed)load();else{window['ga-disable-'+id]=true;clear();}banner.hidden=true;};
 const init=()=>{
  const style=document.createElement('style');style.textContent='#lt-analytics-banner{position:fixed;inset:auto 12px 54px;z-index:10000;max-width:720px;margin:auto;padding:18px;background:#151616;color:#edf8ff;border:1px solid #00b8ff;border-radius:10px;box-shadow:0 8px 32px #0008;font:15px/1.5 Arial,sans-serif}#lt-analytics-banner[hidden]{display:none}#lt-analytics-banner p{margin:0 0 12px}#lt-analytics-banner a{text-decoration:underline}#lt-analytics-banner button,#lt-cookie-settings{font:inherit;padding:10px 14px;border:1px solid #00b8ff;border-radius:5px;background:#151616;color:#edf8ff;cursor:pointer}#lt-analytics-banner .choices{display:flex;gap:12px;flex-wrap:wrap}#lt-cookie-settings{position:fixed;bottom:10px;left:12px;z-index:9999;font:12px Arial,sans-serif}';document.head.append(style);
  banner=document.createElement('section');banner.id='lt-analytics-banner';banner.setAttribute('aria-label','Optional analytics cookies');
  banner.innerHTML='<p><strong>Optional analytics cookies</strong><br>With your permission, we use Google Analytics to understand website visits and approximate locations. Advertising features are off. <a href="/analytics-privacy.html">Analytics privacy details</a></p><div class="choices"><button type="button" data-lt-accept>Accept analytics</button><button type="button" data-lt-reject>Reject analytics</button></div>';
  document.body.append(banner);banner.querySelector('[data-lt-accept]').onclick=()=>choose(true);banner.querySelector('[data-lt-reject]').onclick=()=>choose(false);
  const settings=document.createElement('button');settings.id='lt-cookie-settings';settings.type='button';settings.textContent='Cookie settings';settings.onclick=()=>{banner.hidden=false;banner.querySelector('[data-lt-reject]').focus();};document.body.append(settings);
  const allowed=read();banner.hidden=allowed!==null;if(allowed===true)load();else{window['ga-disable-'+id]=true;clear();}
  window.addEventListener('storage',e=>{if(e.key!==key)return;if(read()===true)load();else{window['ga-disable-'+id]=true;clear();}});
 };
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
