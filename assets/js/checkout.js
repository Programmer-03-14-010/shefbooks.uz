/* Shefbooks — kassa: yetkazib berish punktini tanlash (BTS / UZPOST). Ma'lumotlar pickup-data.js da. */
(function () {
  'use strict';
  var cfg = document.getElementById('checkout-config');
  if (!cfg || typeof ALL_LOCATIONS === 'undefined') return;

  var isLoggedIn = cfg.getAttribute('data-logged') === '1';
  var loginUrl = cfg.getAttribute('data-login-url');
  var $ = function (id) { return document.getElementById(id); };

  var selectedId = null, currentRegion = 'all', currentType = 'all', currentSearch = '';
  var addressInput = $('address-value');
  var existing = (addressInput.value || '').trim();
  var matched = null;

  if (existing) {
    for (var i = 0; i < ALL_LOCATIONS.length; i++) {
      if (ALL_LOCATIONS[i].name + ' — ' + ALL_LOCATIONS[i].address === existing) { matched = ALL_LOCATIONS[i]; selectedId = matched.id; break; }
    }
  }

  function normalize(str) {
    return (str || '').toLowerCase().replace(/\u2019/g, "'").replace(/`/g, "'")
      .replace(/o'/g, 'o').replace(/g'/g, 'g').replace(/\s+/g, ' ').trim();
  }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  function getFiltered() {
    var q = normalize(currentSearch);
    return ALL_LOCATIONS.filter(function (l) {
      if (currentRegion !== 'all' && l.region !== currentRegion) return false;
      if (currentType !== 'all' && l.type !== currentType) return false;
      if (q) {
        var hay = normalize(l.name + ' ' + l.address + ' ' + (REGION_NAMES[l.region] || '') + ' ' + (l.index || ''));
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });
  }

  function renderList() {
    var list = $('locations-list'), none = $('no-results'), count = $('locations-count');
    var filtered = getFiltered();
    if (!filtered.length) { list.innerHTML = ''; list.style.display = 'none'; none.style.display = 'block'; count.textContent = ''; return; }
    list.style.display = 'block'; none.style.display = 'none';
    count.textContent = filtered.length + ' ta punkt topildi';
    var html = '';
    filtered.forEach(function (l) {
      var sel = l.id === selectedId;
      var cls = 'loc-item' + (sel ? ' selected' : '') + (sel && l.type === 'uzpost' ? ' uzpost-selected' : '');
      html += '<div class="' + cls + '" data-id="' + esc(l.id) + '">' +
        '<div class="loc-badge ' + l.type + '">' + (l.type === 'bts' ? 'BTS' : 'UZ') + '</div>' +
        '<div><div class="loc-name">' + esc(l.name) + '</div><div class="loc-addr">' + esc(l.address) + '</div>' +
        (l.index ? '<span class="loc-region-tag">📮 ' + esc(l.index) + '</span>' : '') +
        '<span class="loc-region-tag">📍 ' + esc(REGION_NAMES[l.region] || l.region) + '</span></div>' +
        '<div class="loc-check">✓</div></div>';
    });
    list.innerHTML = html;
    if (selectedId) {
      var el = list.querySelector('.loc-item.selected');
      if (el) setTimeout(function () { el.scrollIntoView({ block: 'nearest' }); }, 30);
    }
  }

  function applySelection(loc, fullAddr, scroll) {
    var box = $('picked-box');
    box.className = 'picked ' + (loc ? loc.type : 'bts');
    $('picked-text').textContent = '✓ ' + fullAddr;
    var btn = $('submit-btn');
    btn.disabled = false;
    $('submit-hint').textContent = loc ? 'Tanlandi: ' + loc.name : 'Manzil tanlandi';
    var warn = $('uzpost-warning');
    if (loc && loc.type === 'uzpost') {
      var price = REGION_PRICES[loc.region] || 25000;
      $('uzpost-price-text').textContent = price.toLocaleString('ru-RU') + " so'm";
      warn.classList.add('show');
      if (scroll) setTimeout(function () { warn.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 150);
    } else { warn.classList.remove('show'); }
  }

  $('locations-list').addEventListener('click', function (e) {
    var item = e.target.closest('.loc-item');
    if (!item) return;
    var id = item.getAttribute('data-id');
    var found = ALL_LOCATIONS.filter(function (l) { return l.id === id; })[0];
    if (!found) return;
    selectedId = id;
    var full = found.name + ' — ' + found.address;
    addressInput.value = full;
    renderList();
    applySelection(found, full, true);
  });

  $('region-filter').addEventListener('change', function () { currentRegion = this.value; renderList(); });
  Array.prototype.forEach.call(document.querySelectorAll('.seg button'), function (b) {
    b.addEventListener('click', function () {
      currentType = b.getAttribute('data-type');
      Array.prototype.forEach.call(document.querySelectorAll('.seg button'), function (x) { x.classList.toggle('active', x === b); });
      renderList();
    });
  });
  var timer;
  $('location-search').addEventListener('input', function () {
    var v = this.value; clearTimeout(timer);
    timer = setTimeout(function () { currentSearch = v; renderList(); }, 200);
  });

  $('checkout-form').addEventListener('submit', function (e) {
    if (!isLoggedIn) { e.preventDefault(); window.shefModal('login-modal', true); return; }
    if (!addressInput.value.trim()) { e.preventDefault(); window.shefToast("Yetkazib berish punktini tanlang", 'warning'); }
  });
  var go = $('go-login');
  if (go) go.addEventListener('click', function () { location.href = loginUrl + '?next=' + encodeURIComponent(location.pathname); });

  if (existing) applySelection(matched, existing, false);
  renderList();
})();
