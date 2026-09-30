/* The deck's page script, run by render.py in Chromium on every slide.

   1. Wires: each <i class="wire" data-from="#a" data-to="#b"> becomes an
      arrow drawn from the edge of #a to the edge of #b, after the fonts have
      settled the layout, with TikZ's Stealth tip. Attributes:
        data-from, data-to     selectors of the two boxes
        data-from-side, data-to-side   right|left|top|bottom (default: the
                               facing sides)
        data-route             straight (default), -| (across, then up or
                               down) or |- (up or down, then across)
        data-at, data-at-to    where on the side, 0..1 (default: the middle
                               of the span the two boxes share, else .5)
        data-color             a token name: accent (default), navy, ink ...
        data-width             px, default 3
        data-gap               px left free before the tip, default 6
   2. deckInfo(): what render.py checks: every piece of text with its size and
      its boxes, and what overflows.
   A page may hold every slide, one under the other (render.py prints the
   deck from one such page): each slide's wires are drawn in its own
   coordinates. */
(function () {
  var slides = [].slice.call(document.querySelectorAll('.slide'));
  var slide = slides[0];
  var NS = 'http://www.w3.org/2000/svg';

  // an element's box, measured from the corner of `o` (a slide's box) if given
  function box(el, o) {
    var r = el.getBoundingClientRect(), x = o ? o.left : 0, y = o ? o.top : 0;
    return {l: r.left - x, t: r.top - y, r: r.right - x, b: r.bottom - y, w: r.width, h: r.height};
  }
  function css(name) { return getComputedStyle(document.documentElement).getPropertyValue('--' + name).trim(); }
  function stealth(x, y, ang, w) {
    var L = 6 * w + 4, W = 4.6 * w + 3, inset = .32 * L, c = Math.cos(ang), s = Math.sin(ang);
    function p(u, v) { return (x + u * c - v * s).toFixed(2) + ' ' + (y + u * s + v * c).toFixed(2); }
    return {d: 'M' + p(0, 0) + ' L' + p(-L, W / 2) + ' L' + p(-L + inset, 0) + ' L' + p(-L, -W / 2) + ' Z',
            back: L - inset};
  }
  function side(b, which, at) {
    if (which === 'right') return [b.r, b.t + b.h * at];
    if (which === 'left') return [b.l, b.t + b.h * at];
    if (which === 'top') return [b.l + b.w * at, b.t];
    return [b.l + b.w * at, b.b];
  }
  function facing(a, b) {
    if (b.l >= a.r - 1) return ['right', 'left'];
    if (a.l >= b.r - 1) return ['left', 'right'];
    if (b.t >= a.b - 1) return ['bottom', 'top'];
    return ['top', 'bottom'];
  }
  function drawWires(slide) {
    var old = slide.querySelector('svg.wires');
    if (old) old.remove();
    var wires = slide.querySelectorAll('.wire');
    if (!wires.length) return;
    var sv = document.createElementNS(NS, 'svg');
    sv.setAttribute('class', 'wires');
    sv.setAttribute('viewBox', '0 0 1920 1080');
    slide.appendChild(sv);
    var o = slide.getBoundingClientRect();
    [].forEach.call(wires, function (w) {
      var A = slide.querySelector(w.dataset.from), B = slide.querySelector(w.dataset.to);
      if (!A || !B) { w.dataset.error = 'missing box'; return; }
      var a = box(A, o), b = box(B, o), f = facing(a, b);
      var fs = w.dataset.fromSide || f[0], ts = w.dataset.toSide || f[1];
      var route = w.dataset.route || 'straight';
      var col = css(w.dataset.color || 'accent') || w.dataset.color, lw = +(w.dataset.width || 3);
      var gap = +(w.dataset.gap || 6);
      var at = w.dataset.at, atTo = w.dataset.atTo;
      var p0, p1, pts;
      if (route === 'straight') {
        if (at === undefined) {
          if (fs === 'right' || fs === 'left') {
            var lo = Math.max(a.t, b.t), hi = Math.min(a.b, b.b);
            var y = hi > lo ? (lo + hi) / 2 : (a.t + a.b) / 2;
            p0 = [fs === 'right' ? a.r : a.l, y]; p1 = [ts === 'left' ? b.l : b.r, y];
          } else {
            var lo2 = Math.max(a.l, b.l), hi2 = Math.min(a.r, b.r);
            var x = hi2 > lo2 ? (lo2 + hi2) / 2 : (a.l + a.r) / 2;
            p0 = [x, fs === 'bottom' ? a.b : a.t]; p1 = [x, ts === 'top' ? b.t : b.b];
          }
        } else {
          p0 = side(a, fs, +at); p1 = side(b, ts, atTo === undefined ? +at : +atTo);
        }
        pts = [p0, p1];
      } else {
        p0 = side(a, fs, at === undefined ? .5 : +at);
        p1 = side(b, ts, atTo === undefined ? .5 : +atTo);
        pts = route === '-|' ? [p0, [p1[0], p0[1]], p1] : [p0, [p0[0], p1[1]], p1];
      }
      // the tip stops `gap` short of the box it points at
      var n = pts.length, q = pts[n - 1], r = pts[n - 2];
      var ang = Math.atan2(q[1] - r[1], q[0] - r[0]);
      q = [q[0] - gap * Math.cos(ang), q[1] - gap * Math.sin(ang)];
      var tip = stealth(q[0], q[1], ang, lw);
      var end = [q[0] - tip.back * Math.cos(ang), q[1] - tip.back * Math.sin(ang)];
      var d = 'M' + pts.slice(0, n - 1).map(function (p) { return p[0].toFixed(2) + ' ' + p[1].toFixed(2); }).join(' L') +
              ' L' + end[0].toFixed(2) + ' ' + end[1].toFixed(2);
      var line = document.createElementNS(NS, 'path');
      line.setAttribute('d', d); line.setAttribute('fill', 'none'); line.setAttribute('stroke', col);
      line.setAttribute('stroke-width', lw); line.setAttribute('stroke-linejoin', 'miter');
      if (w.dataset.dash) line.setAttribute('stroke-dasharray', w.dataset.dash);
      sv.appendChild(line);
      var head = document.createElementNS(NS, 'path');
      head.setAttribute('d', tip.d); head.setAttribute('fill', col);
      sv.appendChild(head);
    });
  }

  // ------------------------------------------------------------ the checks
  // The block that holds a piece of text: a formula's pieces are one block,
  // an inline span belongs to its paragraph.
  function blockOf(el) {
    var m = el.closest('.m'); if (m) el = m.parentElement;
    while (el && el !== slide) {
      var d = getComputedStyle(el).display;
      if (d.indexOf('inline') !== 0 && d !== 'contents') return el;
      el = el.parentElement;
    }
    return slide;
  }
  function nameOf(el) {
    return el.id ? '#' + el.id : el.tagName.toLowerCase() +
      (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).join('.') : '');
  }
  window.deckInfo = function () {
    var S = box(slide), blocks = [], problems = [], lines = [], index = new Map();
    var foot = slide.querySelector('.foot'), body = slide.querySelector('.body');
    var fb = foot ? box(foot) : null;
    var walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT), node;
    while ((node = walker.nextNode())) {
      var el = node.parentElement;
      if (el.closest('script,style')) continue;
      var blk = blockOf(el);
      if (!node.nodeValue.trim()) {             // a space between two spans
        if (index.has(blk)) blocks[index.get(blk)].t += ' ';
        continue;
      }
      var cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none') continue;
      if (!index.has(blk)) {
        index.set(blk, blocks.length);
        blocks.push({t: '', px: 1e9, tick: !!blk.closest('.tk'), run: !!blk.closest('.run'),
                     transform: 'none', where: nameOf(blk), el: blk});
      }
      var k = index.get(blk), o = blocks[k];
      if (el.closest('.mk')) { o.t += node.nodeValue; continue; }   // an accent's mark, drawn by CSS
      // a sub- or superscript is read at its formula's size
      var sized = el.closest('.m') && el.closest('sub,sup') ? el.closest('.m') : el;
      o.t += node.nodeValue; o.px = Math.min(o.px, parseFloat(getComputedStyle(sized).fontSize));
      if (cs.textTransform !== 'none') o.transform = cs.textTransform;
      var rg = document.createRange(); rg.selectNodeContents(node);
      var bb = box(blk), turned = getComputedStyle(blk).transform;
      turned = turned && turned !== 'none' && !/^matrix\(1, 0, 0, 1,/.test(turned);
      [].forEach.call(rg.getClientRects(), function (r) {
        if (r.width < .5) return;
        lines.push({k: k, r: {l: r.left, t: r.top, r: r.right, b: r.bottom}});
        // text that runs out of its own box, or off the page's safe area
        if (!turned && (r.left < bb.l - 1.5 || r.right > bb.r + 1.5))
          problems.push('text runs out of its box: "' + node.nodeValue.trim().slice(0, 40) + '" in ' + nameOf(blk));
        if (r.left < S.l + 24 || r.right > S.r - 24 || r.top < S.t + 16 || r.bottom > S.b - 12)
          problems.push('text at the page edge: "' + node.nodeValue.trim().slice(0, 40) + '"');
      });
    }
    // every box inside the page; the body clear of the foot; nothing clipped
    [].forEach.call(slide.querySelectorAll('*'), function (el) {
      if (el.closest('svg') && el.tagName.toLowerCase() !== 'svg') return;
      if (el.classList.contains('wire')) return;
      var b = box(el);
      if (!b.w && !b.h) return;
      if (b.l < S.l - .5 || b.t < S.t - .5 || b.r > S.r + .5 || b.b > S.b + .5)
        problems.push('outside the slide: ' + nameOf(el));
      var cs = getComputedStyle(el);
      if (el !== slide && el.clientWidth > 0 && el.scrollWidth > el.clientWidth + 1 && cs.overflowX !== 'visible')
        problems.push('clipped across: ' + nameOf(el));
      if (el !== slide && el.clientHeight > 0 && el.scrollHeight > el.clientHeight + 1 && cs.overflowY !== 'visible')
        problems.push('clipped down: ' + nameOf(el));
      if (fb && body && el !== body && body.contains(el) && b.h > 0 && b.b > fb.t - 12)
        problems.push('reaches the foot: ' + nameOf(el) + ' (bottom ' + Math.round(b.b) + ', foot ' + Math.round(fb.t) + ')');
    });
    // leading: text that runs to two lines at 1.3 or more; a title or a
    // heading of 30 px and up may be tighter
    blocks.forEach(function (o, k) {
      var el = o.el, cs = getComputedStyle(el), fs = parseFloat(cs.fontSize), lh = parseFloat(cs.lineHeight);
      // lines: pieces whose middles lie within 0.6 em of each other are one line
      var mids = lines.filter(function (l) { return l.k === k; })
                      .map(function (l) { return (l.r.t + l.r.b) / 2; }).sort(function (a, b) { return a - b; });
      var n = 0, last = -1e9;
      mids.forEach(function (m) { if (m - last > .6 * fs) { n++; last = m; } });
      var heading = /^H[1-6]$/.test(el.tagName) || el.classList.contains('title');
      var tf = cs.transform, turned = tf && tf !== 'none' && !/^matrix\(1, 0, 0, 1,/.test(tf);
      if (turned || cs.writingMode.indexOf('vertical') === 0) return;   // a label turned on its side
      if (n >= 2 && lh && lh / fs < 1.28 && !(heading && fs >= 30))
        problems.push('tight leading ' + (lh / fs).toFixed(2) + ' on ' + n + ' lines at ' + fs + 'px: "' + o.t.trim().slice(0, 36) + '"');
    });
    // two pieces of text on top of each other
    for (var a = 0; a < lines.length; a++) for (var c = a + 1; c < lines.length; c++) {
      if (lines[a].k === lines[c].k) continue;
      var p = lines[a].r, q = lines[c].r;
      var ox = Math.min(p.r, q.r) - Math.max(p.l, q.l), oy = Math.min(p.b, q.b) - Math.max(p.t, q.t);
      if (ox > 2 && oy > .3 * Math.min(p.b - p.t, q.b - q.t))
        problems.push('text on text: "' + blocks[lines[a].k].t.trim().slice(0, 30) + '" / "' +
                      blocks[lines[c].k].t.trim().slice(0, 30) + '"');
    }
    [].forEach.call(slide.querySelectorAll('.wire[data-error]'), function (w) {
      problems.push('wire ' + w.dataset.from + ' -> ' + w.dataset.to + ': ' + w.dataset.error);
    });
    var room = null;
    if (body && fb) {
      var bt = box(body).t, low = bt;
      [].forEach.call(body.querySelectorAll('*'), function (el) {
        if (el.classList.contains('wire')) return;
        var r = el.getBoundingClientRect(); if (r.height) low = Math.max(low, r.bottom);
      });
      room = {top: Math.round(bt), limit: Math.round(fb.t - 12), used: Math.round(low)};
    }
    blocks.forEach(function (o) { delete o.el; });
    return {blocks: blocks, room: room, min: slide.dataset.min ? +slide.dataset.min : null,
            problems: problems.filter(function (x, i, all) { return all.indexOf(x) === i; })};
  };

  document.fonts.ready.then(function () {
    requestAnimationFrame(function () {
      slides.forEach(drawWires);
      requestAnimationFrame(function () { window.DECK_READY = true; });
    });
  });
})();
