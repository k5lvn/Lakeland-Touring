import html
from bs4 import BeautifulSoup
BASE='https://lakelandtouring.uk/'
REVIEW='https://search.google.com/local/writereview?placeid=ChIJJ8CuYWGLJ2oR3ygLFOCfnJM'
MAPS='https://maps.google.com/maps?cid=10636552204700035295'
def build(home,data):
 assert data['location_id']=='locations/7797320272030899713'
 reviews=data['reviews'];assert len({r['id'] for r in reviews})==len(reviews)
 assert data['total_count']==len(reviews),'Incomplete snapshot'
 s=BeautifulSoup(home,'html.parser')
 for nav in s.find_all('nav'):
  if not nav.find('a',href='/reviews/'):
   a=s.new_tag('a',href='/reviews/');a.string='Reviews'
   contact=nav.find('a',href='contact.html')
   if contact:contact.insert_before(a)
   else:nav.append(a)
 invitation=s.select_one('.w365-review-copy')
 if invitation and not invitation.find('a',href='/reviews/'):
  a=s.new_tag('a',href='/reviews/');a.string='Read our Google reviews';a['style']='display:inline-block;margin-top:12px;color:#85d5cb;text-decoration:underline';invitation.append(a)
 # Rebuild the homepage banner from the same complete snapshot on every sync.
 for old in s.select('[data-dk-review-banner]'):old.decompose()
 hero=s.select_one('.lt-hero-content');assert hero,'Homepage hero missing'
 if reviews:
  items=[]
  for r in sorted(reviews,key=lambda r:r['created_at'],reverse=True):
   assert isinstance(r['stars'],int) and 1<=r['stars']<=5
   esc=lambda v:html.escape(str(v))
   items.append('<span class="dk-ticker-item"><span class="dk-ticker-stars" aria-label="'+str(r['stars'])+' out of 5 stars">'+'★'*r['stars']+'☆'*(5-r['stars'])+'</span> <strong>'+esc(r['author'])+'</strong><span> — '+esc(r['text'])+'</span></span>')
  group='<div class="dk-ticker-group">'+''.join(items)+'</div>'
  duplicate='<div class="dk-ticker-group" aria-hidden="true">'+''.join(items)+'</div>'
  banner='<div data-dk-review-banner="true" class="dk-review-ticker" role="region" aria-label="Google customer reviews"><a class="dk-ticker-label" href="/reviews/">Google Reviews</a><div class="dk-ticker-window" tabindex="0" aria-label="Scrolling customer reviews"><div class="dk-ticker-track">'+group+duplicate+'</div></div><button type="button" class="dk-ticker-toggle" aria-label="Pause scrolling reviews" aria-pressed="false">Ⅱ</button></div>'
  hero.append(BeautifulSoup(banner,'html.parser'))
  css=s.new_tag('style');css['data-dk-review-banner']='true';css.string="""
.lt-hero-content{min-width:0}.lt-hero{min-width:0}.dk-review-ticker{grid-column:1/-1;display:flex;align-items:center;min-width:0;width:100%;max-width:100%;box-sizing:border-box;margin-top:20px;border:0;background:transparent;text-shadow:0 1px 3px rgba(0,0,0,.8);height:48px;overflow:hidden;text-align:left}
.dk-ticker-label{flex:none;padding:0 16px;color:#85d5cb;font-family:inherit;font-size:16px;font-style:normal;font-weight:700;letter-spacing:.06em;text-decoration:none;white-space:nowrap}
.dk-ticker-window{flex:1;min-width:0;overflow:hidden}.dk-ticker-track{display:flex;width:max-content;animation:dk-review-scroll var(--ticker-duration,90s) linear infinite}
.dk-ticker-group{display:flex;flex:none;align-items:center}.dk-ticker-item{display:inline-flex;align-items:center;gap:8px;white-space:nowrap;padding-right:64px;font-size:16px;line-height:1.4}.dk-ticker-item span{white-space:nowrap}.dk-ticker-item>span:last-child{font-style:italic}.dk-ticker-stars{color:#85d5cb;letter-spacing:2px}
.dk-ticker-toggle{flex:none;border:0;border-left:0;border-radius:0;background:transparent;color:#85d5cb;width:44px;height:46px;cursor:pointer;font-size:16px}
.dk-review-ticker:hover .dk-ticker-track,.dk-review-ticker:focus-within .dk-ticker-track,.dk-review-ticker.is-paused .dk-ticker-track{animation-play-state:paused}
.dk-ticker-window:focus-visible,.dk-ticker-toggle:focus-visible,.dk-ticker-label:focus-visible{outline:2px solid #85d5cb;outline-offset:-3px}
@keyframes dk-review-scroll{to{transform:translateX(-50%)}}
@media(max-width:640px){.dk-review-ticker{height:44px;margin-top:16px}.dk-ticker-label{font-size:15px;padding:0 9px;letter-spacing:.03em}.dk-ticker-item{font-size:15px}.dk-ticker-toggle{height:42px;width:38px}}
@media(prefers-reduced-motion:reduce){.dk-ticker-track{animation:none}.dk-ticker-window{overflow-x:auto}}
"""
  s.head.append(css)
  js=s.new_tag('script');js['data-dk-review-banner']='true';js.string="""
(function(){
 const root=document.querySelector('.dk-review-ticker');if(!root)return;
 const button=root.querySelector('.dk-ticker-toggle'),track=root.querySelector('.dk-ticker-track');
 function setPaused(paused){root.classList.toggle('is-paused',paused);button.textContent=paused?'▶':'Ⅱ';button.setAttribute('aria-label',paused?'Play scrolling reviews':'Pause scrolling reviews');button.setAttribute('aria-pressed',String(paused));}
 button.addEventListener('click',()=>setPaused(!root.classList.contains('is-paused')));
 root.querySelector('.dk-ticker-window').addEventListener('pointerdown',()=>setPaused(true),{passive:true});
 function size(){root.style.setProperty('--ticker-duration',Math.max(25,track.scrollWidth/2/42)+'s');}
 size();window.addEventListener('resize',size);if(document.fonts)document.fonts.ready.then(size);
})();
"""
  s.body.append(js)

 assert len(s.select('.dk-ticker-group:not([aria-hidden]) .dk-ticker-item'))==len(reviews),'Homepage review count mismatch'
 updated=str(s).encode()
 for asset in s.select('[data-dk-review-banner]'):asset.decompose()
 s.body['class']=['page-reviews']
 for a in s.select('nav a'):
  a.attrs.pop('aria-current',None);a['class']=[]
  if a.get('href')=='/reviews/':a['aria-current']='page'
 s.title.string='Google Reviews | Lakeland Touring, Carlisle'
 s.find('link',rel='canonical')['href']=BASE+'reviews/'
 s.find('meta',attrs={'name':'description'})['content']='Read genuine Google customer reviews of Lakeland Touring and share your experience of our work in the UK and Ireland.'
 for t in s.find_all('meta'):
  if t.get('property') in ['og:title','og:description','og:url','og:image']:t.decompose()
 for t in s.find_all('script',type='application/ld+json'):t.decompose()
 for t in s.find_all(True):
  for attr in ['href','src','action']:
   v=t.get(attr,'')
   if v and not v.startswith(('/','#','https:','http:','mailto:','tel:','data:')):t[attr]='/'+v
 cards=[]
 for r in sorted(reviews,key=lambda r:r['created_at'],reverse=True):
  assert isinstance(r['stars'],int) and 1<=r['stars']<=5
  esc=lambda v:html.escape(str(v))
  cards.append('<article class="ld-review-card"><h2>'+esc(r['author'])+'</h2><p aria-label="'+str(r['stars'])+' out of 5 stars" style="color:#85d5cb">'+'★'*r['stars']+'☆'*(5-r['stars'])+'</p><time datetime="'+esc(r['created_at'])+'">'+esc(r['created_at'][:10])+'</time><p style="white-space:pre-wrap">'+esc(r['text'])+'</p><small>Source: Google</small></article>')
 summary=('No Google reviews are available to display yet. Had work completed by us? We’d welcome your honest feedback.' if not reviews else f"{data['total_count']} Google reviews · {data['average_rating']:.1f} out of 5")
 content='<main id="main-content"><section class="pagehead"><div class="wrap"><div class="eyebrow">Your experience matters</div><h1>Customer reviews</h1><p>Feedback from customers of Lakeland Touring.</p><a class="btn" target="_blank" rel="noopener noreferrer" href="'+REVIEW+'">Leave Us a Google Review</a><a class="btn alt" target="_blank" rel="noopener noreferrer" href="'+MAPS+'">View on Google</a></div></section><section><div class="wrap"><p>'+html.escape(summary)+'</p><p>Reviews are checked daily. A new review appears here after Google publishes it and our next successful refresh.</p><p><small>Last checked: '+html.escape(data['checked_at'])+'</small></p><div class="ld-review-grid">'+''.join(cards)+'</div></div></section></main>'
 s.main.replace_with(BeautifulSoup(content,'html.parser'))
 style=s.new_tag('style');style.string='main#main-content{padding:130px 6% 70px;max-width:1250px;margin:auto;color:#eaf5ff}main#main-content .btn{display:inline-block;margin:12px 16px 20px 0;padding:14px 22px;background:#127fc5;color:white;border-radius:8px}main#main-content h1{font-size:clamp(36px,6vw,64px)}.ld-review-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.ld-review-card{padding:24px;border:1px solid #85d5cb;background:#071321;overflow-wrap:anywhere}.ld-review-card h2{font-size:24px;margin:0}.ld-review-card time,.ld-review-card small{color:var(--muted)}@media(max-width:640px){.ld-review-grid{grid-template-columns:1fr}.pagehead h1{font-size:40px}}';s.head.append(style)
 return updated,str(s).encode()
