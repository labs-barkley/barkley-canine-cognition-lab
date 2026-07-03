/* ════════════════════════════════════════════════════════════════════
   Barkley Halo — the signature mark.
   An organic, breathing neon halo. Not a circle: a loop sampled around an
   ellipse and perturbed by low-frequency sines so it morphs continuously
   without ever spiking into chaos. Cyan → blue → violet, single pass.

   Usage:
     BarkleyHalo.mount(element, {
       wobble, squash, speed, pulse, pulseHz, osc, oscHz, rotSpeed,
       stroke, bloom, baseR
     });
   The element is sized by CSS; the SVG fills it (overflow visible so the
   bloom bleeds out). One shared rAF loop drives every instance; instances
   pause automatically when scrolled off-screen and honour
   prefers-reduced-motion.
═══════════════════════════════════════════════════════════════════════ */
(function (global) {
  'use strict';

  var SVGNS = 'http://www.w3.org/2000/svg';
  var instances = [];
  var uid = 0;
  var reduceMotion = global.matchMedia &&
    global.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Barkley palette: cyan → blue → violet (single sweep, no repeat).
  var STOPS = [
    ['0%',   '#2ee0ff'],
    ['28%',  '#4d9bff'],
    ['55%',  '#7b9fff'],
    ['80%',  '#a87bff'],
    ['100%', '#c97bff']
  ];

  function el(tag, attrs) {
    var n = document.createElementNS(SVGNS, tag);
    if (attrs) for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  // Closed Catmull-Rom → cubic Bézier. Smooth, seamless loop.
  function buildLoopPath(pts) {
    var n = pts.length, t = 0.5, d = '';
    for (var i = 0; i < n; i++) {
      var p0 = pts[(i - 1 + n) % n], p1 = pts[i],
          p2 = pts[(i + 1) % n], p3 = pts[(i + 2) % n];
      if (i === 0) d += 'M' + p1[0].toFixed(2) + ',' + p1[1].toFixed(2) + ' ';
      var c1x = p1[0] + (p2[0] - p0[0]) * (t / 3),
          c1y = p1[1] + (p2[1] - p0[1]) * (t / 3),
          c2x = p2[0] - (p3[0] - p1[0]) * (t / 3),
          c2y = p2[1] - (p3[1] - p1[1]) * (t / 3);
      d += 'C' + c1x.toFixed(2) + ',' + c1y.toFixed(2) + ' ' +
                 c2x.toFixed(2) + ',' + c2y.toFixed(2) + ' ' +
                 p2[0].toFixed(2) + ',' + p2[1].toFixed(2) + ' ';
    }
    return d + 'Z';
  }

  function sampleHalo(p, time) {
    var N = p.N, pts = new Array(N);
    // Two low-frequency harmonics → round-but-organic, never a blob/molecule.
    var f1 = 2, s1 = 0.62, f2 = 3, s2 = 0.28;
    var ph1 = time * 0.55, ph2 = time * 0.85 + 1.7;
    // Pulsation: uniform radial breathing.
    var pulseAmt = 1 + Math.sin(time * p.pulseHz * Math.PI * 2) * p.pulse;
    // Oscillation: the wobble amplitude itself swells and recedes.
    var wobbleNow = p.wobble * (1 + Math.sin(time * p.oscHz * Math.PI * 2) * p.osc);
    // Slow tilt drift so the lean never feels locked.
    var tilt = Math.sin(time * 0.22) * 0.06, cs = Math.cos(tilt), sn = Math.sin(tilt);
    for (var i = 0; i < N; i++) {
      var a = (i / N) * Math.PI * 2;
      var w = Math.sin(a * f1 + ph1) * s1 + Math.sin(a * f2 + ph2) * s2;
      var r = (p.baseR + w * wobbleNow) * pulseAmt;
      var x0 = Math.cos(a) * r, y0 = Math.sin(a) * r * p.squash;
      pts[i] = [x0 * cs - y0 * sn, x0 * sn + y0 * cs];
    }
    return pts;
  }

  function makeInstance(container, opts) {
    var p = {
      wobble:   opts.wobble   != null ? opts.wobble   : 6,
      squash:   opts.squash   != null ? opts.squash   : 0.92,
      speed:    opts.speed    != null ? opts.speed    : 1,
      pulse:    opts.pulse    != null ? opts.pulse    : 0.07,
      pulseHz:  opts.pulseHz  != null ? opts.pulseHz  : 0.5,
      osc:      opts.osc      != null ? opts.osc      : 0.35,
      oscHz:    opts.oscHz    != null ? opts.oscHz    : 0.16,
      rotSpeed: opts.rotSpeed != null ? opts.rotSpeed : 0.16,
      stroke:   opts.stroke   != null ? opts.stroke   : 2.4,
      bloom:    opts.bloom    != null ? opts.bloom    : 1,
      baseR:    150,
      N:        80
    };

    var id = ++uid;
    var svg = el('svg', {
      viewBox: '-200 -200 400 400',
      preserveAspectRatio: 'xMidYMid meet'
    });
    svg.style.width = '100%';
    svg.style.height = '100%';
    svg.style.display = 'block';
    svg.style.overflow = 'visible';

    var defs = el('defs');
    var grad = el('linearGradient', {
      id: 'bhGrad' + id, gradientUnits: 'userSpaceOnUse',
      x1: '-180', y1: '-180', x2: '180', y2: '180'
    });
    STOPS.forEach(function (s) {
      grad.appendChild(el('stop', { offset: s[0], 'stop-color': s[1] }));
    });
    defs.appendChild(grad);

    function filt(fid, dev, ext) {
      var f = el('filter', {
        id: fid, x: ext, y: ext,
        width: (1 + 2 * parseFloat(ext) / -100) + '%' , height: '0'
      });
      // simpler explicit bounds:
      f.setAttribute('x', '-150%'); f.setAttribute('y', '-150%');
      f.setAttribute('width', '400%'); f.setAttribute('height', '400%');
      f.appendChild(el('feGaussianBlur', { stdDeviation: dev }));
      return f;
    }
    defs.appendChild(filt('bhHuge' + id, 28));
    defs.appendChild(filt('bhBig' + id, 14));
    defs.appendChild(filt('bhMed' + id, 3));
    svg.appendChild(defs);

    var url = 'url(#bhGrad' + id + ')';
    var layers = [];
    function addPath(w, filtId, op) {
      var pa = el('path', {
        fill: 'none', stroke: url, 'stroke-width': w,
        'stroke-linecap': 'round', 'stroke-linejoin': 'round',
        opacity: op
      });
      if (filtId) pa.setAttribute('filter', 'url(#' + filtId + ')');
      svg.appendChild(pa);
      layers.push(pa);
    }
    var b = p.bloom;
    addPath(p.stroke * 5.5, 'bhHuge' + id, 0.55 * b);
    addPath(p.stroke * 4,   'bhBig' + id,  0.85 * b);
    addPath(p.stroke * 2.4, 'bhMed' + id,  0.95);
    addPath(p.stroke,       null,          1);

    container.appendChild(svg);

    var inst = { p: p, grad: grad, layers: layers, el: container, t: Math.random() * 40, visible: true };
    instances.push(inst);

    if (reduceMotion) renderOnce(inst); // single static frame
    return inst;
  }

  function setGradientAngle(grad, ang) {
    var R = 220, cx = Math.cos(ang) * R, cy = Math.sin(ang) * R;
    grad.setAttribute('x1', (-cx).toFixed(2));
    grad.setAttribute('y1', (-cy).toFixed(2));
    grad.setAttribute('x2', ( cx).toFixed(2));
    grad.setAttribute('y2', ( cy).toFixed(2));
  }

  function renderInstance(inst) {
    var d = buildLoopPath(sampleHalo(inst.p, inst.t));
    for (var i = 0; i < inst.layers.length; i++) inst.layers[i].setAttribute('d', d);
    setGradientAngle(inst.grad, inst.t * inst.p.rotSpeed * Math.PI * 2);
  }
  function renderOnce(inst) { renderInstance(inst); }

  var last = performance.now();
  function tick(now) {
    var dt = (now - last) / 1000; last = now;
    if (dt > 0.1) dt = 0.1;
    for (var i = 0; i < instances.length; i++) {
      var inst = instances[i];
      if (!inst.visible) continue;
      inst.t += dt * inst.p.speed;
      renderInstance(inst);
    }
    requestAnimationFrame(tick);
  }
  if (!reduceMotion) requestAnimationFrame(tick);

  // Visibility gating for performance.
  var io = ('IntersectionObserver' in global) ? new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      for (var i = 0; i < instances.length; i++) {
        if (instances[i].el === e.target) instances[i].visible = e.isIntersecting;
      }
    });
  }, { threshold: 0.01 }) : null;

  var BarkleyHalo = {
    mount: function (element, opts) {
      if (typeof element === 'string') element = document.querySelector(element);
      if (!element) return null;
      var inst = makeInstance(element, opts || {});
      if (io) io.observe(element);
      return inst;
    },
    // auto-mount everything with [data-barkley-halo], reading data-* options
    auto: function () {
      var nodes = document.querySelectorAll('[data-barkley-halo]');
      Array.prototype.forEach.call(nodes, function (n) {
        if (n.__bhMounted) return;
        n.__bhMounted = true;
        var o = {};
        ['wobble','squash','speed','pulse','pulseHz','osc','oscHz','rotSpeed','stroke','bloom']
          .forEach(function (k) {
            var v = n.getAttribute('data-' + k.toLowerCase());
            if (v != null) o[k] = parseFloat(v);
          });
        BarkleyHalo.mount(n, o);
      });
    }
  };

  global.BarkleyHalo = BarkleyHalo;
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', BarkleyHalo.auto);
  else BarkleyHalo.auto();
})(window);
