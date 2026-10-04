/* The deck's animation runtime (DECK_BRIEF.md "Animated slides"). An animated
   slide has its own page, anim/<stem>.html (render.py writes it): the slide
   as the deck renders it, its config in <script id="deck-anim">, deck.js (the
   wires) and this. It plays the slide from its first moment to its last,
   and its last moment is the slide's photograph: every mark ends where the
   picture has it, and then nothing the runtime set is left on the page.

   What plays (times in seconds):
     data-anim   on a figure's mark or label (fig.py writes it): a list of
                 specs, their times from the figure's start. draw (a stroke
                 draws itself, its dashes kept), pop (it fades in and
                 settles: a mark from 60 % of its size, a label from 10 px
                 below), fade, out (a ghost leaves), wipe (uncovered from a
                 side, eased or at a steady pace), grow (from its base, on a spring) and keys (a value
                 from keyframe to keyframe: where it is, a bar's height, how
                 much of a stroke, opacity, scale, a path's data, a number).
     data-ghost  a mark only the playing slide shows; it must leave (out)
                 before the end, and the picture never has it.
     data-in     on any element of the slide: it arrives then (a number, a
                 figure's cue (letters, digits, _), or a cue plus or minus
                 seconds: "hour+0.3"),
                 as data-as says: pop (the default), fade, wipe, draw (a
                 stroke), none (a figure's wrapper that only starts its
                 figure's clock). data-dur sets how long. A wire with
                 data-in (deck.js) draws itself and its tip comes as it
                 arrives. A figure's clock starts at its wrapper's data-in.
   The springs are Motion's (motion 12.43.0's spring(), bounce 0): a value
   let go at t0 is where it goes after `visual` seconds and exactly there
   once within 0.005 of it and slower than 0.01 a second (fig.py
   spring_done() has the same rule). Strokes and wipes ease in and out, as
   the site's figures do (tools/numfig/engine.js seg()). Every frame is a
   pure function of the clock, so any moment can be drawn exactly.

   The page: ?t=end shows the last moment, ?t=<s> holds that moment, ?wait
   holds the first until DeckAnim.play() (or a message {deckAnim: 'play'}),
   ?speed=<k> plays k times as fast; otherwise it plays once from the start.
   A reader who asks for less motion sees the slide at once. In a frame it
   tells its parent {deckAnim: 'ready' | 'done', stem, length}, and takes
   {deckAnim: 'play' | 'finish'} and {deckAnim: 'seek', t}.

   window.DeckAnim: state (wait, ready, playing, held, done), length,
   seek(t), play(), finish(), report() (what render.py checks: the length,
   the end, the actors, the cues, the schedule, moments worth a frame,
   problems, and the words only the playing slide shows), and, as it plays,
   running (a frame is asked for), frames (drawn) and slowest (ms, the
   longest frame's own work). */
(function () {
  'use strict';
  var root = document.documentElement;
  var slide = document.querySelector('.slide');
  var cfgEl = document.getElementById('deck-anim');
  var cfg = {};
  try { cfg = JSON.parse(cfgEl ? cfgEl.textContent : '{}'); } catch (e) { cfg = {}; }
  var q = new URLSearchParams(location.search);
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var LENGTH = +cfg.length || 0;
  var problems = [];
  if (!(LENGTH > 0)) problems.push('the slide has no length (ANIM["length"], seconds)');

  // ------------------------------------------------------------ time
  function clamp(x, a, b) { return Math.min(b === undefined ? 1 : b, Math.max(a || 0, x)); }
  function easeInOut(x) { return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
  function easeOut(x) { return 1 - Math.pow(1 - x, 3); }
  function seg(tau, d) { return d > 0 ? easeInOut(clamp(tau / d)) : (tau >= 0 ? 1 : 0); }
  // Motion's spring, bounce 0 (critically damped), from rest at 0 to 1
  function spring(tau, visual) {
    if (tau <= 0) return 0;
    var w = 2 * Math.PI / (1.2 * visual), x = w * tau, e = Math.exp(-x);
    if (e * (1 + x) <= .005 && w * w * tau * e <= .01) return 1;
    return 1 - e * (1 + x);
  }
  function springDone(visual) {
    var w = 2 * Math.PI / (1.2 * visual), t = visual;
    while (!(Math.exp(-w * t) * (1 + w * t) <= .005 && w * w * t * Math.exp(-w * t) <= .01)) t += .001;
    return t;
  }

  // ------------------------------------------------------------ cues and starts
  var cues = {};
  function parseIn(s) {
    var m = /^\s*(?:([A-Za-z_]\w*)\s*)?(?:([+-])?\s*(\d*\.?\d+))?\s*$/.exec(String(s));
    if (!m || (!m[1] && m[3] === undefined)) return {bad: true};
    var off = m[3] === undefined ? 0 : (m[2] === '-' ? -1 : 1) * parseFloat(m[3]);
    if (m[1] && !m[2] && m[3] !== undefined) return {bad: true};   // "cue 3": plus or minus
    return {cue: m[1] || null, off: off};
  }
  function resolveIn(s) {
    var p = parseIn(s);
    if (p.bad) return NaN;
    if (!p.cue) return p.off;
    return p.cue in cues ? cues[p.cue] + p.off : NaN;
  }
  // a figure's clock: the data-in of its wrapper (or itself), else 0
  function figStart(fig) {
    var w = fig.closest('[data-in]');
    if (!w || !slide.contains(w)) return 0;
    var t = resolveIn(w.dataset.in);
    return isNaN(t) ? NaN : t;
  }
  function resolveCues() {
    var figs = [].slice.call(slide.querySelectorAll('.fig[data-cues]'));
    for (var pass = 0; pass < 8; pass++) {
      var changed = false;
      figs.forEach(function (f) {
        var own; try { own = JSON.parse(f.dataset.cues); } catch (e) { own = {}; }
        var t0 = figStart(f);
        if (isNaN(t0)) return;
        Object.keys(own).forEach(function (k) {
          var v = t0 + (+own[k]);
          if (cues[k] !== v) { cues[k] = v; changed = true; }
        });
      });
      if (!changed) break;
    }
  }

  // ------------------------------------------------------------ actors
  var NS = 'http://www.w3.org/2000/svg';
  var actors = [], ghostText = [], uid = 0;
  function isSvg(el) { return el instanceof SVGElement; }
  function what(el) {
    if (el.id) return '#' + el.id;
    var c = el.getAttribute('class');
    return el.tagName.toLowerCase() + (c ? '.' + c.trim().split(/\s+/).join('.') : '');
  }
  function num(v, nd) {
    var s;
    if (nd === undefined || nd === null) {
      s = Math.abs(v - Math.round(v)) < 1e-9 ? String(Math.round(v)) : v.toFixed(6).replace(/0+$/, '').replace(/\.$/, '');
    } else s = v.toFixed(nd);
    return s.replace('-', '−');
  }
  var NUM = /[-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/gi;
  function shape(d) {
    var nums = (String(d).match(NUM) || []).map(Number);
    return {tpl: String(d).split(NUM), nums: nums};
  }

  // the weight of each keyframe at clock T: settle (a spring from each), smooth
  // (eased between neighbours), linear, step
  function weights(K, T) {
    var ts = K.t, n = ts.length, w = new Array(n).fill(0), e = K.e || 'settle', k;
    if (e === 'settle') {
      var vd = K.vd || .3, prev = 1;
      for (k = 1; k < n; k++) { var s = spring(T - ts[k], vd); w[k - 1] += prev - s; prev = s; }
      w[n - 1] += prev;
      return w;
    }
    if (T <= ts[0]) { w[0] = 1; return w; }
    if (T >= ts[n - 1]) { w[n - 1] = 1; return w; }
    for (k = 1; k < n; k++) if (T < ts[k]) break;
    if (e === 'step') { w[k - 1] = 1; return w; }
    var u = (T - ts[k - 1]) / Math.max(1e-9, ts[k] - ts[k - 1]);
    if (e === 'smooth') u = easeInOut(u);
    w[k - 1] = 1 - u; w[k] = u;
    return w;
  }
  function mixKeys(K, T) {
    var w = weights(K, T), v = K.v;
    if (K.p === 'd') {
      var out = K.shapes[0].nums.map(function () { return 0; });
      w.forEach(function (wk, k) { if (wk) K.shapes[k].nums.forEach(function (x, i) { out[i] += wk * x; }); });
      var tpl = K.shapes[K.shapes.length - 1].tpl, s = tpl[0];
      for (var i = 0; i < out.length; i++) s += (Math.round(out[i] * 100) / 100) + tpl[i + 1];
      return s;
    }
    if (K.p === 'xy') {
      var xy = [0, 0];
      w.forEach(function (wk, k) { xy[0] += wk * v[k][0]; xy[1] += wk * v[k][1]; });
      return xy;
    }
    var x = 0;
    w.forEach(function (wk, k) { x += wk * v[k]; });
    return x;
  }

  function Actor(el, parts, ghost, label) {
    this.el = el; this.parts = parts; this.ghost = ghost; this.label = label || what(el);
    this.svg = isSvg(el);
    this.last = '';
    var cs = getComputedStyle(el);
    this.opacity = parseFloat(cs.opacity);
    if (isNaN(this.opacity)) this.opacity = 1;
    this.orig = {
      transform: el.getAttribute('transform'), dash: el.getAttribute('stroke-dasharray'),
      clip: el.getAttribute('clip-path'), d: el.getAttribute('d'), text: null
    };
    if (this.svg) {
      var shown = ghost && el.getAttribute('display') === 'none';
      if (shown) el.removeAttribute('display');
      try { this.bb = el.getBBox(); } catch (e) { this.bb = {x: 0, y: 0, width: 0, height: 0}; }
      var stroke = el.getAttribute('stroke') || cs.stroke, fill = el.getAttribute('fill') || cs.fill;
      this.stroked = !!stroke && stroke !== 'none';
      this.filled = !!fill && fill !== 'none' && fill !== 'transparent';
      this.sw = parseFloat(el.getAttribute('stroke-width') || cs.strokeWidth) || 0;
      this.len = this.stroked && el.getTotalLength ? el.getTotalLength() : 0;
      this.pattern = this.orig.dash ? this.orig.dash.split(/[\s,]+/).map(Number).filter(function (x) { return x >= 0; }) : null;
      if (this.pattern && this.pattern.length % 2) this.pattern = this.pattern.concat(this.pattern);
      if (shown) el.setAttribute('display', 'none');
    }
    // when it has arrived and when it is exactly at rest
    var start = Infinity, done = -Infinity;
    parts.forEach(function (p) {
      var a = p.t0, z;
      if (p.k === 'keys') { a = p.t[0]; z = p.t[p.t.length - 1] + ((p.e || 'settle') === 'settle' ? springDone(p.vd || .3) : 0); }
      else if (p.k === 'pop' || p.k === 'grow') z = p.t0 + springDone(p.v);
      else z = p.t0 + (p.d || 0);
      start = Math.min(start, a); done = Math.max(done, z);
    });
    this.start = start; this.done = done;
    this.out = parts.filter(function (p) { return p.k === 'out'; })[0] || null;
  }

  // the state of an actor at clock T: opacity, where it is, its size, how
  // much of its stroke, how much is uncovered, its path, its number
  Actor.prototype.at = function (T) {
    var s = {o: 1, dx: 0, dy: 0, sc: 1, sy: 1, by: null, p: 1, wipe: null, d: null, text: null, rise: 0, on: true};
    var self = this;
    this.parts.forEach(function (p) {
      var tau = T - p.t0;
      switch (p.k) {
        case 'draw':                          // a stroke draws itself; a fill fades in with it
          if (self.svg && self.stroked) s.p *= seg(tau, p.d);
          if (!(self.svg && self.stroked) || self.filled) s.o *= seg(tau, p.d);
          break;
        case 'pop':
          var sp = spring(tau, p.v);
          s.o *= tau <= 0 ? 0 : easeOut(clamp(tau / (.6 * p.v)));
          if (self.svg) s.sc *= .6 + .4 * sp;
          else s.rise += (1 - sp) * (self.block ? 16 : 10);
          break;
        case 'fade': s.o *= seg(tau, p.d); break;
        case 'out': s.o *= 1 - seg(tau, p.d); if (tau >= p.d) s.on = false; break;
        case 'wipe':                          // eased, or at a steady pace (e: 'linear')
          s.wipe = {r: p.e === 'linear' ? (p.d > 0 ? clamp(tau / p.d) : +(tau >= 0)) : seg(tau, p.d),
                    dir: p.dir || 'right'};
          break;
        case 'grow':
          s.sy *= spring(tau, p.v);
          if (tau <= 0) s.o = 0;               // a bar of no height would still show its stroke
          if (p.b !== undefined) s.by = p.b;
          break;
        case 'keys':
          var v = mixKeys(p, T);
          if (p.p === 'xy') { s.dx += v[0]; s.dy += v[1]; }
          else if (p.p === 'x') s.dx += v;
          else if (p.p === 'y') s.dy += v;
          else if (p.p === 'o') s.o *= v;
          else if (p.p === 's') s.sc *= v;
          else if (p.p === 'p') { if (self.svg && self.stroked) s.p *= clamp(v); else s.o *= clamp(v); }
          else if (p.p === 'h') { s.sy *= p.last ? v / p.last : 1; if (p.b !== undefined) s.by = p.b; }
          else if (p.p === 'd') s.d = v;
          else if (p.p === 'text') s.text = num(v, p.nd);
          break;
      }
    });
    if (this.ghost) {
      var first = Math.min.apply(null, this.parts.filter(function (p) { return p.k !== 'out'; })
        .map(function (p) { return p.k === 'keys' ? p.t[0] : p.t0; }).concat([Infinity]));
      if (T < first) s.on = false;
    }
    return s;
  };

  // the dash pattern of a stroke drawn to p of its length: its own dashes
  // up to there (the last one cut), then one gap to the end. A drawing that
  // stops in a gap ends on the dash before it: a dash of no length would
  // still draw a round cap's dot.
  function dashes(pattern, len, p) {
    var L = p * len, big = Math.ceil(len + 1), r = function (x) { return Math.round(x * 100) / 100; };
    if (L <= 0) return '0 ' + big;
    var total = pattern ? pattern.reduce(function (a, b) { return a + b; }, 0) : 0;
    if (!(total > 0)) return r(L) + ' ' + big;
    var out = [], acc = 0;
    for (var i = 0; acc < L; i++) {
      var s = pattern[i % pattern.length];
      if (i % 2 === 0) { var take = Math.min(s, L - acc); out.push(take); acc += take; if (take < s) break; }
      else { if (acc + s >= L) break; out.push(s); acc += s; }
    }
    out.push(big);                              // out ended on a dash
    return out.map(r).join(' ');
  }

  Actor.prototype.apply = function (T, final) {
    var el = this.el;
    if (final || T >= this.done) { this.clear(); return; }
    var s = this.at(T);
    var key = [s.o, s.dx, s.dy, s.sc, s.sy, s.by, s.p, s.wipe && s.wipe.r, s.d, s.text, s.rise, s.on].join('|');
    if (key === this.last) return;
    this.last = key;
    var op = this.opacity * clamp(s.o);
    if (this.ghost) {
      if (this.svg) { if (s.on) el.removeAttribute('display'); else el.setAttribute('display', 'none'); }
      else el.hidden = !s.on;
    }
    el.style.opacity = String(Math.round(op * 1000) / 1000);
    if (this.svg) {
      var bb = this.bb, tf = [];
      if (s.dx || s.dy) tf.push('translate(' + s.dx.toFixed(2) + ' ' + s.dy.toFixed(2) + ')');
      if (s.sc !== 1) {
        var cx = bb.x + bb.width / 2, cy = bb.y + bb.height / 2;
        tf.push('translate(' + cx.toFixed(2) + ' ' + cy.toFixed(2) + ') scale(' + s.sc.toFixed(4) + ') translate(' +
                (-cx).toFixed(2) + ' ' + (-cy).toFixed(2) + ')');
      }
      if (s.sy !== 1) {
        var b = s.by === null ? bb.y + bb.height : s.by;
        tf.push('translate(0 ' + b.toFixed(2) + ') scale(1 ' + Math.max(s.sy, 1e-4).toFixed(4) + ') translate(0 ' + (-b).toFixed(2) + ')');
      }
      if (this.orig.transform) tf.push(this.orig.transform);
      if (tf.length) el.setAttribute('transform', tf.join(' ')); else el.removeAttribute('transform');
      if (this.len && s.p < 1) {
        el.setAttribute('stroke-dasharray', dashes(this.pattern, this.len, Math.max(0, s.p)));
        el.style.visibility = s.p <= 0 ? 'hidden' : '';
      } else {
        if (this.orig.dash === null) el.removeAttribute('stroke-dasharray'); else el.setAttribute('stroke-dasharray', this.orig.dash);
        el.style.visibility = '';
      }
      if (s.wipe) this.wipeSvg(s.wipe); else if (this.clipRect) { this.restoreClip(); }
      if (s.d !== null) el.setAttribute('d', s.d);
    } else {
      el.style.translate = (s.dx || s.dy || s.rise) ? s.dx.toFixed(2) + 'px ' + (s.dy + s.rise).toFixed(2) + 'px' : '';
      el.style.scale = s.sc !== 1 || s.sy !== 1 ? s.sc.toFixed(4) + ' ' + (s.sc * s.sy).toFixed(4) : '';
      if (s.wipe) {
        var r = (1 - s.wipe.r) * 100, d = s.wipe.dir;
        el.style.clipPath = 'inset(' + (d === 'down' ? '0 0 ' + r + '% 0' : d === 'up' ? r + '% 0 0 0' :
          d === 'left' ? '0 0 0 ' + r + '%' : '0 ' + r + '% 0 0') + ')';
      } else el.style.clipPath = '';
      if (s.text !== null) this.setText(s.text);
    }
  };

  Actor.prototype.wipeSvg = function (w) {
    var el = this.el, bb = this.bb, m = this.sw / 2 + 2;
    if (!this.clipRect) {
      var sv = el.ownerSVGElement, defs = sv.querySelector('defs');
      if (!defs) { defs = document.createElementNS(NS, 'defs'); sv.insertBefore(defs, sv.firstChild); }
      var cp = document.createElementNS(NS, 'clipPath');
      cp.id = 'deck-wipe-' + (++uid);
      cp.setAttribute('clipPathUnits', 'userSpaceOnUse');
      this.clipRect = document.createElementNS(NS, 'rect');
      cp.appendChild(this.clipRect); defs.appendChild(cp);
      this.clipId = cp.id;
      el.setAttribute('clip-path', 'url(#' + cp.id + ')');
    }
    var x = bb.x - m, y = bb.y - m, W = bb.width + 2 * m, H = bb.height + 2 * m, r = w.r;
    var R = w.dir === 'left' ? [x + W * (1 - r), y, W * r, H] : w.dir === 'up' ? [x, y + H * (1 - r), W, H * r] :
            w.dir === 'down' ? [x, y, W, H * r] : [x, y, W * r, H];
    ['x', 'y', 'width', 'height'].forEach(function (a, i) { this.clipRect.setAttribute(a, R[i].toFixed(2)); }, this);
  };
  Actor.prototype.restoreClip = function () {
    var cp = this.clipRect && this.clipRect.parentNode;
    if (cp && cp.parentNode) cp.parentNode.removeChild(cp);
    this.clipRect = null;
    if (this.orig.clip === null) this.el.removeAttribute('clip-path'); else this.el.setAttribute('clip-path', this.orig.clip);
  };
  Actor.prototype.setText = function (s) {
    if (this.orig.text === null) this.orig.text = this.el.textContent;
    if (this.el.textContent !== s) this.el.textContent = s;
  };
  // back to the slide as the picture has it
  Actor.prototype.clear = function () {
    if (this.last === 'clear') return;
    this.last = 'clear';
    var el = this.el;
    el.style.opacity = ''; el.style.visibility = '';
    if (this.svg) {
      if (this.orig.transform === null) el.removeAttribute('transform'); else el.setAttribute('transform', this.orig.transform);
      if (this.orig.dash === null) el.removeAttribute('stroke-dasharray'); else el.setAttribute('stroke-dasharray', this.orig.dash);
      if (this.clipRect) this.restoreClip();
      if (this.orig.d !== null && el.getAttribute('d') !== this.orig.d) el.setAttribute('d', this.orig.d);
      if (this.ghost) el.setAttribute('display', 'none');
    } else {
      el.style.translate = ''; el.style.scale = ''; el.style.clipPath = '';
      if (this.orig.text !== null) this.setText(this.orig.text);
      if (this.ghost) el.hidden = true;
    }
    if (!el.getAttribute('style')) el.removeAttribute('style');
  };

  // an element's specs, their times made the slide's
  function specsOf(el) {
    var raw;
    try { raw = JSON.parse(el.dataset.anim); } catch (e) { problems.push('unreadable data-anim on ' + what(el)); return []; }
    var fig = el.closest('.fig'), t0 = fig ? figStart(fig) : 0;
    if (isNaN(t0)) { problems.push('the figure of ' + what(el) + ' starts at a cue no figure has'); t0 = 0; }
    return raw.map(function (p) {
      var q_ = Object.assign({}, p);
      if (p.k === 'keys') {
        q_.t = p.t.map(function (x) { return x + t0; });
        q_.t0 = q_.t[0];
        if (p.p === 'd') q_.shapes = p.v.map(shape);
        if (p.p === 'h') q_.last = p.v[p.v.length - 1];
      } else q_.t0 = (p.t || 0) + t0;
      return q_;
    });
  }
  var KINDS = ['draw', 'pop', 'fade', 'out', 'wipe', 'grow', 'keys'];
  var PROPS = ['xy', 'x', 'y', 'h', 'p', 'o', 's', 'd', 'text'];

  function arrival(el) {
    var t = resolveIn(el.dataset.in);
    if (isNaN(t)) { problems.push('data-in="' + el.dataset.in + '" on ' + what(el) + ' names no cue of a figure'); return null; }
    var as = el.dataset.as || (el.closest('svg') ? 'draw' : 'pop');
    var dur = el.dataset.dur !== undefined ? +el.dataset.dur : null;
    if (as === 'none') return [];
    if (as === 'pop') return [{k: 'pop', t0: t, v: dur || .45}];
    if (as === 'fade') return [{k: 'fade', t0: t, d: dur || .4}];
    if (as === 'draw') return [{k: 'draw', t0: t, d: dur || .5}];
    if (as === 'head') { var d = dur || .5; return [{k: 'fade', t0: t + .8 * d, d: Math.max(.12, .2 * d)}]; }
    if (/^wipe(-(right|left|up|down))?$/.test(as)) return [{k: 'wipe', t0: t, d: dur || .6, dir: as.split('-')[1] || 'right'}];
    problems.push('data-as="' + as + '" on ' + what(el) + ' is not pop, fade, draw, wipe or none');
    return [];
  }

  function collect() {
    resolveCues();
    var seen = new Map();
    function add(el, parts, label) {
      if (!parts.length) return;
      var a = seen.get(el);
      if (a) { a.push.apply(a, parts); return; }
      seen.set(el, parts.slice());
      order.push({el: el, label: label});
    }
    var order = [];
    [].forEach.call(slide.querySelectorAll('[data-in]'), function (el) {
      var parts = arrival(el);
      if (parts) add(el, parts);
    });
    [].forEach.call(slide.querySelectorAll('[data-anim]'), function (el) {
      var parts = specsOf(el).filter(function (p) {
        if (KINDS.indexOf(p.k) < 0) { problems.push('an unknown kind "' + p.k + '" on ' + what(el)); return false; }
        if (p.k === 'keys' && PROPS.indexOf(p.p) < 0) { problems.push('keys on an unknown value "' + p.p + '" on ' + what(el)); return false; }
        return true;
      });
      add(el, parts);
    });
    [].forEach.call(slide.querySelectorAll('[data-ghost]'), function (el) {
      if (!seen.has(el)) problems.push('a ghost with nothing to play: ' + what(el));
    });
    order.forEach(function (o) {
      var el = o.el, ghost = el.hasAttribute('data-ghost');
      var a = new Actor(el, seen.get(el), ghost, o.label);
      a.block = !a.svg && !el.closest('.fig');
      actors.push(a);
      if (!ghost && a.out) problems.push('out() on ' + a.label + ', which is not a ghost: the slide keeps it');
      if (ghost) {
        if (!a.out) problems.push('a ghost that never leaves: ' + a.label);
        if (!a.svg && el.textContent.trim()) ghostText.push(el.textContent.trim());
      }
      if (a.done > LENGTH + 1e-3) problems.push(a.label + ' still moves at ' + a.done.toFixed(2) + ' s, after the slide ends (' + LENGTH + ' s)');
      a.parts.forEach(function (p) {
        if (p.k !== 'keys') return;
        var last = p.v[p.v.length - 1], bad = null;
        if (p.p === 'xy' && (Math.abs(last[0]) > .01 || Math.abs(last[1]) > .01)) bad = last.join(', ');
        else if ((p.p === 'x' || p.p === 'y') && Math.abs(last) > .01) bad = last;
        else if ((p.p === 'o' || p.p === 's' || p.p === 'p') && Math.abs(last - 1) > 1e-6) bad = last;
        else if (p.p === 'h' && a.svg && Math.abs(last - a.bb.height) > .6) bad = last + ' px against ' + a.bb.height.toFixed(1);
        else if (p.p === 'd' && p.shapes[p.shapes.length - 1].nums.join(' ') !== shape(a.orig.d).nums.join(' ')) bad = 'another path';
        else if (p.p === 'text' && num(last, p.nd) !== el.textContent.trim()) bad = num(last, p.nd) + ' against ' + el.textContent.trim();
        if (p.p === 'd' && p.shapes.some(function (sh) { return sh.tpl.join('#') !== p.shapes[0].tpl.join('#'); }))
          problems.push('keys on the path of ' + a.label + ': its shapes differ');
        if (bad !== null) problems.push('keys on ' + p.p + ' of ' + a.label + ' end at ' + bad + ', not where the slide has it');
      });
    });
  }

  // ------------------------------------------------------------ the clock
  var state = 'wait', T = 0, raf = 0, from = 0, t0 = 0, speed = +q.get('speed') || 1;
  var api = {state: 'wait', length: LENGTH, running: false, frames: 0, slowest: 0};
  function draw(t) {
    var w0 = performance.now(), final = t >= LENGTH;
    T = Math.min(t, LENGTH);
    for (var i = 0; i < actors.length; i++) actors[i].apply(T, final);
    return performance.now() - w0;
  }
  function tell(msg) {
    if (window.parent === window) return;
    try { window.parent.postMessage({deckAnim: msg, stem: cfg.stem, length: LENGTH}, '*'); } catch (e) {}
  }
  function set(s) { state = api.state = s; root.dataset.animState = s; }
  function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; api.running = false; }
  function tick(now) {
    raf = 0; api.running = false;
    var t = from + (now - t0) / 1000 * speed;
    var ms = draw(t);
    api.frames++; api.slowest = Math.max(api.slowest, Math.round(ms * 10) / 10);
    if (t >= LENGTH) { set('done'); tell('done'); return; }
    raf = requestAnimationFrame(tick); api.running = true;
  }
  api.play = function () {
    stop();
    if (T >= LENGTH) T = 0;
    from = T; set('playing');
    raf = requestAnimationFrame(function (now) { t0 = now; tick(now); });
    api.running = true;
  };
  api.seek = function (t) {
    stop();
    var x = t === 'end' ? LENGTH : +t;
    draw(x);
    set(x >= LENGTH ? 'done' : 'held');
  };
  api.finish = function () { var was = state; api.seek('end'); if (was !== 'done') tell('done'); };
  api.report = function () {
    var sched = actors.map(function (a) { return [Math.round(a.start * 1000) / 1000, Math.round(a.done * 1000) / 1000, a.label]; })
      .sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
    // a moment worth a frame: each group of arrivals, part of the way in
    var starts = sched.map(function (s) { return s[0]; }), moments = [];
    starts.forEach(function (s) { if (!moments.length || s - moments[moments.length - 1] > .25) moments.push(s); });
    moments = moments.map(function (s) { return Math.round(Math.min(LENGTH, s + .3) * 100) / 100; });
    if (moments.length > 16) moments = moments.filter(function (_, i) { return i % Math.ceil(moments.length / 16) === 0; });
    (cfg.frames || []).forEach(function (m) { moments.push(+m); });
    return {length: LENGTH, end: Math.round(Math.max.apply(null, actors.map(function (a) { return a.done; }).concat([0])) * 1000) / 1000,
            actors: actors.length, cues: cues, schedule: sched, frames: moments,
            problems: problems.slice(), ghostText: ghostText.slice()};
  };
  window.DeckAnim = api;

  // ------------------------------------------------------------ the page
  function fit() {
    var k = Math.min(innerWidth / 1920, innerHeight / 1080);
    slide.style.transform = Math.abs(k - 1) < 1e-6 ? '' : 'scale(' + k + ')';
  }
  addEventListener('resize', fit);
  addEventListener('message', function (e) {
    var m = e.data && e.data.deckAnim;
    if (!m || state === 'wait') return;
    if (m === 'play') api.play();
    else if (m === 'finish') api.finish();
    else if (m === 'seek') api.seek(e.data.t);
  });

  function start() {
    fit();
    collect();
    var at = q.get('t'), end = reduce || at === 'end' || q.has('still');
    if (end) api.seek('end');
    else if (at !== null) api.seek(+at);
    else draw(0);
    root.classList.remove('anim-wait');
    root.dataset.anim = 'ready';
    if (end) { tell('ready'); tell('done'); return; }
    if (at !== null) { tell('ready'); return; }
    set('ready');
    tell('ready');
    if (!q.has('wait')) api.play();
  }
  // after deck.js has drawn the wires on the settled layout
  (function wait() { if (window.DECK_READY === true) start(); else requestAnimationFrame(wait); })();
})();
