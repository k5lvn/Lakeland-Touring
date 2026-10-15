import re,json
from pathlib import Path
LOGO='<img class="touring-official-logo" src="Assets/lakeland-touring-official.png?v=20261015" alt="Lakeland Touring — Caravan holidays in extraordinary places" width="2172" height="724"/>'
CREDIT='<p class="landscape-credit">Lake District photography: <a href="https://commons.wikimedia.org/wiki/File:Derwent_Water_Panorama,_Lake_District_-_June_2009.jpg">Derwentwater by DAVID ILIFF</a> · <a href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a>. Displayed with a responsive crop and dark overlay.</p>'
def build(raw,name):
 raw,n=re.subn(r'(<a class="brand"[^>]*>).*?(</a>)',lambda m:m[1]+LOGO+m[2],raw,count=1,flags=re.S);assert n==1
 raw,n=re.subn(r'(<a[^>]*class="footer-name"[^>]*>).*?(</a>)',lambda m:m[1]+LOGO+m[2],raw,count=1,flags=re.S);assert n==1
 if 'menu-toggle' not in raw:
  raw=raw.replace('</a><nav>','</a><button class="menu-toggle" type="button" aria-label="Open navigation" aria-expanded="false" onclick="document.querySelector(\'.topbar nav\').classList.toggle(\'show\');this.setAttribute(\'aria-expanded\',document.querySelector(\'.topbar nav\').classList.contains(\'show\'))">☰</button><nav>',1)
 raw=re.sub(r'<link[^>]*href="brand\.css[^\"]*"[^>]*>','',raw)
 raw=raw.replace('</head>','<link rel="stylesheet" href="brand.css?v=20261015-1"></head>',1)
 if name=='index.html':
  marker='<section class="hero"><div class="hero-copy">';assert raw.count(marker)==1
  raw=raw.replace(marker,'<section class="hero"><img class="hero-landscape" src="Assets/derwentwater-panorama.jpg" alt="Derwentwater and the Lake District fells seen from Catbells" width="3840" height="924" fetchpriority="high"><div class="hero-copy">'+LOGO.replace('touring-official-logo','hero-brand-logo'),1)
  raw=raw.replace('</footer>',CREDIT+'</footer>',1)
  raw=raw.replace('</head>','<meta property="og:image" content="https://lakelandtouring.uk/Assets/derwentwater-panorama.jpg"><link rel="preload" as="image" href="Assets/derwentwater-panorama.jpg"></head>',1)
  raw=raw.replace('"parentOrganization":','"logo":"https://lakelandtouring.uk/Assets/lakeland-touring-official.png","parentOrganization":',1)
 assert 'noindex' not in raw.lower()
 assert raw.count('alt="Lakeland Touring — Caravan holidays in extraordinary places"')==(3 if name=='index.html' else 2)
 return raw
