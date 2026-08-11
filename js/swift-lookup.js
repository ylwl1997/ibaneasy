// swift-lookup.js — Client-side SWIFT/BIC code search for ibaneasy.com
var SwiftSearch = (function() {
  'use strict';
  var swiftData = [];
  var countryNames = {};

  function loadData() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/swift_codes.json', true);
    xhr.onload = function() {
      if (xhr.status === 200) {
        try { swiftData = JSON.parse(xhr.responseText); }
        catch(e) { swiftData = []; }
        buildCountryFilter();
        renderAll();
      }
    };
    xhr.onerror = function() {
      document.getElementById('swift-count').textContent = 'Failed to load BIC data. Please try again.';
    };
    xhr.send();
  }

  function buildCountryFilter() {
    var seen = {};
    var select = document.getElementById('swift-country-filter');
    if (!select) return;

    for (var i = 0; i < swiftData.length; i++) {
      var cc = swiftData[i].country;
      if (!seen[cc]) { seen[cc] = true; }
    }

    var ccs = Object.keys(seen).sort();
    for (var j = 0; j < ccs.length; j++) {
      var opt = document.createElement('option');
      opt.value = ccs[j];
      opt.textContent = ccs[j];
      select.appendChild(opt);
    }
  }

  function filter() {
    var queryEl = document.getElementById('swift-search');
    var countryEl = document.getElementById('swift-country-filter');
    var query = queryEl ? queryEl.value.toLowerCase().trim() : '';
    var countryFilter = countryEl ? countryEl.value : '';

    var results = [];
    for (var i = 0; i < swiftData.length; i++) {
      var item = swiftData[i];
      var matchesCountry = !countryFilter || item.country === countryFilter;

      var matchesQuery = !query ||
        item.bic.toLowerCase().indexOf(query) !== -1 ||
        item.bankName.toLowerCase().indexOf(query) !== -1 ||
        item.country.toLowerCase().indexOf(query) !== -1 ||
        (item.city && item.city.toLowerCase().indexOf(query) !== -1);

      if (matchesCountry && matchesQuery) {
        results.push(item);
      }
    }

    renderTable(results);
  }

  function renderAll() {
    renderTable(swiftData);
  }

  function renderTable(results) {
    var tbody = document.getElementById('swift-tbody');
    var countEl = document.getElementById('swift-count');
    if (!tbody || !countEl) return;

    countEl.textContent = results.length + ' of ' + swiftData.length + ' BIC codes';

    if (results.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:2rem 0">No matching BIC codes found.</td></tr>';
      return;
    }

    var html = '';
    for (var i = 0; i < results.length; i++) {
      var item = results[i];
      html += '<tr>' +
        '<td><code class="swift-bic-code">' + escHtml(item.bic) + '</code></td>' +
        '<td>' + escHtml(item.bankName) + '</td>' +
        '<td>' + escHtml(item.country) + '</td>' +
        '<td>' + escHtml(item.city || '—') + '</td>' +
        '<td>' + escHtml(item.branch || '—') + '</td>' +
        '</tr>';
    }
    tbody.innerHTML = html;
  }

  function escHtml(s) {
    if (!s) return '';
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // Init when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadData);
  } else {
    loadData();
  }

  return { filter: filter, loadData: loadData };
})();
