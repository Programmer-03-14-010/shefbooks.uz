/* Shefbooks — asosiy JavaScript (kutubxonasiz, jQuery kerak emas) */
(function () {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var body = document.body;

  /* ---------- Preloader ---------- */
  function hideLoader() {
    var l = $('#page-loader');
    if (l) { l.classList.add('done'); setTimeout(function () { l.remove(); }, 700); }
  }
  window.addEventListener('load', hideLoader);
  setTimeout(hideLoader, 2500);

  /* ---------- Toast ---------- */
  var ICONS = { success: 'fa-check-circle', error: 'fa-exclamation-circle', warning: 'fa-exclamation-triangle', info: 'fa-info-circle' };
  window.shefToast = function (msg, type) {
    type = type || 'success';
    var stack = $('#toast-stack');
    if (!stack || !msg) return;
    var el = document.createElement('div');
    el.className = 'toast ' + type;
    el.setAttribute('role', 'status');
    var i = document.createElement('i');
    i.className = 'fa ' + (ICONS[type] || ICONS.info);
    var s = document.createElement('span');
    s.textContent = msg;
    el.appendChild(i); el.appendChild(s);
    stack.appendChild(el);
    setTimeout(function () {
      el.classList.add('leaving');
      setTimeout(function () { el.remove(); }, 400);
    }, 3800);
  };
  (function flushDjangoMessages() {
    var holder = $('#django-messages');
    if (!holder) return;
    $$('[data-msg]', holder).forEach(function (m, idx) {
      var tag = (m.getAttribute('data-tag') || '').split(' ').pop();
      var type = tag === 'error' ? 'error' : tag === 'warning' ? 'warning' : tag === 'info' ? 'info' : 'success';
      setTimeout(function () { window.shefToast(m.getAttribute('data-msg'), type); }, 350 + idx * 450);
    });
  })();

  /* ---------- Header / to-top ---------- */
  var header = $('.site-header');
  var toTop = $('.to-top');
  function onScroll() {
    var y = window.scrollY || document.documentElement.scrollTop;
    if (header) header.classList.toggle('is-stuck', y > 8);
    if (toTop) toTop.classList.toggle('show', y > 600);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (toTop) toTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });

  /* ---------- Drawerlar (mobil menyu, filtrlar) ---------- */
  function closeDrawers() { body.classList.remove('drawer-open', 'filters-open'); }
  $$('[data-drawer-open]').forEach(function (b) { b.addEventListener('click', function () { body.classList.add('drawer-open'); }); });
  $$('[data-drawer-close]').forEach(function (b) { b.addEventListener('click', closeDrawers); });
  $$('[data-filters-open]').forEach(function (b) { b.addEventListener('click', function () { body.classList.add('filters-open'); }); });
  var backdrop = $('.drawer-backdrop');
  if (backdrop) backdrop.addEventListener('click', closeDrawers);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { closeDrawers(); closeModals(); } });

  /* ---------- Modal ---------- */
  function closeModals() { $$('.modal.show').forEach(function (m) { m.classList.remove('show'); }); }
  window.shefModal = function (id, open) {
    var m = document.getElementById(id);
    if (m) m.classList.toggle('show', open !== false);
  };
  $$('.modal').forEach(function (m) { m.addEventListener('click', function (e) { if (e.target === m) closeModals(); }); });

  /* ---------- Reveal ---------- */
  var revealEls = $$('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---------- Count-up ---------- */
  $$('[data-countup]').forEach(function (el) {
    var target = parseInt(el.getAttribute('data-countup'), 10) || 0;
    var suffix = el.getAttribute('data-suffix') || '';
    if (!('IntersectionObserver' in window)) { el.textContent = target + suffix; return; }
    var obs = new IntersectionObserver(function (en) {
      if (!en[0].isIntersecting) return;
      obs.disconnect();
      var t0 = null, dur = 1400;
      function step(ts) {
        if (!t0) t0 = ts;
        var p = Math.min((ts - t0) / dur, 1);
        el.textContent = Math.floor(target * (1 - Math.pow(1 - p, 3))) + suffix;
        if (p < 1) requestAnimationFrame(step); else el.textContent = target + suffix;
      }
      requestAnimationFrame(step);
    }, { threshold: 0.4 });
    obs.observe(el);
  });

  /* ---------- Hero tilt ---------- */
  var stage = $('.hero-stage');
  if (stage && window.matchMedia('(hover: hover)').matches) {
    var books = $$('.hbook', stage);
    stage.addEventListener('mousemove', function (e) {
      var r = stage.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width - 0.5;
      var y = (e.clientY - r.top) / r.height - 0.5;
      books.forEach(function (b, i) {
        var k = (i + 1) * 7;
        b.style.marginLeft = (x * k) + 'px';
        b.style.marginTop = (y * k) + 'px';
      });
    });
    stage.addEventListener('mouseleave', function () {
      books.forEach(function (b) { b.style.marginLeft = b.style.marginTop = '0'; });
    });
  }

  /* ---------- Savat / xohish (AJAX) ---------- */
  function setBadge(sel, n) {
    $$(sel).forEach(function (b) {
      b.textContent = n; b.setAttribute('data-count', n);
      b.classList.remove('bump'); void b.offsetWidth; b.classList.add('bump');
    });
  }
  function refreshMiniCart() {
    var panel = $('#mini-cart-panel');
    if (!panel || !panel.getAttribute('data-url')) return;
    fetch(panel.getAttribute('data-url'), { headers: { 'X-Requested-With': 'XMLHttpRequest' }, credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.text() : null; })
      .then(function (html) { if (html) panel.innerHTML = html; });
  }
  document.addEventListener('submit', function (e) {
    var form = e.target.closest('form[data-ajax]');
    if (!form || !window.fetch) return;
    e.preventDefault();
    var kind = form.getAttribute('data-ajax');
    var btn = form.querySelector('button[type=submit], button:not([type])');
    if (btn) btn.disabled = true;
    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin'
    }).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        var j = res.j;
        if (btn) btn.disabled = false;
        if (!res.ok || !j.ok) { window.shefToast(j.message || "Xatolik yuz berdi", 'warning'); return; }
        setBadge('[data-cart-badge]', j.cart_count);
        setBadge('[data-wish-badge]', j.wish_count);
        if (kind === 'cart' && form.hasAttribute('data-keep')) {
          var box = form.closest('[data-buybox]');
          var radio = box && box.querySelector('.fmt input:checked');
          if (radio) radio.setAttribute('data-incart', j.in_cart ? '1' : '0');
          if (box) syncBuyBox(box);
          refreshMiniCart();
        } else if (kind === 'cart') {
          if (j.in_cart) {
            var link = document.createElement('a');
            link.href = form.getAttribute('data-cart-url') || '/';
            link.className = form.getAttribute('data-class') || 'add-btn in-cart';
            link.innerHTML = '<i class="fa fa-check"></i> <span>Savatda · ko\'rish</span>';
            form.replaceWith(link);
          }
          refreshMiniCart();
        } else if (kind === 'wish') {
          if (btn) btn.classList.toggle('active', !!j.liked);
          var wp = $('#wishlist-page-flag');
          if (wp && !j.liked) {
            var card = form.closest('.book-card');
            if (card) { card.style.transition = 'all .4s'; card.style.opacity = 0; card.style.transform = 'scale(.9)'; setTimeout(function () { card.remove(); }, 400); }
          }
        }
        window.shefToast(j.message || 'Bajarildi', 'success');
      })
      .catch(function () { if (btn) btn.disabled = false; form.removeAttribute('data-ajax'); form.submit(); });
  });

  /* ---------- Tablar (delegatsiya: tez ko'rish oynasida ham ishlaydi) ---------- */
  function openTab(wrap, id) {
    $$('.tab-btn', wrap).forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-tab') === id); });
    $$('.tab-pane', wrap).forEach(function (p) { p.classList.toggle('active', p.id === id); });
  }
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.tab-btn');
    if (!btn) return;
    var wrap = btn.closest('[data-tabs]');
    if (wrap) openTab(wrap, btn.getAttribute('data-tab'));
  });
  var tabsWrap = $('[data-tabs]');
  if (tabsWrap && location.hash === '#reviews' && document.getElementById('tab-reviews')) {
    openTab(tabsWrap, 'tab-reviews');
    setTimeout(function () { tabsWrap.scrollIntoView({ behavior: 'smooth' }); }, 400);
  }

  /* ---------- Format tanlash: narx, tugma va holat ---------- */
  function syncBuyBox(box) {
    var radio = box.querySelector('.fmt input:checked');
    if (!radio) return;
    var fmt = radio.value;
    var now = box.querySelector('[data-now]'), old = box.querySelector('[data-old]');
    if (now) now.textContent = radio.getAttribute('data-price');
    if (old) {
      var o = radio.getAttribute('data-old');
      old.style.display = o ? '' : 'none';
      var ot = old.querySelector('[data-old-text]'); if (ot) ot.textContent = o;
    }
    var fi = box.querySelector('[data-fmt-input]'); if (fi) fi.value = fmt;
    var form = box.querySelector('.buy-form'), link = box.querySelector('[data-incart-link]');
    var btn = box.querySelector('[data-buy-btn]');
    var inCart = radio.getAttribute('data-incart') === '1';
    var avail = radio.getAttribute('data-available') === '1';
    if (form) form.classList.toggle('hide', inCart);
    if (link) link.classList.toggle('hide', !inCart);
    if (btn) {
      btn.disabled = !avail;
      var label = btn.querySelector('span');
      if (label) label.textContent = avail ? (fmt === 'paper' ? "Savatga qo'shish" : "Savatga qo'shish") : "Sotuvda yo'q";
    }
    var pill = box.querySelector('[data-pill]');
    if (pill) { pill.className = 'stock-pill ' + radio.getAttribute('data-pill-class'); pill.textContent = radio.getAttribute('data-pill-text'); }
    var note = box.querySelector('[data-fmt-note]');
    if (note) note.classList.toggle('show', fmt !== 'paper');
  }
  window.syncBuyBox = syncBuyBox;
  document.addEventListener('change', function (e) {
    if (!e.target.matches('.fmt input')) return;
    var box = e.target.closest('[data-buybox]'); if (box) syncBuyBox(box);
  });
  function initBuyBoxes(root) { $$('[data-buybox]', root || document).forEach(syncBuyBox); }
  initBuyBoxes();

  /* ---------- Tez ko'rish oynasi ---------- */
  var qv = $('#qv-modal');
  function closeQuick() { if (qv) { qv.classList.remove('show'); body.classList.remove('qv-open'); var a = $('audio', qv); if (a) a.pause(); } }
  if (qv) {
    var qvContent = $('.qv-content', qv);
    document.addEventListener('click', function (e) {
      var opener = e.target.closest('[data-quick]');
      if (opener) {
        e.preventDefault();
        qvContent.innerHTML = '<div class="qv-loading"><i class="fa fa-spinner fa-spin"></i></div>';
        qv.classList.add('show'); body.classList.add('qv-open');
        fetch(opener.getAttribute('data-url'), { headers: { 'X-Requested-With': 'XMLHttpRequest' }, credentials: 'same-origin' })
          .then(function (r) { if (!r.ok) throw new Error(); return r.text(); })
          .then(function (html) { qvContent.innerHTML = html; initBuyBoxes(qvContent); })
          .catch(function () { closeQuick(); window.shefToast("Ma'lumotni yuklab bo'lmadi", 'error'); });
        return;
      }
      if (e.target.closest('[data-qv-close]') || e.target === qv) closeQuick();
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeQuick(); });
  }

  /* ---------- Taymer (aksiya) ---------- */
  $$('[data-countdown]').forEach(function (el) {
    var end = new Date(el.getAttribute('data-countdown')).getTime();
    var offer = el.closest('.offer');
    var d = $('[data-d]', el), h = $('[data-h]', el), m = $('[data-m]', el), sec = $('[data-s]', el);
    function pad(n) { return (n < 10 ? '0' : '') + n; }
    function tick() {
      var left = Math.max(0, Math.floor((end - Date.now()) / 1000));
      var days = Math.floor(left / 86400);
      if (d) { d.textContent = pad(days); var box = d.closest('.cd-box'); if (box) box.classList.toggle('show', days > 0); }
      h.textContent = pad(Math.floor((left % 86400) / 3600));
      m.textContent = pad(Math.floor((left % 3600) / 60));
      sec.textContent = pad(left % 60);
      if (left === 0) { if (offer) offer.classList.add('ended'); clearInterval(timer); }
    }
    var timer = setInterval(tick, 1000); tick();
  });

  /* ---------- Galereya ---------- */
  var mainImg = $('#mainImg');
  $$('.gallery-thumbs button').forEach(function (b) {
    b.addEventListener('click', function () {
      if (mainImg) mainImg.src = b.getAttribute('data-large');
      $$('.gallery-thumbs button').forEach(function (x) { x.classList.remove('active'); });
      b.classList.add('active');
    });
  });

  /* ---------- Fayl yuklash (chek) ---------- */
  $$('.dropzone').forEach(function (dz) {
    var input = document.getElementById(dz.getAttribute('data-input'));
    if (!input) return;
    dz.addEventListener('click', function () { input.click(); });
    ['dragover', 'dragenter'].forEach(function (ev) { dz.addEventListener(ev, function (e) { e.preventDefault(); dz.style.borderColor = '#000'; }); });
    dz.addEventListener('dragleave', function () { dz.style.borderColor = ''; });
    dz.addEventListener('drop', function (e) {
      e.preventDefault(); dz.style.borderColor = '';
      if (e.dataTransfer.files.length) { input.files = e.dataTransfer.files; input.dispatchEvent(new Event('change')); }
    });
    input.addEventListener('change', function () {
      var f = input.files[0];
      var name = $('.dz-name', dz), img = $('img.preview', dz);
      if (!f) { dz.classList.remove('has-file'); if (name) name.textContent = 'Fayl tanlanmagan'; return; }
      dz.classList.add('has-file');
      if (name) name.textContent = f.name;
      var reader = new FileReader();
      reader.onload = function (ev) { if (img) img.src = ev.target.result; };
      reader.readAsDataURL(f);
    });
  });

  /* ---------- Nusxalash ---------- */
  $$('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var txt = b.getAttribute('data-copy');
      var done = function () { window.shefToast('Karta raqami nusxalandi', 'success'); };
      if (navigator.clipboard) navigator.clipboard.writeText(txt).then(done);
      else { var t = document.createElement('textarea'); t.value = txt; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove(); done(); }
    });
  });

  /* ---------- Parol ko'rsatish ---------- */
  $$('.pw-toggle').forEach(function (b) {
    b.addEventListener('click', function () {
      var input = b.parentElement.querySelector('input');
      var show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      b.querySelector('i').className = 'fa ' + (show ? 'fa-eye-slash' : 'fa-eye');
    });
  });

  /* ---------- Avto-submit (saralash) ---------- */
  $$('[data-autosubmit]').forEach(function (el) { el.addEventListener('change', function () { el.form.submit(); }); });

  /* ---------- Tasdiqlash ---------- */
  $$('[data-confirm]').forEach(function (el) {
    el.addEventListener('submit', function (e) { if (!confirm(el.getAttribute('data-confirm'))) e.preventDefault(); });
  });
})();
