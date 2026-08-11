#!/usr/bin/env python3
"""
build.py — Static site generator for ibaneasy.com
Reads iban_countries.json and generates all SEO pages under src/
Also generates sitemap.xml and robots.txt

Usage: python build.py
Output: src/ directory with all generated pages + sitemap.xml + robots.txt
"""

import json
import os
import re
import random
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src')
DATA = os.path.join(ROOT, 'iban_countries.json')
SITE = 'https://ibaneasy.com'
TODAY = date.today().isoformat()

if not os.path.exists(DATA):
    raise SystemExit(f'ERROR: {DATA} not found — run from project root')

with open(DATA, 'r', encoding='utf-8') as f:
    countries = json.load(f)

# ── Python MOD-97 ────────────────────────────────────────────────
def mod97(num_str):
    """Python can handle huge integers natively, no chunking needed."""
    return int(num_str) % 97

def letter_to_num(c):
    return str(ord(c) - 55)  # A=10, B=11, ..., Z=35

def to_numeric(s):
    return ''.join(letter_to_num(c) if c.isalpha() else c for c in s)

def compute_check(country_code, bban):
    rearranged = bban + country_code + '00'
    numeric = to_numeric(rearranged)
    remainder = mod97(numeric)
    check = 98 - remainder
    return str(check).zfill(2)

def generate_bban(bban_format):
    parts = re.findall(r'(\d+)!([nac])', bban_format)
    bban = ''
    for count_str, t in parts:
        count = int(count_str)
        if t == 'n':
            bban += ''.join(str(random.randint(0, 9)) for _ in range(count))
        elif t == 'a':
            bban += ''.join(chr(random.randint(65, 90)) for _ in range(count))
        else:  # c — alphanumeric
            chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            bban += ''.join(random.choice(chars) for _ in range(count))
    return bban

def generate_iban(country):
    bban = generate_bban(country['bbanFormat'])
    check = compute_check(country['code'], bban)
    return country['code'] + check + bban

def format_iban(iban):
    """Insert spaces every 4 characters."""
    return ' '.join(iban[i:i+4] for i in range(0, len(iban), 4))

# ── Shared HTML Blocks ───────────────────────────────────────────
HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="IBAN Easy">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="{canon}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/style.css">
{extra}
</head>
<body>
<header class="barwrap">
  <div class="bar">
  <a class="brand" href="/"><span>IBAN</span> Easy</a>
  <nav><a href="/countries/">Countries</a><a href="/validate/">Validator</a><a href="/sepa-countries/">SEPA</a><a href="/iban-check-digit/">Check Digits</a></nav>
  </div>
</header>
<main class="prose">
'''

FOOT = '''</main>
<div class="ad-slot ad-banner">
  <script>
    atOptions = {{'key' : 'e952f34ad033773cc0c7f8577847b6f3','format' : 'iframe','height' : 90,'width' : 728,'params' : {{}}}};
  </script>
  <script src="https://www.highperformanceformat.com/e952f34ad033773cc0c7f8577847b6f3/invoke.js"></script>
</div>
<footer class="foot">
  <nav>
    <a href="/">IBAN Generator</a><a href="/countries/">All Countries</a><a href="/validate/">Validator</a><a href="/sepa-countries/">SEPA Countries</a><a href="/iban-check-digit/">Check Digits</a>
  </nav>
  <p>IBAN Easy &mdash; Free online IBAN tools. All generation and validation runs client-side. No data is collected or stored. Generated IBANs are for testing only.</p>
</footer>
</body>
</html>'''

NATIVE_AD = '''<div class="ad-slot ad-native">
  <script async="async" data-cfasync="false" src="https://pl30774768.effectivecpmnetwork.com/f95daa4035d01d0dbb3f7c2c7af03073/invoke.js"></script>
  <div id="container-f95daa4035d01d0dbb3f7c2c7af03073"></div>
</div>'''

# ── Helpers ──────────────────────────────────────────────────────
def page(dirname, content):
    """Write content to src/<dirname>/index.html, creating dirs as needed."""
    d = os.path.join(SRC, dirname)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(content)

def esc(s):
    """Basic HTML entity escape."""
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def slug(name):
    """Convert country name to URL slug."""
    s = name.lower().strip()
    s = s.replace('&', 'and')
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')

def continent_order(name):
    """Sort continents in common order."""
    order = {'Europe': 0, 'North America': 1, 'South America': 2, 'Asia': 3, 'Africa': 4, 'Oceania': 5}
    return order.get(name, 9)

# ── IBAN Structure Diagram ───────────────────────────────────────
def build_structure_diagram(c):
    """Generate the visual IBAN structure block diagram."""
    parts = []
    parts.append('<div class="iban-legend">')
    parts.append('<span><span class="swatch" style="background:var(--accent-light);border-color:var(--accent)"></span> Country ({})</span>'.format(c['code']))
    parts.append('<span><span class="swatch" style="background:var(--success-light);border-color:var(--success)"></span> Check digits</span>')
    parts.append('<span><span class="swatch" style="background:var(--warning-light);border-color:var(--warning)"></span> Bank code ({} {})</span>'.format(c['bankLen'], 'letters' if c['bbanFormat'].startswith(str(c['bankLen'])+'!a') else 'digits'))
    if c.get('branchStart') and c.get('branchLen'):
        parts.append('<span><span class="swatch" style="background:#f0f9ff;border-color:#0284c7"></span> Branch ({} chars)</span>'.format(c['branchLen']))
    parts.append('<span><span class="swatch" style="background:var(--surface);border-color:var(--muted)"></span> Account ({} chars)</span>'.format(c['accountLen']))
    parts.append('</div>')

    parts.append('<div class="iban-structure">')
    # Country
    parts.append('<div class="iban-block country" title="Country code">{}</div>'.format(c['code']))
    # Check digits
    parts.append('<div class="iban-block check" title="Check digits">XX</div>')
    # Bank
    bank_text = 'Bank' if c['bankLen'] <= 6 else 'Bank code'
    parts.append('<div class="iban-block bank" title="Bank code ({} chars)">{}<br><small>{} chars</small></div>'.format(c['bankLen'], bank_text, c['bankLen']))
    # Branch (if applicable)
    if c.get('branchStart') and c.get('branchLen'):
        parts.append('<div class="iban-block branch" title="Branch code">Branch<br><small>{} chars</small></div>'.format(c['branchLen']))
    # Account
    acc_text = 'Account' if c['accountLen'] <= 10 else 'Account number'
    parts.append('<div class="iban-block account" title="Account number ({} chars)">{}<br><small>{} chars</small></div>'.format(c['accountLen'], acc_text, c['accountLen']))
    parts.append('</div>')
    return '\n'.join(parts)

# ── Spec Table ───────────────────────────────────────────────────
def build_spec_table(c):
    rows = [
        ('IBAN Length', '{} characters'.format(c['ibanLen'])),
        ('BBAN Length', '{} characters'.format(c['bbanLen'])),
        ('BBAN Format', '<code>{}</code>'.format(c['bbanFormat'])),
        ('Bank Code', 'Position {}, {} {}'.format(c['bankStart'], c['bankLen'], 'letters' if re.match(r'\d+!a', c['bbanFormat']) else 'digits')),
    ]
    if c.get('branchStart') and c.get('branchLen'):
        rows.append(('Branch Code', 'Position {}, {} chars'.format(c['branchStart'], c['branchLen'])))
    rows.append(('Account Number', 'Position {}, {} chars'.format(c['accountStart'], c['accountLen'])))
    rows.append(('SEPA Member', '&#x2705; Yes' if c['sepa'] else '&#x274C; No'))
    if c.get('notes'):
        rows.append(('Notes', c['notes']))

    html = '<div class="tablewrap"><table>\n<thead><tr><th>Property</th><th>Value</th></tr></thead>\n<tbody>\n'
    for label, val in rows:
        html += '<tr><td>{}</td><td>{}</td></tr>\n'.format(label, val)
    html += '</tbody>\n</table></div>'
    return html

# ── Example IBANs ────────────────────────────────────────────────
def build_examples(c, count=3):
    examples = []
    for _ in range(count):
        iban = generate_iban(c)
        examples.append(format_iban(iban))
    return examples

# ── Country-specific FAQs ────────────────────────────────────────
def country_faqs(c):
    name = c['name']
    return [
        ('What is the IBAN format for {}?'.format(name),
         '{} uses a {}-character IBAN with the country code "{}" followed by two check digits and a {}-character BBAN. The format is <code>{}</code>. The bank code occupies positions {} to {}.'.format(
             name, c['ibanLen'], c['code'], c['bbanLen'], c['bbanFormat'],
             c['bankStart'], c['bankStart'] + c['bankLen'] - 1)),
        ('Is {} a SEPA country?'.format(name),
         'Yes, {} is part of the SEPA (Single Euro Payments Area) and uses IBAN for all domestic and international transfers.'.format(name) if c['sepa'] else
         'No, {} is not a SEPA member, but uses IBAN for international transfers.'.format(name)),
        ('How long is a {} IBAN?'.format(name),
         'A {} IBAN is exactly {} characters long. The BBAN portion accounts for {} characters.'.format(name, c['ibanLen'], c['bbanLen'])),
        ('How do I find my {} IBAN?'.format(name),
         'Your IBAN is printed on your bank statement, available in your online banking portal, or can be obtained from your bank. It typically appears alongside your BIC/SWIFT code for international transfers.'),
        ('Can I generate a valid {} IBAN for testing?'.format(name),
         'Yes! Use the IBAN generator on this page or visit the <a href="/">IBAN Easy homepage</a> to generate mathematically valid IBANs for any supported country. All generation is client-side and private.'),
    ]

# ── Page Builders ────────────────────────────────────────────────

def build_country_page(c):
    """Build a single country detail page."""
    name = c['name']
    code = c['code']
    can_path = '/countries/{}/'.format(code.lower())
    title = '{} IBAN Generator — Format, Structure & Examples'.format(name)
    desc = 'Generate valid {} IBANs. {} IBAN format: {}-character code starting with {}, bank code ({}) + account number. SEPA member: {}. Free online tool.'.format(
        name, name, c['ibanLen'], code, c['bankLen'], 'Yes' if c['sepa'] else 'No')

    extra = '<script type="application/ld+json">' + json.dumps({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in country_faqs(c)]
    }) + '</script>'

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + can_path,
        og_title=esc(title), og_desc=esc(desc),
        extra=extra
    )

    body += '<nav class="crumbs"><a href="/">Home</a><span class="sep">/</span><a href="/countries/">Countries</a><span class="sep">/</span>{}</nav>\n'.format(name)
    body += '<h1>{} IBAN Format &amp; Generator</h1>\n'.format(esc(name))
    body += '<p class="lede">Complete reference for {} IBANs: format structure, bank codes, account numbers, examples, and a free generator for testing.</p>\n'.format(name)

    # Structure diagram
    body += '<h2>IBAN Structure for {}</h2>\n'.format(name)
    body += build_structure_diagram(c)

    # Specs table
    body += '<h2>{} IBAN Technical Specifications</h2>\n'.format(name)
    body += build_spec_table(c)

    # Examples
    examples = build_examples(c, 3)
    body += '<h2>Example {} IBANs</h2>\n'.format(name)
    body += '<p>Here are 3 randomly generated but <strong>mathematically valid</strong> {} IBANs for testing:</p>\n'.format(name)
    body += '<ul>\n'
    for ex in examples:
        body += '<li><code>{}</code></li>\n'.format(ex)
    body += '</ul>\n'
    body += '<p style="font-size:0.85rem;color:var(--muted)">&#x26A0; These are randomly generated test IBANs — not real bank accounts. Do not use for actual transactions.</p>\n'

    # In-page mini generator note
    body += '<h2>Generate More {} IBANs</h2>\n'.format(name)
    body += '<p>Use our <a href="/">free IBAN generator</a> to create more test IBANs for {}. The tool runs entirely in your browser — no data is sent to any server.</p>\n'.format(name)

    # Native Ad
    body += '<h2>Frequently Asked Questions</h2>\n'
    body += NATIVE_AD + '\n'

    # FAQs
    for q, a in country_faqs(c):
        body += '<h3>{}</h3>\n<p>{}</p>\n'.format(q, a)

    # Related countries
    continent = c['continent']
    related = [x for x in countries if x['continent'] == continent and x['code'] != code][:8]
    if related:
        body += '<h2>Other IBAN Countries in {}</h2>\n'.format(continent)
        body += '<ul>\n'
        for r in related:
            body += '<li><a href="/countries/{}/">{} IBAN ({} chars{})</a></li>\n'.format(
                r['code'].lower(), r['name'], r['ibanLen'],
                ', SEPA' if r['sepa'] else '')
        body += '</ul>\n'

    body += FOOT
    return body


def build_countries_index():
    """Build the /countries/ index page listing all countries."""
    title = 'All IBAN Countries — Complete List of 96 IBAN Formats Worldwide'
    desc = 'Browse all 96 countries that use IBAN. Filter by continent and SEPA membership. Each country page includes IBAN format, bank code details, examples, and a free generator.'

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/countries/',
        og_title=esc(title), og_desc=esc(desc),
        extra=''
    )

    body += '<h1>All IBAN Countries</h1>\n'
    body += '<p class="lede">96 countries and territories worldwide use the IBAN system. Browse by continent or SEPA membership. Click any country for full IBAN format details, examples, and a generator.</p>\n'

    # Native Ad
    body += NATIVE_AD + '\n'

    # Search
    body += '<input type="text" class="search-box" id="country-search" placeholder="Search countries..." oninput="filterCountries()" aria-label="Search countries">\n'

    # Stats
    sepa_count = sum(1 for c in countries if c['sepa'])
    body += '<p><strong>{}</strong> SEPA countries | <strong>{}</strong> non-SEPA IBAN countries | <strong>{}</strong> total</p>\n'.format(
        sepa_count, len(countries) - sepa_count, len(countries))

    # Group by continent
    continents = {}
    for c in countries:
        cont = c['continent']
        if cont not in continents:
            continents[cont] = []
        continents[cont].append(c)

    for cont in sorted(continents, key=continent_order):
        body += '<h2>{}</h2>\n'.format(cont)
        body += '<ul class="grid">\n'
        for c in sorted(continents[cont], key=lambda x: x['name']):
            badge = ' <span class="badge badge-sepa">SEPA</span>' if c['sepa'] else ''
            body += '<li><a class="card" href="/countries/{}/"><div class="cc">{}</div><div class="name">{}{}</div><div class="meta">{} chars</div></a></li>\n'.format(
                c['code'].lower(), c['code'], c['name'], badge, c['ibanLen'])
        body += '</ul>\n'

    # Search script
    body += '''<script>
function filterCountries() {
  var q = document.getElementById('country-search').value.toLowerCase();
  var sections = document.querySelectorAll('h2');
  var grids = document.querySelectorAll('.grid');
  for (var i = 0; i < grids.length; i++) {
    var cards = grids[i].querySelectorAll('.card');
    var visible = 0;
    for (var j = 0; j < cards.length; j++) {
      var text = cards[j].textContent.toLowerCase();
      if (text.indexOf(q) !== -1) { cards[j].style.display = ''; visible++; }
      else { cards[j].style.display = 'none'; }
    }
    sections[i+1].style.display = visible > 0 ? '' : 'none';
    if (grids[i].previousElementSibling && grids[i].previousElementSibling.tagName === 'H2') {
      grids[i].previousElementSibling.style.display = visible > 0 ? '' : 'none';
    }
  }
}
</script>'''

    body += FOOT
    return body


def build_validator_page():
    """Build the /validate/ standalone validator page."""
    title = 'Free IBAN Validator — Check Any IBAN Number Online'
    desc = 'Validate any IBAN number instantly. Checks country code, length, and MOD-97 check digits. Supports all 96 IBAN countries. 100% client-side — your data stays private.'

    extra = '<script type="application/ld+json">' + json.dumps({
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        'name': 'IBAN Validator',
        'url': SITE + '/validate/',
        'description': 'Free online IBAN validator — check any IBAN for correctness using MOD-97 algorithm',
        'applicationCategory': 'FinanceApplication'
    }) + '</script>'

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/validate/',
        og_title=esc(title), og_desc=esc(desc),
        extra=extra
    )

    body += '<h1>IBAN Validator</h1>\n'
    body += '<p class="lede">Enter any IBAN to check if it\'s valid. We verify the country code, total length, character format, and MOD-97 check digits.</p>\n'

    body += '<input type="text" class="validator-input" id="iban-input" placeholder="Enter IBAN (e.g., DE89 3704 0044 0532 0130 00)" autocomplete="off" aria-label="Enter IBAN to validate">\n'
    body += '<div class="validator-result" id="result" style="display:none"></div>\n'
    body += '<div style="margin-top:1rem" id="details" style="display:none"></div>\n'

    body += NATIVE_AD + '\n'

    body += '<h2>How IBAN Validation Works</h2>\n'
    body += '<p>IBAN validation involves three checks:</p>\n'
    body += '<ol>\n'
    body += '<li><strong>Format check</strong>: The IBAN must start with two letters (country code), followed by two digits (check digits), then 11-30 alphanumeric characters. Total length must match the country\'s expected length.</li>\n'
    body += '<li><strong>Country check</strong>: The first two characters must be a valid ISO country code that participates in the IBAN system.</li>\n'
    body += '<li><strong>MOD-97 check</strong>: The IBAN is rearranged (move first 4 chars to end), letters are converted to numbers (A=10, B=11, ..., Z=35), and the resulting huge integer must give remainder 1 when divided by 97.</li>\n'
    body += '</ol>\n'

    body += '<p><a href="/iban-check-digit/">Learn more about the MOD-97 algorithm &rarr;</a></p>\n'

    body += '''<script src="/js/iban-core.js"></script>
<script>
(function() {
  var inp = document.getElementById('iban-input');
  var result = document.getElementById('result');
  var details = document.getElementById('details');

  // Country length lookup (populated from the same data)
  var COUNTRY_LENGTHS = {};
  var COUNTRY_NAMES = {};
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/iban_countries.json', true);
  xhr.onload = function() {
    if (xhr.status === 200) {
      var data = JSON.parse(xhr.responseText);
      for (var i = 0; i < data.length; i++) {
        COUNTRY_LENGTHS[data[i].code] = data[i].ibanLen;
        COUNTRY_NAMES[data[i].code] = data[i].name;
      }
    }
  };
  xhr.send();

  function check() {
    var val = inp.value.trim();
    if (!val) { result.style.display = 'none'; details.style.display = 'none'; return; }

    var clean = IBAN.sanitise(val);
    var info = [];

    // Check 1: Country exists
    var cc = clean.slice(0, 2);
    if (COUNTRY_LENGTHS[cc]) {
      info.push('Country: ' + COUNTRY_NAMES[cc] + ' (' + cc + ')');

      // Check 2: Length
      var expectedLen = COUNTRY_LENGTHS[cc];
      if (clean.length !== expectedLen) {
        info.push('Length: ' + clean.length + ' characters (expected ' + expectedLen + ' for ' + COUNTRY_NAMES[cc] + ')');
        inp.className = 'validator-input invalid';
        result.style.display = 'block';
        result.className = 'validator-result invalid';
        result.textContent = '\\u2718 Invalid — Wrong length for ' + COUNTRY_NAMES[cc];
        details.innerHTML = '<div class="tablewrap"><table>' + info.map(function(i) { return '<tr><td>' + i + '</td></tr>'; }).join('') + '</table></div>';
        details.style.display = 'block';
        return;
      }
      info.push('Length: ' + clean.length + ' characters (correct for ' + COUNTRY_NAMES[cc] + ')');
    } else {
      info.push('Country code "' + cc + '" is not a valid IBAN country');
    }

    // Check 3: MOD-97
    var valid = IBAN.isValid(val);
    info.push('MOD-97 check: ' + (valid ? 'Passed \\u2705' : 'Failed \\u274C'));

    if (valid) {
      inp.className = 'validator-input valid';
      result.style.display = 'block';
      result.className = 'validator-result valid';
      result.textContent = '\\u2714 Valid IBAN — ' + (COUNTRY_NAMES[cc] || cc);
    } else {
      inp.className = 'validator-input invalid';
      result.style.display = 'block';
      result.className = 'validator-result invalid';
      result.textContent = '\\u2718 Invalid IBAN';
    }

    details.innerHTML = '<div class="tablewrap"><table>' + info.map(function(i) { return '<tr><td>' + i + '</td></tr>'; }).join('') + '</table></div>';
    details.style.display = 'block';
  }

  inp.addEventListener('input', check);
  inp.addEventListener('paste', function() { setTimeout(check, 50); });
})();
</script>'''

    body += FOOT
    return body


def build_sepa_page():
    """Build the /sepa-countries/ page."""
    title = 'SEPA Countries — Complete List of 36 SEPA IBAN Countries (2026)'
    desc = 'Full list of all 36 SEPA countries and their IBAN formats. SEPA includes EU/EEA states, Switzerland, Monaco, San Marino, Andorra, Vatican City, and UK crown dependencies.'

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/sepa-countries/',
        og_title=esc(title), og_desc=esc(desc),
        extra=''
    )

    body += '<h1>SEPA Countries List</h1>\n'
    body += '<p class="lede">The Single Euro Payments Area (SEPA) includes 36 countries. All SEPA transfers require an IBAN. Here is the complete list with IBAN formats.</p>\n'

    body += NATIVE_AD + '\n'

    sepa = [c for c in countries if c['sepa']]
    body += '<h2>All {} SEPA Members</h2>\n'.format(len(sepa))
    body += '<div class="tablewrap"><table>\n'
    body += '<thead><tr><th>Country</th><th>Code</th><th>IBAN Length</th><th>Bank Code</th><th>Format</th></tr></thead>\n<tbody>\n'
    for c in sorted(sepa, key=lambda x: x['name']):
        body += '<tr><td><a href="/countries/{code}/">{name}</a></td><td><code>{code}</code></td><td>{ibanLen}</td><td>{bankLen} {bankType}</td><td><code>{fmt}</code></td></tr>\n'.format(
            code=c['code'].lower(), name=c['name'], ibanLen=c['ibanLen'],
            bankLen=c['bankLen'],
            bankType='letters' if re.match(r'\d+!a', c['bbanFormat']) else 'digits',
            fmt=c['bbanFormat'])
    body += '</tbody>\n</table></div>\n'

    body += '<h2>What is SEPA?</h2>\n'
    body += '<p>The Single Euro Payments Area (SEPA) is a payment integration initiative of the European Union. It allows customers to make cashless euro payments to anywhere in the SEPA zone using a single bank account and IBAN.</p>\n'
    body += '<ul>\n'
    body += '<li><strong>EU/EEA countries</strong>: 31 members (all EU states plus Norway, Iceland, Liechtenstein)</li>\n'
    body += '<li><strong>Non-EEA SEPA members</strong>: Switzerland, Monaco, San Marino, Andorra, Vatican City</li>\n'
    body += '<li><strong>UK & Crown Dependencies</strong>: Though no longer EU members, UK, Guernsey, Jersey, and Isle of Man remain in SEPA</li>\n'
    body += '</ul>\n'

    body += FOOT
    return body


def build_check_digit_page():
    """Build the /iban-check-digit/ educational page."""
    title = 'IBAN Check Digits Explained — How MOD-97 Validates Your IBAN'
    desc = 'Learn how IBAN check digits work using the MOD-97 algorithm. Step-by-step explanation with examples. Understand why IBANs are so reliable for international banking.'

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/iban-check-digit/',
        og_title=esc(title), og_desc=esc(desc),
        extra=''
    )

    body += '<h1>How IBAN Check Digits Work</h1>\n'
    body += '<p class="lede">Every IBAN includes two check digits that catch 99.9% of typing errors. They use a mathematical formula called MOD-97, first published in ISO 7064. Here\'s how it works.</p>\n'

    body += NATIVE_AD + '\n'

    body += '<h2>The MOD-97 Algorithm</h2>\n'
    body += '<p>The check digits (positions 3-4 in every IBAN) are computed using the MOD-97 algorithm. Here is the step-by-step process:</p>\n'

    body += '<h3>Step 1: Rearrange the IBAN</h3>\n'
    body += '<p>Move the first four characters (country code + check digits) to the end of the string.</p>\n'
    body += '<p>Example for <code>GB29 NWBK 6016 1331 9268 19</code>:</p>\n'
    body += '<pre>Original:  GB29 NWBK 6016 1331 9268 19\nRearrange: NWBK 6016 1331 9268 19 GB29</pre>\n'

    body += '<h3>Step 2: Convert Letters to Numbers</h3>\n'
    body += '<p>Replace each letter with its numeric value: A=10, B=11, ..., Z=35.</p>\n'
    body += '<pre>A=10, B=11, C=12, ..., Z=35\nN → 23, W → 32, B → 11, K → 20, G → 16, B → 11</pre>\n'

    body += '<h3>Step 3: Compute MOD-97</h3>\n'
    body += '<p>Interpret the resulting string as a huge integer and divide by 97. A valid IBAN always gives <strong>remainder 1</strong>.</p>\n'
    body += '<pre>NWBK60161331926819GB29 → (huge integer) mod 97 = 1 ✓</pre>\n'

    body += '<h2>How Check Digits Are Generated</h2>\n'
    body += '<p>When a bank creates an IBAN, it:</p>\n'
    body += '<ol>\n'
    body += '<li>Starts with the country code + "00" + BBAN (domestic account details)</li>\n'
    body += '<li>Moves the first 4 chars to the end</li>\n'
    body += '<li>Converts letters to numbers</li>\n'
    body += '<li>Computes <code>remainder = big_number mod 97</code></li>\n'
    body += '<li>Check digits = <code>98 − remainder</code> (zero-padded to 2 digits)</li>\n'
    body += '</ol>\n'

    body += '<h2>Why 97?</h2>\n'
    body += '<p>97 was chosen because:</p>\n'
    body += '<ul>\n'
    body += '<li>It\'s the largest two-digit prime number</li>\n'
    body += '<li>It catches 99.94% of single-digit typos and transposition errors</li>\n'
    body += '<li>The math works efficiently for numbers of any length</li>\n'
    body += '</ul>\n'

    body += '<h2>Computing MOD-97 in JavaScript</h2>\n'
    body += '<p>Since IBAN numeric strings can be 30+ digits (too large for JavaScript\'s Number type), we process in chunks:</p>\n'
    body += '<pre>function mod97(numStr) {\n  let remainder = numStr;\n  while (remainder.length > 2) {\n    let chunk = remainder.slice(0, 9); // 9 digits safely &lt; MAX_SAFE_INTEGER\n    remainder = (parseInt(chunk, 10) % 97).toString() + remainder.slice(chunk.length);\n  }\n  return parseInt(remainder, 10) % 97;\n}</pre>\n'

    body += '<p><a href="/">Try our IBAN generator &rarr;</a></p>\n'

    body += FOOT
    return body


def build_sitemap():
    """Generate sitemap.xml."""
    today = TODAY
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <url><loc>{}/</loc><lastmod>{}</lastmod><priority>1.0</priority></url>'.format(SITE, today),
        '  <url><loc>{}/countries/</loc><lastmod>{}</lastmod><priority>0.9</priority></url>'.format(SITE, today),
        '  <url><loc>{}/validate/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/sepa-countries/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/iban-check-digit/</loc><lastmod>{}</lastmod><priority>0.7</priority></url>'.format(SITE, today),
    ]
    for c in sorted(countries, key=lambda x: x['name']):
        p = 0.7 if c['sepa'] else 0.5
        lines.append('  <url><loc>{}/countries/{}/</loc><lastmod>{}</lastmod><priority>{}</priority></url>'.format(
            SITE, c['code'].lower(), today, p))
    lines.append('</urlset>')
    return '\n'.join(lines)


def build_robots():
    """Generate robots.txt."""
    return 'User-agent: *\nAllow: /\n\nSitemap: {}/sitemap.xml\n'.format(SITE)


# ── Main ─────────────────────────────────────────────────────────
def main():
    print('=== ibaneasy.com static site generator ===')
    print('Countries loaded: {}'.format(len(countries)))
    print('Output directory: {}'.format(SRC))

    total = 0

    # 1. Country pages
    print('\n[1/6] Generating {} country pages...'.format(len(countries)))
    for i, c in enumerate(countries):
        html = build_country_page(c)
        page('countries/{}'.format(c['code'].lower()), html)
        total += 1
        if (i + 1) % 20 == 0:
            print('  ... {}/{}'.format(i + 1, len(countries)))
    print('  {} country pages done'.format(len(countries)))

    # 2. Countries index
    print('\n[2/6] Countries index page...')
    html = build_countries_index()
    page('countries', html)
    total += 1
    print('  /countries/ done')

    # 3. Validator page
    print('\n[3/6] Validator page...')
    html = build_validator_page()
    page('validate', html)
    total += 1
    print('  /validate/ done')

    # 4. SEPA page
    print('\n[4/6] SEPA countries page...')
    html = build_sepa_page()
    page('sepa-countries', html)
    total += 1
    print('  /sepa-countries/ done')

    # 5. Check digit page
    print('\n[5/6] Check digit explanation page...')
    html = build_check_digit_page()
    page('iban-check-digit', html)
    total += 1
    print('  /iban-check-digit/ done')

    # 6. Sitemap + Robots
    print('\n[6/6] Sitemap and robots.txt...')
    with open(os.path.join(SRC, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(build_sitemap())
    with open(os.path.join(SRC, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write(build_robots())
    total += 2
    print('  sitemap.xml + robots.txt done')

    print('\n=== Done: {} files generated ==='.format(total))


if __name__ == '__main__':
    main()
