# -*- coding: utf-8 -*-
"""motivation: his "Motivation for Creating the Educational Sections", restaged.

build.py hands render() his own block, PROF_MOTIVATION, and puts what comes
back in its place on the home page. The block goes out byte for byte inside
one <section class="motiv">: a --strict build looks for PROF_MOTIVATION
character for character on index.html, and his words then have one source
only. The presentation is all that changes. What this part adds (the wave's
frame, and the canvas the script makes) comes after his block, never inside
it; the numerals, the beads and the thread are the stylesheet's pseudo-
elements of his own <li>s. Every selector sits under .motiv and no :root
variable is written.

The section is a count-in to one line. His four points are the count (his
last paragraph names them "the 4 questions above"), and the line they land
on is "That final realization was my Aha! moment.", the largest type in the
block, with a wave under his "Aha!".

The four points are a progression, and since 29 Sep 2026 (the client: "do
nice things for the 1, 2, 3, 4 part") the page says so in the site's own
language, the column's Big Picture row and the Big Picture page: a hairline
through a bead for each point, and a thought that runs it.

  - Each numeral has a bead beside it, and the beads are joined by one
    thread in his order: across the row where the four stand in a row,
    down between the numerals and the words where they stand in a column.
    At rest that is the whole figure: four points on one line.
  - The first time the points are well in view the thread is drawn by a
    travelling point, in blue ink, and each bead wakes into a small dot orb
    as the thread reaches its numeral: the site's one orb, dots on a
    sphere as dense as the column's, turning, then settling back into its
    bead. So the count is told in order: one topic grasped (1), carried to
    where it is applied (2).
  - At 3, "How similar concepts reappear across different fields", the
    thought branches: an echo runs back along the thread and 2 and 1 wake
    again as it passes, while the thought goes on.
  - At 4, "How deeply interconnected they actually are", the echo reaches 1
    as the thought reaches 4: all four orbs are alive at once and the whole
    thread lights, one connected figure. That is the moment the wave under
    his "Aha!" draws itself, the line's last stroke, if its line is in view
    (else when it comes into view). Then everything rests, about 2s from
    the start, with nothing drawn on the canvas and no frame asked for.
  - A point under the pointer tells its own part again, briefly: 1 thinks,
    2 is reached from 1, 3 sends its echo back, 4 lights the whole thread.

Asked for less motion, with colours forced or without a canvas, none of the
motion exists: the thread and the beads stand as the stylesheet draws them
(the final state), and the wave is simply there (without a script there is
no wave, since the script lays it under the word). Colours are tokens: the
thread is --link let into the paper, the orbs, the thought and the wave are
--link, and the numerals keep the accent, which is text here, not motion.

The wave is an aria-hidden SVG after his block. The script lays it under the
word from a DOM Range over "Aha!" in his text, so his markup is only ever
read, in the file and in the live page alike, and places it again whenever
the column changes size and when the fonts arrive. The page is looked at on
scroll, once a frame at most, with no IntersectionObserver (parts/masthead.py
says why), and the listener goes once everything has played.

render() reads the block's shape first (html.parser). If it no longer holds
one list of points with a paragraph straight after it, the block ships
unstaged, as he wrote it, and the build log says so.
"""

from html.parser import HTMLParser

__all__ = ["CSS", "JS", "render"]

CSS = """
/* ============================== motivation ============================== */
/* The figure's colours, registered so a bead can fade as its orb takes over
   and the thread can fade in as the canvas hands it over. The thread at rest
   is --link let into the paper at 34%, mixed in sRGB: the canvas draws the
   same colour as --link at that alpha over the paper, so the hand-over from
   the drawn thread to the stylesheet's is seamless. */
@property --mv-b{syntax:"<color>";inherits:false;initial-value:transparent}
@property --mv-r{syntax:"<color>";inherits:false;initial-value:transparent}
.motiv{position:relative;--mv-line:color-mix(in srgb,var(--link) 34%,var(--page))}

/* His .col is the query container. It widens to the full content width so
   the four points can take the whole row; his paragraphs keep the reading
   measure. Containment keeps a child's margin inside the column, so the
   last paragraph gives up its 1.15em and the next h2's 47px stands alone. */
.motiv .col{max-width:none;container:motiv/inline-size}
.motiv .col>p{max-width:var(--measure)}
.motiv .col>:last-child{margin-bottom:0}
/* what he typed into his last paragraph and asked to be bold (27 Sep 2026):
   the serif's 600 in the ink, as the About page sets his bold runs */
.motiv strong{font-weight:600;color:var(--ink)}

/* The points, in a column (below 900px of column): each numeral hangs
   beside its point on the baseline of the point's first line, its bead
   between the two, and the thread runs down from bead to bead. --n is the
   numerals' size, --g the gutter the bead sits in, --gap the air between
   points. An empty-string marker rather than none: Safari drops list
   semantics for list-style:none, and keeps them for "" and for ::before
   content, which the numerals are. His words are at the reading size, in
   the ink. */
.motiv ul{--n:30px;--g:26px;--gap:20px;list-style-type:"";counter-reset:motiv;
  display:grid;row-gap:var(--gap);max-width:var(--measure);margin:28px 0 0;padding:0}
.motiv li{counter-increment:motiv;position:relative;display:grid;
  grid-template-columns:calc(var(--n) * .5) minmax(0,1fr);column-gap:var(--g);
  align-items:baseline;margin:0;padding:0;font:400 19px/1.45 var(--serif);color:var(--ink);
  text-wrap:balance}
/* the numerals: the serif at display size, in the accent (5.28:1 on the
   page), lining and tabular, so the four stand one width apiece (0.482em
   in Source Serif 4), a steady count */
.motiv li::before{content:counter(motiv);font:400 var(--n)/1 var(--serif);
  font-variant-numeric:lining-nums tabular-nums;letter-spacing:0;color:var(--accent)}
/* The bead and the thread from it to the next bead: one box, a 7px ring
   (1px, as the column's beads) and a 1px line. The ring's centre is the
   numeral's cap middle: in a line box of line-height 1 the serif's
   baseline stands .8505em down (ascent 1.036em, descent .335em) and its
   capitals are .67em tall, so the middle is .5155em down. Down the column
   the box reaches from this bead to the next (its point's height and the
   gap); the last point's is the bead alone. */
.motiv li::after{content:"";position:absolute;pointer-events:none;
  left:calc(var(--n) * .5 + var(--g) / 2 - 3.5px);top:calc(var(--n) * .5155 - 3.5px);
  width:7px;height:calc(100% + var(--gap));
  --mv-b:var(--mv-line);--mv-r:var(--mv-line);
  background:radial-gradient(circle at 3.5px 3.5px,transparent 2.35px,var(--mv-b) 2.6px 3.15px,
      transparent 3.45px) 0 0/7px 7px no-repeat,
    linear-gradient(var(--mv-r),var(--mv-r)) 3px 7px/1px calc(100% - 7px) no-repeat;
  transition:--mv-b var(--t-quick) var(--ease-state),--mv-r var(--t-fast) var(--ease-state)}
.motiv li:last-child::after{height:7px}
/* while a bead is an orb its ring gives way to the dots: the script marks
   the section (.o1 for the first point's, and so on), never his <li>s */
/*ORBS*/
/* Where the script will draw the thread (html.js, motion welcome), it is
   not drawn before the travelling point draws it: the beads stand alone
   until then. .motiv--done hands it back: the script sets it the moment
   the thread is whole, and at once wherever it will not play. */
@media (prefers-reduced-motion:no-preference){
  .js .motiv:not(.motiv--done) li::after{--mv-r:transparent}
}

/* That final realization was my "Aha!" moment: the line the count lands on,
   a statement in the serif, 28px on a phone, 3vw between, 38px from a
   1267px window up, where it holds one line across the column. More air
   above it than below: it closes the count, and the goal paragraph follows
   on from it. The wave hangs 0.2em under its baseline, inside the line's
   own box, so the margin under it is all air. */
.motiv .col>ul+p{max-width:none;margin:44px 0 26px;
  font:400 clamp(28px,3vw,38px)/1.2 var(--serif);letter-spacing:-.01em;color:var(--ink);
  text-wrap:balance}

/* From 520px of column the numerals grow and the gutter with them. */
@container motiv (min-width:520px){
  .motiv ul{--n:34px;--g:30px;--gap:22px;margin-top:32px}
  .motiv .col>ul+p{margin:56px 0 30px}
}

/* One row of four from 900px: the count reads left to right, straight into
   the line under it. Each column is as wide as its point is long, 1.9, 1.3,
   1 and 1, so the four end together (four lines, four, four and three at
   the full 924px); the narrowest still holds "interconnected" with room to
   spare. Each numeral stands over its point, trimmed to its cap height
   (text-box), and its bead follows it, 9px after the figure's advance, on
   the cap middle. The thread runs from each bead across the gap to 10px
   short of the next numeral, so the four numerals are its stations. */
@container motiv (min-width:900px){
  .motiv ul{--n:44px;grid-template-columns:minmax(0,1.9fr) minmax(0,1.3fr) minmax(0,1fr) minmax(0,1fr);
    column-gap:40px;row-gap:0;max-width:none;margin-top:40px}
  .motiv li{display:block}
  .motiv li::before{display:block;margin-bottom:16px;text-box:trim-both cap alphabetic}
  .motiv li::after{left:calc(var(--n) * .482 + 9px);width:calc(100% + 21px - var(--n) * .482);
    height:7px;background-size:7px 7px,calc(100% - 7px) 1px;background-position:0 0,7px 3px}
  .motiv li:last-child::after{width:7px}
  .motiv .col>ul+p{margin:60px 0 32px}
}
/* trimmed, the numeral's box is its capitals, so their middle is .335em */
@supports (text-box:trim-both cap alphabetic){
  @container motiv (min-width:900px){
    .motiv li::after{top:calc(var(--n) * .335 - 3.5px)}
  }
}

/* The orbs, the thought and its echo: one canvas over the points, made by
   the script only where motion is welcome and colours are not forced. It
   takes no pointer, so his words stay selectable under it, and it holds no
   pixels at rest. */
.motiv__orbs{position:absolute;left:0;top:0;pointer-events:none}

/* The wave under his "Aha!": an ornament the script lays under the word and
   draws, in --link, 1.5px. Until the script has placed it, it is not drawn
   at all. */
.motiv__wave{position:absolute;top:0;left:0;display:none;overflow:visible;
  pointer-events:none;color:var(--link)}
.motiv--wave .motiv__wave{display:block}
/* the draw, once: the line starts fast and settles into the "!", a strong
   ease-out over 700ms. Before it plays the wave is held unseen (a dash
   pushed off the path's start, and hidden, since a round cap would still
   print a dot there). Added here, never clawed back: asked for less motion,
   none of this applies and the wave is drawn from the start. */
@media (prefers-reduced-motion:no-preference){
  .motiv__wave{opacity:0}
  .motiv__wave path{stroke-dasharray:1 2;stroke-dashoffset:1}
  .motiv--drawn .motiv__wave{opacity:1}
  .motiv--drawn .motiv__wave path{stroke-dashoffset:0;
    transition:stroke-dashoffset 700ms cubic-bezier(.16,1,.3,1)}
}
/* Windows contrast themes and paper: the figure is ornament, the words stay */
@media (forced-colors:active){.motiv__wave,.motiv__orbs{display:none!important}}
@media print{.motiv__wave,.motiv__orbs{display:none!important}}
"""

# A bead gives way to its orb: one rule for each place in the list, twice the
# four points his block holds today.
CSS = CSS.replace("/*ORBS*/\n", ",".join(
    f".motiv.o{k} li:nth-child({k})::after" for k in range(1, 9)) + "{--mv-b:transparent}\n")

JS = r"""
/* His motivation (parts/motivation.py). His paragraph and his points are
   only read: the wave is laid under "Aha!" from a DOM Range, and the orbs
   are drawn on a canvas at the beads the stylesheet puts beside his
   numerals. build.py wraps every part's script in its own function scope. */
var sec=document.querySelector('.motiv');
if(!sec)return;
var col=sec.querySelector('.col'),list=col&&col.querySelector('ul'),
    pts=list?[].slice.call(list.children):[],n=pts.length,
    line=sec.querySelector('.col>ul+p'),svg=sec.querySelector('.motiv__wave'),
    path=svg&&svg.querySelector('path'),
    calm=matchMedia('(prefers-reduced-motion: reduce)'),
    fine=matchMedia('(hover: hover) and (pointer: fine)'),
    fonts=document.fonts,ready=!fonts||fonts.status==='loaded',
    word=null,waved=calm.matches,due=0,wdirty=1,lk=0,listening=0;

/* ---- the wave. The box a Range gives is the font's ascent over its
   descent, 1.036em over 0.335em for Source Serif 4 and for the Georgia
   theme.py sizes to stand in for it, so the baseline is 0.335em over the
   box's foot, and the wave's axis runs 0.2em under the baseline, clear of
   "Aha!", which has no descender. It spans the word, two periods starting
   upward, its swell growing from 55% to the full 0.085em under the "!". */
if(line&&path&&document.createRange&&document.createTreeWalker){
  var walk=document.createTreeWalker(line,4),node,at=-1;
  while((node=walk.nextNode())&&(at=node.data.indexOf('Aha!'))<0){}
  if(node){word=document.createRange();word.setStart(node,at);word.setEnd(node,at+4)}
}
function wave(){
  if(!word)return;
  var r=word.getBoundingClientRect(),s=sec.getBoundingClientRect();
  if(!r.width)return;
  var fs=parseFloat(getComputedStyle(line).fontSize),a=.085*fs,h=Math.ceil(2*a+4),
      w=Math.round(r.width),d='',k,t;
  for(k=0;k<=64;k++){
    t=k/64;
    d+=(k?'L':'M')+(t*w).toFixed(2)+' '+(h/2-a*(.55+.45*t)*Math.sin(t*4*Math.PI)).toFixed(2);
  }
  path.setAttribute('d',d);
  svg.setAttribute('width',w);svg.setAttribute('height',h);
  svg.setAttribute('viewBox','0 0 '+w+' '+h);
  svg.style.transform='translate('+(r.left-s.left).toFixed(2)+'px,'+
    (r.bottom-s.top-.135*fs-h/2).toFixed(2)+'px)';
  sec.classList.add('motiv--wave');
}
function drawWave(){
  if(waved)return;
  if(wdirty){wdirty=0;wave()}
  waved=1;sec.classList.add('motiv--drawn');
}

/* ---- the figure. One canvas over the points, sized to them (and 14px
   around, where an orb reaches past its bead), at the device's ratio, 2 at
   most, and emptied at rest. An orb is bpnav.py's: dots on a sphere (a
   Fibonacci lattice, as dense as its 48 on 6.5px), turning about an axis
   tilted 22 degrees toward the reader, each dot darker and larger the
   nearer it is; its life is one number e on a critically damped spring, 0
   the still bead and 1 the thinking orb, and it turns as e cubed, so it
   spins up and down to a stop.
   A traveller (the thought, or its echo) runs the thread on one axis, x
   across the row or y down the column, eased in and out. */
var fig=0,cv=null,g=null,dpr=1,PAD=14,OX=0,OY=0,CW=0,CH=0,vert=0,R1=7,
    BX=[],BY=[],RS=[],RE=[],AF=[],AB=[],
    NS=48,SX=[],SY=[],SZ=[],
    E=[],EV=[],ET=[],EW=[],EH=[],AN=[],OC=[],last=[],
    INK='',M=null,Q=null,FL=0,FT=0,
    raf=0,t0=0,played=0,intro=0,timer=0,dirty=1,
    WAKE=2*Math.PI/.26,REST=2*Math.PI/.6,SPIN=2*Math.PI/1.9,HOLD=320,
    TM=1200,FLASH=700;

function figOn(){
  if(calm.matches||n<2||matchMedia('(forced-colors: active)').matches)return;
  cv=document.createElement('canvas');
  g=cv.getContext&&cv.getContext('2d');
  if(!g){cv=null;return}
  cv.className='motiv__orbs';cv.setAttribute('aria-hidden','true');cv.style.display='none';
  cv.width=cv.height=0;             /* no pixels until the first play */
  sec.appendChild(cv);
  for(var i=0;i<n;i++){E[i]=EV[i]=ET[i]=EH[i]=OC[i]=0;EW[i]=WAKE;AN[i]=i*1.9;last[i]=-1e4}
  fig=1;
}
/* where the beads are, read from the stylesheet's boxes: once a play, and
   again after a resize or the fonts' arrival, never in a frame. The canvas
   stands on whole device pixels, so its 1px lines are as crisp as the
   stylesheet's. RS..RE is the stretch of thread each bead starts; AF is
   where the thought reaches a point going on (the thread's end at its
   numeral, or its bead), AB where the echo reaches it coming back. */
function measure(){
  var s=sec.getBoundingClientRect(),u=list.getBoundingClientRect(),i,r=[],c,x,y,cx,cy;
  dpr=Math.min(2,window.devicePixelRatio||1);
  for(i=0;i<n;i++)r[i]=pts[i].getBoundingClientRect();
  vert=r[1].top-r[0].top>r[1].left-r[0].left;
  cx=Math.round((u.left-PAD)*dpr)/dpr;cy=Math.round((u.top-PAD)*dpr)/dpr;
  OX=cx-s.left;OY=cy-s.top;
  CW=Math.ceil(u.right+PAD-cx);CH=Math.ceil(u.bottom+PAD-cy);
  for(i=0;i<n;i++){
    c=getComputedStyle(pts[i],'::after');
    x=r[i].left-cx+(parseFloat(c.left)||0);y=r[i].top-cy+(parseFloat(c.top)||0);
    BX[i]=x+3.5;BY[i]=y+3.5;
    if(vert){RS[i]=y+7;RE[i]=y+(parseFloat(c.height)||7)}
    else{RS[i]=x+7;RE[i]=x+(parseFloat(c.width)||7)}
  }
  for(i=0;i<n;i++){
    AF[i]=vert?(i?BY[i]-3.5:BY[0]):(i?RE[i-1]:BX[0]);
    AB[i]=vert?BY[i]+3.5:BX[i]+3.5;
  }
  /* an orb about two thirds of its numeral's capitals across; in a column
     it has the bead's gutter to itself, 26 to 30px, so a little more */
  R1=Math.max(6,(parseFloat(getComputedStyle(pts[0],'::before').fontSize)||30)*(vert?.235:.21));
  lattice(Math.max(48,Math.min(110,Math.round(48*R1*R1/42.25))));
  dirty=0;
}
/* the dots, laid evenly on a sphere: the column's orb has 48 on a radius of
   6.5px, and a larger orb keeps its density, so it is the same orb */
function lattice(m){
  if(m===NS&&SX.length)return;
  NS=m;SX.length=SY.length=SZ.length=0;
  for(var i=0;i<NS;i++){
    var y=1-2*(i+.5)/NS,r=Math.sqrt(1-y*y),t=i*2.399963;
    SX[i]=Math.cos(t)*r;SY[i]=y;SZ[i]=Math.sin(t)*r;
  }
}
function size(){
  var w=Math.round(CW*dpr),h=Math.round(CH*dpr);
  if(cv.width!==w||cv.height!==h){cv.width=w;cv.height=h}
  cv.style.width=CW+'px';cv.style.height=CH+'px';
  cv.style.transform='translate('+OX.toFixed(3)+'px,'+OY.toFixed(3)+'px)';
  cv.style.display='';
}
/* the blue, as the wave's own colour resolves it (--link) */
function tokens(){INK=getComputedStyle(svg||sec).color}
function kick(){if(!raf)raf=requestAnimationFrame(frame)}

/* a traveller from a to b on the thread's axis, d ms, waking each point it
   reaches to lv; end() is called as it arrives, woke(k) as it reaches k */
function trip(a,b,d,lv){return {a:a,b:b,d:d,lv:lv,t:-1,p:a,w:0,out:0,end:null,woke:null}}
/* easing in and out over a at each end, even between (bpnav.py's glide) */
function glide(u,a){var k=1/(1-a);return u<a?k*u*u/(2*a):u>1-a?1-k*(1-u)*(1-u)/(2*a):k*(u-a/2)}
function step(T,now){
  if(T.t<0)T.t=now;
  var u=(now-T.t)/T.d,up=T.b>T.a,k;
  if(u>=1)u=1;
  T.p=T.a+(T.b-T.a)*glide(u,.22);
  for(k=0;k<n;k++){
    if(T.w>>k&1)continue;
    /* only the points between where it set out and where it goes */
    if(up?AF[k]>=T.a-.01&&T.p>=AF[k]-.01:AB[k]<=T.a+4&&T.p<=AB[k]+.01){
      T.w|=1<<k;wake(k,now,T.lv);if(T.woke)T.woke(k,now);
    }
  }
  if(u>=1&&!T.out){T.out=now;if(T.end)T.end(now)}
}
/* behind a numeral, across the row, the thought is out of sight */
function hid(p){
  if(vert)return 0;
  for(var k=1;k<n;k++)if(p>RE[k-1]+.5&&p<BX[k]-4)return 1;
  return 0;
}
/* an orb wakes to lv (never lower than it stands), and holds a moment */
function wake(k,now,lv){
  if(!(ET[k]>=lv)){ET[k]=lv;EW[k]=WAKE}
  EH[k]=Math.max(EH[k],now+HOLD);
  bead(k,1);
}
function bead(k,on){if(OC[k]!==on){OC[k]=on;sec.classList.toggle('o'+(k+1),!!on)}}

/* The count, told once: the thought draws the thread from 1 to 4 in 1.2s;
   reaching 3 it sends its echo back to 1, timed to arrive as it reaches 4;
   then the whole figure lights and the wave under "Aha!" is drawn. */
function play(){
  if(played||!fig)return;
  played=intro=1;
  if(dirty)measure();
  tokens();size();
  M=trip(vert?BY[0]:BX[0],vert?BY[n-1]:BX[n-1],TM,1);
  M.woke=function(k,now){
    if(k===n-2&&n>2){
      Q=trip(vert?BY[k]:BX[k],vert?BY[0]:BX[0],Math.max(160,M.t+M.d-now),.72);
      Q.w=1<<k;
    }
  };
  M.end=link;
  kick();
}
/* one connected figure: every orb awake together, the whole thread lit */
function link(now){
  for(var k=0;k<n;k++){ET[k]=1;EW[k]=WAKE;EH[k]=Math.max(EH[k],now+HOLD);bead(k,1)}
  FL=1;FT=now;
  sec.classList.add('motiv--done');
  if(!waved){due=1;soon()}
}
/* A point under the pointer tells its part again: 1 thinks; 2 is reached
   from 1; 3 sends its echo back to 1; 4 lights the whole figure. */
function replay(k){
  if(!fig||intro||document.hidden||k<0)return;
  var now=performance.now();
  if(now-last[k]<900)return;
  last[k]=now;
  if(dirty)measure();
  tokens();size();
  M=Q=null;
  if(k===0)wake(0,now,1);
  else if(k===n-1)link(now);
  else if(k===n-2){wake(k,now,1);Q=trip(vert?BY[k]:BX[k],vert?BY[0]:BX[0],520,.72);Q.w=1<<k}
  else M=trip(vert?BY[k-1]:BX[k-1],vert?BY[k]:BX[k],480,1);
  kick();
}
/* everything to its final state at once: off screen, a hidden tab, a
   resize in the middle of a play */
function hush(){
  if(!fig)return;
  M=Q=null;FL=0;
  for(var k=0;k<n;k++){E[k]=ET[k]=EV[k]=EH[k]=0;bead(k,0)}
  if(raf){cancelAnimationFrame(raf);raf=0}
  sec.classList.add('motiv--done');
  if(!waved)due=1;
  rest();
}
function rest(){
  t0=0;intro=0;
  if(cv){cv.width=cv.height=0;cv.style.display='none'}
}

function frame(now){
  raf=0;
  var dt=t0?Math.min(.05,(now-t0)/1e3):1/60,busy=0,k,d,c,x,w;
  t0=now;
  if(M){step(M,now);if(M.out&&now-M.out>200)M=null;else busy=1}
  if(Q){step(Q,now);if(Q.out&&now-Q.out>200)Q=null;else busy=1}
  if(FL>0){FL=Math.max(0,1-(now-FT)/FLASH);busy=1}
  for(k=0;k<n;k++){
    if(ET[k]>0&&EH[k]&&now>=EH[k]){ET[k]=0;EW[k]=REST;EH[k]=0}
    d=E[k]-ET[k];
    if(d||EV[k]){
      w=EW[k];c=EV[k]+w*d;x=Math.exp(-w*dt);E[k]=ET[k]+(d+c*dt)*x;EV[k]=(EV[k]-w*c*dt)*x;
      if(Math.abs(E[k]-ET[k])<.01&&Math.abs(EV[k])<.05){E[k]=ET[k];EV[k]=0}
      busy=1;
    }
    if(ET[k]>0)busy=1;
    if(OC[k]&&!ET[k]&&E[k]<.45)bead(k,0);
    AN[k]+=dt*SPIN*E[k]*E[k]*E[k];
  }
  if(busy){paint(now);raf=requestAnimationFrame(frame)}
  else rest();
}
function paint(now){
  var k;
  g.setTransform(1,0,0,1,0,0);g.clearRect(0,0,cv.width,cv.height);
  g.setTransform(dpr,0,0,dpr,0,0);
  g.fillStyle=INK;
  /* the thread as the thought draws it, until the stylesheet has it */
  if(M&&intro&&!sec.classList.contains('motiv--done'))runs(M.p,.34);
  if(FL>0)runs(1e5,.8*FL*FL);
  if(M)thought(M,now,1);
  if(Q)thought(Q,now,.8);
  for(k=0;k<n;k++)if(E[k]>0)orb(BX[k],BY[k],E[k],AN[k],!ET[k]);
  g.globalAlpha=1;
}
/* the thread's stretches, as far as p along its axis, at alpha al; each
   line is a CSS pixel on whole device pixels, as the stylesheet draws it */
function runs(p,al){
  g.globalAlpha=al;
  for(var k=0;k<n-1;k++){
    var a=RS[k],b=Math.min(RE[k],p);
    if(b<=a)continue;
    if(vert)g.fillRect(Math.round((BX[k]-.5)*dpr)/dpr,a,1,b-a);
    else g.fillRect(a,Math.round((BY[k]-.5)*dpr)/dpr,b-a,1);
  }
}
/* a traveller: a point of the blue in a soft glow, with 40px of lit
   thread behind it, faded in over 120ms and out over 200ms as it arrives */
function thought(T,now,lv){
  var a=(T.out?Math.max(0,1-(now-T.out)/200):Math.min(1,(now-T.t)/120))*lv,
      up=T.b>T.a?1:-1,k,p,q,x,y;
  if(a<=0)return;
  for(k=0;k<8;k++){
    p=T.p-up*5*k;q=T.p-up*5*(k+1);
    if(up>0?p<=T.a:p>=T.a)break;
    if(up>0?q<T.a:q>T.a)q=T.a;
    if(hid(p)||hid(q))continue;
    g.globalAlpha=a*(1-k/8)*.7;
    if(vert)g.fillRect(Math.round((BX[0]-.5)*dpr)/dpr,Math.min(p,q),1,Math.abs(p-q));
    else g.fillRect(Math.min(p,q),Math.round((BY[0]-.5)*dpr)/dpr,Math.abs(p-q),1);
  }
  if(hid(T.p))return;
  x=vert?BX[0]:T.p;y=vert?T.p:BY[0];
  g.globalAlpha=a*.12;g.beginPath();g.arc(x,y,4.5,0,6.2832);g.fill();
  g.globalAlpha=a*.3;g.beginPath();g.arc(x,y,2.7,0,6.2832);g.fill();
  g.globalAlpha=a;g.beginPath();g.arc(x,y,1.6,0,6.2832);g.fill();
}
/* an orb: it grows out of its bead's ring (radius 3) to R1, its dots on a
   sphere turned by a and tilted toward the reader. Settling, it fades as
   it shrinks, faster than it grew, and the ring (back from e .45) is what
   is left: it collapses into its bead rather than dimming into a spot. */
function orb(x,y,e,a,down){
  var s=e*e*(3-2*e),r=3+(R1-3)*s,f=down?s*s:s,ca=Math.cos(a),sa=Math.sin(a),i,px,pz,py,z,t;
  for(i=0;i<NS;i++){
    px=SX[i]*ca+SZ[i]*sa;pz=SZ[i]*ca-SX[i]*sa;
    py=SY[i]*.93-pz*.37;z=SY[i]*.37+pz*.93;
    t=(z+1)/2;
    g.globalAlpha=f*(.12+.88*t*t);
    g.beginPath();g.arc(x+px*r,y+py*r,.3+.42*t,0,6.2832);g.fill();
  }
}

/* ---- looking, once a frame at most, on scroll: the count plays when the
   points are well in view (all of them with their foot above 84% of the
   window, so on a wide screen the line they land on is in view as they
   land; or, where they stand taller, as a phone's column does, their top
   in the upper 40%), and goes quiet off screen; the wave draws when it is
   due and its line is in view. Nothing is looked at before the fonts are
   in. */
function look(){
  lk=0;
  if(wdirty){wdirty=0;wave()}
  if(!ready)return;
  var vh=innerHeight,r;
  if(fig&&!played&&list){
    r=list.getBoundingClientRect();
    if(r.bottom>0&&r.top<vh*.8&&(r.bottom<=vh*.84||r.top<vh*.4))play();
  }
  if(raf&&list){r=list.getBoundingClientRect();if(r.bottom<=0||r.top>=vh)hush()}
  if(due&&!waved&&line){r=line.getBoundingClientRect();if(r.top<vh*.88&&r.bottom>0)drawWave()}
  if(listening&&(played||!fig)&&waved&&!raf){listening=0;removeEventListener('scroll',soon)}
}
function soon(){if(!lk)lk=requestAnimationFrame(look)}
/* the column changed size (a window resize, the side column folding away, a
   container query turning the points): the figure measures again at its
   next play, and one in the middle of playing goes to its end at once. A
   phone's address bar changes the window, not the column, so it is not
   one of these. The fonts arriving only move the wave. */
function moved(){wdirty=dirty=1;if(raf)hush();soon()}
function fontsIn(){wdirty=dirty=1;soon()}
function loaded(){if(!ready){ready=1;fontsIn()}}

figOn();
if(!fig){sec.classList.add('motiv--done');due=1}
if(fig){
  pts.forEach(function(li,k){
    li.addEventListener('pointerenter',function(e){
      if(e.pointerType!=='mouse'||!fine.matches)return;
      clearTimeout(timer);timer=setTimeout(function(){timer=0;replay(k)},140);
    });
    li.addEventListener('pointerleave',function(){clearTimeout(timer);timer=0});
  });
  /* a point that holds something focusable tells its part as a key reaches it */
  list.addEventListener('focusin',function(e){
    var t=e.target,li=t.closest&&t.closest('.motiv li');
    if(li&&t.matches&&t.matches(':focus-visible'))replay(pts.indexOf(li));
  });
  document.addEventListener('visibilitychange',function(){if(document.hidden&&raf)hush()});
  addEventListener('pagehide',function(){if(raf)hush()});
  if(calm.addEventListener)calm.addEventListener('change',function(){
    if(!calm.matches||!fig)return;
    hush();fig=0;sec.removeChild(cv);cv=null;
  });
}
var cw=-1;
if(window.ResizeObserver&&col)new ResizeObserver(function(es){
  var w=es[0].contentRect.width;
  if(w!==cw){cw=w;moved()}else fontsIn();
}).observe(col);
else addEventListener('resize',moved);
if(fonts){
  if(!ready){fonts.ready.then(loaded);setTimeout(loaded,3000)}
  if(fonts.addEventListener)fonts.addEventListener('loadingdone',fontsIn);
}
if(!waved||fig){listening=1;addEventListener('scroll',soon,{passive:true})}
soon();
"""

# The wave's frame. The script writes its size and its path; until then it
# is not drawn (.motiv__wave is display:none until .motiv--wave).
_WAVE = ('<svg class="motiv__wave" aria-hidden="true" focusable="false" fill="none" '
         'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
         'stroke-linejoin="round"><path pathLength="1"/></svg>')

_VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())


class _Shape(HTMLParser):
    """Every start tag of the block with its depth, in document order."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((self.depth, tag))
        if tag not in _VOID:
            self.depth += 1

    def handle_endtag(self, tag):
        if tag not in _VOID:
            self.depth -= 1

    def fits(self):
        """One h2, one <ul> of two or more <li> and nothing else, a <p> after it."""
        names = [t for _, t in self.tags]
        if self.depth or names.count("h2") != 1 or names.count("ul") != 1:
            return False
        at = names.index("ul")
        d = self.tags[at][0]
        kids, after = [], None
        for depth, tag in self.tags[at + 1:]:
            if depth <= d:
                after = (depth, tag)
                break
            if depth == d + 1:
                kids.append(tag)
        return len(kids) >= 2 and set(kids) == {"li"} and after == (d, "p")


def render(prof_html):
    """His motivation block, staged. His words and his markup ship untouched;
    the wave's frame follows them, inside the section."""
    shape = _Shape()
    shape.feed(prof_html)
    shape.close()
    if not shape.fits():
        print("  !! parts/motivation.py: PROF_MOTIVATION no longer holds one list with a "
              "paragraph after it; shipped as he wrote it, unstaged")
        return prof_html
    return f'<section class="motiv">{prof_html}{_WAVE}</section>\n'
