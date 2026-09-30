/* numfig engine: the shared runtime of the figures redrawn from numerical
   models (tools/numfig/README.md). build_html() in common.py inlines it after
   `const W = ..., H = ...;` and the figure's DATA, and before the figure's own
   script, which defines draw() and may define POSTER_T and reset().

   Same frame as his animations (content/anim/fig*.html): a canvas W by H in
   drawing units, scaled to the width it is given; pause, restart, a click on
   the canvas toggles; paused while off screen. Unlike them the type is
   Computer Modern (CMU Serif, published in ../fonts/), and a reader who asks
   for less motion, or the print still (?still), gets the figure complete at
   POSTER_T instead of the empty first frame. */

const cv = document.getElementById('c'), ctx = cv.getContext('2d');
/* CMU Serif, then Figure Math (Latin Modern Math's symbols, content/fonts-cmu/
   README.txt) for the signs CMU does not carry: every glyph in Computer Modern */
const SERIF = '"CMU Serif", "Figure Math", "Latin Modern Roman", "Latin Modern Math", serif';
const STILL = /[?&]still\b/.test(location.search);
const CHECK = /[?&]overlap\b/.test(location.search);   // ?still&overlap: report ink that collides
const AT = /[?&]t=([\d.]+)/.exec(location.search);   // ?still&t=2.5: one moment, to look at
const REDUCED =matchMedia('(prefers-reduced-motion: reduce)').matches;

/* the palette: the site's inks and blues (site/parts/theme.py) and one
   crimson. Blue is the structure and the primary data, crimson is the one
   thing the eye should follow, grey is guides. The crimson is matched to the
   blue in CIELAB lightness (accent L* 37 = blue, amber L* 50) at hue 20, so
   neither side of a comparison shouts; the names accent/amber/wash are the
   roles, kept from the first palette so no figure had to change. */
const C = {
  ink: '#27221C', body: '#544F48', muted: '#6F6A64', guide: '#8A857C',
  rule: '#D7D2CA', grid: '#ECE8E2',
  navy: '#043052', blue: '#095A94', sky: '#5B8DB8', mist: '#A9C3DA',
  steel: '#E3EBF2', steel2: '#C9D7E4',
  accent: '#A7203A', amber: '#D14457', wash: '#F9EEEE',
};

let t = 0, last = null, visible = true;
let playing = !REDUCED && !STILL;
cv.style.aspectRatio = W + ' / ' + H;

/* ---------------------------------------------------------------- time */
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, s) => a + (b - a) * s;
const easeInOut = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const easeOut = x => 1 - Math.pow(1 - x, 3);
/* progress of a step of the intro that starts at t0 and lasts dur, eased */
const seg = (t0, dur, e = easeInOut) => e(clamp((t - t0) / dur));

/* Motion's spring (motion.dev, MIT; the spring() of motion 12.43.0 alone,
   tools/numfig/motion-spring.min.js). settle(t0, visual, bounce) is the
   progress of a spring let go at t0 that is where it is going after `visual`
   seconds and then settles, sampled at t: a pure function of the clock like
   seg(), so any moment can be drawn exactly. For things that ARRIVE: a label
   or a panel settling into place, a marker gliding to a new point. Strokes
   drawing themselves keep seg() (manim's smooth). bounce 0 unless the thing
   is a physical object that would overshoot.
   The MIT License (MIT). Copyright (c) 2024 Motion (https://motion.dev) B.V. */
(()=>{var G=(e,r,o)=>o>r?r:o<e?e:o;var R=()=>{};var D=e=>e*1e3,S=e=>e/1e3;var W=(e,r,o=10)=>{let a="",s=Math.max(Math.round(r/o),2);for(let c=0;c<s;c++)a+=Math.round(e(c/(s-1))*1e4)/1e4+", ";return`linear(${a.substring(0,a.length-2)})`};function I(e){let r=0,o=50,a=e.next(r);for(;!a.done&&r<2e4;)r+=o,a=e.next(r);return r>=2e4?1/0:r}function z(e,r=100,o){let a=o({...e,keyframes:[0,r]}),s=Math.min(I(a),2e4);return{type:"keyframes",ease:c=>a.next(s*c).value/r,duration:S(s)}}var n={stiffness:100,damping:10,mass:1,velocity:0,duration:800,bounce:.3,visualDuration:.3,restSpeed:{granular:.01,default:2},restDelta:{granular:.005,default:.5},minDuration:.01,maxDuration:10,minDamping:.05,maxDamping:1};function K(e,r){return e*Math.sqrt(1-r*r)}var U=12;function Z(e,r,o){let a=o;for(let s=1;s<U;s++)a=a-e(a)/r(a);return a}var q=.001;function J({duration:e=n.duration,bounce:r=n.bounce,velocity:o=n.velocity,mass:a=n.mass}){let s,c;R(e<=D(n.maxDuration),"Spring duration must be 10 seconds or less","spring-duration-limit");let m=1-r;m=G(n.minDamping,n.maxDamping,m),e=G(n.minDuration,n.maxDuration,S(e)),m<1?(s=f=>{let g=f*m,d=g*e,E=g-o,v=K(f,m),h=Math.exp(-d);return q-E/v*h},c=f=>{let d=f*m*e,E=d*o+o,v=Math.pow(m,2)*Math.pow(f,2)*e,h=Math.exp(-d),i=K(Math.pow(f,2),m);return(-s(f)+q>0?-1:1)*((E-v)*h)/i}):(s=f=>{let g=Math.exp(-f*e),d=(f-o)*e+1;return-q+g*d},c=f=>{let g=Math.exp(-f*e),d=(o-f)*(e*e);return g*d});let u=5/e,A=Z(s,c,u);if(e=D(e),isNaN(A))return{stiffness:n.stiffness,damping:n.damping,duration:e};{let f=Math.pow(A,2)*a;return{stiffness:f,damping:m*2*Math.sqrt(a*f),duration:e}}}var _=["duration","bounce"],$=["stiffness","damping","mass"];function H(e,r){return r.some(o=>e[o]!==void 0)}function Q(e){let r={velocity:n.velocity,stiffness:n.stiffness,damping:n.damping,mass:n.mass,isResolvedFromDuration:!1,...e};if(!H(e,$)&&H(e,_))if(r.velocity=0,e.visualDuration){let o=e.visualDuration,a=2*Math.PI/(o*1.2),s=a*a,c=2*G(.05,1,1-(e.bounce||0))*Math.sqrt(s);r={...r,mass:n.mass,stiffness:s,damping:c}}else{let o=J({...e,velocity:0});r={...r,...o,mass:n.mass},r.isResolvedFromDuration=!0}return r}function B(e=n.visualDuration,r=n.bounce){let o=typeof e!="object"?{visualDuration:e,keyframes:[0,1],bounce:r}:e,{restSpeed:a,restDelta:s}=o,c=o.keyframes[0],m=o.keyframes[o.keyframes.length-1],u={done:!1,value:c},{stiffness:A,damping:f,mass:g,duration:d,velocity:E,isResolvedFromDuration:v}=Q({...o,velocity:-S(o.velocity||0)}),h=E||0,i=f/(2*Math.sqrt(A*g)),x=m-c,p=S(Math.sqrt(A/g)),j=Math.abs(x)<5;a||(a=j?n.restSpeed.granular:n.restSpeed.default),s||(s=j?n.restDelta.granular:n.restDelta.default);let w,P,y,C,k,F;if(i<1)y=K(p,i),C=(h+i*p*x)/y,w=t=>{let l=Math.exp(-i*p*t);return m-l*(C*Math.sin(y*t)+x*Math.cos(y*t))},k=i*p*C+x*y,F=i*p*x-C*y,P=t=>Math.exp(-i*p*t)*(k*Math.sin(y*t)+F*Math.cos(y*t));else if(i===1){w=l=>m-Math.exp(-p*l)*(x+(h+p*x)*l);let t=h+p*x;P=l=>Math.exp(-p*l)*(p*t*l-h)}else{let t=p*Math.sqrt(i*i-1);w=V=>{let b=Math.exp(-i*p*V),T=Math.min(t*V,300);return m-b*((h+i*p*x)*Math.sinh(T)+t*x*Math.cosh(T))/t};let l=(h+i*p*x)/t,M=i*p*l-x*t,O=i*p*x-l*t;P=V=>{let b=Math.exp(-i*p*V),T=Math.min(t*V,300);return b*(M*Math.sinh(T)+O*Math.cosh(T))}}let N={calculatedDuration:v&&d||null,velocity:t=>D(P(t)),next:t=>{if(!v&&i<1){let M=Math.exp(-i*p*t),O=Math.sin(y*t),V=Math.cos(y*t),b=m-M*(C*O+x*V),T=D(M*(k*O+F*V));return u.done=Math.abs(T)<=a&&Math.abs(m-b)<=s,u.value=u.done?m:b,u}let l=w(t);if(v)u.done=t>=d;else{let M=D(P(t));u.done=Math.abs(M)<=a&&Math.abs(m-l)<=s}return u.value=u.done?m:l,u},toString:()=>{let t=Math.min(I(N),2e4),l=W(M=>N.next(t*M).value,t,30);return t+"ms "+l},toTransition:()=>{}};return N}B.applyToOptions=e=>{let r=z(e,100,B);return e.ease=r.ease,e.duration=D(r.duration),e.type="keyframes",e};globalThis.MotionSpring=B;})();
const _springs = {};
function settle(t0, visual, bounce = 0) {
  const k = visual + ':' + bounce;
  const g = _springs[k] || (_springs[k] = MotionSpring({ keyframes: [0, 1], visualDuration: visual, bounce }));
  return t <= t0 ? 0 : g.next((t - t0) * 1000).value;
}

/* ---------------------------------------------------------------- frame */
function fit() {
  const dpr = STILL ? 2 : Math.min(window.devicePixelRatio || 1, 2), w = cv.clientWidth || W;
  cv.width = Math.round(w * dpr); cv.height = Math.round(w * H / W * dpr);
  render();
}
function render() {
  ctx.setTransform(cv.width / W, 0, 0, cv.height / H, 0, 0);
  ctx.save(); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H); ctx.restore();
  ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  _inks.length = 0; _segs.length = 0; _knocks.length = 0; _clip = null; _clips.length = 0;
  draw();
  if (CHECK) _clashes();
}
/* the controls are drawn, not set in a font: crisp at any zoom */
const ICON_PAUSE = '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="4.2" y="3.2" width="2.5" height="9.6" rx=".7"/><rect x="9.3" y="3.2" width="2.5" height="9.6" rx=".7"/></svg>';
const ICON_PLAY = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5.2 3.4v9.2c0 .5.5.8.9.5l7.1-4.6c.4-.2.4-.8 0-1L6.1 2.9c-.4-.3-.9 0-.9.5z"/></svg>';
const pp = document.getElementById('pp');
function setPlay(p) {
  playing = p; pp.innerHTML = p ? ICON_PAUSE : ICON_PLAY;
  pp.setAttribute('aria-label', p ? 'Pause animation' : 'Play animation');
}
const posterT = () => AT ? parseFloat(AT[1]) : typeof POSTER_T === 'number' ? POSTER_T : 0;
function poster() { t = posterT(); render(); }
pp.addEventListener('click', e => { e.stopPropagation(); setPlay(!playing); });
document.getElementById('rs').addEventListener('click', e => {
  e.stopPropagation(); t = 0; if (typeof reset === 'function') reset(); setPlay(true); render();
});
cv.addEventListener('click', () => { if (!_quiet()) setPlay(!playing); });
function loop(ts) {
  if (last === null) last = ts;
  const dt = Math.min((ts - last) / 1000, 0.05); last = ts;
  if (playing && visible) { t += dt; if (typeof step === 'function') step(dt); render(); }
  requestAnimationFrame(loop);
}
/* a figure that sets `var QUIET = true` before boot() is an icon or a cover's
   ornament: it plays once, draws no controls and ignores clicks */
const _quiet = () => typeof QUIET !== 'undefined' && QUIET === true;   // exactly true: a figure's own QUIET list is not the flag
function start() {
  if (STILL || _quiet()) document.querySelector('.ctl').style.display = 'none';
  if (_quiet()) cv.style.cursor = 'default';
  setPlay(playing);
  if (!playing) t = posterT();
  new ResizeObserver(fit).observe(cv);
  new IntersectionObserver(en => { visible = en[0].isIntersecting; }).observe(cv);
  fit();
  document.documentElement.dataset.ready = '1';      // the still is taken after this
  if (!STILL) requestAnimationFrame(loop);
}

/* the figure's script ends with boot(): draw once the type has loaded, so
   no frame is set in a fallback face and then jumps */
function boot() {
  const faces = ['500 16px "CMU Serif"', 'italic 500 16px "CMU Serif"', '700 16px "CMU Serif"'];
  Promise.all([...faces.map(f => document.fonts.load(f)), document.fonts.load('500 16px "Figure Math"', '≈≤∂∞')])
    .then(start, start);
}

/* ---------------------------------------------------------------- check
   ?overlap (with ?still or ?t=): every run of type drawn in the frame is kept
   as its ink box (measureText's actual bounds, through the current transform,
   in drawing units), and every dark stroke as its segments. After the frame,
   window.__overlaps lists pairs of runs from different labels whose ink
   meets, and window.__crossings runs a dark stroke passes through; both are
   outlined in red. Runs of one math() or text() call are one label and never
   collide with themselves; faint things (alpha < .35) and pale strokes
   (guides, grids) are left out. common.overlaps() reads the lists. */
const _inks = [], _segs = [], _knocks = [];
let _grp = 0, _ord = 0;
function _white(c) { return typeof c === 'string' && /^(#fff(fff)?|white|rgb\(255, ?255, ?255\))$/i.test(c); }
function _knock(pts) {                       // a white fill drawn now hides what was drawn before it
  if (!CHECK || ctx.globalAlpha < .35 || !_white(ctx.fillStyle)) return;   // as visible as a label must be
  const P = pts.map(([x, y]) => _map(x, y));
  _knocks.push({ o: ++_ord, x0: Math.min(...P.map(q => q[0])), x1: Math.max(...P.map(q => q[0])),
                 y0: Math.min(...P.map(q => q[1])), y1: Math.max(...P.map(q => q[1])) });
}
let _clip = null, _rect = null;
const _clips = [];
if (CHECK) {
  const fr = ctx.fillRect.bind(ctx);
  ctx.fillRect = (x, y, w, h) => { _knock([[x, y], [x + w, y + h]]); return fr(x, y, w, h); };
  // clips are rectangles in these figures (a plot's area): follow save/restore
  const sv = ctx.save.bind(ctx), rs = ctx.restore.bind(ctx), cl = ctx.clip.bind(ctx), rc = ctx.rect.bind(ctx),
        bp = ctx.beginPath.bind(ctx);
  ctx.save = () => { _clips.push(_clip); return sv(); };
  ctx.restore = () => { _clip = _clips.length ? _clips.pop() : null; return rs(); };
  ctx.beginPath = () => { _rect = null; return bp(); };
  ctx.rect = (x, y, w, h) => { const a = _map(x, y), b = _map(x + w, y + h);
    _rect = [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1])]; return rc(x, y, w, h); };
  ctx.clip = (...a) => { if (_rect) _clip = _clip ? [Math.max(_clip[0], _rect[0]), Math.max(_clip[1], _rect[1]),
    Math.min(_clip[2], _rect[2]), Math.min(_clip[3], _rect[3])] : _rect; return cl(...a); };
}
function _inside(p, q) {                     // the part of segment pq inside the current clip, or null
  if (!_clip) return [p, q];
  const [x0, y0, x1, y1] = _clip, dx = q[0] - p[0], dy = q[1] - p[1];
  let t0 = 0, t1 = 1;
  for (const [pp, qq] of [[-dx, p[0] - x0], [dx, x1 - p[0]], [-dy, p[1] - y0], [dy, y1 - p[1]]]) {
    if (pp === 0) { if (qq < 0) return null; continue; }
    const r = qq / pp;
    if (pp < 0) { if (r > t1) return null; if (r > t0) t0 = r; } else { if (r < t0) return null; if (r < t1) t1 = r; }
  }
  return t1 > t0 ? [[p[0] + t0 * dx, p[1] + t0 * dy], [p[0] + t1 * dx, p[1] + t1 * dy]] : null;
}
function _map(x, y) {
  const m = ctx.getTransform(), k = W / cv.width;
  return [(m.a * x + m.c * y + m.e) * k, (m.b * x + m.d * y + m.f) * k];
}
function _ink(s, x, y) {
  const q = ctx.measureText(s);
  const x0 = x - q.actualBoundingBoxLeft, x1 = x + q.actualBoundingBoxRight;
  const y0 = y - q.actualBoundingBoxAscent, y1 = y + q.actualBoundingBoxDescent;
  if (!(x1 > x0 && y1 > y0)) return;
  const P = [_map(x0, y0), _map(x1, y0), _map(x1, y1), _map(x0, y1)];
  _inks.push({ s, g: _grp, o: ++_ord, a: ctx.globalAlpha, P,
               x0: Math.min(...P.map(p => p[0])), x1: Math.max(...P.map(p => p[0])),
               y0: Math.min(...P.map(p => p[1])), y1: Math.max(...P.map(p => p[1])) });
}
function _pale(c) {
  if (typeof c !== 'string' || !/^#[0-9a-f]{6}$/i.test(c)) return false;
  const [r, g, b] = [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16) / 255);
  return .2126 * r + .7152 * g + .0722 * b > .72;
}
function _seg(pts, color, width) {
  if (!CHECK || ctx.globalAlpha < .35 || width < 1 || _pale(color)) return;
  const o = ++_ord;
  for (let i = 1; i < pts.length; i++) {
    const c = _inside(_map(pts[i - 1][0], pts[i - 1][1]), _map(pts[i][0], pts[i][1]));
    if (c) _segs.push({ o, p: c[0], q: c[1] });
  }
}
function _cuts(sg, b) {                      // does the segment pass through the run's ink, shrunk 1 unit?
  if (b.P && Math.abs(b.P[0][1] - b.P[1][1]) > .5) {   // rotated type: test against its quadrilateral
    const [cx, cy] = [b.P.reduce((a, p) => a + p[0], 0) / 4, b.P.reduce((a, p) => a + p[1], 0) / 4];
    const Q = b.P.map(([x, y]) => { const d = Math.hypot(x - cx, y - cy) || 1; return [x - (x - cx) / d, y - (y - cy) / d]; });
    const seg = [sg.p, sg.q, sg.q, sg.p];
    return _meet(Q, seg, 0);
  }
  const x0 = b.x0 + 1, x1 = b.x1 - 1, y0 = b.y0 + 1, y1 = b.y1 - 1;
  if (x1 <= x0 || y1 <= y0) return false;
  const [ax, ay] = sg.p, [bx, by] = sg.q, dx = bx - ax, dy = by - ay;
  let t0 = 0, t1 = 1;
  for (const [pp, qq] of [[-dx, ax - x0], [dx, x1 - ax], [-dy, ay - y0], [dy, y1 - ay]]) {
    if (pp === 0) { if (qq < 0) return false; continue; }
    const r = qq / pp;
    if (pp < 0) { if (r > t1) return false; if (r > t0) t0 = r; } else { if (r < t0) return false; if (r < t1) t1 = r; }
  }
  return t1 - t0 > 1e-6;
}
function _meet(A, B, m) {                  // convex quads overlap by more than m (separating axes)
  for (const Q of [A, B]) for (let i = 0; i < 4; i++) {
    const [ax, ay] = Q[i], [bx, by] = Q[(i + 1) % 4], nx = ay - by, ny = bx - ax, L = Math.hypot(nx, ny);
    if (L < 1e-9) continue;
    const pa = A.map(([x, y]) => (x * nx + y * ny) / L), pb = B.map(([x, y]) => (x * nx + y * ny) / L);
    if (Math.min(Math.max(...pa), Math.max(...pb)) - Math.max(Math.min(...pa), Math.min(...pb)) <= m) return false;
  }
  return true;
}
function _clashes() {
  const B = _inks.filter(b => b.a >= .35), hit = [], cross = [];
  for (let i = 0; i < B.length; i++) for (let j = i + 1; j < B.length; j++) {
    const p = B[i], q = B[j];
    if (p.g === q.g) continue;
    // the same words drawn again in place is a highlight, not a collision
    if (p.s === q.s && Math.abs(p.x0 - q.x0) < 1.5 && Math.abs(p.y0 - q.y0) < 1.5) continue;
    const w = Math.min(p.x1, q.x1) - Math.max(p.x0, q.x0), h = Math.min(p.y1, q.y1) - Math.max(p.y0, q.y0);
    if (w > 1.5 && h > 1.5 && _meet(p.P, q.P, 1)) hit.push([p, q]);
  }
  // a stroke through a label, unless a white knockout drawn after the stroke covers the label
  const hidden = (sg, b) => _knocks.some(k => k.o > sg.o && k.x0 <= b.x0 + 1 && k.x1 >= b.x1 - 1 && k.y0 <= b.y0 + 1 && k.y1 >= b.y1 - 1);
  for (const b of B) if (_segs.some(sg => _cuts(sg, b) && !hidden(sg, b))) cross.push(b);
  window.__overlaps = hit.map(([p, q]) => [p.s, q.s, Math.round(p.x0), Math.round(p.y0)]);
  window.__crossings = cross.map(b => [b.s, Math.round(b.x0), Math.round(b.y0)]);
  ctx.save(); ctx.setTransform(cv.width / W, 0, 0, cv.height / H, 0, 0); ctx.globalAlpha = 1;
  ctx.lineWidth = 1; ctx.strokeStyle = 'rgba(230,0,0,.9)';
  for (const [p, q] of hit) for (const b of [p, q]) ctx.strokeRect(b.x0, b.y0, b.x1 - b.x0, b.y1 - b.y0);
  ctx.strokeStyle = 'rgba(255,120,0,.9)'; ctx.setLineDash([3, 2]);
  for (const b of cross) ctx.strokeRect(b.x0 - 1, b.y0 - 1, b.x1 - b.x0 + 2, b.y1 - b.y0 + 2);
  ctx.restore();
}

/* ---------------------------------------------------------------- type
   text(s, x, y, o): one run in CMU Serif.
   math(s, x, y, o): TeX-like, a small subset. Latin and Greek letters are
   italic, digits and signs upright; _x or _{..} a subscript, ^x or ^{..} a
   superscript; \rm{..} an upright group (units, d in dx, words); the minus
   sign is U+2212. Returns the width drawn, in drawing units. */
function font(o) { return `${o.italic ? 'italic ' : ''}${o.bold ? '700' : '500'} ${o.size || 16}px ${SERIF}`; }
function text(s, x, y, o = {}) {
  const { size = 16, color = C.ink, align = 'left', base = 'alphabetic', rot = 0, alpha = 1 } = o;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.font = font({ ...o, size }); ctx.fillStyle = color;
  ctx.textAlign = align; ctx.textBaseline = base;
  _grp++;
  if (rot) { ctx.translate(x, y); ctx.rotate(rot); ctx.fillText(s, 0, 0); if (CHECK) _ink(s, 0, 0); }
  else { ctx.fillText(s, x, y); if (CHECK) _ink(s, x, y); }
  const w = ctx.measureText(s).width; ctx.restore(); return w;
}
/* lower-case Greek in math is TeX's math italic (cmmi), not CMU's text italic
   (whose theta is open like a vartheta and whose rho curls): Unicode's
   mathematical italic letters, which Figure Math carries from Latin Modern
   Math. TeX's pairs stay apart: \epsilon is the lunate one, \phi the straight
   one, \vartheta, \varrho, \varpi the variants. */
const _MI = cp => String.fromCodePoint(cp);
const MACROS = {
  alpha: _MI(0x1D6FC), beta: _MI(0x1D6FD), gamma: _MI(0x1D6FE), delta: _MI(0x1D6FF),
  epsilon: _MI(0x1D716), varepsilon: _MI(0x1D700), zeta: _MI(0x1D701), eta: _MI(0x1D702),
  theta: _MI(0x1D703), vartheta: _MI(0x1D717), iota: _MI(0x1D704), kappa: _MI(0x1D705),
  lambda: _MI(0x1D706), mu: _MI(0x1D707), nu: _MI(0x1D708), xi: _MI(0x1D709), pi: _MI(0x1D70B),
  varpi: _MI(0x1D71B), rho: _MI(0x1D70C), varrho: _MI(0x1D71A), sigma: _MI(0x1D70E),
  varsigma: _MI(0x1D70D), tau: _MI(0x1D70F), upsilon: _MI(0x1D710), phi: _MI(0x1D719),
  varphi: _MI(0x1D711), chi: _MI(0x1D712), psi: _MI(0x1D713), omega: _MI(0x1D714),
  Gamma: 'Γ', Delta: 'Δ',
  Theta: 'Θ', Lambda: 'Λ', Pi: 'Π', Sigma: 'Σ', Phi: 'Φ', Psi: 'Ψ', Omega: 'Ω',
  partial: '∂', infty: '∞', cdot: '⋅', times: '×', approx: '≈', ll: '≪', gg: '≫', leq: '≤',
  geq: '≥', neq: '≠', pm: '±', to: '→', propto: '∝', sim: '∼', deg: '°', ',': ' ',
  ' ': ' ', quad: ' ',
};
const _GREEK = { 0x3D1: 0x1D717, 0x3D5: 0x1D719, 0x3D6: 0x1D71B, 0x3F1: 0x1D71A, 0x3F5: 0x1D716 };
function _mathItalic(ch) {                 // α..ω and the variant symbols, as math italic
  const c = ch.codePointAt(0);
  if (ch.length === 1 && c >= 0x3B1 && c <= 0x3C9) return String.fromCodePoint(c - 0x3B1 + 0x1D6FC);
  return _GREEK[c] ? String.fromCodePoint(_GREEK[c]) : null;
}
function _runs(s) {
  const out = []; let i = 0;
  const group = () => {
    if (s[i] === '{') { let d = 1, j = i + 1; while (j < s.length && d) { if (s[j] === '{') d++; else if (s[j] === '}') d--; j++; } const g = s.slice(i + 1, j - 1); i = j; return g; }
    return s[i++];
  };
  while (i < s.length) {
    const c = s[i];
    if (c === '_' || c === '^') { i++; out.push({ kind: c === '_' ? 'sub' : 'sup', runs: _runs(group()) }); }
    else if (s.startsWith('\\rm', i)) {
      i += 3; out.push({ kind: 'rm', s: group().replace(/\\ /g, ' ').replace(/\\,/g, ' ') });
    }
    else if (s.startsWith('\\sqrt', i)) { i += 5; out.push({ kind: 'sqrt', runs: _runs(group()) }); }
    else if (c === '\\') {
      const m = /^\\([A-Za-z]+|.)/.exec(s.slice(i)); i += m[0].length;
      if (/^[A-Za-z]/.test(m[1]) && s[i] === ' ') i++;        // TeX eats the space after a word macro
      out.push({ kind: 'ch', s: MACROS[m[1]] === undefined ? m[1] : MACROS[m[1]] });
    }
    else { out.push({ kind: 'ch', s: c }); i++; }
  }
  return out;
}
function _mathDraw(runs, x, y, size, color, go) {
  let w = 0;
  for (const r of runs) {
    if (r.kind === 'ch' || r.kind === 'rm') {
      // math italic Greek is slanted already: set upright, so nothing slants it twice
      const gk = r.kind === 'ch' ? (_mathItalic(r.s) || (/[\u{1D6E2}-\u{1D71B}]/u.test(r.s) ? r.s : null)) : null;
      const it = !gk && r.kind === 'ch' && /[A-Za-z]/.test(r.s);
      const s = gk || r.s.replace(/-/g, '−');
      ctx.font = font({ size, italic: it });
      if (go) { ctx.fillStyle = color; ctx.fillText(s, x + w, y); if (CHECK && s.trim()) _ink(s, x + w, y); }
      w += ctx.measureText(s).width + (it || gk ? size * .04 : 0);
    } else if (r.kind === 'sqrt') {
      ctx.font = font({ size });
      const rw = ctx.measureText('√').width;
      if (go) { ctx.fillStyle = color; ctx.fillText('√', x + w, y); if (CHECK) _ink('√', x + w, y); }
      const iw = _mathDraw(r.runs, x + w + rw, y, size, color, go);
      if (go) {
        ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = size * .055; ctx.beginPath();
        ctx.moveTo(x + w + rw * .92, y - size * .8); ctx.lineTo(x + w + rw + iw + size * .05, y - size * .8);
        ctx.stroke(); ctx.restore();
      }
      w += rw + iw + size * .1;
    } else {
      const sz = size * .7, dy = r.kind === 'sub' ? size * .24 : -size * .38;
      w += _mathDraw(r.runs, x + w, y + dy, sz, color, go) + size * .04;
    }
  }
  return w;
}
function math(s, x, y, o = {}) {
  const { size = 17, color = C.ink, align = 'left', base = 'alphabetic', alpha = 1, rot = 0 } = o;
  const runs = _runs(s);
  ctx.save(); ctx.globalAlpha *= alpha; ctx.textAlign = 'left'; ctx.textBaseline = base;
  const w = _mathDraw(runs, 0, 0, size, color, false); _grp++;
  const dx = align === 'center' ? -w / 2 : align === 'right' ? -w : 0;
  ctx.translate(x, y); if (rot) ctx.rotate(rot);
  _mathDraw(runs, dx, 0, size, color, true);
  ctx.restore(); return w;
}
/* the label of a panel, as the caption calls it: (a), (b) ... */
function panel(letter, x, y, o = {}) { return text(`(${letter})`, x, y, { size: 19, bold: true, ...o }); }

/* ---------------------------------------------------------------- strokes
   line(pts, o): a polyline [[x,y],...]; o.progress draws its first share by
   arc length (a stroke drawing itself, as manim's Create does). */
function line(pts, o = {}) {
  const { color = C.ink, width = 1.6, dash = null, progress = 1, alpha = 1, fill = null, close = false } = o;
  if (progress <= 0 || pts.length < 2) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.lineWidth = width;
  if (dash) ctx.setLineDash(dash);
  if (progress >= 1) _seg(close ? [...pts, pts[0]] : pts, color, width);
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  if (progress >= 1) { for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); if (close) ctx.closePath(); }
  else {
    let L = 0; const seg_ = [];
    for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg_.push(d); L += d; }
    let left = L * progress;
    for (let i = 1; i < pts.length && left > 0; i++) {
      const d = seg_[i - 1], s = d > left ? left / d : 1;
      ctx.lineTo(lerp(pts[i - 1][0], pts[i][0], s), lerp(pts[i - 1][1], pts[i][1], s)); left -= d;
    }
  }
  if (fill && progress >= 1) { ctx.fillStyle = fill; ctx.fill(); if (CHECK) _knock(pts); }
  ctx.stroke(); ctx.restore();
}
function arrow(x1, y1, x2, y2, o = {}) {
  const { color = C.ink, width = 1.6, head = 10, alpha = 1, both = false, dash = null } = o;
  const a = Math.atan2(y2 - y1, x2 - x1);
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = width;
  if (dash) ctx.setLineDash(dash);
  _seg([[x1, y1], [x2, y2]], color, width);
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2 - Math.cos(a) * head * .6, y2 - Math.sin(a) * head * .6); ctx.stroke();
  ctx.setLineDash([]);
  const tip = (x, y, a) => {       // a TikZ stealth tip
    ctx.beginPath(); ctx.moveTo(x, y);
    ctx.lineTo(x - head * Math.cos(a - .38), y - head * Math.sin(a - .38));
    ctx.lineTo(x - head * .62 * Math.cos(a), y - head * .62 * Math.sin(a));
    ctx.lineTo(x - head * Math.cos(a + .38), y - head * Math.sin(a + .38)); ctx.closePath(); ctx.fill();
  };
  tip(x2, y2, a); if (both) tip(x1, y1, a + Math.PI);
  ctx.restore();
}
function dot(x, y, r = 4, o = {}) {
  const { color = C.ink, fill = color, width = 1.4, alpha = 1 } = o;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.beginPath(); ctx.arc(x, y, r, 0, 2 * Math.PI);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); } ctx.strokeStyle = color; ctx.lineWidth = width; ctx.stroke(); ctx.restore();
}
/* a pin support under (x, y): a triangle on a hatched ground, as TikZ draws it */
function pin(x, y, o = {}) {
  const { s = 16, color = C.ink, alpha = 1, roller = false } = o;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.fillStyle = '#fff'; ctx.lineWidth = 1.4;
  ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - s * .7, y + s); ctx.lineTo(x + s * .7, y + s); ctx.closePath(); ctx.fill(); ctx.stroke();
  let g = y + s;
  if (roller) { for (const dx of [-s * .4, s * .4]) { ctx.beginPath(); ctx.arc(x + dx, g + 3, 3, 0, 2 * Math.PI); ctx.stroke(); } g += 6; }
  ctx.beginPath(); ctx.moveTo(x - s, g); ctx.lineTo(x + s, g); ctx.stroke();
  ctx.lineWidth = 1; for (let k = -s; k < s; k += 4.5) { ctx.beginPath(); ctx.moveTo(x + k + 4, g); ctx.lineTo(x + k, g + 5); ctx.stroke(); }
  ctx.beginPath(); ctx.arc(x, y, 2.4, 0, 2 * Math.PI); ctx.fillStyle = '#fff'; ctx.fill(); ctx.stroke();
  ctx.restore();
}
/* a fixed (clamped) end at x, facing dir = +1 (wall on the left) or -1 */
function fixedEnd(x, y, o = {}) {
  const { h = 30, dir = 1, color = C.ink, alpha = 1 } = o;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.lineWidth = 1.6;
  ctx.beginPath(); ctx.moveTo(x, y - h / 2); ctx.lineTo(x, y + h / 2); ctx.stroke(); ctx.lineWidth = 1;
  for (let k = -h / 2; k < h / 2; k += 4.5) { ctx.beginPath(); ctx.moveTo(x, y + k + 4); ctx.lineTo(x - dir * 5, y + k); ctx.stroke(); }
  ctx.restore();
}
/* a dimension line |<- label ->| between x1 and x2 at height y */
function dim(x1, x2, y, label, o = {}) {
  const { color = C.ink, alpha = 1, size = 17 } = o;
  arrow(x1, y, x2, y, { color, width: 1.1, head: 7, both: true, alpha });
  line([[x1, y - 6], [x1, y + 6]], { color, width: 1, alpha }); line([[x2, y - 6], [x2, y + 6]], { color, width: 1, alpha });
  if (label) {
    ctx.save(); ctx.globalAlpha *= alpha; ctx.font = font({ size }); ctx.restore();
    const w = math(label, 0, -1e4, { size, alpha: 0 });
    // the knockout covers the label's whole ink, superscripts to subscripts and the
    // slash's tail (baseline y + .34 size; ink from .95 size above it to .45 below)
    ctx.save(); ctx.fillStyle = '#fff'; ctx.globalAlpha *= alpha; ctx.fillRect((x1 + x2) / 2 - w / 2 - 4, y - size * .62, w + 8, size * 1.42); ctx.restore();
    math(label, (x1 + x2) / 2, y + size * .34, { size, align: 'center', color, alpha });
  }
}

/* ---------------------------------------------------------------- axes
   axes(o) draws a pgfplots axis: a full box, ticks pointing in, numeric
   tick labels, labels in math, and returns {X, Y, inside} to map data to
   the canvas. o = {x, y, w, h, xlim, ylim, xticks, yticks, xlabel, ylabel,
   xfmt, yfmt, grid, progress, alpha, ylog}. */
function axes(o) {
  const { x, y, w, h, xlim, ylim, xticks = [], yticks = [], xlabel = '', ylabel = '',
          xfmt = v => fmt(v), yfmt = v => fmt(v), grid = false, progress = 1, alpha = 1,
          box = true, tickSize = 15, labelSize = 17 } = o;
  const X = v => x + (v - xlim[0]) / (xlim[1] - xlim[0]) * w;
  const Y = v => y + h - (v - ylim[0]) / (ylim[1] - ylim[0]) * h;
  if (progress > 0) {
    const a = alpha * clamp(progress * 1.4);
    if (grid) {
      for (const v of xticks) line([[X(v), y], [X(v), y + h]], { color: C.grid, width: 1, alpha: a });
      for (const v of yticks) line([[x, Y(v)], [x + w, Y(v)]], { color: C.grid, width: 1, alpha: a });
    }
    const frame = box ? [[x, y + h], [x + w, y + h], [x + w, y], [x, y], [x, y + h]] : null;
    if (box) line(frame, { color: C.ink, width: 1.3, progress, alpha });
    else { line([[x, y + h], [x + w, y + h]], { color: C.ink, width: 1.3, progress, alpha }); line([[x, y + h], [x, y]], { color: C.ink, width: 1.3, progress, alpha }); }
    for (const v of xticks) {
      line([[X(v), y + h], [X(v), y + h - 5]], { color: C.ink, width: 1.1, alpha: a });
      if (box) line([[X(v), y], [X(v), y + 5]], { color: C.ink, width: 1.1, alpha: a });
      math(xfmt(v), X(v), y + h + tickSize + 6, { size: tickSize, align: 'center', alpha: a });
    }
    for (const v of yticks) {
      line([[x, Y(v)], [x + 5, Y(v)]], { color: C.ink, width: 1.1, alpha: a });
      if (box) line([[x + w, Y(v)], [x + w - 5, Y(v)]], { color: C.ink, width: 1.1, alpha: a });
      math(yfmt(v), x - 8, Y(v) + tickSize * .35, { size: tickSize, align: 'right', alpha: a });
    }
    if (xlabel) math(xlabel, x + w / 2, y + h + tickSize + labelSize + 16, { size: labelSize, align: 'center', alpha: a });
    if (ylabel) math(ylabel, x - (o.ylabelGap || 48), y + h / 2, { size: labelSize, align: 'center', rot: -Math.PI / 2, alpha: a });
  }
  const inside = f => { ctx.save(); ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip(); f(); ctx.restore(); };
  return { X, Y, inside };
}
function fmt(v) {
  if (Math.abs(v) < 1e-12) return '0';
  const s = Math.abs(v) >= 100 || Number.isInteger(v) ? String(Math.round(v)) : String(+v.toPrecision(3));
  return s.replace('-', '−');
}

/* ---------------------------------------------------------------- colour
   diverging(v), v in [-1, 1]: navy, white, the warm accent, for a signed
   field (displacement, pressure). seq(v), v in [0, 1]: white to navy. The
   LUTs, 256 entries of r, g, b, colour an ImageData without a call per pixel. */
const _hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
function _ramp(stops) {
  const lut = new Uint8ClampedArray(256 * 3);
  for (let i = 0; i < 256; i++) {
    const u = i / 255 * (stops.length - 1), k = Math.min(stops.length - 2, Math.floor(u)), s = u - k;
    for (let c = 0; c < 3; c++) lut[i * 3 + c] = Math.round(lerp(stops[k][c], stops[k + 1][c], s));
  }
  return lut;
}
/* blue and crimson arms matched stop for stop in CIELAB lightness (19, 43, 75),
   so a value and its negative weigh the same */
const DIVERGING = _ramp(['#043052', '#2E6A9E', '#9CBBD6', '#FFFFFF', '#DEABAB', '#B03F4D', '#651020'].map(_hex));
const SEQ = _ramp(['#FFFFFF', '#C9D7E4', '#5B8DB8', '#095A94', '#043052'].map(_hex));
function _lutc(lut, u) { const i = Math.round(clamp(u) * 255) * 3; return `rgb(${lut[i]},${lut[i + 1]},${lut[i + 2]})`; }
const diverging = v => _lutc(DIVERGING, (v + 1) / 2);
const seq = v => _lutc(SEQ, v);

/* ---------------------------------------------------------------- data
   b64f32(s): a Float32Array from base64, for arrays too long for JSON. */
function b64f32(s) { const b = atob(s), u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return new Float32Array(u.buffer); }
function b64i8(s) { const b = atob(s), u = new Int8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = (b.charCodeAt(i) << 24) >> 24; return u; }
