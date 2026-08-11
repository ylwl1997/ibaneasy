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
SRC = ROOT  # Output to project root so Cloudflare Pages serves at correct URLs
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
<script src="/js/theme.js"></script>
<link rel="stylesheet" href="/style.css">
{extra}
</head>
<body>
<div class="app-container">
<nav class="main-nav">
  <div class="nav-inner">
    <a class="nav-logo" href="/"><span class="lg-accent">IBAN</span><span class="lg-dim"> Easy</span></a>
    <div class="nav-links">
      <a href="/">Home</a>
      <a href="/what-is-iban/">What is IBAN</a>
      <a href="/countries/">Countries</a>
      <a href="/validate/">Validator</a>
      <a href="/sepa-countries/">SEPA</a>
      <a href="/iban-check-digit/">Check Digits</a>
      <a href="/swift-codes/">SWIFT Codes</a>
      <a href="/iban-calculator/">Calculator</a>
      <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle dark/light theme" title="Toggle theme">
        <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>
      </button>
    </div>
  </div>
</nav>
'''

FOOT = '''</main>
<footer class="site-footer">
  <div class="footer-inner">
    <div>
      <div class="footer-brand"><span class="fb-accent">IBAN</span><span class="fb-dim"> Easy</span></div>
      <p class="footer-note">Free online IBAN tools. All generation and validation runs client-side. No data is collected or stored. Generated IBANs are for testing only.</p>
    </div>
    <div class="footer-links">
      <a href="/">IBAN Generator</a>
      <a href="/what-is-iban/">What is an IBAN?</a>
      <a href="/countries/">All Countries</a>
      <a href="/validate/">Validator</a>
      <a href="/sepa-countries/">SEPA Countries</a>
      <a href="/iban-check-digit/">Check Digits</a>
      <a href="/swift-codes/">SWIFT/BIC Codes</a>
      <a href="/iban-calculator/">IBAN Calculator</a>
      <a href="/contact/">Contact</a>
      <a href="/privacy/">Privacy</a>
      <a href="/terms/">Terms</a>
      <a href="/sitemap/">Sitemap</a>
    </div>
  </div>
</footer>
</div><!-- /app-container -->
</body>
</html>'''

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
    parts.append('<span><span class="swatch" style="background:var(--accent-subtle);border-color:var(--accent-light)"></span> Country ({})</span>'.format(c['code']))
    parts.append('<span><span class="swatch" style="background:#2ed5731a;border-color:var(--green)"></span> Check digits</span>')
    parts.append('<span><span class="swatch" style="background:#ffc94a1a;border-color:var(--gold)"></span> Bank code ({} {})</span>'.format(c['bankLen'], 'letters' if c['bbanFormat'].startswith(str(c['bankLen'])+'!a') else 'digits'))
    if c.get('branchStart') and c.get('branchLen'):
        parts.append('<span><span class="swatch" style="background:#a855f71a;border-color:var(--purple)"></span> Branch ({} chars)</span>'.format(c['branchLen']))
    parts.append('<span><span class="swatch" style="background:var(--bg-elev-1);border-color:var(--text-muted)"></span> Account ({} chars)</span>'.format(c['accountLen']))
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

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><a href="/countries/">Countries</a><span class="crumb-sep">/</span><span class="crumb-current">{}</span></nav>\n'.format(name)
    body += '<main class="main-content prose-content">\n'
    body += '<h1>{} IBAN Format &amp; Generator</h1>\n'.format(esc(name))
    body += '<p>Complete reference for {} IBANs: format structure, bank codes, account numbers, examples, and a free generator for testing.</p>\n'.format(name)

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
    body += '<p style="font-size:0.85rem;color:var(--text-muted)">&#x26A0; These are randomly generated test IBANs — not real bank accounts. Do not use for actual transactions.</p>\n'

    # In-page mini generator
    body += '<h2>Generate {} IBANs for Testing</h2>\n'.format(name)
    body += '<p>Generate valid {} IBANs right here. All generation is client-side — no data leaves your browser.</p>\n'.format(name)
    body += '<div class="glass-panel" style="text-align:center">\n'
    body += '<div class="quantity-row" style="max-width:320px;margin:0 auto 0.85rem">\n'
    body += '<label for="mini-qty">Quantity</label>\n'
    body += '<div class="quantity-control">\n'
    body += '<input type="range" id="mini-qty" min="1" max="100" value="5">\n'
    body += '<span class="quantity-num" id="mini-qty-val">5</span>\n'
    body += '</div></div>\n'
    body += '<button class="btn btn-primary" id="mini-gen" style="margin-bottom:0.85rem">&#x21bb; Generate {} IBANs</button>\n'.format(name)
    body += '<div id="mini-results" style="text-align:left;max-height:300px;overflow-y:auto"></div>\n'
    body += '<div style="margin-top:0.75rem;display:none" id="mini-actions">\n'
    body += '<button class="btn btn-ghost btn-sm" id="mini-copy-all">&#x2398; Copy All</button>\n'
    body += '<button class="btn btn-ghost btn-sm" id="mini-csv">CSV</button>\n'
    body += '<button class="btn btn-ghost btn-sm" id="mini-json">JSON</button>\n'
    body += '<button class="btn btn-ghost btn-sm" id="mini-txt">TXT</button>\n'
    body += '</div></div>\n'

    body += '<script src="/js/iban-core.js"></script>\n'
    body += '<script>\n'
    body += '(function() {\n'
    body += '  var COUNTRY = "{}";\n'.format(code)
    body += '  var FORMAT = "{}";\n'.format(c['bbanFormat'])
    body += '  var results = [];\n'
    body += '  var qty = document.getElementById("mini-qty");\n'
    body += '  var qtyVal = document.getElementById("mini-qty-val");\n'
    body += '  qty.addEventListener("input", function() { qtyVal.textContent = qty.value; });\n'
    body += '  document.getElementById("mini-gen").addEventListener("click", function() {\n'
    body += '    var n = parseInt(qty.value, 10);\n'
    body += '    results = [];\n'
    body += '    var html = "";\n'
    body += '    for (var i = 0; i < n; i++) {\n'
    body += '      var iban = IBAN.generate(COUNTRY, FORMAT);\n'
    body += '      var fmt = IBAN.format(iban);\n'
    body += '      results.push({raw: iban, formatted: fmt});\n'
    body += '      html += "<div style=\\"font-family:var(--font-display);padding:0.35rem 0;border-bottom:1px solid #ffffff08;font-size:0.88rem\\">" + fmt + "</div>";\n'
    body += '    }\n'
    body += '    document.getElementById("mini-results").innerHTML = html;\n'
    body += '    document.getElementById("mini-actions").style.display = "";\n'
    body += '  });\n'
    body += '  function download(filename, content, mime) {\n'
    body += '    var b = new Blob([content], {type: mime + ";charset=utf-8"});\n'
    body += '    var u = URL.createObjectURL(b);\n'
    body += '    var a = document.createElement("a");\n'
    body += '    a.href = u; a.download = filename;\n'
    body += '    document.body.appendChild(a); a.click();\n'
    body += '    document.body.removeChild(a); URL.revokeObjectURL(u);\n'
    body += '  }\n'
    body += '  function copyAll() {\n'
    body += '    var t = results.map(function(r) { return r.formatted; }).join("\\n");\n'
    body += '    navigator.clipboard.writeText(t);\n'
    body += '  }\n'
    body += '  document.getElementById("mini-copy-all").addEventListener("click", copyAll);\n'
    body += '  document.getElementById("mini-csv").addEventListener("click", function() {\n'
    body += '    download("ibans.csv", "IBAN\\n" + results.map(function(r) { return r.raw; }).join("\\n"), "text/csv");\n'
    body += '  });\n'
    body += '  document.getElementById("mini-json").addEventListener("click", function() {\n'
    body += '    download("ibans.json", JSON.stringify(results.map(function(r) { return {iban: r.raw, formatted: r.formatted}; }), null, 2), "application/json");\n'
    body += '  });\n'
    body += '  document.getElementById("mini-txt").addEventListener("click", function() {\n'
    body += '    download("ibans.txt", results.map(function(r) { return r.raw; }).join("\\n"), "text/plain");\n'
    body += '  });\n'
    body += '})();\n'
    body += '</script>\n'

    body += '<h2>Frequently Asked Questions</h2>\n'
    body += '<div class="faq-list">\n'
    for q, a in country_faqs(c):
        body += '<details class="faq-item"><summary class="faq-q">{}</summary><div class="faq-a"><p>{}</p></div></details>\n'.format(q, a)
    body += '</div>\n'

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

    # BIC/SWIFT codes section for this country
    bic_file = os.path.join(ROOT, 'swift_codes.json')
    if os.path.exists(bic_file):
        with open(bic_file, 'r', encoding='utf-8') as f:
            bic_data = json.load(f)
        country_bics = [item for item in bic_data if item['country'] == code]
        if country_bics:
            body += '<h2>Major Bank BIC/SWIFT Codes in {}</h2>\n'.format(name)
            body += '<p>BIC (Bank Identifier Code) / SWIFT codes for major banks in {}. These codes are used for international wire transfers alongside the IBAN.</p>\n'.format(name)
            body += '<div class="tablewrap"><table>\n'
            body += '<thead><tr><th>BIC Code</th><th>Bank Name</th><th>City</th></tr></thead>\n<tbody>\n'
            for b in sorted(country_bics, key=lambda x: x['bankName'])[:25]:
                body += '<tr><td><code class="swift-bic-code">{}</code></td><td>{}</td><td>{}</td></tr>\n'.format(
                    esc(b['bic']), esc(b['bankName']), esc(b.get('city', '—')))
            body += '</tbody>\n</table></div>\n'
            if len(country_bics) > 25:
                body += '<p style="font-size:0.85rem;color:var(--text-muted)">Showing 25 of {} banks. <a href="/swift-codes/">Search all SWIFT/BIC codes &rarr;</a></p>\n'.format(len(country_bics))

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

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><span class="crumb-current">Countries</span></nav>\n'
    body += '<main class="main-content">\n'
    body += '<h1>All IBAN Countries</h1>\n'
    body += '<p>96 countries and territories worldwide use the IBAN system. Browse by continent or SEPA membership. Click any country for full IBAN format details, examples, and a generator.</p>\n'

    # Search
    body += '<input type="text" class="search-box" id="country-search" placeholder="Search countries..." oninput="filterCountries()" aria-label="Search countries">\n'

    # Stats
    sepa_count = sum(1 for c in countries if c['sepa'])
    body += '<p class="text-secondary" style="margin-bottom:1.5rem"><strong style="color:var(--text)">{}</strong> SEPA countries | <strong style="color:var(--text)">{}</strong> non-SEPA IBAN countries | <strong style="color:var(--text)">{}</strong> total</p>\n'.format(
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
        body += '<div class="card-grid card-grid-4">\n'
        for c in sorted(continents[cont], key=lambda x: x['name']):
            badge = ' <span class="tag tag-green">SEPA</span>' if c['sepa'] else ''
            body += '<a class="country-card" href="/countries/{}/"><div class="cc-badge">{}</div><div class="cc-name">{} {}</div><div class="cc-meta">{} chars</div></a>\n'.format(
                c['code'].lower(), c['code'], c['name'], badge, c['ibanLen'])
        body += '</div>\n'

    # Search script
    body += '''<script>
function filterCountries() {
  var q = document.getElementById('country-search').value.toLowerCase();
  var sections = document.querySelectorAll('h2');
  var grids = document.querySelectorAll('.card-grid');
  for (var i = 0; i < grids.length; i++) {
    var cards = grids[i].querySelectorAll('.country-card');
    var visible = 0;
    for (var j = 0; j < cards.length; j++) {
      var text = cards[j].textContent.toLowerCase();
      if (text.indexOf(q) !== -1) { cards[j].style.display = ''; visible++; }
      else { cards[j].style.display = 'none'; }
    }
    if (sections[i+1]) sections[i+1].style.display = visible > 0 ? '' : 'none';
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

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><span class="crumb-current">Validator</span></nav>\n'
    body += '<main class="main-content prose-content">\n'
    body += '<h1>IBAN Validator</h1>\n'
    body += '<p>Enter any IBAN to check if it\'s valid. We verify the country code, total length, character format, and MOD-97 check digits.</p>\n'

    body += '<input type="text" class="validator-input" id="iban-input" placeholder="Enter IBAN (e.g., DE89 3704 0044 0532 0130 00)" autocomplete="off" aria-label="Enter IBAN to validate">\n'
    body += '<div class="validator-result" id="result" style="display:none"></div>\n'
    body += '<div style="margin-top:1rem" id="details" style="display:none"></div>\n'

    body += '\n'

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

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><span class="crumb-current">SEPA Countries</span></nav>\n'
    body += '<main class="main-content prose-content">\n'
    body += '<h1>SEPA Countries List</h1>\n'
    body += '<p>The Single Euro Payments Area (SEPA) includes 36 countries. All SEPA transfers require an IBAN. Here is the complete list with IBAN formats.</p>\n'

    body += '\n'

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

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><span class="crumb-current">IBAN Check Digits</span></nav>\n'
    body += '<main class="main-content prose-content">\n'
    body += '<h1>How IBAN Check Digits Work</h1>\n'
    body += '<p>Every IBAN includes two check digits that catch 99.9% of typing errors. They use a mathematical formula called MOD-97, first published in ISO 7064. Here\'s how it works.</p>\n'

    body += '\n'

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


def build_contact_page():
    """Build the /contact/ page."""
    title = 'Contact IBAN Easy — Get in Touch'
    desc = 'Contact the IBAN Easy team. Questions, feedback, or suggestions about our free IBAN generator and validator tools.'

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/contact/',
        og_title=esc(title), og_desc=esc(desc),
        extra=''
    )

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><span class="crumb-current">Contact</span></nav>\n'
    body += '<main class="main-content prose-content">\n'
    body += '<h1>Contact Us</h1>\n'
    body += '<p>Have a question, suggestion, or found an issue? We\'d love to hear from you.</p>\n'

    body += '<h2>Email</h2>\n'
    body += '<p>For general inquiries, bug reports, or feature requests, email us at:</p>\n'
    body += '<p><strong>hello@ibaneasy.com</strong></p>\n'

    body += '<h2>Response Time</h2>\n'
    body += '<p>We aim to respond within 2-3 business days. For urgent issues, please include as much detail as possible in your email.</p>\n'

    body += '<h2>Before You Write</h2>\n'
    body += '<ul>\n'
    body += '<li><strong>IBAN questions?</strong> Check our <a href="/iban-check-digit/">Check Digits guide</a> or <a href="/countries/">country pages</a>.</li>\n'
    body += '<li><strong>Need test IBANs?</strong> Use our <a href="/">free generator</a> — no sign-up needed.</li>\n'
    body += '<li><strong>Privacy concerns?</strong> Read our <a href="/privacy/">Privacy Policy</a> to understand how we handle data (spoiler: we don\'t collect any).</li>\n'
    body += '</ul>\n'

    body += FOOT
    return body


def build_privacy_page():
    """Build the /privacy/ page."""
    title = 'Privacy Policy — IBAN Easy'
    desc = 'IBAN Easy privacy policy. We do not collect, store, or transmit any personal data. All IBAN generation and validation runs entirely in your browser.'

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/privacy/',
        og_title=esc(title), og_desc=esc(desc),
        extra=''
    )

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><span class="crumb-current">Privacy Policy</span></nav>\n'
    body += '<main class="main-content prose-content">\n'
    body += '<h1>Privacy Policy</h1>\n'
    body += '<p><em>Last updated: {}</em></p>\n'.format(TODAY)

    body += '<h2>1. No Data Collection</h2>\n'
    body += '<p>IBAN Easy does <strong>not</strong> collect, store, or transmit any personal data. All IBAN generation and validation is performed entirely in your browser using JavaScript. No data is ever sent to any server.</p>\n'

    body += '<h2>2. No Cookies</h2>\n'
    body += '<p>We do not use cookies for tracking or advertising. The only data stored locally is your generation history (stored in your browser\'s localStorage), which never leaves your device.</p>\n'

    body += '<h2>3. No Analytics</h2>\n'
    body += '<p>We do not use any third-party analytics services (no Google Analytics, no tracking pixels). We may review server-side request logs (anonymized) for security and performance purposes only.</p>\n'

    body += '<h2>4. Third-Party Services</h2>\n'
    body += '<p>Our site loads Google Fonts (Space Grotesk, Inter) for typography. Google may collect usage data according to their own privacy policy when these fonts are loaded. No other third-party services are used.</p>\n'

    body += '<h2>5. Security</h2>\n'
    body += '<p>Since all processing happens client-side, there is no risk of a data breach exposing your information — we simply never have it. The site is served over HTTPS via Cloudflare.</p>\n'

    body += '<h2>6. Contact</h2>\n'
    body += '<p>For any privacy-related questions, contact us at <strong>hello@ibaneasy.com</strong>.</p>\n'

    body += FOOT
    return body


def build_terms_page():
    """Build the /terms/ page."""
    title = 'Terms of Use — IBAN Easy'
    desc = 'Terms of use for IBAN Easy. Our IBAN generator and validator are free tools for testing and development. Read our terms before using the service.'

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/terms/',
        og_title=esc(title), og_desc=esc(desc),
        extra=''
    )

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><span class="crumb-current">Terms of Use</span></nav>\n'
    body += '<main class="main-content prose-content">\n'
    body += '<h1>Terms of Use</h1>\n'
    body += '<p><em>Last updated: {}</em></p>\n'.format(TODAY)

    body += '<h2>1. Acceptance of Terms</h2>\n'
    body += '<p>By using ibaneasy.com, you agree to these terms. If you do not agree, please do not use the site.</p>\n'

    body += '<h2>2. Service Description</h2>\n'
    body += '<p>IBAN Easy provides a free online IBAN generator and validator for testing and development purposes. The service is provided "as is" without any warranty.</p>\n'

    body += '<h2>3. No Financial Advice</h2>\n'
    body += '<p>This website does not provide financial advice. The IBANs generated are <strong>mathematically valid but not real bank accounts</strong>. They must not be used for actual financial transactions, payments, or any production system involving real money.</p>\n'

    body += '<h2>4. Disclaimer</h2>\n'
    body += '<p>IBAN Easy makes no guarantees about the accuracy, completeness, or suitability of the generated data. We are not responsible for any damages resulting from the use of generated IBANs. Users are responsible for verifying any IBAN data against production bank records.</p>\n'

    body += '<h2>5. Acceptable Use</h2>\n'
    body += '<p>You agree not to:</p>\n'
    body += '<ul>\n'
    body += '<li>Use generated IBANs for fraud, money laundering, or any illegal activity</li>\n'
    body += '<li>Attempt to use generated IBANs for real bank transfers</li>\n'
    body += '<li>Scrape, overload, or attempt to disrupt the service</li>\n'
    body += '</ul>\n'

    body += '<h2>6. Changes to Terms</h2>\n'
    body += '<p>We may update these terms at any time. Continued use of the site after changes constitutes acceptance of the new terms.</p>\n'

    body += '<h2>7. Contact</h2>\n'
    body += '<p>Questions about these terms? Email <strong>hello@ibaneasy.com</strong>.</p>\n'

    body += FOOT
    return body


def build_swift_page():
    """Build the /swift-codes/ search page."""
    title = 'SWIFT/BIC Code Lookup — Find Bank BIC Codes Worldwide'
    desc = 'Free SWIFT/BIC code lookup. Search by bank name, country, or BIC code. Database of major banks worldwide. All searches are client-side and private.'

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/swift-codes/',
        og_title=esc(title), og_desc=esc(desc),
        extra=''
    )

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><span class="crumb-current">SWIFT/BIC Codes</span></nav>\n'
    body += '<main class="main-content prose-content">\n'
    body += '<h1>SWIFT/BIC Code Lookup</h1>\n'
    body += '<p>Search for bank SWIFT/BIC codes worldwide. A BIC (Bank Identifier Code) identifies banks for international wire transfers. Search by bank name, country, or BIC code. All searches are private and run locally in your browser.</p>\n'

    # Search UI
    body += '<div class="swift-search-wrap">\n'
    body += '<input type="text" class="swift-search-input" id="swift-search" placeholder="Search bank name, BIC, country, or city..." oninput="SwiftSearch.filter()" aria-label="Search SWIFT/BIC codes">\n'
    body += '<select class="swift-country-filter" id="swift-country-filter" onchange="SwiftSearch.filter()" aria-label="Filter by country">\n'
    body += '<option value="">All Countries</option>\n'
    body += '</select>\n'
    body += '</div>\n'

    body += '<p class="swift-result-count" id="swift-count"></p>\n'

    body += '<div class="tablewrap">\n'
    body += '<table id="swift-table">\n'
    body += '<thead><tr><th>BIC Code</th><th>Bank Name</th><th>Country</th><th>City</th><th>Branch</th></tr></thead>\n'
    body += '<tbody id="swift-tbody"></tbody>\n'
    body += '</table>\n</div>\n'

    body += '<h2>What is a SWIFT/BIC Code?</h2>\n'
    body += '<p>A <strong>SWIFT code</strong> (also called a <strong>BIC</strong> — Bank Identifier Code) is an 8 or 11 character code that identifies a specific bank worldwide. It is used for international wire transfers and messages between financial institutions.</p>\n'
    body += '<h3>BIC Format</h3>\n'
    body += '<ul>\n'
    body += '<li><strong>Bank code</strong> (4 letters): Identifies the bank (e.g., DEUT = Deutsche Bank)</li>\n'
    body += '<li><strong>Country code</strong> (2 letters): ISO country code (e.g., DE = Germany)</li>\n'
    body += '<li><strong>Location code</strong> (2 chars): City or region (e.g., FF = Frankfurt)</li>\n'
    body += '<li><strong>Branch code</strong> (3 chars, optional): Specific branch (XXX = head office)</li>\n'
    body += '</ul>\n'

    body += '<script src="/js/swift-lookup.js"></script>\n'
    body += FOOT
    return body


def build_sitemap_html():
    """Build the /sitemap/ HTML page."""
    title = 'Sitemap — IBAN Easy'
    desc = 'Complete sitemap for ibaneasy.com. Browse all pages including country IBAN guides, tools, and informational pages.'

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/sitemap/',
        og_title=esc(title), og_desc=esc(desc),
        extra=''
    )

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><span class="crumb-current">Sitemap</span></nav>\n'
    body += '<main class="main-content prose-content">\n'
    body += '<h1>Sitemap</h1>\n'
    body += '<p>Complete directory of all pages on ibaneasy.com.</p>\n'

    body += '<h2>Tools</h2>\n'
    body += '<ul>\n'
    body += '<li><a href="/">IBAN Generator (Home)</a></li>\n'
    body += '<li><a href="/validate/">IBAN Validator</a></li>\n'
    body += '<li><a href="/swift-codes/">SWIFT/BIC Code Lookup</a></li>\n'
    body += '</ul>\n'

    body += '<h2>Guides</h2>\n'
    body += '<ul>\n'
    body += '<li><a href="/what-is-iban/">What is an IBAN? — Complete Guide</a></li>\n'
    body += '<li><a href="/iban-check-digit/">How IBAN Check Digits Work</a></li>\n'
    body += '</ul>\n'

    body += '<h2>Reference Pages</h2>\n'
    body += '<ul>\n'
    body += '<li><a href="/countries/">All IBAN Countries</a></li>\n'
    body += '<li><a href="/sepa-countries/">SEPA Countries List</a></li>\n'
    body += '</ul>\n'

    body += '<h2>Country IBAN Guides ({})</h2>\n'.format(len(countries))
    body += '<ul>\n'
    for c in sorted(countries, key=lambda x: x['name']):
        body += '<li><a href="/countries/{}/">{} IBAN ({} chars{})</a></li>\n'.format(
            c['code'].lower(), c['name'], c['ibanLen'],
            ' · SEPA' if c['sepa'] else '')
    body += '</ul>\n'

    body += '<h2>Information</h2>\n'
    body += '<ul>\n'
    body += '<li><a href="/contact/">Contact</a></li>\n'
    body += '<li><a href="/privacy/">Privacy Policy</a></li>\n'
    body += '<li><a href="/terms/">Terms of Use</a></li>\n'
    body += '</ul>\n'

    body += FOOT
    return body


def build_what_is_iban_page():
    """Build the /what-is-iban/ comprehensive guide page."""
    title = 'What is an IBAN? — Complete Guide to International Bank Account Numbers'
    desc = 'Learn what an IBAN is, how it works, its structure, and why it matters for international banking. Covers IBAN format, country codes, check digits, SEPA, and how to find your IBAN.'

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/what-is-iban/',
        og_title=esc(title), og_desc=esc(desc),
        extra=''
    )

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><span class="crumb-current">What is an IBAN?</span></nav>\n'
    body += '<main class="main-content prose-content">\n'
    body += '<h1>What is an IBAN? The Complete Guide to International Bank Account Numbers</h1>\n'
    body += '<p>An <strong>IBAN</strong> (International Bank Account Number) is a standardised system for identifying bank accounts across national borders. Developed in 1997, IBANs now span 96 countries and territories, making international money transfers safer, faster, and more reliable.</p>\n'

    body += '<p>Every IBAN contains a two-letter country code, two check digits, and a domestic bank account identifier (BBAN). Together, these elements uniquely identify a specific bank account anywhere in the world. Whether you\'re sending money to Germany, receiving payments from France, or setting up direct debits across SEPA countries, the IBAN is the universal key to cross-border banking.</p>\n'

    # Structure section
    body += '<h2>IBAN Structure: How an IBAN is Built</h2>\n'
    body += '<p>An IBAN consists of up to 34 alphanumeric characters, divided into two main parts:</p>\n'

    body += '<h3>1. Country Code (2 letters)</h3>\n'
    body += '<p>The first two characters are the ISO 3166-1 alpha-2 country code. For example:</p>\n'
    body += '<ul>\n'
    body += '<li><strong>DE</strong> — Germany</li>\n'
    body += '<li><strong>FR</strong> — France</li>\n'
    body += '<li><strong>GB</strong> — United Kingdom</li>\n'
    body += '<li><strong>ES</strong> — Spain</li>\n'
    body += '<li><strong>BR</strong> — Brazil</li>\n'
    body += '</ul>\n'

    body += '<h3>2. Check Digits (2 digits)</h3>\n'
    body += '<p>Positions 3 and 4 are the check digits, computed using the MOD-97 algorithm (ISO 7064). These two digits catch 99.94% of typing errors. <a href="/iban-check-digit/">Learn how MOD-97 works →</a></p>\n'

    body += '<h3>3. BBAN — Basic Bank Account Number (up to 30 characters)</h3>\n'
    body += '<p>The remaining characters form the BBAN, which varies by country. The BBAN typically contains:</p>\n'
    body += '<ul>\n'
    body += '<li><strong>Bank code</strong>: Identifies the financial institution (e.g., sort code in the UK, BLZ in Germany)</li>\n'
    body += '<li><strong>Branch code</strong>: Identifies a specific branch (used in some countries like France and Italy)</li>\n'
    body += '<li><strong>Account number</strong>: The individual bank account</li>\n'
    body += '</ul>\n'

    # Examples section
    body += '<h2>IBAN Examples by Country</h2>\n'
    body += '<p>Here are examples of IBANs from major countries, showing how the format varies:</p>\n'
    body += '<div class="tablewrap"><table>\n'
    body += '<thead><tr><th>Country</th><th>IBAN Length</th><th>Example</th><th>SEPA</th></tr></thead>\n<tbody>\n'
    examples = [
        ('Germany', 'DE', 22, 'DE89 3704 0044 0532 0130 00', True),
        ('France', 'FR', 27, 'FR14 2004 1010 0505 0001 3M02 606', True),
        ('United Kingdom', 'GB', 22, 'GB29 NWBK 6016 1331 9268 19', True),
        ('Spain', 'ES', 24, 'ES91 2100 0418 4502 0005 1332', True),
        ('Italy', 'IT', 27, 'IT60 X054 2811 1010 0000 0123 456', True),
        ('Netherlands', 'NL', 18, 'NL91 ABNA 0417 1643 00', True),
        ('Switzerland', 'CH', 21, 'CH93 0076 2011 6238 5295 7', True),
        ('Poland', 'PL', 28, 'PL61 1090 1014 0000 0712 1981 2874', True),
        ('Brazil', 'BR', 29, 'BR97 0036 0305 0000 1000 9795 493P 1', False),
        ('UAE', 'AE', 23, 'AE07 0331 2345 6789 0123 456', False),
    ]
    for name, code, length, example, sepa in examples:
        body += '<tr><td><a href="/countries/{}/">{}</a></td><td>{}</td><td><code>{}</code></td><td>{}</td></tr>\n'.format(
            code.lower(), name, length, example, '&#x2705;' if sepa else '&#x274C;')
    body += '</tbody>\n</table></div>\n'

    # History section
    body += '<h2>History: Why Was IBAN Created?</h2>\n'
    body += '<p>Before IBAN, international bank transfers were error-prone. Different countries used different account numbering systems, and there was no standard way to identify accounts across borders. Routing errors were common, transfers were slow, and banks charged high fees for manual processing.</p>\n'
    body += '<p>The <strong>European Committee for Banking Standards (ECBS)</strong> developed the IBAN system in 1997 to solve these problems. It was later adopted as the international standard <strong>ISO 13616</strong>. The European Union mandated IBAN usage through the <strong>Payment Services Directive (PSD)</strong>, and today all SEPA transfers require both IBAN and BIC/SWIFT codes.</p>\n'

    # Which countries
    body += '<h2>Which Countries Use IBAN?</h2>\n'
    body += '<p>As of 2026, <strong>96 countries and territories</strong> use the IBAN system. These include:</p>\n'
    body += '<ul>\n'
    body += '<li><strong>All 36 SEPA countries</strong>: Every EU/EEA member state plus Switzerland, Monaco, San Marino, Andorra, Vatican City, and UK crown dependencies</li>\n'
    body += '<li><strong>60+ non-SEPA countries</strong>: Including Brazil, Turkey, UAE, Saudi Arabia, Pakistan, Costa Rica, Dominican Republic, and many Middle Eastern and African nations</li>\n'
    body += '</ul>\n'
    body += '<p>Notable countries that <strong>do not</strong> use IBAN include the United States, Canada, Australia, China, and Japan — though they can still <em>receive</em> IBAN payments.</p>\n'
    body += '<p><a href="/countries/">Browse the complete list of IBAN countries →</a></p>\n'

    # IBAN vs SWIFT
    body += '<h2>IBAN vs SWIFT/BIC: What\'s the Difference?</h2>\n'
    body += '<p>People often confuse IBANs and SWIFT/BIC codes, but they serve different purposes:</p>\n'
    body += '<div class="tablewrap"><table>\n'
    body += '<thead><tr><th>Feature</th><th>IBAN</th><th>SWIFT/BIC</th></tr></thead>\n<tbody>\n'
    body += '<tr><td><strong>Purpose</strong></td><td>Identifies a specific bank account</td><td>Identifies a specific bank</td></tr>\n'
    body += '<tr><td><strong>Format</strong></td><td>Up to 34 alphanumeric characters</td><td>8 or 11 alphanumeric characters</td></tr>\n'
    body += '<tr><td><strong>Contains</strong></td><td>Country code + check digits + bank/account details</td><td>Bank code + country code + location + branch</td></tr>\n'
    body += '<tr><td><strong>Example</strong></td><td><code>DE89 3704 0044 0532 0130 00</code></td><td><code>DEUTDEFFXXX</code></td></tr>\n'
    body += '<tr><td><strong>When needed</strong></td><td>SEPA transfers, most international wires</td><td>International wires, interbank messages</td></tr>\n'
    body += '</tbody>\n</table></div>\n'
    body += '<p>For international transfers, you typically need <strong>both</strong> the recipient\'s IBAN and the bank\'s BIC/SWIFT code. <a href="/swift-codes/">Look up SWIFT/BIC codes →</a></p>\n'

    # How to find
    body += '<h2>How to Find Your IBAN</h2>\n'
    body += '<p>You can find your IBAN in several ways:</p>\n'
    body += '<ol>\n'
    body += '<li><strong>Bank statement</strong>: Most banks print your IBAN on every statement</li>\n'
    body += '<li><strong>Online banking</strong>: Log into your bank\'s website or app — your IBAN is usually displayed in your account details</li>\n'
    body += '<li><strong>Bank card</strong>: Some countries print the IBAN on debit/credit cards</li>\n'
    body += '<li><strong>Contact your bank</strong>: Customer service can provide your IBAN</li>\n'
    body += '<li><strong>IBAN calculator</strong>: If you know your domestic bank code and account number, you can calculate your IBAN. Try our <a href="/">IBAN generator</a></li>\n'
    body += '</ol>\n'

    # FAQ
    body += '<h2>Frequently Asked Questions</h2>\n'
    faqs = [
        ('What does IBAN stand for?',
         'IBAN stands for <strong>International Bank Account Number</strong>. It is a standardised format for identifying bank accounts internationally, defined by ISO 13616.'),
        ('Is IBAN the same as an account number?',
         'No. An IBAN <em>contains</em> your account number but adds a country code, check digits, and bank/branch identifiers. Your domestic account number is just one part of the full IBAN.'),
        ('Do I need an IBAN to receive money from abroad?',
         'If you live in an IBAN country: <strong>yes</strong>. Senders in SEPA countries and most international banks will ask for your IBAN. If you live outside IBAN countries (US, Canada, Australia, etc.), you\'ll use your domestic account number plus a SWIFT/BIC code instead.'),
        ('Are IBAN and SWIFT code the same thing?',
         'No. An IBAN identifies a <strong>specific bank account</strong>, while a SWIFT/BIC code identifies a <strong>specific bank</strong>. For international transfers, you often need both.'),
        ('Can I calculate an IBAN from an account number?',
         'Yes! If you know your country\'s IBAN format and your domestic bank/account numbers, you can compute the IBAN. The check digits are calculated using the MOD-97 algorithm. Try our <a href="/">IBAN generator</a> to see how it works.'),
        ('Why doesn\'t the United States use IBAN?',
         'The US uses a different system (ABA routing numbers + account numbers) for domestic transfers and SWIFT codes for international wires. While US banks can process incoming IBAN payments, they don\'t issue IBANs to their customers.'),
        ('How long is an IBAN number?',
         'IBAN length varies by country, from 15 characters (Norway) to 34 characters (Malta, Saint Lucia). Most European IBANs are 20-27 characters long. Each country chooses its own BBAN format within the ISO 13616 framework.'),
    ]
    body += '<div class="faq-list">\n'
    for q, a in faqs:
        body += '<details class="faq-item"><summary class="faq-q">{}</summary><div class="faq-a"><p>{}</p></div></details>\n'.format(q, a)
    body += '</div>\n'

    # Internal links
    body += '<h2>Explore IBAN Tools & Resources</h2>\n'
    body += '<div class="card-grid card-grid-2" style="margin-top:1rem">\n'
    body += '<a class="country-card" href="/"><div class="cc-badge">&#x1F4A0;</div><div class="cc-name">IBAN Generator</div><div class="cc-meta">Generate valid IBANs for any country — free, no sign-up</div></a>\n'
    body += '<a class="country-card" href="/validate/"><div class="cc-badge">&#x2714;</div><div class="cc-name">IBAN Validator</div><div class="cc-meta">Check any IBAN for correctness using MOD-97</div></a>\n'
    body += '<a class="country-card" href="/countries/"><div class="cc-badge">&#x1F30D;</div><div class="cc-name">All IBAN Countries</div><div class="cc-meta">Complete reference for 96 IBAN formats worldwide</div></a>\n'
    body += '<a class="country-card" href="/swift-codes/"><div class="cc-badge">&#x1F4E8;</div><div class="cc-name">SWIFT/BIC Lookup</div><div class="cc-meta">Find bank BIC codes for international transfers</div></a>\n'
    body += '</div>\n'

    body += FOOT
    return body


def build_iban_calculator_page():
    """Build the /iban-calculator/ interactive check digit calculator."""
    title = 'IBAN Calculator — Calculate & Validate IBAN Check Digits'
    desc = 'Free online IBAN calculator. Enter a country code and account details to compute the correct IBAN check digits using MOD-97. See step-by-step calculation. Supports all 96 IBAN countries.'

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/iban-calculator/',
        og_title=esc(title), og_desc=esc(desc),
        extra=''
    )

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><span class="crumb-current">IBAN Calculator</span></nav>\n'
    body += '<main class="main-content prose-content">\n'
    body += '<h1>IBAN Calculator — Compute Check Digits</h1>\n'
    body += '<p>Use this calculator to compute IBAN check digits from a country code and domestic account details. Enter a country, type the BBAN (domestic bank + account number), and we\'ll calculate the correct check digits using the MOD-97 algorithm.</p>\n'

    # Calculator UI
    body += '<div class="glass-panel" style="margin:1.5rem 0">\n'
    body += '<h2 style="margin-bottom:1rem">Calculate IBAN Check Digits</h2>\n'

    # Country selector
    body += '<div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-bottom:1rem">\n'
    body += '<select id="calc-country" style="flex:1;min-width:200px;font-family:var(--font);padding:0.65rem 1rem;background:var(--bg-elev-1);color:var(--text);border:1px solid var(--border);border-radius:var(--radius-sm);font-size:0.92rem;cursor:pointer">\n'
    body += '<option value="">Select a country...</option>\n'
    for c in sorted(countries, key=lambda x: x['name']):
        body += '<option value="{}">{}</option>\n'.format(c['code'], esc(c['name']))
    body += '</select>\n'
    body += '</div>\n'

    # BBAN input
    body += '<div style="margin-bottom:1rem">\n'
    body += '<label for="calc-bban" style="display:block;color:var(--text-secondary);font-size:0.82rem;margin-bottom:0.35rem">BBAN (domestic bank code + account number, without country code or check digits)</label>\n'
    body += "<input type=\"text\" id=\"calc-bban\" placeholder=\"e.g., 370400440532013000 for Germany\" style=\"width:100%;font-family:var(--font-display);padding:0.75rem 1rem;background:var(--bg-elev-1);color:var(--text);border:1px solid var(--border);border-radius:var(--radius-sm);font-size:0.95rem;outline:none\" oninput=\"calculateIban()\" onfocus=\"this.style.borderColor='var(--accent-light)'\" onblur=\"this.style.borderColor='var(--border)'\">\n"
    body += '<p style="font-size:0.78rem;color:var(--text-muted);margin-top:0.3rem" id="calc-format-hint"></p>\n'
    body += '</div>\n'

    # Calculate button
    body += '<button class="btn btn-primary" id="calc-btn" onclick="calculateIban()" style="margin-bottom:1rem">&#x2699; Calculate IBAN</button>\n'

    # Results
    body += '<div id="calc-result" style="display:none">\n'
    body += '<h3>Result</h3>\n'
    body += '<div style="font-family:var(--font-display);font-size:1.3rem;font-weight:700;padding:0.75rem 1rem;background:var(--bg-elev-1);border:1px solid var(--border-active);border-radius:var(--radius-sm);margin-bottom:0.75rem;letter-spacing:0.02em" id="calc-iban-output"></div>\n'

    body += '<h3>Step-by-Step Calculation</h3>\n'
    body += '<div style="font-size:0.88rem;line-height:1.8;color:var(--text-secondary)" id="calc-steps"></div>\n'
    body += '</div>\n'

    body += '</div>\n'  # glass-panel

    # JavaScript
    body += '<script src="/js/iban-core.js"></script>\n'
    body += '<script>\n'
    body += '(function() {\n'
    body += '  var countries = {};\n'
    body += '  var xhr = new XMLHttpRequest();\n'
    body += '  xhr.open("GET", "/iban_countries.json", true);\n'
    body += '  xhr.onload = function() {\n'
    body += '    if (xhr.status === 200) {\n'
    body += '      var data = JSON.parse(xhr.responseText);\n'
    body += '      for (var i = 0; i < data.length; i++) {\n'
    body += '        countries[data[i].code] = data[i];\n'
    body += '      }\n'
    body += '    }\n'
    body += '  };\n'
    body += '  xhr.send();\n'
    body += '\n'
    body += '  window.calculateIban = function() {\n'
    body += '    var cc = document.getElementById("calc-country").value;\n'
    body += '    var bban = document.getElementById("calc-bban").value.replace(/\\s/g, "").toUpperCase();\n'
    body += '    var resultDiv = document.getElementById("calc-result");\n'
    body += '    var output = document.getElementById("calc-iban-output");\n'
    body += '    var steps = document.getElementById("calc-steps");\n'
    body += '    var hint = document.getElementById("calc-format-hint");\n'
    body += '\n'
    body += '    if (!cc || !bban) { hint.textContent = "Please select a country and enter the BBAN."; return; }\n'
    body += '    var c = countries[cc];\n'
    body += '    if (!c) { hint.textContent = "Country not found in database."; return; }\n'
    body += '    if (bban.length !== c.bbanLen) { hint.textContent = "BBAN should be " + c.bbanLen + " characters for " + c.name + " (you entered " + bban.length + ")."; resultDiv.style.display = "none"; return; }\n'
    body += '\n'
    body += '    hint.textContent = c.name + " — " + c.bbanLen + "-character BBAN, format: " + c.bbanFormat;\n'
    body += '\n'
    body += '    // Step 1: Assemble country + "00" + BBAN\n'
    body += '    var step1 = cc + "00" + bban;\n'
    body += '    var s = [];\n'
    body += '    s.push("<strong>Step 1:</strong> Start with country code + \\"00\\" + BBAN = <code>" + step1 + "</code>");\n'
    body += '\n'
    body += '    // Step 2: Move first 4 chars to end\n'
    body += '    var step2 = step1.slice(4) + step1.slice(0, 4);\n'
    body += '    s.push("<strong>Step 2:</strong> Move first 4 characters to the end = <code>" + step2 + "</code>");\n'
    body += '\n'
    body += '    // Step 3: Convert letters to numbers\n'
    body += '    var step3 = "";\n'
    body += '    for (var i = 0; i < step2.length; i++) {\n'
    body += '      var ch = step2[i];\n'
    body += '      if (ch >= "A" && ch <= "Z") { step3 += (ch.charCodeAt(0) - 55).toString(); }\n'
    body += '      else { step3 += ch; }\n'
    body += '    }\n'
    body += '    s.push("<strong>Step 3:</strong> Convert letters to numbers (A=10, B=11, ...) = <code>" + step3.slice(0, 20) + "..." + step3.slice(-10) + "</code>");\n'
    body += '\n'
    body += '    // Step 4: MOD-97\n'
    body += '    var remainder = IBAN.mod97(step3);\n'
    body += '    s.push("<strong>Step 4:</strong> Compute MOD-97: the huge number mod 97 = <code>" + remainder + "</code>");\n'
    body += '\n'
    body += '    // Step 5: Check digits = 98 - remainder\n'
    body += '    var checkDigits = 98 - remainder;\n'
    body += '    var checkStr = ("0" + checkDigits).slice(-2);\n'
    body += '    s.push("<strong>Step 5:</strong> Check digits = 98 − " + remainder + " = <code>" + checkStr + "</code>");\n'
    body += '\n'
    body += '    // Final IBAN\n'
    body += '    var iban = cc + checkStr + bban;\n'
    body += '    var formatted = IBAN.format(iban);\n'
    body += '    output.textContent = formatted;\n'
    body += '    s.push("<br><strong style=\\"color:var(--accent-light)\\">Final IBAN:</strong> <code style=\\"font-size:1rem\\">" + formatted + "</code>");\n'
    body += '    s.push("<span style=\\"color:var(--text-muted);font-size:0.82rem\\">This IBAN passes MOD-97 validation.</span>");\n'
    body += '\n'
    body += '    steps.innerHTML = s.join("<br>");\n'
    body += '    resultDiv.style.display = "";\n'
    body += '  };\n'
    body += '\n'
    body += '  // Country change handler\n'
    body += '  document.getElementById("calc-country").addEventListener("change", function() {\n'
    body += '    var cc = this.value;\n'
    body += '    var c = countries[cc];\n'
    body += '    var hint = document.getElementById("calc-format-hint");\n'
    body += '    var ibanBban = document.getElementById("calc-bban");\n'
    body += '    if (c) {\n'
    body += '      hint.textContent = c.name + " — BBAN: " + c.bbanLen + " chars, format " + c.bbanFormat;\n'
    body += '      ibanBban.placeholder = "Enter " + c.bbanLen + "-character BBAN...";\n'
    body += '    }\n'
    body += '    calculateIban();\n'
    body += '  });\n'
    body += '})();\n'
    body += '</script>\n'

    # Educational content below calculator
    body += '<h2>How the IBAN Calculator Works</h2>\n'
    body += '<p>The calculator follows the official ISO 13616 algorithm for computing IBAN check digits:</p>\n'
    body += '<ol>\n'
    body += '<li><strong>Assemble</strong>: Take the country code + "00" (placeholder check digits) + BBAN (domestic account details)</li>\n'
    body += '<li><strong>Rearrange</strong>: Move the first 4 characters (country code + "00") to the end of the string</li>\n'
    body += '<li><strong>Convert</strong>: Replace each letter with its numeric value (A=10, B=11, ..., Z=35)</li>\n'
    body += '<li><strong>Divide</strong>: Interpret the result as a single large integer and compute remainder modulo 97</li>\n'
    body += '<li><strong>Finalise</strong>: Check digits = 98 − remainder (zero-padded to 2 digits)</li>\n'
    body += '</ol>\n'

    body += '<h2>Why Would You Need an IBAN Calculator?</h2>\n'
    body += '<ul>\n'
    body += '<li><strong>Verify your IBAN</strong>: If you know your domestic bank code and account number, use this calculator to verify your IBAN\'s check digits are correct</li>\n'
    body += '<li><strong>Understand the algorithm</strong>: See each step of the MOD-97 calculation to understand how IBAN validation works</li>\n'
    body += '<li><strong>Educational purposes</strong>: Students and developers learning about international banking can explore the IBAN structure interactively</li>\n'
    body += '<li><strong>Testing and QA</strong>: Validate that your payment system\'s IBAN generation logic produces correct check digits</li>\n'
    body += '</ul>\n'

    body += '<h2>IBAN Calculator vs IBAN Generator</h2>\n'
    body += '<p>This <strong>calculator</strong> computes check digits from your existing domestic bank details. Our <a href="/">IBAN Generator</a> creates entirely random (but mathematically valid) IBANs for testing. Use the calculator when you have real bank data and need to verify the check digits; use the generator when you need test data.</p>\n'

    # FAQ
    body += '<h2>Frequently Asked Questions</h2>\n'
    calc_faqs = [
        ('Can I calculate an IBAN from just a sort code and account number?',
         'Yes! The IBAN calculator does exactly this. Enter the country, type your domestic bank code + account number (the BBAN), and we compute the correct check digits using MOD-97.'),
        ('What if my calculated IBAN doesn\'t match the one on my bank statement?',
         'Your bank\'s IBAN is the authoritative source. If there\'s a discrepancy, double-check that you entered the correct domestic bank code and account number. Some banks use proprietary BBAN formats that differ slightly from the standard.'),
        ('Is the MOD-97 algorithm the same for all countries?',
         'Yes. All IBAN countries use the same MOD-97 check digit algorithm (ISO 7064). The only difference between countries is the BBAN format — the length and structure of the domestic bank/account details.'),
        ('Can I use this calculator for any IBAN country?',
         'Yes! The calculator supports all 96 IBAN countries. Select your country from the dropdown, enter the BBAN in the correct format, and we\'ll compute the check digits.'),
    ]
    body += '<div class="faq-list">\n'
    for q, a in calc_faqs:
        body += '<details class="faq-item"><summary class="faq-q">{}</summary><div class="faq-a"><p>{}</p></div></details>\n'.format(q, a)
    body += '</div>\n'

    # Internal links
    body += '<h2>Related Tools</h2>\n'
    body += '<div class="card-grid card-grid-2" style="margin-top:1rem">\n'
    body += '<a class="country-card" href="/"><div class="cc-badge">&#x1F4A0;</div><div class="cc-name">IBAN Generator</div><div class="cc-meta">Generate random valid IBANs for testing</div></a>\n'
    body += '<a class="country-card" href="/validate/"><div class="cc-badge">&#x2714;</div><div class="cc-name">IBAN Validator</div><div class="cc-meta">Check if any IBAN is valid using MOD-97</div></a>\n'
    body += '<a class="country-card" href="/what-is-iban/"><div class="cc-badge">&#x2753;</div><div class="cc-name">What is an IBAN?</div><div class="cc-meta">Complete guide to international bank account numbers</div></a>\n'
    body += '<a class="country-card" href="/iban-check-digit/"><div class="cc-badge">&#x1F522;</div><div class="cc-name">Check Digits Explained</div><div class="cc-meta">Deep dive into the MOD-97 algorithm</div></a>\n'
    body += '</div>\n'

    body += FOOT
    return body



def build_sitemap():
    """Generate sitemap.xml."""
    today = TODAY
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <url><loc>{}/</loc><lastmod>{}</lastmod><priority>1.0</priority></url>'.format(SITE, today),
        '  <url><loc>{}/what-is-iban/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/iban-calculator/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/countries/</loc><lastmod>{}</lastmod><priority>0.9</priority></url>'.format(SITE, today),
        '  <url><loc>{}/validate/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/sepa-countries/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/iban-check-digit/</loc><lastmod>{}</lastmod><priority>0.7</priority></url>'.format(SITE, today),
        '  <url><loc>{}/swift-codes/</loc><lastmod>{}</lastmod><priority>0.7</priority></url>'.format(SITE, today),
        '  <url><loc>{}/zh/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/contact/</loc><lastmod>{}</lastmod><priority>0.3</priority></url>'.format(SITE, today),
        '  <url><loc>{}/privacy/</loc><lastmod>{}</lastmod><priority>0.3</priority></url>'.format(SITE, today),
        '  <url><loc>{}/terms/</loc><lastmod>{}</lastmod><priority>0.3</priority></url>'.format(SITE, today),
        '  <url><loc>{}/sitemap/</loc><lastmod>{}</lastmod><priority>0.4</priority></url>'.format(SITE, today),
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


# ── Multi-Language Homepage ─────────────────────────────────────────

def build_translated_homepage(lang_code, title_zh, desc_zh):
    """Build Chinese homepage at /zh/index.html by translating the English version."""
    src_index = os.path.join(ROOT, 'index.html')
    if not os.path.exists(src_index):
        print('  WARNING: index.html not found, skipping {}'.format(lang_code))
        return None

    with open(src_index, 'r', encoding='utf-8') as f:
        html = f.read()

    can_path = '/{}/'.format(lang_code)

    # Metadata replacements
    html = html.replace('<html lang="en">', '<html lang="{}">'.format(lang_code))
    # Title
    html = html.replace(
        '<title>Free Online IBAN Generator — Generate Valid IBAN Numbers Instantly</title>',
        '<title>{}</title>'.format(title_zh)
    )
    # Meta description
    html = html.replace(
        '<meta name="description" content="Generate valid random IBAN numbers for 96+ countries. Free IBAN generator and validator — no signup, pure client-side, no data sent to any server. Supports all SEPA and international IBAN formats.">',
        '<meta name="description" content="{}">'.format(desc_zh)
    )
    # OG title
    html = html.replace(
        '<meta property="og:title" content="Free Online IBAN Generator — Generate Valid IBAN Numbers Instantly">',
        '<meta property="og:title" content="{}">'.format(title_zh)
    )
    # OG description
    html = html.replace(
        '<meta property="og:description" content="Generate valid random IBAN numbers for 96+ countries. Free, no signup, client-side only.">',
        '<meta property="og:description" content="{}">'.format(desc_zh[:160])
    )
    html = html.replace(
        '<link rel="canonical" href="https://ibaneasy.com/">',
        '<link rel="canonical" href="{}{}">'.format(SITE, can_path)
    )
    html = html.replace(
        '<meta property="og:url" content="https://ibaneasy.com/">',
        '<meta property="og:url" content="{}{}">'.format(SITE, can_path)
    )

    # Add hreflang and i18n script before </head>
    hreflang = (
        '<link rel="alternate" hreflang="en" href="{}">\n'.format(SITE + '/') +
        '<link rel="alternate" hreflang="zh" href="{}">\n'.format(SITE + '/zh/') +
        '<link rel="alternate" hreflang="x-default" href="{}">\n'.format(SITE + '/') +
        '<script src="/js/i18n.js" defer></script>'
    )
    html = html.replace('</head>', hreflang + '\n</head>')

    # Update JSON-LD
    html = html.replace(
        '"url":"https://ibaneasy.com"',
        '"url":"{}{}"'.format(SITE, can_path)
    )

    # ── Nav translations ──
    html = html.replace('>Home<', '>首页<')
    html = html.replace('>Countries<', '>国家<')
    html = html.replace('>Validator<', '>验证器<')
    html = html.replace('>SWIFT Codes<', '>SWIFT代码<')
    html = html.replace('>SEPA<', '>SEPA<')  # Keep acronym
    html = html.replace('>Check Digits<', '>校验位<')
    html = html.replace('>Calculator<', '>计算器<')

    # ── Breadcrumb ──
    html = html.replace('<span class="crumb-current">Home</span>',
                        '<span class="crumb-current">首页</span>')

    # ── Hero section ──
    html = html.replace('Free · No sign-up · 100% Client-Side',
                        '免费 · 无需注册 · 100% 客户端运行')
    html = html.replace('The <span class="text-gradient">IBAN Generator</span><br>for Every Country',
                        '<span>适用于所有国家的</span><span class="text-gradient">IBAN 生成器</span>')
    html = html.replace('Generate <strong class="text-gold">mathematically valid</strong> IBANs for 96+ countries in your browser. ISO 13616 compliant, MOD-97 verified, zero data sent to any server.',
                        '在浏览器中为 96+ 个国家生成<strong class="text-gold">数学上有效</strong>的 IBAN。符合 ISO 13616 标准，MOD-97 验证，零数据传输至任何服务器。')
    html = html.replace('>&#x21bb; Generate IBAN<', '>&#x21bb; 生成 IBAN<')
    html = html.replace('>&#x2714; Validate an IBAN<', '>&#x2714; 验证 IBAN<')
    html = html.replace('>Countries<', '>96+ 国家<', 1)  # First occurrence is nav, already replaced. This catches hero-trust.
    # Fix hero-trust labels
    html = html.replace('<span class="ht-l">+ International</span>',
                        '<span class="ht-l">+ 国际</span>')
    html = html.replace('<span class="ht-l">Server Calls</span>',
                        '<span class="ht-l">服务器调用</span>')
    html = html.replace('<span class="ht-l">Forever</span>',
                        '<span class="ht-l">永久免费</span>')

    # ── Generator dial ──
    html = html.replace('>Generate an IBAN<', '>生成 IBAN<')
    html = html.replace('placeholder="Search country..."',
                        'placeholder="搜索国家..."')
    html = html.replace('>Select a country<', '>选择国家<')
    html = html.replace('for="quantity-slider">Quantity<',
                        'for="quantity-slider">数量<')
    html = html.replace('>&#x21bb; Generate IBAN<', '>&#x21bb; 生成 IBAN<')  # Generate button (dup of hero btn)
    html = html.replace('>Length<', '>长度<')
    html = html.replace('>&#x2398; Copy<', '>&#x2398; 复制<')
    html = html.replace('>Copied!<', '>已复制！<')

    # ── Bulk results ──
    html = html.replace('>Generated IBANs<', '>生成的 IBAN<')
    html = html.replace('>&#x2398; Copy All<', '>&#x2398; 复制全部<')

    # ── History ──
    html = html.replace('>History<', '>历史记录<')
    html = html.replace('>Recent History<', '>最近历史<')
    html = html.replace('>Clear<', '>清空<')

    # ── How It Works ──
    html = html.replace('>How It Works<', '>使用方法<')
    html = html.replace('>1. Select a Country<', '>1. 选择国家<')
    html = html.replace('>Pick any country from the dropdown — all 96+ IBAN-using countries, from Germany and France to Brazil and the UAE. SEPA and international formats supported.<',
                        '>从下拉菜单选择任何使用 IBAN 的国家 — 涵盖全部 96+ 个国家，支持 SEPA 和国际格式。<')
    html = html.replace('>2. Generate an IBAN<', '>2. 生成 IBAN<')
    html = html.replace('>A <strong>mathematically valid</strong> IBAN is created using the MOD-97 check digit algorithm (ISO 13616). Every generated IBAN passes full validation.<',
                        '>使用 MOD-97 校验位算法（ISO 13616）创建<strong>数学上有效</strong>的 IBAN。每个生成的 IBAN 都通过完整验证。<')
    html = html.replace('>3. Copy &amp; Use for Testing<', '>3. 复制用于测试<')
    html = html.replace('>Use generated IBANs to test payment forms, validate software, or learn how IBAN formats work across countries. Built for developers and QA engineers.<',
                        '>使用生成的 IBAN 测试支付表单、验证软件或了解各国的 IBAN 格式。专为开发者和 QA 工程师设计。<')
    html = html.replace('>4. 100% Private &amp; Secure<', '>4. 100% 私密安全<')
    html = html.replace('>No server, no database, no analytics. Everything runs in your browser. Your data never leaves your device — inspect the source to verify.<',
                        '>无服务器、无数据库、无分析追踪。一切在您的浏览器中运行。数据永远不会离开您的设备 — 可查看源代码验证。<')

    # ── What is IBAN ──
    html = html.replace('>What is an IBAN?<', '>什么是 IBAN？<')
    html = html.replace('>IBAN stands for <strong>International Bank Account Number</strong>. It is a standardised way of identifying bank accounts across national borders, used in over 95 countries worldwide. An IBAN contains a two-letter country code, two check digits, and a Basic Bank Account Number (BBAN) that includes the domestic bank code, branch code, and account number.<',
                        '>IBAN 代表<strong>国际银行账号</strong>。它是一种跨国境识别银行账户的标准化方式，在全球 95+ 个国家使用。IBAN 包含两位字母国家代码、两位校验位，以及包含国内银行代码、分行代码和账号的基本银行账号（BBAN）。<')
    html = html.replace('>The IBAN system was developed by the European Committee for Banking Standards (ECBS) and later adopted as <strong>ISO 13616</strong>. Today, all SEPA (Single Euro Payments Area) transfers require an IBAN, making it essential for international banking in Europe and beyond.<',
                        '>IBAN 系统由欧洲银行标准委员会（ECBS）开发，后被采纳为 <strong>ISO 13616</strong> 标准。如今，所有 SEPA（单一欧元支付区）转账都需要 IBAN，使其成为欧洲及全球国际银行业务的必需品。<')

    # ── IBAN by Region ──
    html = html.replace('>IBAN by Region<', '>按地区查看 IBAN<')
    html = html.replace('>SEPA Countries<', '>SEPA 国家<')
    html = html.replace('>36 European countries — unified euro payment zone<',
                        '>36 个欧洲国家 — 统一欧元支付区<')
    html = html.replace('>Worldwide IBAN<', '>全球 IBAN<')
    html = html.replace('>60+ non-SEPA countries — Brazil, UAE, Saudi Arabia, Turkey &amp; more<',
                        '>60+ 个非 SEPA 国家 — 巴西、阿联酋、沙特阿拉伯、土耳其等<')
    html = html.replace('>International<', '>国际<')

    # ── Popular IBAN Formats ──
    html = html.replace('>Popular IBAN Formats<', '>常用 IBAN 格式<')
    html = html.replace('>Country</th><th>Length</th><th>Format Example</th><th>SEPA</th>',
                        '>国家</th><th>长度</th><th>格式示例</th><th>SEPA</th>')

    # ── FAQ ──
    html = html.replace('>Frequently Asked Questions<', '>常见问题<')
    html = html.replace('>Are these real IBANs?<', '>这些 IBAN 是真实的吗？<')
    html = html.replace('>No. The IBANs generated here are <strong>mathematically valid</strong> (they pass the MOD-97 check digit verification) but use randomly generated bank codes and account numbers. They are intended for <strong>testing purposes only</strong> — do not use them for actual bank transfers.<',
                        '>不是。这里生成的 IBAN <strong>数学上有效</strong>（通过 MOD-97 校验位验证），但使用随机生成的银行代码和账号。它们仅供<strong>测试用途</strong> — 请勿用于实际的银行转账。<')
    html = html.replace('>How does the IBAN check digit work?<', '>IBAN 校验位如何工作？<')
    html = html.replace('>IBAN uses the MOD-97 algorithm (ISO 7064). The country code letters are converted to numbers (A=10, B=11, ..., Z=35), the string is rearranged, and the result must equal 1 modulo 97. This catches 99.94% of typing errors. <a href="/iban-check-digit/">Learn more &rarr;</a><',
                        '>IBAN 使用 MOD-97 算法（ISO 7064）。将国家代码字母转换为数字（A=10，B=11，...，Z=35），重新排列字符串，结果必须等于 1 对 97 取模。这能捕捉 99.94% 的输入错误。<a href="/iban-check-digit/">了解更多 →</a><')
    html = html.replace('>Is my data safe?<', '>我的数据安全吗？<')
    html = html.replace('>Yes — 100%. All IBAN generation and validation happens in your browser using JavaScript. No data is ever sent to any server. We do not use cookies, analytics trackers, or any form of data collection. You can verify this by inspecting the source code.<',
                        '>是的 — 100%。所有 IBAN 生成和验证都在您的浏览器中使用 JavaScript 完成。没有任何数据发送到任何服务器。我们不使用 Cookie、分析追踪器或任何形式的数据收集。您可以通过查看源代码来验证。<')
    html = html.replace('>Which countries are supported?<', '>支持哪些国家？<')
    html = html.replace('>We support 96 countries and territories — covering all 36 SEPA members plus 60+ international IBAN formats. <a href="/countries/">Browse the full list &rarr;</a><',
                        '>我们支持 96 个国家和地区 — 涵盖所有 36 个 SEPA 成员国以及 60+ 个国际 IBAN 格式。<a href="/countries/">浏览完整列表 →</a><')

    # ── CTA ──
    html = html.replace('>Ready to start?<', '>准备开始？<')
    html = html.replace('>96 Countries. <span class="text-gradient">One Tool.</span><',
                        '>96 个国家。<span class="text-gradient">一个工具。</span><')
    html = html.replace('>Generate valid IBANs for any supported country, validate existing IBANs, or explore the complete IBAN format reference — all from one place, all running locally in your browser.<',
                        '>为任何支持的国家生成有效的 IBAN，验证现有 IBAN，或浏览完整的 IBAN 格式参考 — 全部在一个地方，在您的浏览器中本地运行。<')
    html = html.replace('>&#x1F30D; Browse All Countries<', '>&#x1F30D; 浏览所有国家<')
    html = html.replace('>&#x2714; Validate an IBAN<', '>&#x2714; 验证 IBAN<')  # CTA validate button
    html = html.replace('>SEPA countries<', '>SEPA 国家<')
    html = html.replace('>How check digits work<', '>校验位如何工作<')
    html = html.replace('>Germany IBAN<', '>德国 IBAN<')
    html = html.replace('>France IBAN<', '>法国 IBAN<')
    html = html.replace('>UK IBAN<', '>英国 IBAN<')
    html = html.replace('>Spain IBAN<', '>西班牙 IBAN<')

    # ── Footer ──
    html = html.replace('>Free online IBAN generator and validator. All generation runs client-side — no data is ever collected, stored, or transmitted. Generated IBANs are for testing purposes only.<',
                        '>免费的在线 IBAN 生成器和验证器。所有生成均在客户端运行 — 不会收集、存储或传输任何数据。生成的 IBAN 仅供测试使用。<')
    html = html.replace('>IBAN Generator<', '>IBAN 生成器<')
    html = html.replace('>All Countries<', '>所有国家<')
    html = html.replace('>Validator<', '>验证器<')
    html = html.replace('>SEPA Countries<', '>SEPA 国家<')
    html = html.replace('>SWIFT/BIC Codes<', '>SWIFT/BIC 代码<')
    html = html.replace('>Contact<', '>联系我们<')
    html = html.replace('>Privacy<', '>隐私政策<')
    html = html.replace('>Terms<', '>使用条款<')
    html = html.replace('>Sitemap<', '>网站地图<')

    return html


# ── Main ─────────────────────────────────────────────────────────
def main():
    print('=== ibaneasy.com static site generator ===')
    print('Countries loaded: {}'.format(len(countries)))
    print('Output directory: {}'.format(SRC))

    total = 0

    # 1. Country pages
    print('\n[1/9] Generating {} country pages...'.format(len(countries)))
    for i, c in enumerate(countries):
        html = build_country_page(c)
        page('countries/{}'.format(c['code'].lower()), html)
        total += 1
        if (i + 1) % 20 == 0:
            print('  ... {}/{}'.format(i + 1, len(countries)))
    print('  {} country pages done'.format(len(countries)))

    # 2. Countries index
    print('\n[2/9] Countries index page...')
    html = build_countries_index()
    page('countries', html)
    total += 1
    print('  /countries/ done')

    # 3. Validator page
    print('\n[3/9] Validator page...')
    html = build_validator_page()
    page('validate', html)
    total += 1
    print('  /validate/ done')

    # 4. SEPA page
    print('\n[4/9] SEPA countries page...')
    html = build_sepa_page()
    page('sepa-countries', html)
    total += 1
    print('  /sepa-countries/ done')

    # 5. Check digit page
    print('\n[5/9] Check digit explanation page...')
    html = build_check_digit_page()
    page('iban-check-digit', html)
    total += 1
    print('  /iban-check-digit/ done')

    # 5a. What-is-IBAN guide page
    print('\n[5a/9] What-is-IBAN guide page...')
    html = build_what_is_iban_page()
    page('what-is-iban', html)
    total += 1
    print('  /what-is-iban/ done')

    # 5b. IBAN Calculator page
    print('\n[5b/9] IBAN Calculator page...')
    html = build_iban_calculator_page()
    page('iban-calculator', html)
    total += 1
    print('  /iban-calculator/ done')

    # 6. SWIFT/BIC page
    print('\n[6/9] SWIFT/BIC codes page...')
    html = build_swift_page()
    page('swift-codes', html)
    total += 1
    print('  /swift-codes/ done')

    # 7. Sitemap + Robots + Legal pages
    print('\n[7/9] Sitemap, robots.txt, and legal pages...')
    with open(os.path.join(SRC, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(build_sitemap())
    with open(os.path.join(SRC, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write(build_robots())
    total += 2

    # 8. Contact, Privacy, Terms, Sitemap HTML
    print('\n[8/9] Contact, Privacy, Terms, and HTML Sitemap...')
    html = build_contact_page()
    page('contact', html)
    total += 1
    print('  /contact/ done')
    html = build_privacy_page()
    page('privacy', html)
    total += 1
    print('  /privacy/ done')
    html = build_terms_page()
    page('terms', html)
    total += 1
    print('  /terms/ done')
    html = build_sitemap_html()
    page('sitemap', html)
    total += 1
    print('  /sitemap/ done')

    # 9. Translated homepage (Chinese)
    print('\n[9/9] Chinese homepage (/zh/)...')
    zh_html = build_translated_homepage(
        'zh',
        '免费在线IBAN生成器 — 即时生成有效IBAN号码',
        '为96+个国家生成有效的随机IBAN号码。免费的IBAN生成器和验证器，无需注册，纯客户端运行，不向任何服务器发送数据。支持所有SEPA和国际IBAN格式。'
    )
    if zh_html:
        page('zh', zh_html)
        total += 1
        print('  /zh/ done')
    else:
        print('  /zh/ SKIPPED (index.html not found)')

    print('\n=== Done: {} files generated ==='.format(total))


if __name__ == '__main__':
    main()
