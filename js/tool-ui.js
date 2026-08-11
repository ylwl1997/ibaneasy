// tool-ui.js — Interactive UI for the IBAN generator on the homepage
(function() {
  'use strict';

  var select = document.getElementById('country-select');
  var display = document.getElementById('iban-display');
  var btnGenerate = document.getElementById('btn-generate');
  var btnBulk = document.getElementById('btn-bulk');
  var btnCopy = document.getElementById('btn-copy');
  var copyMsg = document.getElementById('copy-msg');

  var countries = [];
  var currentIBAN = '';

  // ── Load country data ──────────────────────────────────────────
  function loadCountries() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/iban_countries.json', true);
    xhr.onload = function() {
      if (xhr.status === 200) {
        countries = JSON.parse(xhr.responseText);
        populateSelect();
      }
    };
    xhr.onerror = function() {
      select.innerHTML = '<option value="">Failed to load countries</option>';
    };
    xhr.send();
  }

  function populateSelect() {
    // Sort: SEPA first, then alphabetically
    countries.sort(function(a, b) {
      if (a.sepa !== b.sepa) return a.sepa ? -1 : 1;
      return a.name.localeCompare(b.name);
    });

    var html = '<option value="">-- Select a country --</option>';
    var currentGroup = '';

    for (var i = 0; i < countries.length; i++) {
      var c = countries[i];
      var group = c.continent;
      if (c.sepa && group === 'Europe') group = 'SEPA (Europe)';
      else if (c.sepa) group = 'SEPA (' + group + ')';
      else group = 'Non-SEPA (' + group + ')';

      if (group !== currentGroup) {
        if (currentGroup !== '') html += '</optgroup>';
        html += '<optgroup label="' + group + '">';
        currentGroup = group;
      }
      html += '<option value="' + c.code + '" data-format="' + c.bbanFormat + '">' +
              c.code + ' — ' + c.name + ' (' + c.ibanLen + ' chars)</option>';
    }
    html += '</optgroup>';
    select.innerHTML = html;
  }

  // ── Generate ───────────────────────────────────────────────────
  function generateOne() {
    var code = select.value;
    if (!code) {
      display.textContent = 'Select a country and click Generate';
      display.classList.remove('generated');
      btnCopy.style.display = 'none';
      return;
    }

    var option = select.options[select.selectedIndex];
    var format = option.getAttribute('data-format');
    currentIBAN = IBAN.generate(code, format);
    display.textContent = IBAN.format(currentIBAN);
    display.classList.add('generated');
    btnCopy.style.display = 'inline-flex';
    copyMsg.style.display = 'none';
  }

  function generateBulk() {
    var code = select.value;
    if (!code) {
      display.textContent = 'Select a country first';
      return;
    }

    var option = select.options[select.selectedIndex];
    var format = option.getAttribute('data-format');
    var lines = [];
    for (var i = 0; i < 10; i++) {
      lines.push(IBAN.format(IBAN.generate(code, format)));
    }
    currentIBAN = lines.join('\n');
    display.textContent = currentIBAN;
    display.classList.add('generated');
    display.style.whiteSpace = 'pre';
    display.style.fontSize = '1rem';
    display.style.textAlign = 'left';
    btnCopy.style.display = 'inline-flex';
    copyMsg.style.display = 'none';
  }

  function resetDisplay() {
    if (display.style.whiteSpace === 'pre') {
      display.style.whiteSpace = '';
      display.style.fontSize = '';
      display.style.textAlign = '';
    }
  }

  // ── Copy ───────────────────────────────────────────────────────
  function copyToClipboard() {
    if (!currentIBAN) return;
    navigator.clipboard.writeText(currentIBAN).then(function() {
      copyMsg.style.display = 'inline';
      setTimeout(function() { copyMsg.style.display = 'none'; }, 2000);
    }).catch(function() {
      // Fallback for older browsers
      var ta = document.createElement('textarea');
      ta.value = currentIBAN;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      copyMsg.style.display = 'inline';
      setTimeout(function() { copyMsg.style.display = 'none'; }, 2000);
    });
  }

  // ── FAQ Accordion ──────────────────────────────────────────────
  function initFAQ() {
    var items = document.querySelectorAll('.faq-item');
    for (var i = 0; i < items.length; i++) {
      (function(item) {
        var q = item.querySelector('.faq-q');
        q.addEventListener('click', function() {
          item.classList.toggle('open');
        });
      })(items[i]);
    }
  }

  // ── Bind events ────────────────────────────────────────────────
  btnGenerate.addEventListener('click', function() {
    resetDisplay();
    generateOne();
  });

  btnBulk.addEventListener('click', function() {
    generateBulk();
  });

  btnCopy.addEventListener('click', copyToClipboard);

  // Generate on country change (convenience)
  select.addEventListener('change', function() {
    resetDisplay();
    if (select.value) generateOne();
  });

  // ── Init ───────────────────────────────────────────────────────
  loadCountries();
  initFAQ();
})();
