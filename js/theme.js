// theme.js — Dark/Light theme toggle for ibaneasy.com
// Must load BEFORE body to prevent flash of unstyled content (FOUC)
(function() {
  'use strict';

  var KEY = 'ibaneasy_theme';
  var stored = localStorage.getItem(KEY);

  // Determine initial theme: stored preference > system preference > dark
  if (stored === 'light' || stored === 'dark') {
    document.documentElement.setAttribute('data-theme', stored);
  } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
    document.documentElement.setAttribute('data-theme', 'light');
  } else {
    document.documentElement.setAttribute('data-theme', 'dark');
  }

  // Listen for system preference changes
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', function(e) {
      if (!localStorage.getItem(KEY)) {
        document.documentElement.setAttribute('data-theme', e.matches ? 'light' : 'dark');
      }
    });
  }

  // Toggle function — called by the toggle button in navbar
  window.toggleTheme = function() {
    var current = document.documentElement.getAttribute('data-theme');
    var next = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem(KEY, next);
  };
})();
