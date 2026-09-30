"""Gallery: his photographs from the field and the laboratory, gallery.html.

The page is his old Wix gallery (content/gallery/manifest.json, copied from the
live site by tools/wix_pull.py): the sets in his order, each under his own
caption, and a viewer that opens any photo at full size. build.py writes the
image files and hands render() the sets; this module draws them.

Layout. A set is one row of photos at one height, as each row stood on his
page. The row fills the text column unless that would make it taller than
--hmax; then it keeps --hmax and stops short, so a single photo never swells
to the width of the page. The widths come from each photo's proportions (the
flex arithmetic below), so no photo is cropped: many are his annotated
laboratory pictures, and a crop would cut their labels. On a phone the row
breaks into pairs (a pair whose two photos would come out shorter than about
a third of the screen's width stays two single rows). Both layouts are fixed
at build time, so nothing moves once the page is drawn.

Viewer. A photo is a link to its full-size file, so without JavaScript it
still opens. With it the link opens a modal <dialog>: the photo grows out of
its thumbnail, sharpens when the full file arrives, and goes back to the
thumbnail it came from on close. Arrow keys, Home and End step through the
whole gallery, the buttons do the same, a horizontal swipe follows the finger
and carries its speed into the change, a swipe down closes, and Escape (or the
Android back gesture, through the dialog) closes. Focus goes to the close
button and comes back to the thumbnail of the photo on screen. Reduced motion
keeps only short fades.

The video. His one film sits in the first set, a poster tile with a play mark.
Wix's static host takes no video files, so the stream stays where Wix keeps
his media (video.wixstatic.com) and is fetched only when he or a visitor
presses play: no byte of it loads with the page. That address lives only as
long as his Wix media library does. A YouTube upload by him would be more
durable; then `stream` becomes the embed and nothing else here changes. The
film has sound, so it has captions (FILM_CAPTIONS): what can be heard, off
until the reader turns them on in the player.
"""

import html

__all__ = ["CSS", "JS", "render", "rows", "vtt", "FILM_CAPTIONS"]

CSS = """
/* ---------- gallery: his photographs, set by set ---------- */
.gal{--gap:8px;--hmax:380px}
/* a narrower column keeps a single photo from taking the whole first screen */
@media (max-width:1200px){ .gal{--hmax:330px} }
/* one set: his caption, then its row. Sets are 56px apart, the caption sits
   16px over its photos, so each caption reads with the row it names */
.gset{margin:40px 0 0}
.gset+.gset{margin-top:56px}
.gset__h{max-width:var(--measure);margin:0 0 16px;
  font:600 21px/1.35 var(--serif);letter-spacing:-.004em;color:var(--ink);text-wrap:balance}
.gset__t{display:block}
/* "(during my Ph.D.)": his words, one step quieter than the rest of the line */
.gset__era{display:block;margin-top:2px;font-size:16px;font-weight:400;line-height:1.5;
  letter-spacing:0;color:var(--muted)}

/* A row: each photo as wide as its share of the row's summed proportions
   (--ar over --r), so every photo in it has one height. --r and --n belong to
   the row (its proportions summed, its photos counted); the row stops at the
   width that makes it --hmax tall. */
.gset__row{display:flex;gap:var(--gap);margin:0;padding:0;list-style:none;
  max-width:calc(var(--r) * var(--hmax) + (var(--n) - 1) * var(--gap))}
.gph{flex:none;margin:0;width:calc((100% - (var(--n) - 1) * var(--gap)) * var(--ar) / var(--r))}
.gph__a{position:relative;display:block;border-radius:var(--r-md);cursor:zoom-in;
  color:inherit;-webkit-tap-highlight-color:transparent}
/* a hairline, not a border: it keeps the white of his annotated pictures off
   the paper without adding a pixel to the arithmetic above */
.gph img{display:block;width:100%;height:auto;border-radius:var(--r-md);
  background:var(--surface);box-shadow:0 0 0 1px var(--rule);
  transition:transform var(--spring-quick),filter var(--t-quick) var(--ease-state)}
/* pressed: the photo gives a little under the finger, and comes back at once */
.gph__a:active img{transform:scale(.985)}
.gph__a:focus-visible{outline:2px solid var(--focus);outline-offset:3px}
@media (hover:hover){
  .gph__a:hover img{filter:brightness(1.03) saturate(1.04)}
}

/* the film: its poster, a play mark, its length */
.gph--video .gph__a{cursor:pointer}
.gph__play{position:absolute;inset:0;display:grid;place-items:center;pointer-events:none}
.gph__play svg{display:block;width:56px;height:56px;
  filter:drop-shadow(0 2px 10px rgba(0,0,0,.28))}
.gph__len{position:absolute;right:8px;bottom:8px;padding:2px 7px;border-radius:var(--r-pill);
  background:rgba(20,17,14,.62);color:#fff;font:600 12px/1.35 var(--sans);letter-spacing:.02em;
  font-variant-numeric:lining-nums tabular-nums;pointer-events:none}

/* a phone: pairs, each pair one height, laid by the same arithmetic with the
   pair's own sums (--pr, --pn). The .01px keeps a rounding error from pushing
   the second photo of a pair onto a line of its own. */
@media (max-width:640px){
  .gset{margin-top:32px}
  .gset+.gset{margin-top:44px}
  .gset__h{font-size:19px;margin-bottom:14px}
  .gset__row{flex-wrap:wrap;max-width:none}
  .gph{width:calc((100% - (var(--pn) - 1) * var(--gap)) * var(--ar) / var(--pr) - .01px)}
}

/* ---------- the viewer ---------- */
/* A modal <dialog> over the whole window, on a warm near-black so the photo
   carries the colour. The chrome (close, previous, next, the caption and the
   count) is quiet white on the dark and never covers the photo on a wide
   screen: the stage keeps clear of it. */
html.lb-open{overflow:hidden;background:#13100D}
.lb{position:fixed;inset:0;width:100%;height:100%;max-width:none;max-height:none;
  margin:0;padding:0;border:0;background:transparent;color:#EDE9E3;overflow:hidden;
  font-family:var(--serif)}
.lb::backdrop{background:transparent}
.lb:focus{outline:none}
.lb__bg{position:absolute;inset:0;background:rgb(19 16 13 / .985)}
.lb__stage{position:absolute;inset:0 0 var(--bar,104px);display:grid;place-items:center;
  padding:64px 88px 8px;touch-action:none;-webkit-user-select:none;user-select:none}
.lb__stage.is-zoomed{touch-action:auto}
.lb__media{position:relative;display:block;border-radius:4px;background:#1D1A17;
  will-change:transform;box-shadow:0 18px 60px rgba(0,0,0,.45)}
.lb__img,.lb__video{display:block;width:100%;height:100%;border-radius:4px;object-fit:contain;
  -webkit-user-drag:none}
/* the film takes the photo's place: the still steps aside (display:block
   above would otherwise keep it, and push the film out of the box) */
.lb__img[hidden]{display:none}
.lb__video{background:#000}
.lb__play{position:absolute;inset:0;display:grid;place-items:center;width:100%;margin:0;padding:0;
  border:0;border-radius:4px;background:transparent;color:#fff;cursor:pointer}
.lb__play svg{width:76px;height:76px;filter:drop-shadow(0 2px 14px rgba(0,0,0,.35));
  transition:transform var(--spring-quick)}
.lb__play:active svg{transform:scale(.94)}
.lb__play:focus-visible{outline:2px solid #fff;outline-offset:-6px}

.lb__bar{position:absolute;left:0;right:0;bottom:0;
  display:flex;align-items:flex-start;justify-content:space-between;gap:12px 32px;
  padding:18px 28px calc(18px + env(safe-area-inset-bottom))}
.lb__cap{max-width:var(--measure);margin:0;font-size:17px;line-height:1.45;color:#EDE9E3;
  text-wrap:pretty}
.lb__t{font-weight:600}
.lb__era{color:#ADA79F}
.lb__count{flex:none;margin:3px 0 0;font:600 13px/1.3 var(--sans);letter-spacing:.03em;
  color:#ADA79F;font-variant-numeric:lining-nums tabular-nums;white-space:nowrap}

.lb__btn{position:absolute;z-index:1;display:grid;place-items:center;width:44px;height:44px;
  margin:0;padding:0;border:0;border-radius:var(--r-pill);background:rgb(255 255 255 / .09);
  color:#fff;cursor:pointer;-webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-quick) var(--ease-state),opacity var(--t-quick) var(--ease-state),
    transform var(--spring-quick)}
.lb__btn svg{display:block;pointer-events:none}
.lb__x{top:14px;right:16px}
.lb__prev,.lb__next{top:calc(50% - var(--bar,104px) / 2 + 28px);margin-top:-22px}
.lb__prev{left:22px}
.lb__next{right:22px}
@media (hover:hover){
  .lb__btn:hover{background:rgb(255 255 255 / .18)}
}
.lb__btn:active{transform:scale(.94);background:rgb(255 255 255 / .22)}
.lb__btn:focus-visible{outline:2px solid #fff;outline-offset:2px}
.lb__btn[disabled]{opacity:.28;cursor:default;pointer-events:none}

/* a phone: the photo takes the width; previous and next sit at the foot,
   where a thumb reaches them, either side of the count, under the caption */
@media (max-width:640px){
  .lb__stage{padding:56px 0 4px}
  .lb__media,.lb__img,.lb__video{border-radius:0}
  .lb__bar{flex-direction:column;align-items:stretch;gap:6px;
    padding:12px 16px calc(8px + env(safe-area-inset-bottom))}
  .lb__cap{font-size:16px}
  .lb__count{display:flex;align-items:center;justify-content:center;min-height:44px;margin:0}
  .lb__prev,.lb__next{top:auto;bottom:calc(8px + env(safe-area-inset-bottom));margin:0}
  .lb__prev{left:12px}
  .lb__next{right:12px}
  .lb__x{top:8px;right:8px}
}
@media (forced-colors:active){
  .lb__btn{border:1px solid ButtonBorder}
}
"""

JS = r"""
var gal=document.querySelector('.gal');
if(!gal||!window.HTMLDialogElement||!Element.prototype.animate)return;
var links=[].slice.call(gal.querySelectorAll('.gph__a'));
if(!links.length)return;
var reduce=matchMedia('(prefers-reduced-motion: reduce)'),EASE='cubic-bezier(.2,.8,.2,1)';
/* a photo arriving or springing back travels on Motion's spring of that
   visual time (parts/springs.py): [its settle time, its linear() curve],
   where the browser knows linear(); elsewhere the site's curve over the
   visual time. Leaving keeps the shorter curve. */
var SPRING={},LIN=!!(window.CSS&&CSS.supports&&CSS.supports('transition-timing-function','linear(0, 1)'));
function travel(name,ms){return LIN&&SPRING[name]?SPRING[name]:[ms,EASE];}
var items=links.map(function(a){
  var h=a.closest('.gset').querySelector('.gset__h');
  return {a:a,full:a.getAttribute('data-full'),w:+a.getAttribute('data-w'),
    h:+a.getAttribute('data-h'),stream:a.getAttribute('data-stream')||'',
    vtt:a.getAttribute('data-vtt')||'',
    thumb:a.querySelector('img'),t:h.querySelector('.gset__t').textContent,
    era:(h.querySelector('.gset__era')||{}).textContent||''};
});
var CHEV=function(d){return '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" '+
  'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '+
  'aria-hidden="true"><path d="'+d+'"/></svg>';};
var dlg=document.createElement('dialog');
dlg.className='lb';
dlg.setAttribute('aria-label','Photo viewer');
dlg.innerHTML='<div class="lb__bg"></div>'+
  '<button class="lb__btn lb__x" type="button" aria-label="Close">'+CHEV('M6.5 6.5l11 11M17.5 6.5l-11 11')+'</button>'+
  '<div class="lb__stage"><div class="lb__media"><img class="lb__img" alt="" decoding="async"></div></div>'+
  '<div class="lb__bar"><p class="lb__cap"><span class="lb__t"></span> <span class="lb__era"></span></p>'+
  '<p class="lb__count" aria-live="polite"></p></div>'+
  '<button class="lb__btn lb__prev" type="button" aria-label="Previous photo">'+CHEV('m14.5 6-6 6 6 6')+'</button>'+
  '<button class="lb__btn lb__next" type="button" aria-label="Next photo">'+CHEV('m9.5 6 6 6-6 6')+'</button>';
document.body.appendChild(dlg);
var bg=dlg.querySelector('.lb__bg'),stage=dlg.querySelector('.lb__stage'),
  media=dlg.querySelector('.lb__media'),img=dlg.querySelector('.lb__img'),
  bar=dlg.querySelector('.lb__bar'),tEl=dlg.querySelector('.lb__t'),eEl=dlg.querySelector('.lb__era'),
  count=dlg.querySelector('.lb__count'),prev=dlg.querySelector('.lb__prev'),
  next=dlg.querySelector('.lb__next'),shut=dlg.querySelector('.lb__x'),
  chrome=[bar,prev,next,shut],cur=-1,video=null,play=null,closing=false,grow=null,cues='';

/* the photo's box on the stage: as large as the stage allows, never past its pixels */
function fit(it){
  var s=getComputedStyle(stage),
    W=stage.clientWidth-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight),
    H=stage.clientHeight-parseFloat(s.paddingTop)-parseFloat(s.paddingBottom),
    k=Math.min(W/it.w,H/it.h,1);
  media.style.width=Math.round(it.w*k)+'px';media.style.height=Math.round(it.h*k)+'px';
}
function layout(){
  dlg.style.setProperty('--bar',Math.ceil(bar.getBoundingClientRect().height)+'px');
  if(cur>=0)fit(items[cur]);
}
function stopVideo(){
  if(video){video.pause();video.removeAttribute('src');video.load();video.remove();video=null;}
  if(cues){URL.revokeObjectURL(cues);cues='';}
  if(play){play.remove();play=null;}
  img.hidden=false;
}
function startVideo(it){
  if(play){play.remove();play=null;}
  video=document.createElement('video');
  video.className='lb__video';video.controls=true;video.playsInline=true;
  video.setAttribute('playsinline','');video.poster=it.full;video.src=it.stream;
  /* the film has sound: its captions, off until the reader turns them on in
     the player, from a file made here (the page's own origin, so the player
     takes it beside a stream served from elsewhere) */
  if(it.vtt&&window.Blob&&window.URL){
    var tr=document.createElement('track');tr.kind='captions';tr.srclang='en';tr.label='English';
    tr.src=cues=URL.createObjectURL(new Blob([it.vtt],{type:'text/vtt'}));video.appendChild(tr);
  }
  img.hidden=true;media.appendChild(video);
  var p=video.play();if(p&&p.catch)p.catch(function(){});
  video.focus({preventScroll:true});
}
function show(i,autoplay){
  var it=items[i];cur=i;stopVideo();
  tEl.textContent=it.t;eEl.textContent=it.era;
  count.textContent=(i+1)+' of '+items.length;
  prev.disabled=i===0;next.disabled=i===items.length-1;
  layout();
  img.alt=it.t;
  img.src=it.thumb.currentSrc||it.thumb.src;      /* at once: already on the page */
  var full=new Image();full.decoding='async';full.src=it.full;
  (full.decode?full.decode():Promise.resolve()).then(function(){if(cur===i)img.src=it.full;},function(){});
  if(it.stream){
    if(autoplay)startVideo(it);
    else{
      play=document.createElement('button');play.type='button';play.className='lb__play';
      play.setAttribute('aria-label','Play the video');
      play.innerHTML='<svg viewBox="0 0 76 76" aria-hidden="true"><circle cx="38" cy="38" r="37" '+
        'fill="rgba(20,17,14,.5)" stroke="rgba(255,255,255,.85)" stroke-width="1.5"/>'+
        '<path d="M31 25.5v25l20-12.5z" fill="#fff"/></svg>';
      play.onclick=function(){startVideo(it);};
      media.appendChild(play);
    }
  }
  [i-1,i+1].forEach(function(k){if(items[k]){var p=new Image();p.src=items[k].full;}});
}
/* run fn once when the animation ends: on its finish event, or when its time is up,
   for a tab that paints no frames (a background tab sends no finish events) */
function after(a,ms,fn){var done=false;function go(){if(!done){done=true;fn();}}
  a.onfinish=go;setTimeout(go,ms+60);return a;}
function rect(el){var r=el.getBoundingClientRect();return {x:r.left,y:r.top,w:r.width,h:r.height};}
function onScreen(r){return r.w>0&&r.y+r.h>0&&r.y<innerHeight&&r.x+r.w>0&&r.x<innerWidth;}
/* the photo grows out of its thumbnail: a transform on its own box, drawn
   from its top left corner. Home, the corner is let go, so a pull down
   shrinks the photo about its centre */
function morph(from,to,name,ms){
  var tr=travel(name,ms),sx=from.w/to.w,dx=from.x-to.x,dy=from.y-to.y;
  media.style.transformOrigin='0 0';
  var a=media.animate([{transform:'translate('+dx+'px,'+dy+'px) scale('+sx+')',borderRadius:'8px'},
    {transform:'none',borderRadius:getComputedStyle(media).borderRadius}],
    {duration:tr[0],easing:tr[1],fill:'both'});
  grow=a;
  return after(a,tr[0],function(){a.cancel();
    if(grow===a){grow=null;if(!closing)media.style.transformOrigin='';}});
}
function fade(els,a,b,dur,delay){
  els.forEach(function(el){el.animate([{opacity:a},{opacity:b}],
    {duration:dur,delay:delay||0,easing:'linear',fill:'backwards'});});
}
function open(i,autoplay){
  if(dlg.open)return;
  closing=false;
  document.documentElement.classList.add('lb-open');
  dlg.showModal();
  show(i,autoplay);
  shut.focus({preventScroll:true});
  if(reduce.matches){fade([dlg],0,1,120);return;}
  var t=rect(items[i].thumb);
  fade([bg],0,1,240);fade(chrome,0,1,160,120);
  if(onScreen(t))morph(t,rect(media),'draw',340);
}
function close(){
  if(!dlg.open||closing)return;
  closing=true;
  var it=items[cur],from=rect(media),t=rect(it.thumb);
  stopVideo();
  var ended=false;
  function end(){
    if(ended)return;ended=true;
    if(dlg.open)dlg.close();closing=false;
    document.documentElement.classList.remove('lb-open');
    media.getAnimations().forEach(function(a){a.cancel();});
    media.style.transform='';media.style.transformOrigin='';bg.style.opacity='';
    it.a.focus();
  }
  if(reduce.matches){after(dlg.animate([{opacity:1},{opacity:0}],{duration:120}),120,end);return;}
  /* back from where the photo is on screen (at rest, pulled down, thrown,
     coming in), as transforms on its own box measured without one: a photo
     let go mid-pull lands on its thumbnail, not a pull's length away */
  flight=grow=null;
  media.getAnimations().forEach(function(a){a.cancel();});
  media.style.transform='';media.style.transformOrigin='0 0';
  var base=rect(media);
  function at(r){return 'translate('+(r.x-base.x)+'px,'+(r.y-base.y)+'px) scale('+r.w/base.w+')';}
  fade([bg],getComputedStyle(bg).opacity,0,220);fade(chrome,1,0,120);
  chrome.concat([bg]).forEach(function(el){el.style.opacity='0';});
  if(onScreen(t)){
    after(media.animate([{transform:at(from)},{transform:at(t),borderRadius:'8px'}],
      {duration:260,easing:EASE,fill:'forwards'}),260,function(){reset();end();});
  }else{
    var k=.96,to={x:from.x+from.w*(1-k)/2,y:from.y+from.h*(1-k)/2,w:from.w*k};
    after(media.animate([{opacity:1,transform:at(from)},{opacity:0,transform:at(to)}],
      {duration:180,easing:EASE,fill:'forwards'}),180,function(){reset();end();});
  }
  function reset(){chrome.concat([bg]).forEach(function(el){el.style.opacity='';});}
}
/* a step through the gallery. From a key or a button the photo changes at
   once, with a 120ms fade: a step that can come many times a second must not
   make anyone wait. A swipe arrives here with the photo already moving. */
function go(d,swiped){
  var i=cur+d;if(!items[i])return;
  show(i,false);
  if(reduce.matches||swiped)return;
  media.animate([{opacity:.4},{opacity:1}],{duration:120,easing:'linear'});
}
links.forEach(function(a,i){
  a.addEventListener('click',function(e){
    if(e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;   /* a new tab keeps the file */
    e.preventDefault();open(i,!!items[i].stream);
  });
});
shut.addEventListener('click',close);
prev.addEventListener('click',function(){go(-1);});
next.addEventListener('click',function(){go(1);});
dlg.addEventListener('cancel',function(e){e.preventDefault();close();});
/* closed by the browser itself (a second Escape is never held back): tidy up */
dlg.addEventListener('close',function(){
  if(!document.documentElement.classList.contains('lb-open'))return;
  stopVideo();document.documentElement.classList.remove('lb-open');
  media.getAnimations().forEach(function(a){a.cancel();});
  media.style.transform='';media.style.transformOrigin='';
  chrome.concat([bg]).forEach(function(el){el.style.opacity='';});
  if(items[cur])items[cur].a.focus();
});
dlg.addEventListener('keydown',function(e){
  if(e.target===video)return;                      /* the film's own keys: seek, volume */
  var k=e.key;
  if(k==='ArrowRight'||k==='ArrowLeft'||k==='Home'||k==='End'){
    e.preventDefault();
    go(k==='ArrowRight'?1:k==='ArrowLeft'?-1:k==='Home'?-cur:items.length-1-cur);
  }
});
addEventListener('resize',function(){if(dlg.open)layout();});
/* a click on the dark around the photo closes, as the close button does */
var moved=false;
stage.addEventListener('click',function(e){if(e.target===stage&&!moved)close();});

/* Touch: the photo follows the finger. Sideways past a quarter of the stage,
   or flicked faster than .35px/ms, it leaves the way it was thrown and the
   next one comes in behind it; otherwise it springs back. Down the same way
   closes. Past the first or last photo the pull meets rising resistance. A
   photo zoomed with two fingers keeps the browser's own pan.
   A finger never waits for an animation: one that lands on a photo still
   moving (thrown, coming in, springing back) stops it where it is on
   screen and drags it on from there. A photo thrown out and not yet gone
   lands at once: the next one is there, under the finger; so does one still
   growing out of its thumbnail. */
var vv=window.visualViewport,drag=null,flight=null;
function zoomed(){return vv&&vv.scale>1.01;}
if(vv)vv.addEventListener('resize',function(){stage.classList.toggle('is-zoomed',zoomed());});
function band(x,dim){return x*dim*.55/(dim+.55*Math.abs(x));}
/* stop the photo where it is: its moves cancelled, its live place written in */
function grab(){
  if(flight)flight(false);
  if(grow){grow.cancel();grow=null;media.style.transformOrigin='';}
  var live=media.getAnimations(),m=null;
  if(!live.length)return [0,0];
  var cs=getComputedStyle(media),tr=cs.transform,op=+cs.opacity;
  if(tr&&tr!=='none'){try{m=new DOMMatrixReadOnly(tr);}catch(_){}}
  live.forEach(function(a){a.cancel();});
  media.style.transform=m?tr:'';
  if(op<1&&!reduce.matches)media.animate([{opacity:op},{opacity:1}],{duration:120,easing:EASE});
  return m?[m.m41,m.m42]:[0,0];
}
stage.addEventListener('pointerdown',function(e){
  if(e.pointerType==='mouse'||drag||zoomed()||closing||e.target.closest('.lb__play,video'))return;
  var at=grab();
  drag={id:e.pointerId,x:e.clientX,y:e.clientY,axis:'',x0:at[0],y0:at[1],dx:at[0],dy:at[1],
    hist:[[e.timeStamp,e.clientX,e.clientY]]};
  moved=false;
  try{stage.setPointerCapture(e.pointerId);}catch(_){}
});
stage.addEventListener('pointermove',function(e){
  if(!drag||e.pointerId!==drag.id)return;
  var dx=e.clientX-drag.x,dy=e.clientY-drag.y;
  if(!drag.axis){
    if(Math.abs(dx)<10&&Math.abs(dy)<10)return;
    drag.axis=Math.abs(dx)>Math.abs(dy)?'x':(dy>0?'y':'');
    if(!drag.axis){drag=null;return;}
    moved=true;
  }
  drag.hist.push([e.timeStamp,e.clientX,e.clientY]);
  if(drag.hist.length>6)drag.hist.shift();
  if(drag.axis==='x'){
    var W=stage.clientWidth,to=drag.x0+dx,edge=(to>0&&cur===0)||(to<0&&cur===items.length-1);
    drag.dx=edge?band(to,W):to;
    media.style.transform='translate('+drag.dx+'px,'+drag.y0+'px)';
  }else{
    drag.dy=Math.max(0,drag.y0+dy);
    var p=Math.min(drag.dy/(stage.clientHeight*.6),1);
    media.style.transform='translate('+drag.x0+'px,'+drag.dy+'px) scale('+(1-p*.12)+')';
    bg.style.opacity=String(1-p*.7);
    chrome.forEach(function(el){el.style.opacity=String(1-p);});
  }
});
function release(e){
  if(!drag||e.pointerId!==drag.id)return;
  var d=drag;drag=null;
  var h=d.hist,a=h[0],b=h[h.length-1],dt=Math.max(b[0]-a[0],1),
    vx=(b[1]-a[1])/dt,vy=(b[2]-a[2])/dt;
  if(d.axis==='x'){
    var W=stage.clientWidth,dir=d.dx<0?1:-1,
      ok=items[cur+dir]&&(Math.abs(d.dx)>W*.25||Math.abs(vx)>.35&&Math.sign(vx)===-dir);
    if(ok&&!reduce.matches){
      var out=-dir*W*.6,t=Math.max(90,Math.min(220,Math.abs(out-d.dx)/Math.max(Math.abs(vx),.8)));
      var fly=media.animate([{transform:media.style.transform||'none',opacity:1},
        {transform:'translateX('+out+'px)',opacity:0}],{duration:t,easing:'cubic-bezier(.3,.7,.4,1)'});
      /* the photo in flight; a finger that lands before it is gone lands it at once */
      flight=function(enter){
        flight=null;fly.cancel();media.style.transform='';go(dir,true);
        var tr=travel('mid',220);
        if(enter)media.animate([{transform:'translateX('+(dir*48)+'px)',opacity:0},{transform:'none',opacity:1}],
          {duration:tr[0],easing:tr[1]});
      };
      after(fly,t,function(){if(flight)flight(true);});
      media.style.transform='translateX('+out+'px)';
    }else if(ok){media.style.transform='';go(dir,true);}
    else settle(media.style.transform);
  }else if(d.axis==='y'){
    if(d.dy>stage.clientHeight*.18||vy>.5){close();}
    else{
      settle(media.style.transform);
      bg.animate([{opacity:bg.style.opacity},{opacity:1}],{duration:200,easing:EASE});
      bg.style.opacity='';chrome.forEach(function(el){el.style.opacity='';});
    }
  }else if(media.style.transform)settle(media.style.transform);   /* caught, then let go */
  setTimeout(function(){moved=false;},0);
}
/* back to rest from wherever the photo is now */
function settle(from){
  media.style.transform='';
  if(from&&from!=='none'&&!reduce.matches)
    media.animate([{transform:from},{transform:'none'}],{duration:travel('mid',220)[0],easing:travel('mid',220)[1]});
}
stage.addEventListener('pointerup',release);
stage.addEventListener('pointercancel',function(e){
  if(drag&&e.pointerId===drag.id){drag=null;settle(media.style.transform);
    bg.style.opacity='';chrome.forEach(function(el){el.style.opacity='';});}
});
"""


def _springs():
    import json
    from .springs import SPRINGS
    return json.dumps({k: [settle, easing] for k, (_, settle, easing) in SPRINGS.items()},
                      separators=(",", ":"))


JS = JS.replace("var SPRING={},", "var SPRING=" + _springs() + ",", 1)

# His play mark on the poster: a dark disc with a white rim and triangle,
# the same drawing the viewer's play button uses at 76px.
_PLAY = ('<svg viewBox="0 0 76 76" aria-hidden="true"><circle cx="38" cy="38" r="37" '
         'fill="rgba(20,17,14,.5)" stroke="rgba(255,255,255,.85)" stroke-width="1.5"/>'
         '<path d="M31 25.5v25l20-12.5z" fill="#fff"/></svg>')

# The film's captions (it has sound: WCAG 1.2.2), keyed by its Wix media id:
# what can be heard, as a WebVTT file the viewer hands the player. Voices
# are faint in its first seconds; a speech recogniser makes out a few words
# there, not surely enough to publish as anyone's words, so the cue says
# only that they are there. Someone who listens can put the words in.
FILM_CAPTIONS = {
    "ce0a40_338c1c5cfd504efd8a5f1136c4e3eb88": (
        (0.0, 6.0, "[Faint voices]"),
        (6.0, 29.55, "[The truck grows louder as it comes up the track and passes]"),
    ),
}


def vtt(stream):
    """The WebVTT text for the film that plays from `stream`, or "" when the
    page holds no captions for it."""
    cues = next((c for k, c in FILM_CAPTIONS.items() if k in (stream or "")), ())
    if not cues:
        return ""

    def ts(s):
        return f"{int(s // 60):02d}:{s % 60:06.3f}"
    return "WEBVTT\n" + "".join(f"\n{ts(a)} --> {ts(b)}\n{text}\n" for a, b, text in cues)


PAIR_MAX = 3.0   # two photos share a phone row only while their proportions sum to this


def rows(ars, pair_max=PAIR_MAX):
    """A set's photos in phone rows: pairs in order, and a photo alone where
    it and its neighbour would be too wide together (their proportions summed
    above pair_max: at 390px that is a pair under 113px tall). Returns a list
    of lists of indices."""
    out, i = [], 0
    while i < len(ars):
        if i + 1 < len(ars) and ars[i] + ars[i + 1] <= pair_max:
            out.append([i, i + 1])
            i += 2
        else:
            out.append([i])
            i += 1
    return out


def _num(x):
    return f"{x:.4f}".rstrip("0").rstrip(".")


def _length(seconds):
    s = round(seconds or 0)
    return f"{s // 60}:{s % 60:02d}"


def render(sets):
    """The gallery's sets as HTML. `sets` is build.py's list: for each set his
    caption `lines` (the last is his "(during my ...)") and its `items`, each
    with `kind` ("photo" or "video"), `full`/`fw`/`fh` (the file the viewer
    shows), `thumb`/`tw`/`th` (the file the row shows), and for the video
    `stream` (where the film is fetched from, on play only) and `duration`."""
    out, eager = [], 2          # the first two photos are the page's first paint
    for k, s in enumerate(sets, 1):
        lines = s["lines"]
        era = lines[-1] if len(lines) > 1 and lines[-1].startswith("(") else ""
        title = " ".join(lines[:-1] if era else lines)
        head = (f'<h2 class="gset__h" id="gset-{k}"><span class="gset__t">'
                f'{html.escape(title, quote=False)}</span>'
                + (f' <span class="gset__era">{html.escape(era, quote=False)}</span>' if era else "")
                + '</h2>')
        items = s["items"]
        ars = [it["fw"] / it["fh"] for it in items]
        pair = {}
        for row in rows(ars):
            for j in row:
                pair[j] = (sum(ars[x] for x in row), len(row))
        photos = sum(1 for it in items if it["kind"] == "photo")
        lis, nth = [], 0
        for j, it in enumerate(items):
            load = 'loading="eager" fetchpriority="high"' if eager > 0 else 'loading="lazy"'
            eager -= 1
            img = (f'<img src="{it["thumb"]}" width="{it["tw"]}" height="{it["th"]}" alt="" '
                   f'{load} decoding="async">')
            style = (f'--ar:{_num(ars[j])};--pr:{_num(pair[j][0])};--pn:{pair[j][1]}')
            data = f'data-full="{it["full"]}" data-w="{it["fw"]}" data-h="{it["fh"]}"'
            if it["kind"] == "video":
                name = f"Play the video, {_length(it.get('duration'))}"
                cap = vtt(it["stream"])
                cap = f' data-vtt="{html.escape(cap)}"' if cap else ""
                lis.append(
                    f'<li class="gph gph--video" style="{style}"><a class="gph__a" '
                    f'href="{html.escape(it["stream"])}" {data} '
                    f'data-stream="{html.escape(it["stream"])}"{cap} aria-label="{name}">{img}'
                    f'<span class="gph__play">{_PLAY}</span>'
                    f'<span class="gph__len" aria-hidden="true">{_length(it.get("duration"))}'
                    f'</span></a></li>')
            else:
                nth += 1
                name = f"Photo {nth} of {photos}" if photos > 1 else "Photo"
                lis.append(
                    f'<li class="gph" style="{style}"><a class="gph__a" href="{it["full"]}" '
                    f'{data} aria-label="{name}, full size">{img}</a></li>')
        total = sum(ars)
        out.append(
            f'<section class="gset" aria-labelledby="gset-{k}">{head}'
            f'<ul class="gset__row" role="list" style="--r:{_num(total)};--n:{len(items)}">'
            f'{"".join(lis)}</ul></section>')
    return f'<div class="gal">{"".join(out)}</div>'
