// iban-core.js — IBAN validation, generation, and formatting
// Pure JavaScript, no dependencies. Compatible with all browsers (ES5+).
// MOD-97 algorithm per ISO 13616 / ISO 7064 MOD 97-10

var IBAN = (function() {
  'use strict';

  // ── Letter-to-number conversion ───────────────────────────────
  // A=10, B=11, ..., Z=35
  function charToNum(c) {
    return c.charCodeAt(0) - 55;
  }

  // Convert rearranged string (BBAN + country + check) to digit string
  function toNumeric(str) {
    return str.replace(/[A-Z]/g, function(c) {
      return charToNum(c).toString();
    });
  }

  // ── MOD-97 (chunked, safe up to ~30 digits without BigInt) ────
  function mod97(numStr) {
    var remainder = numStr;
    while (remainder.length > 2) {
      var chunk = remainder.slice(0, 9); // 9 digits safely < MAX_SAFE_INTEGER
      remainder = (parseInt(chunk, 10) % 97).toString() + remainder.slice(chunk.length);
    }
    return parseInt(remainder, 10) % 97;
  }

  // ── Sanitise ──────────────────────────────────────────────────
  // Strip spaces, dashes, dots; uppercase
  function sanitise(iban) {
    return iban.replace(/[^A-Za-z0-9]/g, '').toUpperCase();
  }

  // ── Validate ──────────────────────────────────────────────────
  function isValid(iban) {
    if (!iban) return false;
    var clean = sanitise(iban);
    // Must start with 2 letters, 2 digits, rest alphanumeric
    if (!/^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$/.test(clean)) return false;
    // Rearrange: move first 4 chars to end
    var rearranged = clean.slice(4) + clean.slice(0, 4);
    var numeric = toNumeric(rearranged);
    return mod97(numeric) === 1;
  }

  // ── Generate check digits ─────────────────────────────────────
  function computeCheckDigits(countryCode, bban) {
    // Build: BBAN + country + "00"
    var rearranged = bban + countryCode + '00';
    var numeric = toNumeric(rearranged);
    var remainder = mod97(numeric);
    var check = 98 - remainder;
    // Zero-pad to 2 digits
    return check < 10 ? '0' + check : check.toString();
  }

  // ── Random digit string ───────────────────────────────────────
  function randDigits(count) {
    var s = '';
    for (var i = 0; i < count; i++) {
      s += Math.floor(Math.random() * 10).toString();
    }
    return s;
  }

  // ── Random alphabetic string (uppercase) ──────────────────────
  function randLetters(count) {
    var s = '';
    for (var i = 0; i < count; i++) {
      s += String.fromCharCode(65 + Math.floor(Math.random() * 26));
    }
    return s;
  }

  // ── Random alphanumeric string ────────────────────────────────
  function randAlphaNum(count) {
    var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    var s = '';
    for (var i = 0; i < count; i++) {
      s += chars.charAt(Math.floor(Math.random() * 36));
    }
    return s;
  }

  // ── Generate BBAN from format spec ────────────────────────────
  // format: "8!n10!n" or "4!a6!n8!n" or "5!n5!n11!c2!n"
  // Notation: n=digit, a=letter, c=alphanumeric
  function generateBBAN(format) {
    var bban = '';
    var parts = format.match(/(\d+)!([nac])/g);
    if (!parts) return '';
    for (var i = 0; i < parts.length; i++) {
      var m = parts[i].match(/(\d+)!([nac])/);
      var count = parseInt(m[1], 10);
      var type = m[2];
      if (type === 'n') {
        bban += randDigits(count);
      } else if (type === 'a') {
        bban += randLetters(count);
      } else if (type === 'c') {
        bban += randAlphaNum(count);
      }
    }
    return bban;
  }

  // ── Generate valid IBAN ───────────────────────────────────────
  function generate(countryCode, bbanFormat) {
    var bban = generateBBAN(bbanFormat);
    var check = computeCheckDigits(countryCode, bban);
    return countryCode + check + bban;
  }

  // ── Format IBAN (groups of 4, space-separated) ────────────────
  function format(iban) {
    var clean = sanitise(iban);
    var groups = [];
    for (var i = 0; i < clean.length; i += 4) {
      groups.push(clean.slice(i, i + 4));
    }
    return groups.join(' ');
  }

  // ── Parse IBAN into components ────────────────────────────────
  // Returns { country, check, bban } or null if invalid format
  function parse(iban) {
    var clean = sanitise(iban);
    if (clean.length < 5) return null;
    return {
      country: clean.slice(0, 2),
      check: clean.slice(2, 4),
      bban: clean.slice(4)
    };
  }

  // ── Identify country from IBAN ────────────────────────────────
  function getCountry(iban) {
    var clean = sanitise(iban);
    if (clean.length < 2) return null;
    return clean.slice(0, 2);
  }

  // ── Public API ────────────────────────────────────────────────
  return {
    isValid: isValid,
    generate: generate,
    computeCheckDigits: computeCheckDigits,
    generateBBAN: generateBBAN,
    format: format,
    parse: parse,
    getCountry: getCountry,
    sanitise: sanitise,
    mod97: mod97
  };
})();

// Export for Node.js if needed
if (typeof module !== 'undefined' && module.exports) {
  module.exports = IBAN;
}
