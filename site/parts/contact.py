# -*- coding: utf-8 -*-
"""contact: the Contact page (contact.html).

The page is a register, the way a letterhead or a university directory sets
a person's particulars: one row for each thing a reader needs, a key in the
interface's sans on the left and the particulars in his serif on the right,
a hairline between the rows, all in the lede's measure. The order is the
order of need, and the groups are the ones his first Contact page had:
Email; Where to find me; Elsewhere (his CV and his profiles). Round 10's
navy card, its pulse-echo channel and its filled button are gone (27 Sep
2026: the professor found the blue area unprofessional, and his rule is
that the reader grasps at once, without confusion, how to reach him).

Email holds his two addresses, both first-class (29 Sep 2026: at his word,
his personal address is public for contact beside his institute's). Each is
named over it in the brief's eyebrow, Institutional or Personal, so the
reader knows at once which is which; each is his serif at up to 28px in the
site's link blue, underlined in a hairline of itself, and writes to him; and
each has its own control under it on the same edge, the brief's ghost
button (DESIGN_BRIEF 4, 6), which copies it. The institute's comes first.

Where to find me: his department and his institute, each linked to its own
site, the city, and the local time in Izmir now (Intl, Europe/Istanbul, with
its offset from UTC). The time line is kept from the first paint and filled
by the script, so it never moves the page; without a script it is not drawn.

Motion clarifies and nothing plays on its own. A copy is answered where it
happened, the way Motion's copy button answers it: the button gives a little
under the finger; the copy glyph goes small through a 2px blur as a check
draws itself in its place; "Copy" crosses to "Copied" through the same blur
while the face slides the few pixels that centre it; and the wash the site
selects text with sweeps across the address it took, left to right, as a
selection is made, and lets it go. Two seconds on, it settles back. The
clipboard holds one address, so copying one settles the other at once.
Under reduced motion nothing travels: the faces, the check and the light
swap by opacity alone. Under the pointer the profile arrows draw as the
site's arrows do.

Copy: without JavaScript the buttons are not drawn (@media (scripting:none)),
so the page is the addresses and their mail links; with it they are laid out
from the first paint. A button uses the async clipboard where the page is a
secure context and falls back to execCommand on a selection of its address;
if both fail that address is left selected for the keyboard. A visually
hidden polite live line says which address was copied. Each button's
accessible name, "Copy institutional address" or "Copy personal address",
holds its visible "Copy" and stays the same throughout.

Serif is his voice, sans is the interface's. Every colour is a theme.py
token or a color-mix of one; no :root property is written. Selectors are
scoped under .contact.
"""

import html as _html
from urllib.parse import urlsplit

__all__ = ["CSS", "JS", "render"]

CSS = """
/* =============================== contact =============================== */
.contact{container:contact/inline-size}
.contact>.lede{margin-bottom:0}

/* ---------------------------------------------------------- the register */
/* It keeps the lede's measure (608px), so the page is one column of type
   and every rule ends where the lede does. The key column is 136px and
   32px from the values, which leaves them 440px: the wider address at
   28px is 367px of it. On a phone each key stands over its values, on the
   page's one edge. */
.contact__reg{max-width:var(--measure);margin-top:48px}
.contact__row{display:grid;grid-template-columns:136px minmax(0,1fr);column-gap:32px;
  align-items:baseline;padding:28px 0;border-top:1px solid var(--rule)}
/* the keys name each row without calling over it: the interface's sans at
   a control label's size, in --muted (5.10:1) */
.contact__key{margin:0;font:600 15px/1.4 var(--sans);letter-spacing:.01em;color:var(--muted)}
.contact__val{display:grid;justify-items:start;min-width:0}
@container contact (width < 560px){
  .contact__reg{margin-top:40px}
  .contact__row{grid-template-columns:minmax(0,1fr);row-gap:10px;padding:24px 0}
}

/* ---------------------------------------------------------- the addresses */
/* His two addresses, one entry each: what it is, the address, and its
   control on the same edge. 10px and 14px inside an entry, 32px between
   the two, so each control reads with its own address. */
.contact__mails{display:grid;row-gap:32px;min-width:0;margin:0;padding:0;list-style:none}
.contact__mail{display:grid;justify-items:start;min-width:0;margin:0}
/* what it is, in the brief's eyebrow (sans 600, 12px, caps, --muted 5.10:1),
   on the key's baseline, so "Email" and the first kind read as one line */
.contact__kind{margin:0 0 10px;font:600 12px/1.1 var(--sans);letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted)}
/* The two large lines and the page's links in colour: his serif at 500, up
   to 28px, so the pair stays under the 40px title, in the site's link blue
   (6.89:1 on the page), because blue is where a reader can go and this is
   where the page sends them. The wider, his personal one, is 13.11em
   (measured; his institute's is 12.66em), so at 7.2cqi it fills 94% of
   the column, and at the 20px floor it keeps one line from 262px up. */
.contact__addr{position:relative;isolation:isolate;margin:0;
  font:500 clamp(20px,7.2cqi,28px)/1.2 var(--serif);letter-spacing:-.01em;color:var(--ink);
  font-variant-numeric:lining-nums;overflow-wrap:anywhere}
.contact__addr a{color:var(--link);text-decoration-thickness:1px;text-underline-offset:.18em;
  text-decoration-color:color-mix(in oklab,currentColor,transparent 70%)}
@media (hover:hover){.contact__addr a:hover{text-decoration-color:currentColor}}
.contact__addr a:focus-visible{outline:2px solid var(--focus);outline-offset:4px;
  border-radius:2px;text-decoration-color:currentColor}
/* what a copy took: the address lights in the wash the site selects text
   with and lets it go. Here by opacity alone; the sweep is motion's, below */
.contact__addr::before{content:"";position:absolute;inset:-2px -8px;z-index:-1;
  border-radius:var(--r-sm);background:var(--wash);opacity:0;pointer-events:none;
  transition:opacity var(--t-slow) var(--ease-state)}
.contact__addr.is-copied::before{opacity:1;transition-duration:var(--t-fast)}

/* Copy: the brief's ghost button, one under each address. Its outline is
   the only border here that is an affordance (--line-strong, 3.49:1); the
   ring around it widens the target to 46px. Without a script it could do
   nothing, so it is not drawn. */
.contact__copy{position:relative;display:inline-flex;align-items:center;
  min-height:40px;margin:14px 0 0;padding:0 14px;border:1px solid var(--line-strong);
  border-radius:var(--r-pill);background:transparent;color:var(--ink);
  font:600 15px/1.2 var(--sans);letter-spacing:.01em;cursor:pointer;
  -webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-fast) var(--ease-state),
    border-color var(--t-fast) var(--ease-state)}
.contact__copy::after{content:"";position:absolute;inset:-3px -1px}
.contact__copy svg{flex:none;display:block;overflow:visible}
@media (scripting:none){.contact__copy{display:none}}
@media (hover:hover){.contact__copy:hover{background:var(--card);border-color:var(--ink)}}
/* pressed: one step deeper at once (and, where motion is welcome, it gives
   a little under the finger) */
.contact__copy:active{background:var(--rule);border-color:var(--ink);transition-duration:0s}
.contact__copy:focus-visible{outline:2px solid var(--focus);outline-offset:2px;
  background:var(--card);border-color:var(--ink);transition:none}
/* Its face: the glyph and the label. The two labels share one grid cell,
   so the button keeps the width of "Copied" and nothing beside it moves; at
   rest the face is centred in it, shifted by half of what "Copied" is wider
   (--dx, which the script measures; .42em is Source Sans 3's) */
.contact__in{display:inline-flex;align-items:center;gap:8px;
  transform:translateX(var(--dx,.42em))}
.contact__copy.is-done .contact__in{transform:none}
.contact__lbl{display:grid;justify-items:start;text-align:left}
.contact__lbl>span{grid-area:1/1}
.contact__lbl-b,.contact__ck{opacity:0}
.contact__copy.is-done :is(.contact__lbl-a,.contact__cp){opacity:0}
.contact__copy.is-done :is(.contact__lbl-b,.contact__ck){opacity:1}
.contact__say{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;
  clip-path:inset(50%);white-space:nowrap;border:0}

/* ------------------------------------------------------ where he works */
.contact__where{margin:0;font:400 19px/1.5 var(--serif);font-style:normal;color:var(--body)}
.contact__where a{color:var(--ink);text-decoration-thickness:1px;text-underline-offset:4px;
  text-decoration-color:color-mix(in oklab,currentColor,transparent 72%)}
@media (hover:hover){.contact__where a:hover{text-decoration-color:currentColor}}
.contact__where a:focus-visible{outline:2px solid var(--focus);outline-offset:2px;
  border-radius:2px;text-decoration-color:currentColor}
/* the time in Izmir: the sans, its figures lining and even, so a minute
   turning over moves nothing; kept from the first paint, drawn when set */
.contact__clock{margin:10px 0 0;font:400 15px/1.4 var(--sans);letter-spacing:.006em;
  color:var(--muted);font-variant-numeric:lining-nums tabular-nums;visibility:hidden}
.contact__clock.is-set{visibility:visible}
.contact__clock time{font-weight:600;color:var(--ink)}
@media (scripting:none){.contact__clock{display:none}}

/* ---------------------------------------------------- CV and profiles */
/* One line each: a glyph, the name in his serif, the site's arrow, set in
   the line so the name keeps its baseline (the glyphs sit 4px under it,
   centred on the lower case). Each line is a 46px target. Wide, the glyphs
   hang in the gutter, so the names start on the values' edge. */
.contact__links{display:grid;justify-items:start;margin:-10px 0;padding:0;list-style:none}
.contact__links>li{margin:0}
.contact__link{display:inline-block;padding:10px 0;color:var(--ink);text-decoration:none;
  font:400 19px/1.35 var(--serif);-webkit-tap-highlight-color:transparent}
.contact__link>span{text-decoration:underline;text-decoration-thickness:1px;
  text-underline-offset:4px;text-decoration-color:transparent;
  transition:text-decoration-color var(--t-fast) var(--ease-state)}
.contact__glyph,.contact__go{display:inline-block;vertical-align:-4px;color:var(--muted);
  transition:color var(--t-quick) var(--ease-state)}
.contact__glyph{margin-right:12px}
.contact__go{margin-left:6px}
@container contact (width >= 560px){.contact__links{margin-left:-32px}}
@media (hover:hover){
  .contact__link:hover>span{text-decoration-color:color-mix(in oklab,currentColor,transparent 45%)}
  .contact__link:hover :is(.contact__glyph,.contact__go){color:var(--ink)}
}
.contact__link:focus-visible{outline:2px solid var(--focus);outline-offset:2px;
  border-radius:var(--r-sm)}
.contact__link:focus-visible>span{text-decoration-color:color-mix(in oklab,currentColor,transparent 45%)}
.contact__link:focus-visible :is(.contact__glyph,.contact__go){color:var(--ink)}

/* ----------------------------------------------------------------- motion
   Added here, never clawed back: without a no-preference answer none of it
   travels. */
@media (prefers-reduced-motion:no-preference){
  /* A copy, answered where it happened, whole in 300ms. Whatever leaves
     goes quick (120ms) and whatever comes follows behind it: the check 40ms
     behind the glyph, so one shape becomes the other, and a label 60ms
     behind the other, so the two words never read double. Settling back,
     the other way round. The press: the button gives 3% under the finger,
     on the quick spring, and lets go on it */
  .contact__copy{transition:background-color var(--t-fast) var(--ease-state),
    border-color var(--t-fast) var(--ease-state),transform var(--spring-quick)}
  .contact__copy:active{transform:scale(.97);transition-duration:0s,0s,var(--t-quick)}
  /* the face slides home as "Copied" takes the room: the move Motion's
     layout prop would make, made with a transform on the mid spring */
  .contact__in{transition:transform var(--spring-mid)}
  /* the copy glyph goes small through a 2px blur (and, settling back,
     waits 80ms for the check to go)... */
  .contact__cp{transform-box:fill-box;transform-origin:50% 50%;
    transition:opacity var(--t-fast) var(--ease-state) 80ms,
      filter var(--t-fast) var(--ease-state) 80ms,transform var(--spring-fast) 80ms}
  .contact__copy.is-done .contact__cp{transform:scale(.55);filter:blur(2px);
    transition:opacity var(--t-quick) var(--ease-state),
      filter var(--t-quick) var(--ease-state),transform var(--spring-fast)}
  /* ...and in its place the check draws itself, left to right */
  .contact__ck{stroke-dasharray:1;stroke-dashoffset:1;
    transition:opacity var(--t-quick) var(--ease-state),stroke-dashoffset 0s var(--t-quick)}
  .contact__copy.is-done .contact__ck{stroke-dashoffset:0;
    transition:opacity 0s 40ms,stroke-dashoffset var(--spring-mid) 40ms}
  /* "Copy" goes into a 2px blur and "Copied" comes out of one */
  .contact__lbl-a{transition:opacity var(--t-fast) var(--ease-state) 60ms,
    filter var(--t-fast) var(--ease-state) 60ms}
  .contact__lbl-b{filter:blur(2px);transition:opacity var(--t-quick) var(--ease-state),
    filter var(--t-quick) var(--ease-state)}
  .contact__copy.is-done .contact__lbl-a{filter:blur(2px);
    transition:opacity var(--t-quick) var(--ease-state),filter var(--t-quick) var(--ease-state)}
  .contact__copy.is-done .contact__lbl-b{filter:none;
    transition:opacity var(--t-fast) var(--ease-state) 60ms,
      filter var(--t-fast) var(--ease-state) 60ms}
  /* the wash sweeps across the address it took, left to right, as a
     selection is made; it lets go by opacity and folds away once unseen */
  .contact__addr::before{clip-path:inset(0 100% 0 0);
    transition:opacity var(--t-slow) var(--ease-state),clip-path 0s var(--t-slow)}
  .contact__addr.is-copied::before{clip-path:inset(0);
    transition:opacity var(--t-fast) var(--ease-state),clip-path var(--spring-mid)}
  /* the site's arrows: at rest the shaft stops where the head opens; under
     the pointer it draws and the head travels 5px (the external one up and
     out), 60ms behind. A key gets that end state at once. */
  .contact__go .ar-shaft{transition:stroke-dashoffset var(--spring-fast)}
  .contact__go .ar-head{transition:transform var(--spring-fast)}
  .contact__link:focus-visible .ar-shaft{stroke-dashoffset:0;transition:none}
  .contact__link:focus-visible .ar-head{transform:translateX(5px);transition:none}
  .contact__link:focus-visible .ar-out{transform:translate(2.5px,-2.5px)}
}
@media (hover:hover) and (prefers-reduced-motion:no-preference){
  .contact__link:hover .ar-shaft{stroke-dashoffset:0;transition:stroke-dashoffset var(--spring-mid)}
  .contact__link:hover .ar-head{transform:translateX(5px);transition:transform var(--spring-mid) 60ms}
  .contact__link:hover .ar-out{transform:translate(2.5px,-2.5px)}
}
/* Asked for less motion, nothing above applies: the faces, the check and
   the light swap by opacity alone (the shell stops every transition there),
   the check is whole at once, and nothing gives under the finger. */

/* Windows contrast themes paint no fill: the controls keep their edge and
   the light, which would be a solid box there, goes */
@media (forced-colors:active){
  .contact__copy{border-color:ButtonText}
  .contact__addr::before{display:none}
}
/* paper: the register as it stands, without the controls or the clock */
@media print{
  .contact__copy,.contact__clock{display:none}
  .contact__addr a{text-decoration:none}
}
"""

# build.py wraps each part's script in its own function scope, so `return`
# ends this one only.
JS = """
var root=document.querySelector('.contact');
if(!root)return;
var say=root.querySelector('.contact__say'),speak=0,mails=[];
/* the address as a selection: the fallback copies that, and if even that
   fails it is left selected for the keyboard */
function legacy(addr){
  var r=document.createRange(),s=window.getSelection(),ok=false;
  r.selectNodeContents(addr);s.removeAllRanges();s.addRange(r);
  try{ok=document.execCommand('copy');}catch(e){}
  if(ok)s.removeAllRanges();
  return ok;
}
function tell(text){
  clearTimeout(speak);say.textContent='';
  if(text)speak=setTimeout(function(){say.textContent=text;},60);
}
/* At rest the face is centred in the width "Copied" keeps: half of what
   that label is wider than "Copy", in em, so it holds at any text size */
function centre(m){
  var a=m.b.querySelector('.contact__lbl-a'),c=m.b.querySelector('.contact__lbl-b'),
      fs=parseFloat(getComputedStyle(m.b).fontSize);
  if(!a||!c||!fs)return;
  var d=(c.getBoundingClientRect().width-a.getBoundingClientRect().width)/2;
  if(d>=0)m.b.style.setProperty('--dx',(d/fs).toFixed(3)+'em');
}
function settle(m){
  clearTimeout(m.t);clearTimeout(m.l);
  m.b.classList.remove('is-done');m.a.classList.remove('is-copied');
}
/* A copy is answered where it happened: the check and "Copied" on its
   button, and its address lit for a moment, so the eye sees what was
   taken. The clipboard holds one address, so the other one settles. */
function done(m,ok){
  for(var i=0;i<mails.length;i++)settle(mails[i]);
  if(ok){
    m.b.classList.add('is-done');m.a.classList.add('is-copied');
    m.l=setTimeout(function(){m.a.classList.remove('is-copied');},900);
  }
  tell(ok?m.name+' address copied.':'The address is selected. Copy it with your keyboard.');
  m.t=setTimeout(function(){m.b.classList.remove('is-done');tell('');},ok?2000:6000);
}
[].forEach.call(root.querySelectorAll('.contact__mail'),function(li){
  var b=li.querySelector('.contact__copy'),a=li.querySelector('.contact__addr'),
      k=li.querySelector('.contact__kind');
  if(!b||!a||!say)return;
  var m={b:b,a:a,name:k?k.textContent:'Email',t:0,l:0};
  mails.push(m);centre(m);
  b.addEventListener('click',function(){
    var cb=navigator.clipboard,text=b.getAttribute('data-copy');
    if(cb&&cb.writeText&&window.isSecureContext){
      cb.writeText(text).then(function(){done(m,true);},function(){done(m,legacy(a));});
    }else done(m,legacy(a));
  });
});
if(document.fonts&&document.fonts.ready)
  document.fonts.ready.then(function(){for(var i=0;i<mails.length;i++)centre(mails[i]);});
/* iOS Safari shows :active only where a touch listener exists */
root.addEventListener('touchstart',function(){},{passive:true});

/* The time in Izmir, from the reader's clock and the time zone database,
   set now and on each minute while the tab is visible. */
var clk=root.querySelector('.contact__clock');
if(!clk||!window.Intl)return;
var fmt,off='';
try{
  fmt=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Istanbul',hour:'2-digit',
    minute:'2-digit',hourCycle:'h23'});
}catch(e){return;}
try{
  var parts=new Intl.DateTimeFormat('en-US',{timeZone:'Europe/Istanbul',
    timeZoneName:'shortOffset'}).formatToParts(new Date());
  for(var i=0;i<parts.length;i++)if(parts[i].type==='timeZoneName')off=parts[i].value;
}catch(e){}
off=off.replace(/^GMT/,'UTC');
var time=clk.querySelector('time'),zone=clk.querySelector('.contact__utc'),tick=0;
function show(){
  var now=new Date(),t=fmt.format(now).replace(/[^0-9:]/g,'');
  time.textContent=t;time.setAttribute('datetime',t);
  if(zone)zone.textContent=off?' ('+off+')':'';
  clk.classList.add('is-set');
  clearTimeout(tick);
  tick=setTimeout(show,60000-now.getSeconds()*1000-now.getMilliseconds()+40);
}
show();
document.addEventListener('visibilitychange',function(){
  if(document.hidden)clearTimeout(tick);else show();
});
"""

# ------------------------------------------------------------------ the data

# The two addresses the site publishes, and no other (build.py PUBLIC_EMAILS,
# which a test holds this to): his institute's, and since 29 Sep 2026, at his
# word, his personal one. Each is named on the page for what it is, and the
# institute's comes first.
_KINDS_OF = {"korkutkaynardag@iyte.edu.tr": "Institutional",
             "korkut.kaynardag@gmail.com": "Personal"}
PUBLIC_EMAILS = frozenset(_KINDS_OF)

_DEFAULTS = {
    "email": "korkutkaynardag@iyte.edu.tr",
    "personal": "korkut.kaynardag@gmail.com",
    "department": "Department of Civil Engineering",
    "institute": "Izmir Institute of Technology",
    "city": "Izmir",
    "country": "Turkiye",
    "links": (),
    "cv_href": "cv.html",
}

# The department's and the institute's own sites, in English (checked 27 Sep
# 2026), linked from their names where the page names them so.
_PLACES = {
    "Department of Civil Engineering": "https://civil.iyte.edu.tr/en/home-page/",
    "Izmir Institute of Technology": "https://en.iyte.edu.tr/",
}

# The profile kinds cv.json carries, in the order the About page lists them,
# and each one's name as the service writes it.
_KINDS = ("scholar", "linkedin", "researchgate", "github", "youtube")
_NAMES = {"scholar": "Google Scholar", "linkedin": "LinkedIn",
          "researchgate": "ResearchGate", "github": "GitHub", "youtube": "YouTube"}

# ------------------------------------------------------------------ the glyphs
# The inline family (DESIGN_BRIEF 7.1): a 24-unit grid drawn at 20px, stroke
# 1.5, round caps and joins, in currentColor, beside a text label. Each is
# drawn for its service and none comes from an icon set.
_G = ('<svg class="contact__glyph" viewBox="0 0 24 24" width="20" height="20" fill="none" '
      'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
      'stroke-linejoin="round" aria-hidden="true" focusable="false">{body}</svg>')
_GLYPHS = {
    # a mortarboard, the cap Scholar's own mark is drawn from
    "scholar": '<path d="M12 4.75 2.75 9.5 12 14.25l9.25-4.75z"/>'
               '<path d="M6.5 11.65v4.1c0 1.4 2.45 2.5 5.5 2.5s5.5-1.1 5.5-2.5v-4.1"/>'
               '<path d="M21.25 9.5v5"/>',
    # "in" in a rounded square
    "linkedin": '<rect x="3.25" y="3.25" width="17.5" height="17.5" rx="3.5"/>'
                '<path d="M8.25 10.75v5.75M12 16.5v-5.75m0 2.5c0-1.55 1.05-2.7 2.5-2.7'
                's2.25 1.05 2.25 2.6v3.35"/>'
                '<circle cx="8.25" cy="7.6" r="1" fill="currentColor" stroke="none"/>',
    # R and a raised G in a rounded square
    "researchgate": '<rect x="3.25" y="3.25" width="17.5" height="17.5" rx="3.5"/>'
                    '<path d="M7.25 16.75V8.25h2.9a2.1 2.1 0 0 1 0 4.2H7.25m2.75 0 2.5 4.3"/>'
                    '<path d="M17.35 7.3a2.25 2.25 0 1 0 .6 1.95h-1.55"/>',
    # a branch leaving the line and coming back: a repository's history
    "github": '<circle cx="7" cy="6" r="2"/><circle cx="7" cy="18" r="2"/>'
              '<circle cx="17" cy="8.5" r="2"/>'
              '<path d="M7 8v8M17 10.5c0 3.2-2.4 4.4-5.4 4.4H10.5c-1.9 0-3.5.5-3.5 1.1"/>',
    # a screen with the play mark
    "youtube": '<rect x="2.75" y="5.5" width="18.5" height="13" rx="3.75"/>'
               '<path d="M10.25 9.4v5.2l4.5-2.6z"/>',
    # anything else: two links of a chain
    "link": '<path d="M10.5 13.5a3.5 3.5 0 0 0 5 0l3-3a3.54 3.54 0 0 0-5-5l-1 1"/>'
            '<path d="M13.5 10.5a3.5 3.5 0 0 0-5 0l-3 3a3.54 3.54 0 0 0 5 5l1-1"/>',
    # the CV: a page with its owner on it
    "cv": '<path d="M6.25 3.25h8.5l3.5 3.5v14h-12z"/><path d="M14.75 3.25v3.5h3.5"/>'
          '<circle cx="12" cy="9.6" r="1.9"/>'
          '<path d="M8.9 14.6c.55-1.3 1.7-2 3.1-2s2.55.7 3.1 2M9.25 17.5h5.5"/>',
}
# the copy glyph and the check that replaces it, in one drawing
_COPY = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
         'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '
         'aria-hidden="true" focusable="false"><g class="contact__cp">'
         '<rect x="8.75" y="8.75" width="11" height="11" rx="2.25"/>'
         '<path d="M15.25 8.75v-2a2 2 0 0 0-2-2h-6.5a2 2 0 0 0-2 2v6.5a2 2 0 0 0 2 2h2"/></g>'
         '<path class="contact__ck" d="m5.5 12.6 4.2 4.2 8.8-9.1" pathLength="1"/></svg>')

# The site's arrow (build.py ARROW): two paths, so the shaft can draw while
# the head travels. The dash attributes keep it whole without the CSS. The
# external one points up and out, its shaft ending where its head opens.
_ARROW = ('<svg class="contact__go" viewBox="0 0 24 24" width="20" height="20" fill="none" '
          'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
          'stroke-linejoin="round" aria-hidden="true" focusable="false">'
          '<path class="ar-shaft" d="M3.5 12h13" stroke-dasharray="13" stroke-dashoffset="5"/>'
          '<path class="ar-head" d="m11.5 6.8 5.2 5.2-5.2 5.2"/></svg>')
_OUT = ('<svg class="contact__go" viewBox="0 0 24 24" width="20" height="20" fill="none" '
        'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true" focusable="false">'
        '<path class="ar-shaft" d="M6.5 17.5 15.6 8.4" stroke-dasharray="12.9" '
        'stroke-dashoffset="3.5"/>'
        '<path class="ar-head ar-out" d="M9.5 7.25h7.25v7.25"/></svg>')

# ------------------------------------------------------------------ helpers


def _e(text):
    return _html.escape(str(text), quote=True)


def _mail(address):
    """The address as text that may break after the @. His Gmail is set
    whole: build.py's privacy gate knows it only as one unbroken string."""
    local, at, domain = address.partition("@")
    if not at or domain.lower() == "gmail.com":
        return _e(address)
    return f"{_e(local)}@<wbr>{_e(domain)}"


def _addresses(c):
    """The addresses the Email row shows: email and personal, each one of the
    two public addresses or refused for its default, said once each, the
    institute's first."""
    found = []
    for key in ("email", "personal"):
        email = str(c.get(key) or "").strip().lower() or _DEFAULTS[key]
        if email not in PUBLIC_EMAILS:
            print(f"  !! parts/contact.py: refused {c.get(key)!r}; the site publishes "
                  f"{' and '.join(_KINDS_OF)} only")
            email = _DEFAULTS[key]
        if email not in found:
            found.append(email)
    order = list(_KINDS_OF)
    return sorted(found, key=order.index)


def _address(email):
    """One address: what it is, the address that writes to him, and the
    control that copies it."""
    kind = _KINDS_OF[email]
    return (f'<li class="contact__mail">\n'
            f'     <p class="contact__kind">{kind}</p>\n'
            f'     <p class="contact__addr"><a href="mailto:{_e(email)}">{_mail(email)}</a></p>\n'
            f'     <button class="contact__copy" type="button" data-copy="{_e(email)}" '
            f'aria-label="Copy {kind.lower()} address"><span class="contact__in">{_COPY}'
            f'<span class="contact__lbl"><span class="contact__lbl-a">Copy</span>'
            f'<span class="contact__lbl-b" aria-hidden="true">Copied</span></span></span>'
            f'</button>\n    </li>')


def _host(href):
    host = urlsplit(href).hostname or ""
    return host[4:] if host.startswith("www.") else host


def _profiles(links):
    """cv.json's links, as (kind, name, href): known kinds first, in _KINDS
    order, then any other http(s) link. This site's own address, a mail link
    and anything that is not a web address are left out."""
    rows = []
    for ln in links or ():
        href = _html.unescape(str(ln.get("href") or "")).strip()
        kind = str(ln.get("kind") or "").strip().lower()
        if urlsplit(href).scheme not in ("http", "https"):
            continue
        if _host(href).endswith("wavesanddata.com") or kind in ("website", "webpage", "site"):
            continue
        name = _NAMES.get(kind) or str(ln.get("label") or "").strip() or _host(href)
        rows.append((kind, name, href))
    order = {k: i for i, k in enumerate(_KINDS)}
    rows.sort(key=lambda r: order.get(r[0], len(_KINDS)))
    return rows


def _link(glyph, name, href, out=False):
    rel = ' rel="me"' if out else ""
    return (f'<li><a class="contact__link" href="{_e(href)}"{rel}>'
            f'{_G.format(body=_GLYPHS[glyph])}<span>{_e(name)}</span>'
            f'{_OUT if out else _ARROW}</a></li>')


def _row(key_id, key, body):
    return (f'\n  <section class="contact__row" aria-labelledby="{key_id}">\n'
            f'   <h2 class="contact__key" id="{key_id}">{key}</h2>\n'
            f'   {body}\n  </section>')


# ------------------------------------------------------------------ the page

def render(info=None):
    """Return the Contact page body: <div class="wrap contact"> with the h1.

    info: dict(email, personal, department, institute, city, country, links,
      cv_href). links is cv.json's list of {"label", "href", "kind"}. A missing
      key takes its default. email and personal must each be one of the two
      public addresses (PUBLIC_EMAILS); any other is refused for its default.
    """
    c = dict(_DEFAULTS)
    c.update({k: v for k, v in (info or {}).items() if v is not None})
    city = ", ".join(str(p).strip() for p in (c["city"], c["country"]) if p)

    def place(name):
        href = _PLACES.get(str(name).strip())
        return f'<a href="{_e(href)}">{_e(name)}</a>' if href else _e(name)

    mails = "\n    ".join(_address(m) for m in _addresses(c))
    rows = [_row("contact-email", "Email", f"""<div class="contact__val">
    <ul class="contact__mails" role="list">
    {mails}
    </ul>
    <p class="contact__say" role="status" aria-live="polite"></p>
   </div>""")]

    # one line each, broken as a postal address is, so the lines stay apart
    # when the address is copied or read aloud
    where = [place(c[k]) for k in ("department", "institute") if c[k]]
    if city:
        where.append(_e(city))
    if where:
        # the clock is Izmir's: drawn only where the city is Izmir
        clock = ""
        if str(c["city"]).strip().lower() == "izmir":
            clock = ('\n    <p class="contact__clock"><time></time> local time'
                     '<span class="contact__utc"></span></p>')
        rows.append(_row("contact-where", "Where to find me", f"""<div class="contact__val">
    <address class="contact__where">{"<br>".join(where)}</address>{clock}
   </div>"""))

    # his CV and his profiles, one list, as his first Contact page grouped them
    links = [_link("cv", "Curriculum vitae", c["cv_href"])] if c["cv_href"] else []
    links += [_link(k if k in _GLYPHS else "link", name, href, out=True)
              for k, name, href in _profiles(c["links"])]
    if links:
        rows.append(_row("contact-elsewhere", "Elsewhere",
                         f'<ul class="contact__links" role="list">{"".join(links)}</ul>'))

    return f"""<div class="wrap contact">
 <h1>Contact</h1>
 <p class="lede">Feel free to reach out about research, collaboration, or the educational
 sections of this site, especially if you are a student or newcomer to these topics.</p>
 <div class="contact__reg">{"".join(rows)}
 </div>
</div>"""
