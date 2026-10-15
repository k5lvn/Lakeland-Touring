import re
PHOTOS=[('11','Caravan exterior'),('01','Front lounge'),('02','View through the caravan'),('04','Kitchen and appliances'),('05','Family dining area'),('06','Bunk beds and storage'),('07','Rear dining area'),('08','Washroom'),('09','Front lounge arranged as a bed'),('10','Rear sleeping area')]
def gallery():
 buttons=''.join(f'<button type="button" data-photo="Assets/touring-{n}.jpg" aria-label="Open photo {i+1}: {alt}"><img src="Assets/touring-{n}.jpg" alt="{alt}" loading="lazy" decoding="async"></button>' for i,(n,alt) in enumerate(PHOTOS))
 return '<div class="touring-gallery" data-touring-gallery>'+buttons+'</div><button class="touring-view-all" type="button" data-view-all>View all 10 photos ↗</button>'
DIALOG='''<dialog id="touring-photo-viewer" class="touring-photo-viewer" aria-label="Lakeland Touring photo gallery"><div class="viewer-toolbar"><span class="viewer-count" aria-live="polite">1 / 10</span><button type="button" data-close aria-label="Close photo viewer">×</button></div><div class="viewer-stage"><img class="viewer-image" alt=""><button type="button" data-previous aria-label="Previous photo">‹</button><button type="button" data-next aria-label="Next photo">›</button></div><div class="viewer-thumbnails" aria-label="Choose a photo"></div></dialog>'''
def build(raw):
 raw,n=re.subn(r'<div class="gallery">.*?</div>\s*<p class="photo-disclaimer">.*?</p>',lambda _:gallery(),raw,count=1,flags=re.S);assert n==1,'Gallery markup changed'
 raw=raw.replace('</head>','<link rel="stylesheet" href="gallery.css?v=20261015-1"></head>',1)
 raw=raw.replace('</body>',DIALOG+'<script src="gallery.js?v=20261015-1" defer></script></body>',1)
 assert raw.count('data-photo=')==10 and 'photo-disclaimer' not in raw and '<figcaption>' not in raw
 assert 'noindex' not in raw.lower()
 return raw
if __name__=='__main__':
 from pathlib import Path
 css=Path('touring-gallery/gallery.css').read_text()
 Path('touring-gallery/test.html').write_text('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>*{box-sizing:border-box}body{margin:0;background:#111;padding:15px}'+css+'</style></head><body>'+gallery().replace('Assets/','../site/Assets/')+DIALOG+'<script src="gallery.js"></script></body></html>')
