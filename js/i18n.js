// i18n.js — Lightweight internationalization for ibaneasy.com
// Detects language from URL path prefix (/zh/, /es/, etc.)
// Applies translations from JSON files to elements with data-i18n attributes
(function() {
  'use strict';
  var currentLang = 'en';
  var translations = {};

  // Detect language from URL path
  function detectLang() {
    var path = window.location.pathname;
    var m = path.match(/^\/(zh|es|de|fr|ja|ko|ar)\//);
    return m ? m[1] : 'en';
  }

  // Load translation JSON
  function loadTranslations(lang, callback) {
    if (lang === 'en') { callback(); return; }
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/js/i18n/' + lang + '.json', true);
    xhr.onload = function() {
      if (xhr.status === 200) {
        try { translations = JSON.parse(xhr.responseText); } catch(e) { translations = {}; }
      }
      callback();
    };
    xhr.onerror = function() { callback(); };
    xhr.send();
  }

  // Apply translations to DOM — textContent replacement
  function applyTranslations() {
    // data-i18n for text content
    var elements = document.querySelectorAll('[data-i18n]');
    for (var i = 0; i < elements.length; i++) {
      var key = elements[i].getAttribute('data-i18n');
      if (translations[key]) {
        elements[i].textContent = translations[key];
      }
    }

    // data-i18n-placeholder for input placeholders
    var placeholders = document.querySelectorAll('[data-i18n-placeholder]');
    for (var j = 0; j < placeholders.length; j++) {
      var pkey = placeholders[j].getAttribute('data-i18n-placeholder');
      if (translations[pkey]) {
        placeholders[j].setAttribute('placeholder', translations[pkey]);
      }
    }

    // data-i18n-aria for aria-labels
    var ariaEls = document.querySelectorAll('[data-i18n-aria]');
    for (var k = 0; k < ariaEls.length; k++) {
      var akey = ariaEls[k].getAttribute('data-i18n-aria');
      if (translations[akey]) {
        ariaEls[k].setAttribute('aria-label', translations[akey]);
      }
    }

    // Update lang attribute on html element
    document.documentElement.setAttribute('lang', currentLang);
  }

  // Public API for dynamic strings (used by tool-ui.js)
  window.i18n = function(key, defaultText) {
    return translations[key] || defaultText || key;
  };

  // Expose current language
  window.i18n_lang = function() { return currentLang; };

  function init() {
    currentLang = detectLang();
    loadTranslations(currentLang, function() {
      applyTranslations();
    });
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
