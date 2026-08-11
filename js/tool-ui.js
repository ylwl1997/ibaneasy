// tool-ui.js — Interactive UI for IBAN generator on homepage
// Features: searchable country selector, quantity slider, export, history, format legend
(function() {
  'use strict';

  // ── DOM refs ─────────────────────────────────────────────────────
  var countryButton = document.getElementById('country-button');
  var countryFlag = document.getElementById('country-flag');
  var countryLabel = document.getElementById('country-label');
  var countryMenu = document.getElementById('country-menu');
  var countrySearch = document.getElementById('country-search');
  var countryList = document.getElementById('country-list');

  var quantitySlider = document.getElementById('quantity-slider');
  var quantityValue = document.getElementById('quantity-value');

  var btnGenerate = document.getElementById('btn-generate');
  var ibanDisplay = document.getElementById('iban-display');
  var ibanLength = document.getElementById('iban-length');
  var ibanStructure = document.getElementById('iban-structure');
  var ibanFeedback = document.getElementById('iban-feedback');
  var singleResult = document.getElementById('single-result');
  var btnCopy = document.getElementById('btn-copy');
  var copyMsg = document.getElementById('copy-msg');

  var bulkResult = document.getElementById('bulk-result');
  var bulkList = document.getElementById('bulk-list');
  var btnCopyAll = document.getElementById('btn-copy-all');
  var btnExportCSV = document.getElementById('btn-export-csv');
  var btnExportJSON = document.getElementById('btn-export-json');
  var btnExportTXT = document.getElementById('btn-export-txt');

  var historyToggle = document.getElementById('history-toggle');
  var historyPanel = document.getElementById('history-panel');
  var historyItems = document.getElementById('history-items');
  var historyClear = document.getElementById('history-clear');
  var historyCount = document.getElementById('history-count');

  // Full dataset elements
  var datasetEnable = document.getElementById('dataset-enable');
  var datasetPanel = document.getElementById('dataset-panel');
  var dsFields = {
    iban: document.getElementById('ds-iban'),
    bic: document.getElementById('ds-bic'),
    bank: document.getElementById('ds-bank'),
    bankCity: document.getElementById('ds-bank-city'),
    name: document.getElementById('ds-name'),
    dob: document.getElementById('ds-dob'),
    age: document.getElementById('ds-age'),
    country: document.getElementById('ds-country'),
    city: document.getElementById('ds-city'),
    address: document.getElementById('ds-address'),
    postcode: document.getElementById('ds-postcode'),
    phone: document.getElementById('ds-phone'),
    email: document.getElementById('ds-email'),
    occupation: document.getElementById('ds-occupation'),
    passport: document.getElementById('ds-passport'),
    nid: document.getElementById('ds-nid'),
    licence: document.getElementById('ds-licence'),
    vehicle: document.getElementById('ds-vehicle'),
    ssn: document.getElementById('ds-ssn'),
  };
  var currentDataset = null;
  var currentDatasets = [];
  var datasetEnabled = false;

  var countries = [];
  var selectedCountry = null;
  var currentIBANs = [];
  var HISTORY_KEY = 'ibaneasy_history';
  var MAX_HISTORY = 30;

  // ── Flag emoji converter ─────────────────────────────────────────
  function countryToFlag(code) {
    return String.fromCodePoint(0x1F1E6 - 65 + code.charCodeAt(0)) +
           String.fromCodePoint(0x1F1E6 - 65 + code.charCodeAt(1));
  }

  // ── Load countries ───────────────────────────────────────────────
  function loadCountries() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/iban_countries.json', true);
    xhr.onload = function() {
      if (xhr.status === 200) {
        countries = JSON.parse(xhr.responseText);
        countries.sort(function(a, b) {
          if (a.sepa !== b.sepa) return a.sepa ? -1 : 1;
          return a.name.localeCompare(b.name);
        });
        buildCountryList();
        // Default to Germany
        var de = countries.filter(function(c) { return c.code === 'DE'; })[0];
        if (de) selectCountry(de);
      }
    };
    xhr.send();
  }

  // ── Build country dropdown list ──────────────────────────────────
  function buildCountryList() {
    var html = '';
    for (var i = 0; i < countries.length; i++) {
      var c = countries[i];
      var flag = countryToFlag(c.code);
      var sepaMark = c.sepa ? ' <span class="co-tag co-tag-sepa">SEPA</span>' : '';
      html += '<button class="country-option" type="button" data-index="' + i + '">' +
        '<span class="co-flag">' + flag + '</span>' +
        '<span class="co-name">' + c.name + sepaMark + '</span>' +
        '<span class="co-code">' + c.code + '</span>' +
      '</button>';
    }
    countryList.innerHTML = html;

    // Click handlers
    var options = countryList.querySelectorAll('.country-option');
    for (var j = 0; j < options.length; j++) {
      (function(idx) {
        options[j].addEventListener('click', function() {
          selectCountry(countries[idx]);
          closeCountryMenu();
        });
      })(j);
    }
  }

  function selectCountry(c) {
    selectedCountry = c;
    countryFlag.textContent = countryToFlag(c.code);
    countryLabel.textContent = c.name + ' (' + c.code + ')';
    countryLabel.className = '';
  }

  // ── Country menu open/close ──────────────────────────────────────
  function openCountryMenu() {
    countryMenu.classList.add('open');
    countryButton.setAttribute('aria-expanded', 'true');
    countrySearch.value = '';
    filterCountries('');
    setTimeout(function() { countrySearch.focus(); }, 100);
  }

  function closeCountryMenu() {
    countryMenu.classList.remove('open');
    countryButton.setAttribute('aria-expanded', 'false');
  }

  function filterCountries(q) {
    var opts = countryList.querySelectorAll('.country-option');
    var ql = q.toLowerCase();
    for (var i = 0; i < opts.length; i++) {
      var text = opts[i].textContent.toLowerCase();
      opts[i].style.display = text.indexOf(ql) !== -1 ? '' : 'none';
    }
  }

  countryButton.addEventListener('click', function(e) {
    e.stopPropagation();
    if (countryMenu.classList.contains('open')) {
      closeCountryMenu();
    } else {
      openCountryMenu();
    }
  });

  countrySearch.addEventListener('input', function() {
    filterCountries(countrySearch.value);
  });

  countrySearch.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeCountryMenu();
  });

  document.addEventListener('click', function(e) {
    if (!countryMenu.contains(e.target) && e.target !== countryButton && !countryButton.contains(e.target)) {
      closeCountryMenu();
    }
  });

  // ── Quantity slider ──────────────────────────────────────────────
  quantitySlider.addEventListener('input', function() {
    quantityValue.textContent = quantitySlider.value;
  });

  // ── Generate ─────────────────────────────────────────────────────
  function generateIBANs() {
    if (!selectedCountry) {
      ibanDisplay.innerHTML = '<span class="placeholder">Select a country and click Generate</span>';
      return;
    }

    var count = parseInt(quantitySlider.value, 10);
    var c = selectedCountry;
    var results = [];

    // Build datasets first (needed for bulk "Data Set" buttons)
    var banks = (window.Dataset && Dataset.getBanks) ? Dataset.getBanks(c.code) : null;
    var wantsDataset = datasetEnable && datasetEnable.checked;
    currentDatasets = [];
    for (var i = 0; i < count; i++) {
      var iban = IBAN.generate(c.code, c.bbanFormat);
      var ds = null;
      if (wantsDataset && window.Dataset) {
        ds = Dataset.generate(c.code, iban, banks);
      }
      results.push({
        raw: iban,
        formatted: IBAN.format(iban),
        dataset: ds
      });
      if (ds) currentDatasets.push(ds);
    }

    currentIBANs = results;
    showResults(results, c);
    addToHistory(results, c);

    if (wantsDataset) {
      currentDataset = currentDatasets.length ? currentDatasets[0] : null;
      renderDataset();
    } else {
      currentDataset = null;
      hideDataset();
    }
  }

  function renderDataset() {
    if (!datasetPanel || !currentDataset) return;
    var d = currentDataset;

    dsFields.iban.textContent = d.iban;
    dsFields.bic.textContent = d.swiftBic || '—';
    dsFields.bank.textContent = d.bank.bankName || '—';
    dsFields.bankCity.textContent = d.bank.bankCity || '—';

    dsFields.name.textContent = d.identity.fullName;
    dsFields.dob.textContent = d.identity.dob;
    dsFields.age.textContent = d.identity.age;
    dsFields.country.textContent = d.identity.country;
    dsFields.city.textContent = d.identity.city;
    dsFields.address.textContent = d.identity.address;
    dsFields.postcode.textContent = d.identity.postcode;
    dsFields.phone.textContent = d.identity.phone;
    dsFields.email.textContent = d.identity.email;
    dsFields.occupation.textContent = d.identity.occupation;

    dsFields.passport.textContent = d.documents.passport;
    dsFields.nid.textContent = d.documents.nationalId;
    dsFields.licence.textContent = d.documents.drivingLicence;
    dsFields.vehicle.textContent = d.documents.vehicleReg;
    dsFields.ssn.textContent = d.documents.socialSecurity;

    var wrap = document.getElementById('dataset-wrap');
    if (wrap) wrap.style.display = '';
  }

  function hideDataset() {
    var wrap = document.getElementById('dataset-wrap');
    if (wrap) wrap.style.display = 'none';
  }

  // Show the dataset for a specific bulk row
  function showDatasetFor(idx) {
    if (!currentDatasets || !currentDatasets[idx]) return;
    currentDataset = currentDatasets[idx];
    renderDataset();
    // Scroll the panel into view if it's below the fold
    var wrap = document.getElementById('dataset-wrap');
    if (wrap) wrap.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Add a "Data Set" button to each bulk row
  function updateBulkDatasetButtons() {
    if (!currentDatasets || !currentDatasets.length) return;
    var rows = bulkList.querySelectorAll('.bulk-row');
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].querySelector('.bulk-ds-btn')) continue;
      var btn = document.createElement('button');
      btn.className = 'bulk-ds-btn';
      btn.setAttribute('data-idx', String(i));
      btn.title = 'View full data set for this IBAN';
      btn.innerHTML = '&#x1F4CB; Data Set';
      rows[i].appendChild(btn);
    }
    // Bind clicks
    var btns = bulkList.querySelectorAll('.bulk-ds-btn');
    for (var k = 0; k < btns.length; k++) {
      if (btns[k].getAttribute('data-bound') === '1') continue;
      btns[k].setAttribute('data-bound', '1');
      (function(idx) {
        btns[k].addEventListener('click', function() {
          showDatasetFor(idx);
        });
      })(parseInt(btns[k].getAttribute('data-idx'), 10));
    }
  }

  function showResults(results, c) {
    // Single result display (first IBAN)
    var first = results[0];
    ibanDisplay.textContent = first.formatted;
    ibanDisplay.classList.add('generated');
    ibanLength.textContent = c.ibanLen + ' characters';
    ibanStructure.textContent = c.bbanFormat;
    btnCopy.style.display = 'inline-flex';
    copyMsg.style.display = 'none';
    singleResult.style.display = '';

    // Show format breakdown if we have bank/branch/account info
    if (c.bankStart && c.bankLen) {
      var parts = IBAN.parse(first.raw);
      if (parts) {
        var bban = parts.bban;
        var bankPart = bban.slice(c.bankStart - 5, c.bankStart - 5 + c.bankLen);
        var accPart = bban.slice(c.accountStart - 5, c.accountStart - 5 + c.accountLen);
        var legendHtml = '<span style="color:var(--accent-light)">' + parts.country + '</span> ' +
          '<span style="color:var(--green)">' + parts.check + '</span> ';
        if (c.branchStart && c.branchLen) {
          var branchPart = bban.slice(c.branchStart - 5, c.branchStart - 5 + c.branchLen);
          legendHtml += '<span style="color:var(--gold)">' + bankPart + '</span> ' +
            '<span style="color:var(--purple)">' + branchPart + '</span> ';
        } else {
          legendHtml += '<span style="color:var(--gold)">' + bankPart + '</span> ';
        }
        legendHtml += '<span style="color:var(--text-secondary)">' + accPart + '</span>';
        ibanFeedback.innerHTML = legendHtml;
        ibanFeedback.style.display = '';
      }
    }

    // Bulk result
    if (results.length > 1) {
      var listHtml = '';
      for (var i = 0; i < results.length; i++) {
        listHtml += '<div class="bulk-row" data-idx="' + i + '">' +
          '<span class="bulk-iban">' + results[i].formatted + '</span>' +
          '<div class="bulk-actions">' +
            '<button class="bulk-copy-one" data-idx="' + i + '" title="Copy">&#x2398;</button>' +
          '</div>' +
        '</div>';
      }
      bulkList.innerHTML = listHtml;
      bulkResult.style.display = '';
      if (datasetEnable && datasetEnable.checked) updateBulkDatasetButtons();

      // Per-row copy buttons
      var copyBtns = bulkList.querySelectorAll('.bulk-copy-one');
      for (var j = 0; j < copyBtns.length; j++) {
        (function(idx) {
          copyBtns[j].addEventListener('click', function() {
            copySingle(results[idx].formatted);
          });
        })(j);
      }
    } else {
      bulkResult.style.display = 'none';
    }
  }

  // ── Copy ─────────────────────────────────────────────────────────
  function copySingle(text) {
    navigator.clipboard.writeText(text).then(function() {
      showToast('Copied!');
    }).catch(function() {
      fallbackCopy(text);
    });
  }

  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showToast('Copied!');
  }

  function copyAll() {
    if (!currentIBANs.length) return;
    var text = currentIBANs.map(function(r) { return r.formatted; }).join('\n');
    navigator.clipboard.writeText(text).then(function() {
      showToast('All ' + currentIBANs.length + ' IBANs copied!');
    }).catch(function() {
      fallbackCopy(text);
    });
  }

  // ── Export ───────────────────────────────────────────────────────
  function exportCSV() {
    if (!currentIBANs.length) return;
    var lines = ['IBAN'];
    for (var i = 0; i < currentIBANs.length; i++) {
      lines.push(currentIBANs[i].formatted.replace(/\s/g, ''));
    }
    downloadFile('ibans.csv', lines.join('\n'), 'text/csv');
  }

  function exportJSON() {
    if (!currentIBANs.length) return;
    var arr = currentIBANs.map(function(r) {
      return { iban: r.raw, formatted: r.formatted };
    });
    downloadFile('ibans.json', JSON.stringify(arr, null, 2), 'application/json');
  }

  function exportTXT() {
    if (!currentIBANs.length) return;
    var text = currentIBANs.map(function(r) { return r.raw; }).join('\n');
    downloadFile('ibans.txt', text, 'text/plain');
  }

  function downloadFile(filename, content, mime) {
    var blob = new Blob([content], { type: mime + ';charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // ── History ──────────────────────────────────────────────────────
  function loadHistory() {
    try {
      var raw = localStorage.getItem(HISTORY_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch(e) { return []; }
  }

  function saveHistory(entries) {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(entries.slice(0, MAX_HISTORY)));
    } catch(e) {}
  }

  function addToHistory(results, c) {
    var entries = loadHistory();
    entries.unshift({
      ts: Date.now(),
      country: c.code,
      countryName: c.name,
      count: results.length,
      sample: results[0].formatted,
      all: results.map(function(r) { return r.formatted; })
    });
    saveHistory(entries);
    renderHistoryPanel();
  }

  function renderHistoryPanel() {
    var entries = loadHistory();
    historyCount.textContent = entries.length;
    if (entries.length > 0) {
      historyCount.classList.remove('hidden');
      historyClear.style.display = '';
    } else {
      historyCount.classList.add('hidden');
      historyClear.style.display = 'none';
    }

    var html = '';
    for (var i = 0; i < entries.length; i++) {
      var e = entries[i];
      var flag = countryToFlag(e.country);
      var time = new Date(e.ts);
      var timeStr = time.toLocaleDateString() + ' ' + time.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
      html += '<div class="hist-item">' +
        '<div class="hist-head"><span class="hist-flag">' + flag + '</span><span class="hist-country">' + e.countryName + '</span><span class="hist-count">' + e.count + ' IBAN' + (e.count > 1 ? 's' : '') + '</span><span class="hist-time">' + timeStr + '</span></div>' +
        '<div class="hist-sample">' + e.sample + '</div>' +
        '<div class="hist-actions">' +
          '<button class="hist-replay" data-idx="' + i + '">&#x21bb; Regenerate</button>' +
          '<button class="hist-copy" data-idx="' + i + '">&#x2398; Copy</button>' +
        '</div>' +
      '</div>';
    }
    if (!entries.length) {
      html = '<div class="hist-empty">No history yet. Generate some IBANs!</div>';
    }
    historyItems.innerHTML = html;
  }

  historyToggle.addEventListener('click', function(e) {
    e.stopPropagation();
    var open = !historyPanel.classList.contains('open');
    historyPanel.classList.toggle('open', open);
    historyToggle.setAttribute('aria-expanded', String(open));
    if (open) renderHistoryPanel();
  });

  document.addEventListener('click', function(e) {
    if (!historyPanel.contains(e.target) && e.target !== historyToggle && !historyToggle.contains(e.target)) {
      historyPanel.classList.remove('open');
      historyToggle.setAttribute('aria-expanded', 'false');
    }
  });

  historyItems.addEventListener('click', function(e) {
    var btn = e.target.closest('button');
    if (!btn) return;
    var idx = parseInt(btn.getAttribute('data-idx'), 10);
    var entries = loadHistory();
    if (idx < 0 || idx >= entries.length) return;
    var entry = entries[idx];

    if (btn.classList.contains('hist-replay')) {
      // Find and select country, set quantity, generate
      var c = countries.filter(function(c) { return c.code === entry.country; })[0];
      if (c) {
        selectCountry(c);
        quantitySlider.value = Math.min(entry.count, 100);
        quantityValue.textContent = quantitySlider.value;
        generateIBANs();
      }
    } else if (btn.classList.contains('hist-copy')) {
      var text = entry.all.join('\n');
      navigator.clipboard.writeText(text).then(function() {
        showToast('Copied ' + entry.count + ' IBANs!');
      }).catch(function() {
        fallbackCopy(text);
      });
    }
    historyPanel.classList.remove('open');
  });

  historyClear.addEventListener('click', function() {
    saveHistory([]);
    renderHistoryPanel();
  });

  // ── Toast ────────────────────────────────────────────────────────
  function showToast(msg) {
    var toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(function() {
      toast.classList.remove('show');
    }, 2000);
  }

  // ── Full dataset copy/download ──────────────────────────────────
  function copyDatasetJSON() {
    if (!currentDataset) return;
    var json = JSON.stringify(currentDataset, null, 2);
    navigator.clipboard.writeText(json).then(function() {
      showToast('Full data set copied!');
    }).catch(function() {
      fallbackCopy(json);
    });
  }

  function downloadDataset() {
    if (!currentDataset) return;
    var json = JSON.stringify(currentDataset, null, 2);
    var fname = 'iban-dataset-' + currentDataset.ibanRaw.toLowerCase() + '.json';
    downloadFile(fname, json, 'application/json');
  }

  // ── Bind events ──────────────────────────────────────────────────
  btnGenerate.addEventListener('click', generateIBANs);

  btnCopy.addEventListener('click', function() {
    if (currentIBANs.length > 0) copySingle(currentIBANs[0].formatted);
  });

  btnCopyAll.addEventListener('click', copyAll);
  btnExportCSV.addEventListener('click', exportCSV);
  btnExportJSON.addEventListener('click', exportJSON);
  btnExportTXT.addEventListener('click', exportTXT);

  var btnDsCopy = document.getElementById('btn-ds-copy-json');
  if (btnDsCopy) btnDsCopy.addEventListener('click', copyDatasetJSON);
  var btnDsDownload = document.getElementById('btn-ds-download');
  if (btnDsDownload) btnDsDownload.addEventListener('click', downloadDataset);

  // Keyboard shortcut: Enter in country search selects first visible
  countrySearch.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      var firstVisible = countryList.querySelector('.country-option:not([style*="display: none"])');
      if (firstVisible) {
        var idx = parseInt(firstVisible.getAttribute('data-index'), 10);
        selectCountry(countries[idx]);
        closeCountryMenu();
      }
    }
  });

  // ── Init ─────────────────────────────────────────────────────────
  loadCountries();
  renderHistoryPanel();
  if (window.Dataset && Dataset.loadBanks) Dataset.loadBanks(function(){});
})();
