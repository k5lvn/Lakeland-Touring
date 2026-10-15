(() => {
 const gallery=document.querySelector('[data-touring-gallery]');
 const dialog=document.querySelector('#touring-photo-viewer');
 if(!gallery||!dialog)return;
 const photos=Array.from(gallery.querySelectorAll('[data-photo]')).map(button=>({src:button.dataset.photo,alt:button.querySelector('img').alt}));
 const image=dialog.querySelector('.viewer-image'),count=dialog.querySelector('.viewer-count'),thumbs=dialog.querySelector('.viewer-thumbnails');
 let current=0,opener=null,start=null;
 photos.forEach((photo,index)=>{const button=document.createElement('button');button.type='button';button.setAttribute('aria-label',`View photo ${index+1}: ${photo.alt}`);button.innerHTML='<img alt="" loading="lazy">';button.firstChild.src=photo.src;button.addEventListener('click',()=>show(index));thumbs.append(button)});
 function show(index){current=(index+photos.length)%photos.length;image.src=photos[current].src;image.alt=photos[current].alt;count.textContent=`${current+1} / ${photos.length}`;Array.from(thumbs.children).forEach((el,i)=>el.setAttribute('aria-current',String(i===current)));thumbs.children[current].scrollIntoView({block:'nearest',inline:'nearest'});const preload=new Image();preload.src=photos[(current+1)%photos.length].src}
 function open(index,button){opener=button;dialog.showModal();document.body.classList.add('photo-viewer-open');show(index);dialog.querySelector('[data-close]').focus()}
 gallery.querySelectorAll('[data-photo]').forEach((button,index)=>button.addEventListener('click',()=>open(index,button)));
 document.querySelector('[data-view-all]').addEventListener('click',event=>open(0,event.currentTarget));
 dialog.querySelector('[data-close]').addEventListener('click',()=>dialog.close());
 dialog.querySelector('[data-previous]').addEventListener('click',()=>show(current-1));
 dialog.querySelector('[data-next]').addEventListener('click',()=>show(current+1));
 dialog.addEventListener('keydown',event=>{if(event.key==='ArrowRight'){event.preventDefault();show(current+1)}if(event.key==='ArrowLeft'){event.preventDefault();show(current-1)}});
 dialog.addEventListener('close',()=>{document.body.classList.remove('photo-viewer-open');if(opener)opener.focus()});
 dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close()});
 image.addEventListener('touchstart',event=>{if(event.touches.length===1)start={x:event.touches[0].clientX,y:event.touches[0].clientY};else start=null},{passive:true});
 image.addEventListener('touchend',event=>{if(!start||!event.changedTouches.length)return;const dx=event.changedTouches[0].clientX-start.x,dy=event.changedTouches[0].clientY-start.y;if(Math.abs(dx)>55&&Math.abs(dx)>Math.abs(dy)*1.4)show(current+(dx<0?1:-1));start=null},{passive:true});
})();
