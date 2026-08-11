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
<link rel="alternate" hreflang="en" href="https://ibaneasy.com/">
<link rel="alternate" hreflang="de" href="https://ibaneasy.com/de/">
<link rel="alternate" hreflang="es" href="https://ibaneasy.com/es/">
<link rel="alternate" hreflang="fr" href="https://ibaneasy.com/fr/">
<link rel="alternate" hreflang="zh" href="https://ibaneasy.com/zh/">
<link rel="alternate" hreflang="x-default" href="https://ibaneasy.com/">
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
      <a href="/learn/">Learn</a>
      <div class="lang-switch">
        <button class="lang-btn" type="button" aria-expanded="false" aria-controls="lang-menu" onclick="toggleLangMenu()">
          <span id="lang-current">🌐</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
        </button>
        <div class="lang-menu" id="lang-menu">
          <a href="/" data-lang="en">🇬🇧 English</a>
          <a href="/de/" data-lang="de">🇩🇪 Deutsch</a>
          <a href="/es/" data-lang="es">🇪🇸 Español</a>
          <a href="/fr/" data-lang="fr">🇫🇷 Français</a>
          <a href="/zh/" data-lang="zh">🇨🇳 中文</a>
        </div>
      </div>
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
      <a href="/learn/">Learn</a>
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

# ── Schema Helpers ────────────────────────────────────────────────
def schema_script(data):
    """Wrap a dict/list as a JSON-LD script tag."""
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>\n'


def breadcrumb_schema(crumbs):
    """Build a BreadcrumbList schema from a list of (name, url) tuples."""
    items = []
    for i, (name, url) in enumerate(crumbs, start=1):
        item = {'@type': 'ListItem', 'position': i, 'name': name}
        if url:
            item['item'] = url
        items.append(item)
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': items,
    }


def itemlist_schema(items):
    """Build an ItemList schema from a list of (name, url) tuples."""
    return {
        '@context': 'https://schema.org',
        '@type': 'ItemList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': name, 'url': url}
            for i, (name, url) in enumerate(items, start=1)
        ],
    }

# ── Country Banking System Descriptions ───────────────────────────
# Used to add unique descriptive content to each country page
BANKING_NOTES = {
    'DE': 'Germany has one of the largest banking sectors in Europe, with over 1,600 banks including Deutsche Bank, Commerzbank, and hundreds of cooperative and savings banks (Sparkassen, Volksbanken). All German IBANs start with DE followed by 20 characters including the 8-digit BLZ (Bankleitzahl) bank code. IBAN has been mandatory for all domestic and cross-border SEPA transfers since 2014.',
    'FR': 'France has a highly developed banking system with major institutions like BNP Paribas, Societe Generale, and Credit Agricole. French IBANs are 27 characters long and include a 5-digit bank code (code banque), 5-digit branch code (code guichet), and an 11-digit account number. IBAN is required for all SEPA transfers in France.',
    'GB': 'The United Kingdom uses a 22-character IBAN that incorporates the 6-digit sort code and 8-digit account number. Major UK banks include HSBC, Barclays, Lloyds, and NatWest. Despite leaving the EU, the UK remains part of SEPA, and IBAN is required for international transfers. The Faster Payments system handles domestic transfers without IBAN.',
    'ES': 'Spain\'s banking system features major banks like Banco Santander, BBVA, and CaixaBank. Spanish IBANs are 24 characters and contain a 4-digit bank code, 4-digit branch code, 2-digit control code, and 10-digit account number. IBAN has been mandatory for all SEPA transfers in Spain since 2014.',
    'IT': 'Italy has over 400 banks, led by UniCredit, Intesa Sanpaolo, and Banco BPM. Italian IBANs are 27 characters with a 5-digit bank code (ABI), 5-digit branch code (CAB), and 12-digit account number. The CIN (Control Internal Number) check character precedes the BBAN.',
    'NL': 'The Netherlands has a modern banking system dominated by ING, Rabobank, and ABN AMRO. Dutch IBANs are 18 characters — the shortest in the EU — and use the bank\'s BIC-derived bank code. The Netherlands was an early adopter of IBAN and has fully transitioned away from the old domestic account numbering system.',
    'CH': 'Switzerland is a global banking hub with major institutions like UBS, Credit Suisse (now part of UBS), and Raiffeisen. Swiss IBANs are 21 characters with a 5-digit bank clearing number and a 12-digit account identifier. Though not an EU member, Switzerland participates in SEPA and requires IBAN for cross-border transfers.',
    'AT': 'Austria has a well-established banking system with Erste Group, Raiffeisen Bank International, and Bank Austria. Austrian IBANs are 20 characters and include a 5-digit bank code (BLZ) and an 11-digit account number. IBAN is mandatory for all SEPA transfers.',
    'BE': 'Belgium has a sophisticated banking sector with KBC, BNP Paribas Fortis, and Belfius. Belgian IBANs are 16 characters with a 3-digit bank code and a 7+2 digit account number structure. Belgium was one of the first countries to mandate IBAN for domestic transfers.',
    'PL': 'Poland has a well-regulated banking system with PKO Bank Polski, Pekao, and Santander Bank Polska. Polish IBANs are 28 characters — one of the longest in Europe — with an 8-digit bank sort code (including a 3-digit branch code) and a 16-digit account number.',
    'SE': 'Sweden has a modern banking sector with Swedbank, SEB, Nordea, and Handelsbanken. Swedish IBANs are 24 characters with a 3-digit bank code and a 17-digit account number. Sweden has largely transitioned to digital payments, with bankgiro and plusgiro systems for domestic transfers.',
    'DK': 'Denmark has a well-developed banking system with Danske Bank, Nordea, and Jyske Bank. Danish IBANs are 18 characters with a 4-digit bank code and a 10-digit account number. Denmark uses the PBS (Payment Business Services) system for domestic clearing.',
    'NO': 'Norway has a robust banking sector with DNB, Sparebanken, and Nordea. Norwegian IBANs are 15 characters — among the shortest — with a 4-digit bank code and a 6-digit account number. Norway participates in SEPA despite not being an EU member.',
    'FI': 'Finland has a highly digitised banking system with Nordea, OP Financial Group, and Danske Bank. Finnish IBANs are 18 characters with a 6-digit bank/branch code and a 7-8 digit account number. Finland was an early IBAN adopter.',
    'PT': 'Portugal has a well-structured banking system with Caixa Geral de Depósitos, Millennium BCP, and Novo Banco. Portuguese IBANs are 25 characters with a 4-digit bank code, 4-digit branch code, and 11-digit account number. IBAN is mandatory for all SEPA transfers.',
    'IE': 'Ireland has a modern banking sector with Allied Irish Banks (AIB), Bank of Ireland, and Permanent TSB. Irish IBANs are 22 characters with a 4-digit bank sort code and an 8-digit account number. Ireland uses IBAN for all SEPA transfers.',
    'BR': 'Brazil has the largest banking sector in Latin America, with Itaú Unibanco, Banco do Brasil, Bradesco, and Santander Brasil. Brazilian IBANs are 29 characters with an 8-digit bank code (ISPB), 5-digit branch code, and 10-digit account number. IBAN is used for international transfers alongside the domestic PIX instant payment system.',
    'TR': 'Turkey has a growing banking sector with Ziraat Bankası, İş Bankası, and Garanti BBVA. Turkish IBANs are 26 characters with a 5-digit bank code and a 16-digit account number. IBAN has been mandatory in Turkey since 2010.',
    'AE': 'The United Arab Emirates has a well-capitalised banking system with Emirates NBD, First Abu Dhabi Bank, and Dubai Islamic Bank. UAE IBANs are 23 characters with a 3-digit bank code and a 14-digit account number. IBAN is mandatory for all cross-border transfers.',
    'SA': 'Saudi Arabia has a strong banking sector with Saudi National Bank (SNB), Al Rajhi Bank, and Riyad Bank. Saudi IBANs are 24 characters with a 2-digit bank code and a variable-length account identifier. IBAN is mandatory for all domestic and international transfers.',
    'HU': 'Hungary has a stable banking system with OTP Bank, K&H Bank, and Erste Bank Hungary. Hungarian IBANs are 28 characters with a 3-digit bank code, 4-digit branch code, and a 16+1 digit account number. IBAN is required for SEPA transfers.',
    'CZ': 'The Czech Republic has a developed banking sector with Česká spořitelna, ČSOB, and Komerční banka. Czech IBANs are 24 characters with a 4-digit bank code and a 16-digit account number. IBAN is mandatory for SEPA transfers.',
    'RO': 'Romania has a growing banking sector with Banca Transilvania, BCR, and BRD. Romanian IBANs are 24 characters with a 4-digit bank code and a 16-digit account number. IBAN is mandatory for all SEPA transfers.',
    'GR': 'Greece has a well-established banking system with National Bank of Greece, Eurobank, Alpha Bank, and Piraeus Bank. Greek IBANs are 27 characters with a 3-digit bank code, 4-digit branch code, and a 16-digit account number.',
    'BG': 'Bulgaria has a stable banking system with UniCredit Bulbank, DSK Bank, and United Bulgarian Bank. Bulgarian IBANs are 22 characters with a 4-digit bank code (BIC-based), 4-digit branch code, and a 10-digit account number.',
    'HR': 'Croatia has a modern banking system with Zagrebačka banka, Privredna banka Zagreb, and Erste Bank Croatia. Croatian IBANs are 21 characters. Croatia adopted the euro in January 2023, making IBAN mandatory for all SEPA transfers.',
    'LU': 'Luxembourg is a major international financial centre with BGL BNP Paribas, Banque Internationale à Luxembourg, and numerous private banks. Luxembourg IBANs are 20 characters with a 3-digit bank code and a 13-digit account number.',
    'MT': 'Malta has a growing financial sector with Bank of Valletta, HSBC Malta, and APS Bank. Maltese IBANs are 31 characters with a 4-digit bank code, 5-digit branch code, and an 18-digit account number.',
    'CY': 'Cyprus has a well-developed banking system with Bank of Cyprus, Hellenic Bank, and AstroBank. Cypriot IBANs are 28 characters with a 3-digit bank code, 5-digit branch code, and a 16-digit account number.',
    'IS': 'Iceland has a small but robust banking system with Íslandsbanki, Landsbankinn, and Arion Bank. Icelandic IBANs are 26 characters with a 4-digit bank code and an 18-digit account number.',
    'LI': 'Liechtenstein has a specialised financial centre with LGT Group, VP Bank, and Liechtensteinische Landesbank. Liechtenstein IBANs are 21 characters. The country uses the Swiss franc and participates in SEPA.',
    'SG': 'Singapore is a global financial hub with DBS, OCBC, and UOB. Singapore does not officially use IBAN — international transfers use SWIFT/BIC codes with domestic account numbers.',
    'HK': 'Hong Kong is a major international financial centre with HSBC, Bank of China (Hong Kong), and Standard Chartered. Hong Kong does not use IBAN — international transfers use SWIFT/BIC codes with domestic account numbers.',
    'JP': 'Japan has a large banking system with MUFG Bank, Sumitomo Mitsui Banking Corporation, and Mizuho. Japan does not use IBAN — international transfers use SWIFT/BIC codes with domestic account numbers.',
    'AU': 'Australia has a well-regulated banking system with Commonwealth Bank, Westpac, ANZ, and NAB. Australia does not use IBAN — domestic transfers use BSB (Bank State Branch) codes, and international transfers use SWIFT/BIC codes.',
    'CA': 'Canada has a stable banking system with RBC, TD, Scotiabank, BMO, and CIBC. Canada does not use IBAN — international transfers use SWIFT/BIC codes with domestic transit and account numbers.',
    'US': 'The United States has the world\'s largest banking system with JPMorgan Chase, Bank of America, Citibank, and Wells Fargo. The US does not use IBAN — domestic transfers use ABA routing numbers, and international transfers use SWIFT/BIC codes.',
}

def _banking_overview(c):
    """Generate a banking system overview paragraph for a country page."""
    code = c['code']
    name = c['name']
    if code in BANKING_NOTES:
        return '<p>{}</p>\n'.format(BANKING_NOTES[code])
    # Generic fallback based on SEPA status and continent
    parts = []
    if c['sepa']:
        parts.append('{} is a SEPA member country.'.format(name))
        parts.append('All SEPA credit transfers and direct debits in {} require a valid IBAN.'.format(name))
    else:
        parts.append('{} uses the IBAN system for international bank transfers.'.format(name))
    parts.append('The {} IBAN is {} characters long and consists of the ISO country code "{}", two MOD-97 check digits, and a Basic Bank Account Number (BBAN) containing the domestic bank code ({} digits), account number, and any branch/routing identifiers.'.format(
        name, c['ibanLen'], code, c['bankLen']))
    return '<p>{}</p>\n'.format(' '.join(parts))

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

    extra = schema_script({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in country_faqs(c)]
    }) + schema_script(breadcrumb_schema([
        ('Home', SITE + '/'),
        ('Countries', SITE + '/countries/'),
        ('{} IBAN'.format(name), SITE + can_path),
    ]))

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

    # Banking system overview
    body += '<h2>Banking System in {}</h2>\n'.format(name)
    body += _banking_overview(c)

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

    # Related tools & resources (internal linking)
    body += '<h2>IBAN Tools &amp; Resources</h2>\n'
    body += '<div class="card-grid card-grid-2" style="margin-top:0.5rem">\n'
    body += '<a class="country-card" href="/iban-calculator/"><div class="cc-badge">&#x1F522;</div><div class="cc-name">IBAN Calculator</div><div class="cc-meta">Compute check digits for {} IBANs from domestic account details</div></a>\n'.format(name)
    body += '<a class="country-card" href="/validate/"><div class="cc-badge">&#x2714;</div><div class="cc-name">IBAN Validator</div><div class="cc-meta">Check any IBAN (including {} IBANs) with MOD-97</div></a>\n'.format(name)
    body += '<a class="country-card" href="/what-is-iban/"><div class="cc-badge">&#x2753;</div><div class="cc-name">What is an IBAN?</div><div class="cc-meta">Complete guide to IBAN structure and how it works</div></a>\n'
    body += '<a class="country-card" href="/learn/iban-vs-swift/"><div class="cc-badge">&#x1F4E8;</div><div class="cc-name">IBAN vs SWIFT</div><div class="cc-meta">When do you need an IBAN, a SWIFT code, or both?</div></a>\n'
    body += '<a class="country-card" href="/learn/how-to-get-an-iban/"><div class="cc-badge">&#x1F4CD;</div><div class="cc-name">How to Find Your IBAN</div><div class="cc-meta">5 ways to locate your {} IBAN quickly</div></a>\n'.format(name)
    body += '<a class="country-card" href="/swift-codes/"><div class="cc-badge">&#x1F4E8;</div><div class="cc-name">SWIFT/BIC Lookup</div><div class="cc-meta">Find bank BIC codes for international transfers</div></a>\n'
    body += '</div>\n'

    body += FOOT
    return body


def build_countries_index():
    """Build the /countries/ index page listing all countries."""
    title = 'All IBAN Countries — Complete List of 96 IBAN Formats Worldwide'
    desc = 'Browse all 96 countries that use IBAN. Filter by continent and SEPA membership. Each country page includes IBAN format, bank code details, examples, and a free generator.'

    extra = schema_script(itemlist_schema([
        (c['name'], SITE + '/countries/{}/'.format(c['code'].lower()))
        for c in sorted(countries, key=lambda x: x['name'])
    ])) + schema_script(breadcrumb_schema([
        ('Home', SITE + '/'),
        ('Countries', SITE + '/countries/'),
    ]))

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/countries/',
        og_title=esc(title), og_desc=esc(desc),
        extra=extra
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

    extra = schema_script({
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        'name': 'IBAN Validator',
        'url': SITE + '/validate/',
        'description': 'Free online IBAN validator — check any IBAN for correctness using MOD-97 algorithm',
        'applicationCategory': 'FinanceApplication'
    }) + schema_script(breadcrumb_schema([
        ('Home', SITE + '/'),
        ('IBAN Validator', SITE + '/validate/'),
    ]))

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

    sepa_countries = [c for c in countries if c['sepa']]
    extra = schema_script(itemlist_schema([
        (c['name'], SITE + '/countries/{}/'.format(c['code'].lower()))
        for c in sorted(sepa_countries, key=lambda x: x['name'])
    ])) + schema_script(breadcrumb_schema([
        ('Home', SITE + '/'),
        ('SEPA Countries', SITE + '/sepa-countries/'),
    ]))

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/sepa-countries/',
        og_title=esc(title), og_desc=esc(desc),
        extra=extra
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

    extra = schema_script(breadcrumb_schema([
        ('Home', SITE + '/'),
        ('IBAN Check Digits', SITE + '/iban-check-digit/'),
    ]))

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/iban-check-digit/',
        og_title=esc(title), og_desc=esc(desc),
        extra=extra
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

    extra = schema_script({
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        'name': 'SWIFT/BIC Code Lookup',
        'url': SITE + '/swift-codes/',
        'description': 'Free SWIFT/BIC code lookup for banks worldwide',
        'applicationCategory': 'FinanceApplication'
    }) + schema_script(breadcrumb_schema([
        ('Home', SITE + '/'),
        ('SWIFT/BIC Codes', SITE + '/swift-codes/'),
    ]))

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/swift-codes/',
        og_title=esc(title), og_desc=esc(desc),
        extra=extra
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
    body += '<li><a href="/learn/">Learn — IBAN Blog &amp; Guides</a></li>\n'
    for art in BLOG_ARTICLES:
        body += '<li><a href="/learn/{}/">{}</a></li>\n'.format(art['slug'], esc(art['title']))
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


# ── Blog / Learn Section ──────────────────────────────────────────
# Each article: slug, title, desc, date, reading time, keyword, body builder
BLOG_ARTICLES = [
    {
        'slug': 'iban-vs-swift',
        'title': 'IBAN vs SWIFT: What\'s the Difference and When Do You Need Each?',
        'desc': 'IBAN identifies your bank account, SWIFT identifies your bank. Learn the key differences, when you need each, and why international transfers usually require both.',
        'date': '2026-07-28',
        'read': '7 min read',
        'sections': [
            ('IBAN vs SWIFT at a Glance',
             'IBAN and SWIFT codes are often confused because both are used for international banking. The simple distinction: an <strong>IBAN</strong> (International Bank Account Number) identifies a <strong>specific bank account</strong>, while a <strong>SWIFT/BIC code</strong> identifies a <strong>specific bank</strong>.'),
            ('Quick Comparison',
             'Here is the essential comparison in one table:',
             [
                 ('Feature', 'IBAN', 'SWIFT/BIC'),
                 ('What it identifies', 'A bank account', 'A bank'),
                 ('Length', 'Up to 34 characters', '8 or 11 characters'),
                 ('Format', 'Country code + check digits + account details', 'Bank code + country + location + branch'),
                 ('Example', '<code>DE89 3704 0044 0532 0130 00</code>', '<code>DEUTDEFFXXX</code>'),
                 ('Where used', 'Europe, Middle East, parts of Africa & South America', 'Worldwide'),
                 ('Regulated by', 'ISO 13616', 'ISO 9362'),
             ]),
            ('What is an IBAN?',
             'An IBAN is a standardised international bank account number used in over 96 countries. It contains a two-letter country code, two MOD-97 check digits, and a Basic Bank Account Number (BBAN) holding your domestic bank code and account number. The IBAN was designed so that a single account number works across borders — the check digits catch 99.94% of typing errors. <a href="/what-is-iban/">Read the full guide to IBAN →</a>'),
            ('What is a SWIFT Code?',
             'A SWIFT code (technically called a BIC — Bank Identifier Code) is an 8 or 11 character code that identifies a bank, not an account. Every bank has at least one SWIFT code; larger banks have many (one per branch). When you wire money internationally, the SWIFT code tells the network which bank should receive it. <a href="/swift-codes/">Search SWIFT/BIC codes →</a>'),
            ('When Do You Need Each?',
             'For most international transfers you need <strong>both</strong>:',
             [
                 ('SEPA transfers', 'IBAN only', 'BIC usually not required'),
                 ('EU/EEA international wire', 'IBAN required', 'BIC required'),
                 ('Non-EU wire (e.g., US, Asia)', 'IBAN optional / domestic account', 'BIC required'),
                 ('Domestic transfer', 'No IBAN needed', 'No BIC needed'),
             ]),
            ('Which Countries Use IBAN?',
             'IBAN is mandatory throughout the European Union and EEA, and is widely used in Switzerland, the Middle East, and parts of Africa and South America. The United States, Canada, Australia, China, and Japan do <strong>not</strong> use IBAN — they rely on domestic routing numbers plus SWIFT codes for international transfers. <a href="/countries/">See the full list of 96 IBAN countries →</a>'),
            ('Common Mistakes to Avoid',
             'Three frequent mistakes cause failed or delayed transfers:',
             [
                 ('Using an old account number', 'Always use the full IBAN, not just your domestic account number, when sending to an IBAN country.'),
                 ('Mixing up IBAN and BIC', 'For non-SEPA transfers you almost always need both. Ask the recipient for their bank\'s BIC if unsure.'),
                 ('Typos in the check digits', 'The check digits are your protection — the bank will reject the transfer if they don\'t match, so double-check before sending.'),
             ]),
        ],
    },
    {
        'slug': 'iban-check-digit-explained',
        'title': 'IBAN Check Digits Explained: How MOD-97 Catches Errors',
        'desc': 'The two check digits in every IBAN are not random. Learn how the MOD-97 algorithm works step by step, why it catches 99.94% of errors, and how to verify an IBAN yourself.',
        'date': '2026-07-20',
        'read': '8 min read',
        'sections': [
            ('Why IBAN Has Check Digits',
             'Every IBAN contains exactly two check digits, located right after the country code (positions 3 and 4). Their job is to verify that the rest of the IBAN was entered correctly. If you make a typo when typing an IBAN, the check digits will not match, and the bank will reject the transfer — protecting you from sending money to the wrong account.'),
            ('The MOD-97 Algorithm',
             'The check digits are calculated using the <strong>MOD-97 algorithm</strong>, defined by ISO 7064. Here is the step-by-step process:',
             [
                 ('Step 1', 'Move the first four characters (country code + check digits) to the end of the IBAN.'),
                 ('Step 2', 'Convert every letter to a number: A=10, B=11, C=12, ..., Z=35.'),
                 ('Step 3', 'The result is a long number. Divide it by 97 and check the remainder.'),
                 ('Step 4', 'The remainder must be exactly <strong>1</strong>. If it is anything else, the IBAN is invalid.'),
             ]),
            ('Worked Example: Germany',
             'Let\'s verify <code>DE89 3704 0044 0532 0130 00</code> (the classic German example IBAN). First strip spaces, then move the country code and check digits to the end: <code>370400440532013000</code> + <code>DE89</code> → <code>370400440532013000DE89</code>. Convert letters: D=13, E=14, so <code>370400440532013000131489</code>. Now compute this number modulo 97. The result is 1 — the IBAN is valid.'),
            ('Why 97 and 99.94%?',
             'The number 97 is prime, which makes the algorithm extremely effective at catching errors. A single changed digit, two swapped digits, or a missing digit will almost always change the remainder. The ISO 7064 standard reports that MOD-97 detects about <strong>99.94% of all errors</strong> — far better than any simple checksum.'),
            ('Try It Yourself',
             'You can verify any IBAN instantly with our free tools:',
             [
                 ('IBAN Validator', '/validate/', 'Check any IBAN against the MOD-97 algorithm'),
                 ('IBAN Calculator', '/iban-calculator/', 'Compute the correct check digits from domestic account details'),
                 ('Check Digit Generator', '/', 'Generate random valid IBANs for testing'),
             ]),
        ],
    },
    {
        'slug': 'what-is-bban',
        'title': 'What is a BBAN? Understanding the Core of Your IBAN',
        'desc': 'The Basic Bank Account Number (BBAN) is the domestic part of an IBAN. Learn how BBANs differ by country, what bank codes they contain, and how they map to IBAN.',
        'date': '2026-07-12',
        'read': '6 min read',
        'sections': [
            ('BBAN Definition',
             'A <strong>BBAN</strong> (Basic Bank Account Number) is the country-specific part of an IBAN. It identifies your bank and account number using the domestic numbering system of your country. The BBAN is always embedded inside the IBAN, after the country code and check digits.'),
            ('How a BBAN Fits Inside an IBAN',
             'An IBAN has three parts:',
             [
                 ('Country code', '2 letters (e.g., DE for Germany)', 'Identifies the country'),
                 ('Check digits', '2 digits (e.g., 89)', 'Validates the whole IBAN'),
                 ('BBAN', 'Variable length, up to 30 chars', 'Your domestic bank + account details'),
             ]),
            ('BBAN Structure Varies by Country',
             'Each country defines its own BBAN format. Here are examples from major countries:',
             [
                 ('Germany', '22 chars total', '8-digit BLZ bank code + 10-digit account number'),
                 ('United Kingdom', '22 chars total', '6-digit sort code + 8-digit account number'),
                 ('France', '27 chars total', '5-digit bank code + 5-digit branch + 11-digit account'),
                 ('Spain', '24 chars total', '4-digit bank + 4-digit branch + 2-digit control + 10-digit account'),
                 ('Brazil', '29 chars total', '8-digit ISPB bank code + branch + account'),
             ]),
            ('Why the BBAN Matters',
             'The BBAN is what banks use to route domestic payments. When you transfer within your own country, the bank reads the BBAN. When you transfer internationally, the IBAN is used. Understanding your BBAN helps you know <em>which</em> parts of your account number matter for different types of payments.'),
            ('Find Your BBAN',
             'Your BBAN is simply your IBAN with the country code and check digits removed. For example, if your IBAN is <code>GB29 NWBK 6016 1331 9268 19</code>, your BBAN is <code>NWBK 6016 1331 9268 19</code>.'),
        ],
    },
    {
        'slug': 'sepa-vs-swift',
        'title': 'SEPA vs SWIFT Transfers: Costs, Speed, and When to Use Each',
        'desc': 'SEPA transfers are fast and cheap within Europe, while SWIFT handles global payments. Compare costs, speed, limits, and requirements to choose the right one.',
        'date': '2026-07-05',
        'read': '7 min read',
        'sections': [
            ('SEPA vs SWIFT: The Big Picture',
             'If you are sending money within Europe, you\'ll likely use <strong>SEPA</strong>. If you are sending money anywhere else in the world, you\'ll use the <strong>SWIFT</strong> network. They solve the same problem — moving money between banks — but they operate very differently.'),
            ('What is SEPA?',
             'The Single Euro Payments Area (SEPA) unifies payments across 36 European countries. All SEPA transfers are treated as domestic: they move in euro, usually within one business day, and (for consumers) at domestic rates. SEPA covers credit transfers, direct debits, and card payments. <a href="/sepa-countries/">See all SEPA countries →</a>'),
            ('What is SWIFT?',
             'SWIFT is a global messaging network connecting over 11,000 banks in more than 200 countries. It doesn\'t move money itself — it sends secure payment instructions between banks. SWIFT is how most international wires work, from Europe to the US, Asia, Africa, and beyond.'),
            ('Cost Comparison',
             'The cost difference is significant:',
             [
                 ('SEPA credit transfer', 'Usually free or a few euros', '1 business day', 'Euro only'),
                 ('SEPA instant (SCT Inst)', 'Similar to domestic', '10 seconds', 'Euro only'),
                 ('SWIFT international wire', '€10–€40 + FX spread', '1–4 business days', 'Any currency'),
                 ('SWIFT with intermediary banks', 'Additional fees deducted', 'Longer', 'Any currency'),
             ]),
            ('When to Use Each',
             'Use SEPA when both sender and recipient are in SEPA countries and the transfer is in euro. Use SWIFT when: the recipient is outside SEPA, the currency is not euro, or the amount is large enough that you need a reliable international route. For the US, Canada, Asia, or Africa, SWIFT is the standard choice.'),
            ('Both Require IBAN (Sometimes)',
             'SEPA transfers <strong>require an IBAN</strong> for both sender and recipient. SWIFT transfers typically require the recipient\'s IBAN (if their country uses it) plus the bank\'s BIC/SWIFT code. Check which one your recipient needs before you initiate a transfer.'),
            ('Which Is Right for You?',
             'Rule of thumb: within SEPA, use SEPA — it\'s cheaper and faster. Outside SEPA, use SWIFT and expect higher fees and longer processing. Always confirm the recipient\'s IBAN and BIC in advance to avoid rejected or delayed transfers.'),
        ],
    },
    {
        'slug': 'how-to-get-an-iban',
        'title': 'How to Get an IBAN: 5 Ways to Find Your International Bank Account Number',
        'desc': 'Need your IBAN for an international transfer? Learn the 5 fastest ways to find it — bank statements, online banking, calculators, and more.',
        'date': '2026-06-28',
        'read': '5 min read',
        'sections': [
            ('Everyone Needs an IBAN Eventually',
             'Whether you\'re receiving salary from abroad, sending money to family, or getting paid by a client, you\'ll eventually be asked for your IBAN. Here are the five fastest ways to find it.'),
            ('Method 1: Check Your Bank Statement',
             'The easiest way. Most banks print your IBAN on every account statement, both paper and digital. Look near the top or in the account details section — it will be clearly labelled "IBAN".'),
            ('Method 2: Log Into Online Banking',
             'Your bank\'s website or mobile app almost always shows your IBAN in account details. For most banks: log in → select the account → look for "Account details" or "IBAN". Some apps even let you copy it with one tap.'),
            ('Method 3: Use an IBAN Calculator',
             'If you know your country, bank code, and account number, you can <strong>calculate</strong> your IBAN in seconds. Our free <a href="/iban-calculator/">IBAN calculator</a> computes the correct check digits for any country. This is especially useful if you\'ve changed banks and don\'t have your new IBAN handy.'),
            ('Method 4: Check Your Bank Card',
             'In some countries (notably Germany, Austria, and Switzerland), the IBAN is printed directly on debit cards. Check the front or back of your card before calling your bank.'),
            ('Method 5: Contact Your Bank',
             'Customer service can provide your IBAN instantly. When you call, have your account number ready. In most countries, you can also request an IBAN confirmation letter — some banks charge a small fee for this.'),
            ('Which Method Is Fastest?',
             'Online banking is usually fastest (30 seconds). Bank statements are second. IBAN calculators are useful when you need it immediately and know your account details. If you\'re unsure your IBAN is correct, use our free <a href="/validate/">IBAN validator</a> to check it before sending.'),
        ],
    },
]


def build_learn_index():
    """Build the /learn/ blog index page."""
    title = 'Learn About IBAN — Guides, Tips & Resources'
    desc = 'Learn everything about IBAN: what it is, how check digits work, the difference between IBAN and SWIFT, SEPA vs SWIFT transfers, and how to find your IBAN.'

    extra = schema_script(itemlist_schema([
        (art['title'], SITE + '/learn/{}/'.format(art['slug']))
        for art in BLOG_ARTICLES
    ])) + schema_script(breadcrumb_schema([
        ('Home', SITE + '/'),
        ('Learn', SITE + '/learn/'),
    ]))

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/learn/',
        og_title=esc(title), og_desc=esc(desc),
        extra=extra
    )

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><span class="crumb-current">Learn</span></nav>\n'
    body += '<main class="main-content prose-content">\n'
    body += '<h1>Learn About IBAN</h1>\n'
    body += '<p>Practical guides to international bank account numbers — from the basics to advanced topics. Written to be clear, accurate, and useful for real-world transfers.</p>\n'

    for art in BLOG_ARTICLES:
        body += '<article class="blog-card">\n'
        body += '<p class="blog-meta">{date} · {read}</p>\n'.format(date=art['date'], read=art['read'])
        body += '<h2><a href="/learn/{}/">{}</a></h2>\n'.format(art['slug'], esc(art['title']))
        body += '<p>{}</p>\n'.format(esc(art['desc']))
        body += '<p><a class="btn btn-ghost btn-sm" href="/learn/{}/">Read article &rarr;</a></p>\n'.format(art['slug'])
        body += '</article>\n'

    # Tools section
    body += '<h2>IBAN Tools</h2>\n'
    body += '<div class="card-grid card-grid-2" style="margin-top:1rem">\n'
    body += '<a class="country-card" href="/"><div class="cc-badge">&#x1F4A0;</div><div class="cc-name">IBAN Generator</div><div class="cc-meta">Generate valid test IBANs for any country</div></a>\n'
    body += '<a class="country-card" href="/iban-calculator/"><div class="cc-badge">&#x1F522;</div><div class="cc-name">IBAN Calculator</div><div class="cc-meta">Compute check digits from domestic account details</div></a>\n'
    body += '<a class="country-card" href="/validate/"><div class="cc-badge">&#x2714;</div><div class="cc-name">IBAN Validator</div><div class="cc-meta">Verify any IBAN with MOD-97</div></a>\n'
    body += '<a class="country-card" href="/swift-codes/"><div class="cc-badge">&#x1F4E8;</div><div class="cc-name">SWIFT/BIC Lookup</div><div class="cc-meta">Find bank codes for international transfers</div></a>\n'
    body += '</div>\n'

    body += FOOT
    return body


def build_article_page(art):
    """Build a single blog article page."""
    slug = art['slug']
    title = art['title']
    desc = art['desc']
    can_path = '/learn/{}/'.format(slug)

    extra = schema_script({
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': title,
        'description': desc,
        'datePublished': art['date'],
        'author': {'@type': 'Organization', 'name': 'IBAN Easy'},
        'publisher': {'@type': 'Organization', 'name': 'IBAN Easy', 'url': SITE},
        'mainEntityOfPage': SITE + can_path,
    }) + schema_script(breadcrumb_schema([
        ('Home', SITE + '/'),
        ('Learn', SITE + '/learn/'),
        (art['title'], SITE + can_path),
    ]))

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + can_path,
        og_title=esc(title), og_desc=esc(desc),
        extra=extra
    )

    body += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="crumb-sep">/</span><a href="/learn/">Learn</a><span class="crumb-sep">/</span><span class="crumb-current">{}</span></nav>\n'.format(esc(title))
    body += '<main class="main-content prose-content">\n'
    body += '<p class="blog-meta">{date} · {read}</p>\n'.format(date=art['date'], read=art['read'])
    body += '<h1>{}</h1>\n'.format(esc(title))

    for section in art['sections']:
        heading = section[0]
        body += '<h2>{}</h2>\n'.format(esc(heading))
        if len(section) == 2:
            # Paragraph only
            body += '<p>{}</p>\n'.format(section[1])
        elif len(section) == 3:
            content = section[1]
            rows = section[2]
            # Detect table vs list: first row is a header row
            if isinstance(rows[0], (list, tuple)):
                body += '<p>{}</p>\n'.format(content)
                body += '<div class="tablewrap"><table>\n<thead><tr>'
                for h in rows[0]:
                    body += '<th>{}</th>'.format(esc(str(h)))
                body += '</tr></thead>\n<tbody>\n'
                for row in rows[1:]:
                    body += '<tr>'
                    for cell in row:
                        body += '<td>{}</td>'.format(cell)
                    body += '</tr>\n'
                body += '</tbody>\n</table></div>\n'
            else:
                # List of (title, text) or (title, url, text) tuples → description list
                body += '<p>{}</p>\n'.format(content)
                body += '<ul>\n'
                for row in rows:
                    if len(row) == 3:
                        name, url, text = row
                        body += '<li><strong><a href="{}">{}</a></strong> — {}</li>\n'.format(url, esc(name), text)
                    else:
                        name, text = row
                        body += '<li><strong>{}</strong> — {}</li>\n'.format(esc(name), text)
                body += '</ul>\n'

    # Article footer with related links
    body += '<hr style="margin:2rem 0;border-color:var(--border)">\n'
    body += '<h2>Related Resources</h2>\n'
    body += '<div class="card-grid card-grid-2">\n'
    body += '<a class="country-card" href="/"><div class="cc-badge">&#x1F4A0;</div><div class="cc-name">IBAN Generator</div><div class="cc-meta">Generate valid test IBANs for 96+ countries</div></a>\n'
    body += '<a class="country-card" href="/learn/"><div class="cc-badge">&#x1F4D6;</div><div class="cc-name">More IBAN Guides</div><div class="cc-meta">Browse all articles in the Learn section</div></a>\n'
    body += '</div>\n'

    body += FOOT
    return body


def build_what_is_iban_page():
    """Build the /what-is-iban/ comprehensive guide page."""
    title = 'What is an IBAN? — Complete Guide to International Bank Account Numbers'
    desc = 'Learn what an IBAN is, how it works, its structure, and why it matters for international banking. Covers IBAN format, country codes, check digits, SEPA, and how to find your IBAN.'

    extra = schema_script({
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': 'What is an IBAN? The Complete Guide to International Bank Account Numbers',
        'description': desc,
        'datePublished': '2026-07-01',
        'author': {'@type': 'Organization', 'name': 'IBAN Easy'},
        'publisher': {'@type': 'Organization', 'name': 'IBAN Easy', 'url': SITE},
        'mainEntityOfPage': SITE + '/what-is-iban/',
    }) + schema_script(breadcrumb_schema([
        ('Home', SITE + '/'),
        ('What is an IBAN?', SITE + '/what-is-iban/'),
    ]))

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/what-is-iban/',
        og_title=esc(title), og_desc=esc(desc),
        extra=extra
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
    body += '<a class="country-card" href="/iban-calculator/"><div class="cc-badge">&#x1F522;</div><div class="cc-name">IBAN Calculator</div><div class="cc-meta">Compute IBAN check digits from domestic account details</div></a>\n'
    body += '<a class="country-card" href="/countries/"><div class="cc-badge">&#x1F30D;</div><div class="cc-name">All IBAN Countries</div><div class="cc-meta">Complete reference for 96 IBAN formats worldwide</div></a>\n'
    body += '<a class="country-card" href="/swift-codes/"><div class="cc-badge">&#x1F4E8;</div><div class="cc-name">SWIFT/BIC Lookup</div><div class="cc-meta">Find bank BIC codes for international transfers</div></a>\n'
    body += '<a class="country-card" href="/learn/"><div class="cc-badge">&#x1F4D6;</div><div class="cc-name">IBAN Guides &amp; Tips</div><div class="cc-meta">Practical articles on IBAN, SEPA, and SWIFT</div></a>\n'
    body += '</div>\n'

    body += '<h2>Related Articles</h2>\n'
    body += '<div class="card-grid card-grid-2" style="margin-top:1rem">\n'
    body += '<a class="country-card" href="/learn/iban-vs-swift/"><div class="cc-badge">&#x1F4E8;</div><div class="cc-name">IBAN vs SWIFT</div><div class="cc-meta">The key differences and when you need each</div></a>\n'
    body += '<a class="country-card" href="/learn/iban-check-digit-explained/"><div class="cc-badge">&#x1F522;</div><div class="cc-name">MOD-97 Explained</div><div class="cc-meta">How IBAN check digits catch 99.94% of errors</div></a>\n'
    body += '<a class="country-card" href="/learn/sepa-vs-swift/"><div class="cc-badge">&#x1F30D;</div><div class="cc-name">SEPA vs SWIFT</div><div class="cc-meta">Costs, speed, and when to use each</div></a>\n'
    body += '<a class="country-card" href="/learn/what-is-bban/"><div class="cc-badge">&#x1F4CB;</div><div class="cc-name">What is a BBAN?</div><div class="cc-meta">Understanding the domestic part of your IBAN</div></a>\n'
    body += '</div>\n'

    body += FOOT
    return body


def build_iban_calculator_page():
    """Build the /iban-calculator/ interactive check digit calculator."""
    title = 'IBAN Calculator — Calculate & Validate IBAN Check Digits'
    desc = 'Free online IBAN calculator. Enter a country code and account details to compute the correct IBAN check digits using MOD-97. See step-by-step calculation. Supports all 96 IBAN countries.'

    extra = schema_script({
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        'name': 'IBAN Calculator',
        'url': SITE + '/iban-calculator/',
        'description': 'Free online IBAN calculator — compute check digits using MOD-97',
        'applicationCategory': 'FinanceApplication'
    }) + schema_script(breadcrumb_schema([
        ('Home', SITE + '/'),
        ('IBAN Calculator', SITE + '/iban-calculator/'),
    ]))

    body = HEAD.format(
        title=esc(title), desc=esc(desc),
        canon=SITE + '/iban-calculator/',
        og_title=esc(title), og_desc=esc(desc),
        extra=extra
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
        '  <url><loc>{}/learn/</loc><lastmod>{}</lastmod><priority>0.7</priority></url>'.format(SITE, today),
        '  <url><loc>{}/countries/</loc><lastmod>{}</lastmod><priority>0.9</priority></url>'.format(SITE, today),
        '  <url><loc>{}/validate/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/sepa-countries/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/iban-check-digit/</loc><lastmod>{}</lastmod><priority>0.7</priority></url>'.format(SITE, today),
        '  <url><loc>{}/swift-codes/</loc><lastmod>{}</lastmod><priority>0.7</priority></url>'.format(SITE, today),
        '  <url><loc>{}/zh/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/de/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/es/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/fr/</loc><lastmod>{}</lastmod><priority>0.8</priority></url>'.format(SITE, today),
        '  <url><loc>{}/contact/</loc><lastmod>{}</lastmod><priority>0.3</priority></url>'.format(SITE, today),
        '  <url><loc>{}/privacy/</loc><lastmod>{}</lastmod><priority>0.3</priority></url>'.format(SITE, today),
        '  <url><loc>{}/terms/</loc><lastmod>{}</lastmod><priority>0.3</priority></url>'.format(SITE, today),
        '  <url><loc>{}/sitemap/</loc><lastmod>{}</lastmod><priority>0.4</priority></url>'.format(SITE, today),
    ]
    for c in sorted(countries, key=lambda x: x['name']):
        p = 0.7 if c['sepa'] else 0.5
        lines.append('  <url><loc>{}/countries/{}/</loc><lastmod>{}</lastmod><priority>{}</priority></url>'.format(
            SITE, c['code'].lower(), today, p))
    for art in BLOG_ARTICLES:
        lines.append('  <url><loc>{}/learn/{}/</loc><lastmod>{}</lastmod><priority>0.6</priority></url>'.format(
            SITE, art['slug'], today))
    lines.append('</urlset>')
    return '\n'.join(lines)


def build_robots():
    """Generate robots.txt."""
    return 'User-agent: *\nAllow: /\n\nSitemap: {}/sitemap.xml\n'.format(SITE)


# ── Multi-Language Homepage ─────────────────────────────────────────
# Per-language translations for the homepage (string replacements applied to index.html)
LANG_CONFIG = {
    'zh': {
        'lang_name': '简体中文',
        'title': '免费在线IBAN生成器 — 即时生成有效IBAN号码',
        'desc': '为96+个国家生成有效的随机IBAN号码。免费的IBAN生成器和验证器，无需注册，纯客户端运行，不向任何服务器发送数据。支持所有SEPA和国际IBAN格式。',
        'nav': [
            ('>Home<', '>首页<'),
            ('>What is IBAN<', '>IBAN是什么<'),
            ('>Countries<', '>国家<'),
            ('>Validator<', '>验证器<'),
            ('>SEPA<', '>SEPA<'),
            ('>Check Digits<', '>校验位<'),
            ('>SWIFT Codes<', '>SWIFT代码<'),
            ('>Calculator<', '>计算器<'),
            ('>Learn<', '>学习<'),
        ],
        'crumb_home': ('<span class="crumb-current">Home</span>', '<span class="crumb-current">首页</span>'),
        'hero': [
            ('Free · No sign-up · 100% Client-Side', '免费 · 无需注册 · 100% 客户端运行'),
            ('The <span class="text-gradient">IBAN Generator</span><br>for Every Country',
             '<span>适用于所有国家的</span><span class="text-gradient">IBAN 生成器</span>'),
            ('Generate <strong class="text-gold">mathematically valid</strong> IBANs for 96+ countries in your browser. ISO 13616 compliant, MOD-97 verified, zero data sent to any server.',
             '在浏览器中为 96+ 个国家生成<strong class="text-gold">数学上有效</strong>的 IBAN。符合 ISO 13616 标准，MOD-97 验证，零数据传输至任何服务器。'),
            ('>&#x21bb; Generate IBAN<', '>&#x21bb; 生成 IBAN<'),
            ('>&#x2714; Validate an IBAN<', '>&#x2714; 验证 IBAN<'),
            ('<span class="ht-l">+ International</span>', '<span class="ht-l">+ 国际</span>'),
            ('<span class="ht-l">Server Calls</span>', '<span class="ht-l">服务器调用</span>'),
            ('<span class="ht-l">Forever</span>', '<span class="ht-l">永久免费</span>'),
        ],
        'dial': [
            ('>Generate an IBAN<', '>生成 IBAN<'),
            ('placeholder="Search country..."', 'placeholder="搜索国家..."'),
            ('>Select a country<', '>选择国家<'),
            ('for="quantity-slider">Quantity<', 'for="quantity-slider">数量<'),
            ('>Length<', '>长度<'),
            ('>&#x2398; Copy<', '>&#x2398; 复制<'),
            ('>Copied!<', '>已复制！<'),
        ],
        'bulk': [
            ('>Generated IBANs<', '>生成的 IBAN<'),
            ('>&#x2398; Copy All<', '>&#x2398; 复制全部<'),
        ],
        'history': [
            ('>History<', '>历史记录<'),
            ('>Recent History<', '>最近历史<'),
            ('>Clear<', '>清空<'),
        ],
        'how': [
            ('>How It Works<', '>使用方法<'),
            ('>1. Select a Country<', '>1. 选择国家<'),
            ('>Pick any country from the dropdown — all 96+ IBAN-using countries, from Germany and France to Brazil and the UAE. SEPA and international formats supported.<',
             '>从下拉菜单选择任何使用 IBAN 的国家 — 涵盖全部 96+ 个国家，支持 SEPA 和国际格式。<'),
            ('>2. Generate an IBAN<', '>2. 生成 IBAN<'),
            ('>A <strong>mathematically valid</strong> IBAN is created using the MOD-97 check digit algorithm (ISO 13616). Every generated IBAN passes full validation.<',
             '>使用 MOD-97 校验位算法（ISO 13616）创建<strong>数学上有效</strong>的 IBAN。每个生成的 IBAN 都通过完整验证。<'),
            ('>3. Copy &amp; Use for Testing<', '>3. 复制用于测试<'),
            ('>Use generated IBANs to test payment forms, validate software, or learn how IBAN formats work across countries. Built for developers and QA engineers.<',
             '>使用生成的 IBAN 测试支付表单、验证软件或了解各国的 IBAN 格式。专为开发者和 QA 工程师设计。<'),
            ('>4. 100% Private &amp; Secure<', '>4. 100% 私密安全<'),
            ('>No server, no database, no analytics. Everything runs in your browser. Your data never leaves your device — inspect the source to verify.<',
             '>无服务器、无数据库、无分析追踪。一切在您的浏览器中运行。数据永远不会离开您的设备 — 可查看源代码验证。<'),
        ],
        'whatis': [
            ('>What is an IBAN?<', '>什么是 IBAN？<'),
            ('>IBAN stands for <strong>International Bank Account Number</strong>. It is a standardised way of identifying bank accounts across national borders, used in over 95 countries worldwide. An IBAN contains a two-letter country code, two check digits, and a Basic Bank Account Number (BBAN) that includes the domestic bank code, branch code, and account number.<',
             '>IBAN 代表<strong>国际银行账号</strong>。它是一种跨国境识别银行账户的标准化方式，在全球 95+ 个国家使用。IBAN 包含两位字母国家代码、两位校验位，以及包含国内银行代码、分行代码和账号的基本银行账号（BBAN）。<'),
            ('>The IBAN system was developed by the European Committee for Banking Standards (ECBS) and later adopted as <strong>ISO 13616</strong>. Today, all SEPA (Single Euro Payments Area) transfers require an IBAN, making it essential for international banking in Europe and beyond.<',
             '>IBAN 系统由欧洲银行标准委员会（ECBS）开发，后被采纳为 <strong>ISO 13616</strong> 标准。如今，所有 SEPA（单一欧元支付区）转账都需要 IBAN，使其成为欧洲及全球国际银行业务的必需品。<'),
        ],
        'region': [
            ('>IBAN by Region<', '>按地区查看 IBAN<'),
            ('>SEPA Countries<', '>SEPA 国家<'),
            ('>36 European countries — unified euro payment zone<', '>36 个欧洲国家 — 统一欧元支付区<'),
            ('>Worldwide IBAN<', '>全球 IBAN<'),
            ('>60+ non-SEPA countries — Brazil, UAE, Saudi Arabia, Turkey &amp; more<', '>60+ 个非 SEPA 国家 — 巴西、阿联酋、沙特阿拉伯、土耳其等<'),
            ('>International<', '>国际<'),
        ],
        'formats': [
            ('>Popular IBAN Formats<', '>常用 IBAN 格式<'),
            ('>Country</th><th>Length</th><th>Format Example</th><th>SEPA</th>',
             '>国家</th><th>长度</th><th>格式示例</th><th>SEPA</th>'),
        ],
        'faq': [
            ('>Frequently Asked Questions<', '>常见问题<'),
            ('>Are these real IBANs?<', '>这些 IBAN 是真实的吗？<'),
            ('>No. The IBANs generated here are <strong>mathematically valid</strong> (they pass the MOD-97 check digit verification) but use randomly generated bank codes and account numbers. They are intended for <strong>testing purposes only</strong> — do not use them for actual bank transfers.<',
             '>不是。这里生成的 IBAN <strong>数学上有效</strong>（通过 MOD-97 校验位验证），但使用随机生成的银行代码和账号。它们仅供<strong>测试用途</strong> — 请勿用于实际的银行转账。<'),
            ('>How does the IBAN check digit work?<', '>IBAN 校验位如何工作？<'),
            ('>IBAN uses the MOD-97 algorithm (ISO 7064). The country code letters are converted to numbers (A=10, B=11, ..., Z=35), the string is rearranged, and the result must equal 1 modulo 97. This catches 99.94% of typing errors. <a href="/iban-check-digit/">Learn more &rarr;</a><',
             '>IBAN 使用 MOD-97 算法（ISO 7064）。将国家代码字母转换为数字（A=10，B=11，...，Z=35），重新排列字符串，结果必须等于 1 对 97 取模。这能捕捉 99.94% 的输入错误。<a href="/iban-check-digit/">了解更多 →</a><'),
            ('>Is my data safe?<', '>我的数据安全吗？<'),
            ('>Yes — 100%. All IBAN generation and validation happens in your browser using JavaScript. No data is ever sent to any server. We do not use cookies, analytics trackers, or any form of data collection. You can verify this by inspecting the source code.<',
             '>是的 — 100%。所有 IBAN 生成和验证都在您的浏览器中使用 JavaScript 完成。没有任何数据发送到任何服务器。我们不使用 Cookie、分析追踪器或任何形式的数据收集。您可以通过查看源代码来验证。<'),
            ('>Which countries are supported?<', '>支持哪些国家？<'),
            ('>We support 96 countries and territories — covering all 36 SEPA members plus 60+ international IBAN formats. <a href="/countries/">Browse the full list &rarr;</a><',
             '>我们支持 96 个国家和地区 — 涵盖所有 36 个 SEPA 成员国以及 60+ 个国际 IBAN 格式。<a href="/countries/">浏览完整列表 →</a><'),
        ],
        'cta': [
            ('>Ready to start?<', '>准备开始？<'),
            ('>96 Countries. <span class="text-gradient">One Tool.</span><', '>96 个国家。<span class="text-gradient">一个工具。</span><'),
            ('>Generate valid IBANs for any supported country, validate existing IBANs, or explore the complete IBAN format reference — all from one place, all running locally in your browser.<',
             '>为任何支持的国家生成有效的 IBAN，验证现有 IBAN，或浏览完整的 IBAN 格式参考 — 全部在一个地方，在您的浏览器中本地运行。<'),
            ('>&#x1F30D; Browse All Countries<', '>&#x1F30D; 浏览所有国家<'),
            ('>&#x2714; Validate an IBAN<', '>&#x2714; 验证 IBAN<'),
            ('>SEPA countries<', '>SEPA 国家<'),
            ('>How check digits work<', '>校验位如何工作<'),
            ('>Germany IBAN<', '>德国 IBAN<'),
            ('>France IBAN<', '>法国 IBAN<'),
            ('>UK IBAN<', '>英国 IBAN<'),
            ('>Spain IBAN<', '>西班牙 IBAN<'),
        ],
        'footer': [
            ('>Free online IBAN generator and validator. All generation runs client-side — no data is ever collected, stored, or transmitted. Generated IBANs are for testing purposes only.<',
             '>免费的在线 IBAN 生成器和验证器。所有生成均在客户端运行 — 不会收集、存储或传输任何数据。生成的 IBAN 仅供测试使用。<'),
            ('>IBAN Generator<', '>IBAN 生成器<'),
            ('>All Countries<', '>所有国家<'),
            ('>Validator<', '>验证器<'),
            ('>SEPA Countries<', '>SEPA 国家<'),
            ('>SWIFT/BIC Codes<', '>SWIFT/BIC 代码<'),
            ('>Contact<', '>联系我们<'),
            ('>Privacy<', '>隐私政策<'),
            ('>Terms<', '>使用条款<'),
            ('>Sitemap<', '>网站地图<'),
        ],
    },
    'de': {
        'lang_name': 'Deutsch',
        'title': 'Kostenloser Online-IBAN-Generator — Gültige IBAN-Nummern sofort generieren',
        'desc': 'Generieren Sie gültige zufällige IBAN-Nummern für 96+ Länder. Kostenloser IBAN-Generator und -Validator, keine Anmeldung, rein clientseitig, keine Daten an Server. Unterstützt alle SEPA- und internationalen IBAN-Formate.',
        'nav': [
            ('>Home<', '>Startseite<'),
            ('>What is IBAN<', '>Was ist IBAN<'),
            ('>Countries<', '>Länder<'),
            ('>Validator<', '>Validator<'),
            ('>SEPA<', '>SEPA<'),
            ('>Check Digits<', '>Prüfziffern<'),
            ('>SWIFT Codes<', '>SWIFT-Codes<'),
            ('>Calculator<', '>Rechner<'),
            ('>Learn<', '>Lernen<'),
        ],
        'crumb_home': ('<span class="crumb-current">Home</span>', '<span class="crumb-current">Startseite</span>'),
        'hero': [
            ('Free · No sign-up · 100% Client-Side', 'Kostenlos · Keine Anmeldung · 100% Clientseitig'),
            ('The <span class="text-gradient">IBAN Generator</span><br>for Every Country',
             'Der <span class="text-gradient">IBAN-Generator</span><br>für jedes Land'),
            ('Generate <strong class="text-gold">mathematically valid</strong> IBANs for 96+ countries in your browser. ISO 13616 compliant, MOD-97 verified, zero data sent to any server.',
             'Generieren Sie <strong class="text-gold">mathematisch gültige</strong> IBANs für 96+ Länder direkt im Browser. ISO 13616-konform, MOD-97-geprüft, keine Daten an Server.'),
            ('>&#x21bb; Generate IBAN<', '>&#x21bb; IBAN generieren<'),
            ('>&#x2714; Validate an IBAN<', '>&#x2714; IBAN prüfen<'),
            ('<span class="ht-l">+ International</span>', '<span class="ht-l">+ International</span>'),
            ('<span class="ht-l">Server Calls</span>', '<span class="ht-l">Serveraufrufe</span>'),
            ('<span class="ht-l">Forever</span>', '<span class="ht-l">Für immer</span>'),
        ],
        'dial': [
            ('>Generate an IBAN<', '>IBAN generieren<'),
            ('placeholder="Search country..."', 'placeholder="Land suchen..."'),
            ('>Select a country<', '>Land auswählen<'),
            ('for="quantity-slider">Quantity<', 'for="quantity-slider">Anzahl<'),
            ('>Length<', '>Länge<'),
            ('>&#x2398; Copy<', '>&#x2398; Kopieren<'),
            ('>Copied!<', '>Kopiert!<'),
        ],
        'bulk': [
            ('>Generated IBANs<', '>Generierte IBANs<'),
            ('>&#x2398; Copy All<', '>&#x2398; Alle kopieren<'),
        ],
        'history': [
            ('>History<', '>Verlauf<'),
            ('>Recent History<', '>Letzter Verlauf<'),
            ('>Clear<', '>Löschen<'),
        ],
        'how': [
            ('>How It Works<', '>So funktioniert es<'),
            ('>1. Select a Country<', '>1. Land auswählen<'),
            ('>Pick any country from the dropdown — all 96+ IBAN-using countries, from Germany and France to Brazil and the UAE. SEPA and international formats supported.<',
             '>Wählen Sie ein beliebiges Land aus dem Dropdown — alle 96+ IBAN-Länder, von Deutschland und Frankreich bis Brasilien und den VAE. SEPA- und internationale Formate werden unterstützt.<'),
            ('>2. Generate an IBAN<', '>2. IBAN generieren<'),
            ('>A <strong>mathematically valid</strong> IBAN is created using the MOD-97 check digit algorithm (ISO 13616). Every generated IBAN passes full validation.<',
             '>Eine <strong>mathematisch gültige</strong> IBAN wird mit dem MOD-97-Prüfziffernalgorithmus (ISO 13616) erstellt. Jede generierte IBAN besteht die vollständige Validierung.<'),
            ('>3. Copy &amp; Use for Testing<', '>3. Kopieren &amp; zum Testen verwenden<'),
            ('>Use generated IBANs to test payment forms, validate software, or learn how IBAN formats work across countries. Built for developers and QA engineers.<',
             '>Verwenden Sie generierte IBANs zum Testen von Zahlungsformularen, zur Software-Validierung oder um IBAN-Formate verschiedener Länder kennenzulernen. Für Entwickler und QA-Ingenieure.<'),
            ('>4. 100% Private &amp; Secure<', '>4. 100% privat &amp; sicher<'),
            ('>No server, no database, no analytics. Everything runs in your browser. Your data never leaves your device — inspect the source to verify.<',
             '>Kein Server, keine Datenbank, keine Analysen. Alles läuft in Ihrem Browser. Ihre Daten verlassen nie Ihr Gerät — prüfen Sie den Quellcode zur Bestätigung.<'),
        ],
        'whatis': [
            ('>What is an IBAN?<', '>Was ist eine IBAN?<'),
            ('>IBAN stands for <strong>International Bank Account Number</strong>. It is a standardised way of identifying bank accounts across national borders, used in over 95 countries worldwide. An IBAN contains a two-letter country code, two check digits, and a Basic Bank Account Number (BBAN) that includes the domestic bank code, branch code, and account number.<',
             '>IBAN steht für <strong>International Bank Account Number</strong> (Internationale Bankkontonummer). Es ist eine standardisierte Möglichkeit, Bankkonten über Ländergrenzen hinweg zu identifizieren, die in über 95 Ländern weltweit verwendet wird. Eine IBAN enthält einen zweistelligen Ländercode, zwei Prüfziffern und eine Basic Bank Account Number (BBAN) mit Bankleitzahl, Filialcode und Kontonummer.<'),
            ('>The IBAN system was developed by the European Committee for Banking Standards (ECBS) and later adopted as <strong>ISO 13616</strong>. Today, all SEPA (Single Euro Payments Area) transfers require an IBAN, making it essential for international banking in Europe and beyond.<',
             '>Das IBAN-System wurde vom European Committee for Banking Standards (ECBS) entwickelt und später als <strong>ISO 13616</strong> übernommen. Heute erfordern alle SEPA-Überweisungen (Single Euro Payments Area) eine IBAN, was sie für das internationale Bankwesen in Europa und darüber hinaus unverzichtbar macht.<'),
        ],
        'region': [
            ('>IBAN by Region<', '>IBAN nach Region<'),
            ('>SEPA Countries<', '>SEPA-Länder<'),
            ('>36 European countries — unified euro payment zone<', '>36 europäische Länder — einheitliche Euro-Zahlungszone<'),
            ('>Worldwide IBAN<', '>Weltweit IBAN<'),
            ('>60+ non-SEPA countries — Brazil, UAE, Saudi Arabia, Turkey &amp; more<', '>60+ Nicht-SEPA-Länder — Brasilien, VAE, Saudi-Arabien, Türkei &amp; mehr<'),
            ('>International<', '>International<'),
        ],
        'formats': [
            ('>Popular IBAN Formats<', '>Beliebte IBAN-Formate<'),
            ('>Country</th><th>Length</th><th>Format Example</th><th>SEPA</th>',
             '>Land</th><th>Länge</th><th>Format-Beispiel</th><th>SEPA</th>'),
        ],
        'faq': [
            ('>Frequently Asked Questions<', '>Häufig gestellte Fragen<'),
            ('>Are these real IBANs?<', '>Sind das echte IBANs?<'),
            ('>No. The IBANs generated here are <strong>mathematically valid</strong> (they pass the MOD-97 check digit verification) but use randomly generated bank codes and account numbers. They are intended for <strong>testing purposes only</strong> — do not use them for actual bank transfers.<',
             '>Nein. Die hier generierten IBANs sind <strong>mathematisch gültig</strong> (sie bestehen die MOD-97-Prüfziffernprüfung), verwenden aber zufällig generierte Bankcodes und Kontonummern. Sie sind nur für <strong>Testzwecke</strong> gedacht — verwenden Sie sie nicht für echte Banküberweisungen.<'),
            ('>How does the IBAN check digit work?<', '>Wie funktioniert die IBAN-Prüfziffer?<'),
            ('>IBAN uses the MOD-97 algorithm (ISO 7064). The country code letters are converted to numbers (A=10, B=11, ..., Z=35), the string is rearranged, and the result must equal 1 modulo 97. This catches 99.94% of typing errors. <a href="/iban-check-digit/">Learn more &rarr;</a><',
             '>Die IBAN verwendet den MOD-97-Algorithmus (ISO 7064). Die Buchstaben des Ländercodes werden in Zahlen umgewandelt (A=10, B=11, ..., Z=35), die Zeichenfolge wird umgeordnet, und das Ergebnis muss Modulo 97 gleich 1 sein. Dies erkennt 99,94% der Tippfehler.<a href="/iban-check-digit/">Mehr erfahren →</a><'),
            ('>Is my data safe?<', '>Sind meine Daten sicher?<'),
            ('>Yes — 100%. All IBAN generation and validation happens in your browser using JavaScript. No data is ever sent to any server. We do not use cookies, analytics trackers, or any form of data collection. You can verify this by inspecting the source code.<',
             '>Ja — 100%. Alle IBAN-Generierung und -Validierung erfolgt in Ihrem Browser mit JavaScript. Es werden keine Daten an Server gesendet. Wir verwenden keine Cookies, Analyse-Tracker oder Datenkollektion. Sie können dies im Quellcode überprüfen.<'),
            ('>Which countries are supported?<', '>Welche Länder werden unterstützt?<'),
            ('>We support 96 countries and territories — covering all 36 SEPA members plus 60+ international IBAN formats. <a href="/countries/">Browse the full list &rarr;</a><',
             '>Wir unterstützen 96 Länder und Gebiete — alle 36 SEPA-Mitglieder plus 60+ internationale IBAN-Formate.<a href="/countries/">Vollständige Liste ansehen →</a><'),
        ],
        'cta': [
            ('>Ready to start?<', '>Bereit zu starten?<'),
            ('>96 Countries. <span class="text-gradient">One Tool.</span><', '>96 Länder. <span class="text-gradient">Ein Tool.</span><'),
            ('>Generate valid IBANs for any supported country, validate existing IBANs, or explore the complete IBAN format reference — all from one place, all running locally in your browser.<',
             '>Generieren Sie gültige IBANs für jedes unterstützte Land, validieren Sie bestehende IBANs oder erkunden Sie die vollständige IBAN-Formatreferenz — alles an einem Ort, alles lokal im Browser.<'),
            ('>&#x1F30D; Browse All Countries<', '>&#x1F30D; Alle Länder ansehen<'),
            ('>&#x2714; Validate an IBAN<', '>&#x2714; IBAN prüfen<'),
            ('>SEPA countries<', '>SEPA-Länder<'),
            ('>How check digits work<', '>So funktionieren Prüfziffern<'),
            ('>Germany IBAN<', '>Deutschland IBAN<'),
            ('>France IBAN<', '>Frankreich IBAN<'),
            ('>UK IBAN<', '>Großbritannien IBAN<'),
            ('>Spain IBAN<', '>Spanien IBAN<'),
        ],
        'footer': [
            ('>Free online IBAN generator and validator. All generation runs client-side — no data is ever collected, stored, or transmitted. Generated IBANs are for testing purposes only.<',
             '>Kostenloser Online-IBAN-Generator und -Validator. Alle Generierung läuft clientseitig — es werden keine Daten gesammelt, gespeichert oder übertragen. Generierte IBANs sind nur für Testzwecke.<'),
            ('>IBAN Generator<', '>IBAN-Generator<'),
            ('>All Countries<', '>Alle Länder<'),
            ('>Validator<', '>Validator<'),
            ('>SEPA Countries<', '>SEPA-Länder<'),
            ('>SWIFT/BIC Codes<', '>SWIFT/BIC-Codes<'),
            ('>Contact<', '>Kontakt<'),
            ('>Privacy<', '>Datenschutz<'),
            ('>Terms<', '>AGB<'),
            ('>Sitemap<', '>Sitemap<'),
        ],
    },
    'es': {
        'lang_name': 'Español',
        'title': 'Generador de IBAN en línea gratuito — Genera números IBAN válidos al instante',
        'desc': 'Genera números IBAN aleatorios válidos para 96+ países. Generador y validador de IBAN gratuito, sin registro, 100% en tu navegador, sin enviar datos a ningún servidor. Soporta todos los formatos SEPA e internacionales.',
        'nav': [
            ('>Home<', '>Inicio<'),
            ('>What is IBAN<', '>Qué es IBAN<'),
            ('>Countries<', '>Países<'),
            ('>Validator<', '>Validador<'),
            ('>SEPA<', '>SEPA<'),
            ('>Check Digits<', '>Dígitos de control<'),
            ('>SWIFT Codes<', '>Códigos SWIFT<'),
            ('>Calculator<', '>Calculadora<'),
            ('>Learn<', '>Aprende<'),
        ],
        'crumb_home': ('<span class="crumb-current">Home</span>', '<span class="crumb-current">Inicio</span>'),
        'hero': [
            ('Free · No sign-up · 100% Client-Side', 'Gratis · Sin registro · 100% en tu navegador'),
            ('The <span class="text-gradient">IBAN Generator</span><br>for Every Country',
             'El <span class="text-gradient">generador de IBAN</span><br>para cada país'),
            ('Generate <strong class="text-gold">mathematically valid</strong> IBANs for 96+ countries in your browser. ISO 13616 compliant, MOD-97 verified, zero data sent to any server.',
             'Genera IBAN <strong class="text-gold">matemáticamente válidos</strong> para 96+ países en tu navegador. Conforme a ISO 13616, verificado con MOD-97, cero datos enviados a servidores.'),
            ('>&#x21bb; Generate IBAN<', '>&#x21bb; Generar IBAN<'),
            ('>&#x2714; Validate an IBAN<', '>&#x2714; Validar un IBAN<'),
            ('<span class="ht-l">+ International</span>', '<span class="ht-l">+ Internacional</span>'),
            ('<span class="ht-l">Server Calls</span>', '<span class="ht-l">Llamadas al servidor</span>'),
            ('<span class="ht-l">Forever</span>', '<span class="ht-l">Para siempre</span>'),
        ],
        'dial': [
            ('>Generate an IBAN<', '>Generar un IBAN<'),
            ('placeholder="Search country..."', 'placeholder="Buscar país..."'),
            ('>Select a country<', '>Seleccionar un país<'),
            ('for="quantity-slider">Quantity<', 'for="quantity-slider">Cantidad<'),
            ('>Length<', '>Longitud<'),
            ('>&#x2398; Copy<', '>&#x2398; Copiar<'),
            ('>Copied!<', '>¡Copiado!<'),
        ],
        'bulk': [
            ('>Generated IBANs<', '>IBANs generados<'),
            ('>&#x2398; Copy All<', '>&#x2398; Copiar todo<'),
        ],
        'history': [
            ('>History<', '>Historial<'),
            ('>Recent History<', '>Historial reciente<'),
            ('>Clear<', '>Borrar<'),
        ],
        'how': [
            ('>How It Works<', '>Cómo funciona<'),
            ('>1. Select a Country<', '>1. Selecciona un país<'),
            ('>Pick any country from the dropdown — all 96+ IBAN-using countries, from Germany and France to Brazil and the UAE. SEPA and international formats supported.<',
             '>Elige cualquier país del menú — los 96+ países que usan IBAN, desde Alemania y Francia hasta Brasil y los EAU. Se admiten formatos SEPA e internacionales.<'),
            ('>2. Generate an IBAN<', '>2. Genera un IBAN<'),
            ('>A <strong>mathematically valid</strong> IBAN is created using the MOD-97 check digit algorithm (ISO 13616). Every generated IBAN passes full validation.<',
             '>Se crea un IBAN <strong>matemáticamente válido</strong> con el algoritmo de dígitos de control MOD-97 (ISO 13616). Cada IBAN generado pasa la validación completa.<'),
            ('>3. Copy &amp; Use for Testing<', '>3. Copia y úsalo para pruebas<'),
            ('>Use generated IBANs to test payment forms, validate software, or learn how IBAN formats work across countries. Built for developers and QA engineers.<',
             '>Usa los IBAN generados para probar formularios de pago, validar software o aprender cómo funcionan los formatos IBAN en distintos países. Hecho para desarrolladores e ingenieros de QA.<'),
            ('>4. 100% Private &amp; Secure<', '>4. 100% privado y seguro<'),
            ('>No server, no database, no analytics. Everything runs in your browser. Your data never leaves your device — inspect the source to verify.<',
             '>Sin servidor, sin base de datos, sin análisis. Todo funciona en tu navegador. Tus datos nunca salen de tu dispositivo — inspecciona el código para verificar.<'),
        ],
        'whatis': [
            ('>What is an IBAN?<', '>¿Qué es un IBAN?<'),
            ('>IBAN stands for <strong>International Bank Account Number</strong>. It is a standardised way of identifying bank accounts across national borders, used in over 95 countries worldwide. An IBAN contains a two-letter country code, two check digits, and a Basic Bank Account Number (BBAN) that includes the domestic bank code, branch code, and account number.<',
             '>IBAN significa <strong>International Bank Account Number</strong> (Número de Cuenta Bancaria Internacional). Es una forma estandarizada de identificar cuentas bancarias a través de fronteras, usada en más de 95 países. Un IBAN contiene un código de país de dos letras, dos dígitos de control y una Basic Bank Account Number (BBAN) con el código bancario nacional, sucursal y número de cuenta.<'),
            ('>The IBAN system was developed by the European Committee for Banking Standards (ECBS) and later adopted as <strong>ISO 13616</strong>. Today, all SEPA (Single Euro Payments Area) transfers require an IBAN, making it essential for international banking in Europe and beyond.<',
             '>El sistema IBAN fue desarrollado por el European Committee for Banking Standards (ECBS) y adoptado como <strong>ISO 13616</strong>. Hoy, todas las transferencias SEPA (Single Euro Payments Area) requieren IBAN, siendo esencial para la banca internacional en Europa y más allá.<'),
        ],
        'region': [
            ('>IBAN by Region<', '>IBAN por región<'),
            ('>SEPA Countries<', '>Países SEPA<'),
            ('>36 European countries — unified euro payment zone<', '>36 países europeos — zona de pago en euros unificada<'),
            ('>Worldwide IBAN<', '>IBAN mundial<'),
            ('>60+ non-SEPA countries — Brazil, UAE, Saudi Arabia, Turkey &amp; more<', '>60+ países no SEPA — Brasil, EAU, Arabia Saudita, Turquía y más<'),
            ('>International<', '>Internacional<'),
        ],
        'formats': [
            ('>Popular IBAN Formats<', '>Formatos IBAN populares<'),
            ('>Country</th><th>Length</th><th>Format Example</th><th>SEPA</th>',
             '>País</th><th>Longitud</th><th>Ejemplo de formato</th><th>SEPA</th>'),
        ],
        'faq': [
            ('>Frequently Asked Questions<', '>Preguntas frecuentes<'),
            ('>Are these real IBANs?<', '>¿Son IBAN reales?<'),
            ('>No. The IBANs generated here are <strong>mathematically valid</strong> (they pass the MOD-97 check digit verification) but use randomly generated bank codes and account numbers. They are intended for <strong>testing purposes only</strong> — do not use them for actual bank transfers.<',
             '>No. Los IBAN generados aquí son <strong>matemáticamente válidos</strong> (pasan la verificación MOD-97) pero usan códigos bancarios y números de cuenta aleatorios. Son solo para <strong>fines de prueba</strong> — no los uses para transferencias reales.<'),
            ('>How does the IBAN check digit work?<', '>¿Cómo funciona el dígito de control del IBAN?<'),
            ('>IBAN uses the MOD-97 algorithm (ISO 7064). The country code letters are converted to numbers (A=10, B=11, ..., Z=35), the string is rearranged, and the result must equal 1 modulo 97. This catches 99.94% of typing errors. <a href="/iban-check-digit/">Learn more &rarr;</a><',
             '>El IBAN usa el algoritmo MOD-97 (ISO 7064). Las letras del código de país se convierten a números (A=10, B=11, ..., Z=35), la cadena se reordena y el resultado debe ser igual a 1 módulo 97. Esto detecta el 99,94% de los errores de escritura.<a href="/iban-check-digit/">Aprende más →</a><'),
            ('>Is my data safe?<', '>¿Mis datos están seguros?<'),
            ('>Yes — 100%. All IBAN generation and validation happens in your browser using JavaScript. No data is ever sent to any server. We do not use cookies, analytics trackers, or any form of data collection. You can verify this by inspecting the source code.<',
             '>Sí — 100%. Toda la generación y validación de IBAN ocurre en tu navegador con JavaScript. No se envía ningún dato a servidores. No usamos cookies, rastreadores de análisis ni recolección de datos. Puedes verificarlo inspeccionando el código fuente.<'),
            ('>Which countries are supported?<', '>¿Qué países se admiten?<'),
            ('>We support 96 countries and territories — covering all 36 SEPA members plus 60+ international IBAN formats. <a href="/countries/">Browse the full list &rarr;</a><',
             '>Soportamos 96 países y territorios — los 36 miembros SEPA más 60+ formatos IBAN internacionales.<a href="/countries/">Ver la lista completa →</a><'),
        ],
        'cta': [
            ('>Ready to start?<', '>¿Listo para empezar?<'),
            ('>96 Countries. <span class="text-gradient">One Tool.</span><', '>96 países. <span class="text-gradient">Una herramienta.</span><'),
            ('>Generate valid IBANs for any supported country, validate existing IBANs, or explore the complete IBAN format reference — all from one place, all running locally in your browser.<',
             '>Genera IBAN válidos para cualquier país compatible, valida IBAN existentes o explora la referencia completa de formatos IBAN — todo en un lugar, todo local en tu navegador.<'),
            ('>&#x1F30D; Browse All Countries<', '>&#x1F30D; Ver todos los países<'),
            ('>&#x2714; Validate an IBAN<', '>&#x2714; Validar un IBAN<'),
            ('>SEPA countries<', '>Países SEPA<'),
            ('>How check digits work<', '>Cómo funcionan los dígitos de control<'),
            ('>Germany IBAN<', '>IBAN de Alemania<'),
            ('>France IBAN<', '>IBAN de Francia<'),
            ('>UK IBAN<', '>IBAN de Reino Unido<'),
            ('>Spain IBAN<', '>IBAN de España<'),
        ],
        'footer': [
            ('>Free online IBAN generator and validator. All generation runs client-side — no data is ever collected, stored, or transmitted. Generated IBANs are for testing purposes only.<',
             '>Generador y validador de IBAN gratuito en línea. Toda la generación se ejecuta en tu navegador — no se recopilan, almacenan ni transmiten datos. Los IBAN generados son solo para pruebas.<'),
            ('>IBAN Generator<', '>Generador de IBAN<'),
            ('>All Countries<', '>Todos los países<'),
            ('>Validator<', '>Validador<'),
            ('>SEPA Countries<', '>Países SEPA<'),
            ('>SWIFT/BIC Codes<', '>Códigos SWIFT/BIC<'),
            ('>Contact<', '>Contacto<'),
            ('>Privacy<', '>Privacidad<'),
            ('>Terms<', '>Términos<'),
            ('>Sitemap<', '>Mapa del sitio<'),
        ],
    },
    'fr': {
        'lang_name': 'Français',
        'title': 'Générateur d\'IBAN en ligne gratuit — Générez des numéros IBAN valides instantanément',
        'desc': 'Générez des numéros IBAN aléatoires valides pour 96+ pays. Générateur et validateur d\'IBAN gratuit, sans inscription, 100% côté client, aucune donnée envoyée à un serveur. Prend en charge tous les formats SEPA et internationaux.',
        'nav': [
            ('>Home<', '>Accueil<'),
            ('>What is IBAN<', '>Qu\'est-ce que l\'IBAN<'),
            ('>Countries<', '>Pays<'),
            ('>Validator<', '>Validateur<'),
            ('>SEPA<', '>SEPA<'),
            ('>Check Digits<', '>Chiffres de contrôle<'),
            ('>SWIFT Codes<', '>Codes SWIFT<'),
            ('>Calculator<', '>Calculateur<'),
            ('>Learn<', '>Apprendre<'),
        ],
        'crumb_home': ('<span class="crumb-current">Home</span>', '<span class="crumb-current">Accueil</span>'),
        'hero': [
            ('Free · No sign-up · 100% Client-Side', 'Gratuit · Sans inscription · 100% côté client'),
            ('The <span class="text-gradient">IBAN Generator</span><br>for Every Country',
             'Le <span class="text-gradient">générateur d\'IBAN</span><br>pour chaque pays'),
            ('Generate <strong class="text-gold">mathematically valid</strong> IBANs for 96+ countries in your browser. ISO 13616 compliant, MOD-97 verified, zero data sent to any server.',
             'Générez des IBAN <strong class="text-gold">mathématiquement valides</strong> pour 96+ pays dans votre navigateur. Conforme ISO 13616, vérifié MOD-97, zéro donnée envoyée à un serveur.'),
            ('>&#x21bb; Generate IBAN<', '>&#x21bb; Générer un IBAN<'),
            ('>&#x2714; Validate an IBAN<', '>&#x2714; Valider un IBAN<'),
            ('<span class="ht-l">+ International</span>', '<span class="ht-l">+ International</span>'),
            ('<span class="ht-l">Server Calls</span>', '<span class="ht-l">Appels serveur</span>'),
            ('<span class="ht-l">Forever</span>', '<span class="ht-l">Pour toujours</span>'),
        ],
        'dial': [
            ('>Generate an IBAN<', '>Générer un IBAN<'),
            ('placeholder="Search country..."', 'placeholder="Rechercher un pays..."'),
            ('>Select a country<', '>Sélectionner un pays<'),
            ('for="quantity-slider">Quantity<', 'for="quantity-slider">Quantité<'),
            ('>Length<', '>Longueur<'),
            ('>&#x2398; Copy<', '>&#x2398; Copier<'),
            ('>Copied!<', '>Copié !<'),
        ],
        'bulk': [
            ('>Generated IBANs<', '>IBAN générés<'),
            ('>&#x2398; Copy All<', '>&#x2398; Tout copier<'),
        ],
        'history': [
            ('>History<', '>Historique<'),
            ('>Recent History<', '>Historique récent<'),
            ('>Clear<', '>Effacer<'),
        ],
        'how': [
            ('>How It Works<', '>Comment ça marche<'),
            ('>1. Select a Country<', '>1. Sélectionnez un pays<'),
            ('>Pick any country from the dropdown — all 96+ IBAN-using countries, from Germany and France to Brazil and the UAE. SEPA and international formats supported.<',
             '>Choisissez n\'importe quel pays dans la liste — les 96+ pays utilisant l\'IBAN, de l\'Allemagne et la France au Brésil et aux EAU. Formats SEPA et internationaux pris en charge.<'),
            ('>2. Generate an IBAN<', '>2. Générez un IBAN<'),
            ('>A <strong>mathematically valid</strong> IBAN is created using the MOD-97 check digit algorithm (ISO 13616). Every generated IBAN passes full validation.<',
             '>Un IBAN <strong>mathématiquement valide</strong> est créé avec l\'algorithme MOD-97 (ISO 13616). Chaque IBAN généré passe la validation complète.<'),
            ('>3. Copy &amp; Use for Testing<', '>3. Copiez et utilisez pour tester<'),
            ('>Use generated IBANs to test payment forms, validate software, or learn how IBAN formats work across countries. Built for developers and QA engineers.<',
             '>Utilisez les IBAN générés pour tester des formulaires de paiement, valider des logiciels ou apprendre comment fonctionnent les formats IBAN selon les pays. Conçu pour les développeurs et ingénieurs QA.<'),
            ('>4. 100% Private &amp; Secure<', '>4. 100% privé et sécurisé<'),
            ('>No server, no database, no analytics. Everything runs in your browser. Your data never leaves your device — inspect the source to verify.<',
             '>Pas de serveur, pas de base de données, pas d\'analyse. Tout fonctionne dans votre navigateur. Vos données ne quittent jamais votre appareil — inspectez le code pour vérifier.<'),
        ],
        'whatis': [
            ('>What is an IBAN?<', '>Qu\'est-ce qu\'un IBAN ?<'),
            ('>IBAN stands for <strong>International Bank Account Number</strong>. It is a standardised way of identifying bank accounts across national borders, used in over 95 countries worldwide. An IBAN contains a two-letter country code, two check digits, and a Basic Bank Account Number (BBAN) that includes the domestic bank code, branch code, and account number.<',
             '>IBAN signifie <strong>International Bank Account Number</strong> (Numéro de Compte Bancaire International). C\'est un moyen standardisé d\'identifier les comptes bancaires à travers les frontières, utilisé dans plus de 95 pays. Un IBAN contient un code pays de deux lettres, deux chiffres de contrôle et un Basic Bank Account Number (BBAN) avec le code bancaire national, l\'agence et le numéro de compte.<'),
            ('>The IBAN system was developed by the European Committee for Banking Standards (ECBS) and later adopted as <strong>ISO 13616</strong>. Today, all SEPA (Single Euro Payments Area) transfers require an IBAN, making it essential for international banking in Europe and beyond.<',
             '>Le système IBAN a été développé par l\'European Committee for Banking Standards (ECBS) et adopté comme <strong>ISO 13616</strong>. Aujourd\'hui, tous les virements SEPA (Single Euro Payments Area) exigent un IBAN, ce qui le rend essentiel pour la banque internationale en Europe et au-delà.<'),
        ],
        'region': [
            ('>IBAN by Region<', '>IBAN par région<'),
            ('>SEPA Countries<', '>Pays SEPA<'),
            ('>36 European countries — unified euro payment zone<', '>36 pays européens — zone de paiement en euros unifiée<'),
            ('>Worldwide IBAN<', '>IBAN mondial<'),
            ('>60+ non-SEPA countries — Brazil, UAE, Saudi Arabia, Turkey &amp; more<', '>60+ pays hors SEPA — Brésil, EAU, Arabie saoudite, Turquie et plus<'),
            ('>International<', '>International<'),
        ],
        'formats': [
            ('>Popular IBAN Formats<', '>Formats IBAN populaires<'),
            ('>Country</th><th>Length</th><th>Format Example</th><th>SEPA</th>',
             '>Pays</th><th>Longueur</th><th>Exemple de format</th><th>SEPA</th>'),
        ],
        'faq': [
            ('>Frequently Asked Questions<', '>Questions fréquentes<'),
            ('>Are these real IBANs?<', '>Sont-ce de vrais IBAN ?<'),
            ('>No. The IBANs generated here are <strong>mathematically valid</strong> (they pass the MOD-97 check digit verification) but use randomly generated bank codes and account numbers. They are intended for <strong>testing purposes only</strong> — do not use them for actual bank transfers.<',
             '>Non. Les IBAN générés ici sont <strong>mathématiquement valides</strong> (ils passent la vérification MOD-97) mais utilisent des codes bancaires et numéros de compte aléatoires. Ils sont destinés <strong>uniquement aux tests</strong> — ne les utilisez pas pour de vrais virements.<'),
            ('>How does the IBAN check digit work?<', '>Comment fonctionne le chiffre de contrôle de l\'IBAN ?<'),
            ('>IBAN uses the MOD-97 algorithm (ISO 7064). The country code letters are converted to numbers (A=10, B=11, ..., Z=35), the string is rearranged, and the result must equal 1 modulo 97. This catches 99.94% of typing errors. <a href="/iban-check-digit/">Learn more &rarr;</a><',
             '>L\'IBAN utilise l\'algorithme MOD-97 (ISO 7064). Les lettres du code pays sont converties en nombres (A=10, B=11, ..., Z=35), la chaîne est réorganisée et le résultat doit être égal à 1 modulo 97. Cela détecte 99,94% des erreurs de frappe.<a href="/iban-check-digit/">En savoir plus →</a><'),
            ('>Is my data safe?<', '>Mes données sont-elles sûres ?<'),
            ('>Yes — 100%. All IBAN generation and validation happens in your browser using JavaScript. No data is ever sent to any server. We do not use cookies, analytics trackers, or any form of data collection. You can verify this by inspecting the source code.<',
             '>Oui — 100%. Toute la génération et validation d\'IBAN se fait dans votre navigateur avec JavaScript. Aucune donnée n\'est envoyée à un serveur. Nous n\'utilisons pas de cookies, traceurs d\'analyse ou collecte de données. Vous pouvez vérifier en inspectant le code source.<'),
            ('>Which countries are supported?<', '>Quels pays sont pris en charge ?<'),
            ('>We support 96 countries and territories — covering all 36 SEPA members plus 60+ international IBAN formats. <a href="/countries/">Browse the full list &rarr;</a><',
             '>Nous prenons en charge 96 pays et territoires — les 36 membres SEPA plus 60+ formats IBAN internationaux.<a href="/countries/">Voir la liste complète →</a><'),
        ],
        'cta': [
            ('>Ready to start?<', '>Prêt à commencer ?<'),
            ('>96 Countries. <span class="text-gradient">One Tool.</span><', '>96 pays. <span class="text-gradient">Un outil.</span><'),
            ('>Generate valid IBANs for any supported country, validate existing IBANs, or explore the complete IBAN format reference — all from one place, all running locally in your browser.<',
             '>Générez des IBAN valides pour n\'importe quel pays pris en charge, validez des IBAN existants ou explorez la référence complète des formats IBAN — tout au même endroit, tout en local dans votre navigateur.<'),
            ('>&#x1F30D; Browse All Countries<', '>&#x1F30D; Voir tous les pays<'),
            ('>&#x2714; Validate an IBAN<', '>&#x2714; Valider un IBAN<'),
            ('>SEPA countries<', '>Pays SEPA<'),
            ('>How check digits work<', '>Comment fonctionnent les chiffres de contrôle<'),
            ('>Germany IBAN<', '>IBAN Allemagne<'),
            ('>France IBAN<', '>IBAN France<'),
            ('>UK IBAN<', '>IBAN Royaume-Uni<'),
            ('>Spain IBAN<', '>IBAN Espagne<'),
        ],
        'footer': [
            ('>Free online IBAN generator and validator. All generation runs client-side — no data is ever collected, stored, or transmitted. Generated IBANs are for testing purposes only.<',
             '>Générateur et validateur d\'IBAN gratuit en ligne. Toute la génération se fait côté client — aucune donnée n\'est collectée, stockée ou transmise. Les IBAN générés sont uniquement pour les tests.<'),
            ('>IBAN Generator<', '>Générateur d\'IBAN<'),
            ('>All Countries<', '>Tous les pays<'),
            ('>Validator<', '>Validateur<'),
            ('>SEPA Countries<', '>Pays SEPA<'),
            ('>SWIFT/BIC Codes<', '>Codes SWIFT/BIC<'),
            ('>Contact<', '>Contact<'),
            ('>Privacy<', '>Confidentialité<'),
            ('>Terms<', '>Conditions<'),
            ('>Sitemap<', '>Plan du site<'),
        ],
    },
}

# Order of hreflang alternates (default/en first, then all supported)
SUPPORTED_LANGS = ['zh', 'de', 'es', 'fr']


def build_translated_homepage(lang_code, title=None, desc=None):
    """Build a translated homepage at /<lang>/index.html by applying string replacements."""
    cfg = LANG_CONFIG.get(lang_code)
    if not cfg:
        print('  WARNING: no translation config for {}'.format(lang_code))
        return None

    src_index = os.path.join(ROOT, 'index.html')
    if not os.path.exists(src_index):
        print('  WARNING: index.html not found, skipping {}'.format(lang_code))
        return None

    with open(src_index, 'r', encoding='utf-8') as f:
        html = f.read()

    title = title or cfg['title']
    desc = desc or cfg['desc']
    can_path = '/{}/'.format(lang_code)

    # Metadata replacements
    html = html.replace('<html lang="en">', '<html lang="{}">'.format(lang_code))
    html = html.replace(
        '<title>Free Online IBAN Generator — Generate Valid IBAN Numbers Instantly</title>',
        '<title>{}</title>'.format(title)
    )
    html = html.replace(
        '<meta name="description" content="Generate valid random IBAN numbers for 96+ countries. Free IBAN generator and validator — no signup, pure client-side, no data sent to any server. Supports all SEPA and international IBAN formats.">',
        '<meta name="description" content="{}">'.format(desc)
    )
    html = html.replace(
        '<meta property="og:title" content="Free Online IBAN Generator — Generate Valid IBAN Numbers Instantly">',
        '<meta property="og:title" content="{}">'.format(title)
    )
    html = html.replace(
        '<meta property="og:description" content="Generate valid random IBAN numbers for 96+ countries. Free, no signup, client-side only.">',
        '<meta property="og:description" content="{}">'.format(desc[:160])
    )
    html = html.replace(
        '<link rel="canonical" href="https://ibaneasy.com/">',
        '<link rel="canonical" href="{}{}">'.format(SITE, can_path)
    )
    html = html.replace(
        '<meta property="og:url" content="https://ibaneasy.com/">',
        '<meta property="og:url" content="{}{}">'.format(SITE, can_path)
    )

    # Add hreflang for all supported languages + i18n script before </head>
    hreflang = (
        '<link rel="alternate" hreflang="en" href="{}">\n'.format(SITE + '/') +
        '<link rel="alternate" hreflang="{}" href="{}">\n'.format(lang_code, SITE + can_path) +
        '<link rel="alternate" hreflang="x-default" href="{}">\n'.format(SITE + '/') +
        '<script src="/js/i18n.js" defer></script>'
    )
    html = html.replace('</head>', hreflang + '\n</head>')

    # Update JSON-LD
    html = html.replace(
        '"url":"https://ibaneasy.com"',
        '"url":"{}{}"'.format(SITE, can_path)
    )

    # Apply all string replacements from config
    for group_key in ['nav', 'hero', 'dial', 'bulk', 'history', 'how', 'whatis',
                      'region', 'formats', 'faq', 'cta', 'footer']:
        for old, new in cfg.get(group_key, []):
            html = html.replace(old, new)

    # Breadcrumb home
    if 'crumb_home' in cfg:
        html = html.replace(cfg['crumb_home'][0], cfg['crumb_home'][1])

    return html


# ── Main ─────────────────────────────────────────────────────────
def main():
    print('=== ibaneasy.com static site generator ===')
    print('Countries loaded: {}'.format(len(countries)))
    print('Output directory: {}'.format(SRC))

    total = 0

    # 1. Country pages
    print('\n[1/10] Generating {} country pages...'.format(len(countries)))
    for i, c in enumerate(countries):
        html = build_country_page(c)
        page('countries/{}'.format(c['code'].lower()), html)
        total += 1
        if (i + 1) % 20 == 0:
            print('  ... {}/{}'.format(i + 1, len(countries)))
    print('  {} country pages done'.format(len(countries)))

    # 2. Countries index
    print('\n[2/10] Countries index page...')
    html = build_countries_index()
    page('countries', html)
    total += 1
    print('  /countries/ done')

    # 3. Validator page
    print('\n[3/10] Validator page...')
    html = build_validator_page()
    page('validate', html)
    total += 1
    print('  /validate/ done')

    # 4. SEPA page
    print('\n[4/10] SEPA countries page...')
    html = build_sepa_page()
    page('sepa-countries', html)
    total += 1
    print('  /sepa-countries/ done')

    # 5. Check digit page
    print('\n[5/10] Check digit explanation page...')
    html = build_check_digit_page()
    page('iban-check-digit', html)
    total += 1
    print('  /iban-check-digit/ done')

    # 5a. What-is-IBAN guide page
    print('\n[5a/10] What-is-IBAN guide page...')
    html = build_what_is_iban_page()
    page('what-is-iban', html)
    total += 1
    print('  /what-is-iban/ done')

    # 5b. IBAN Calculator page
    print('\n[5b/10] IBAN Calculator page...')
    html = build_iban_calculator_page()
    page('iban-calculator', html)
    total += 1
    print('  /iban-calculator/ done')

    # 6. SWIFT/BIC page
    print('\n[6/10] SWIFT/BIC codes page...')
    html = build_swift_page()
    page('swift-codes', html)
    total += 1
    print('  /swift-codes/ done')

    # 7. Sitemap + Robots + Legal pages
    print('\n[7/10] Sitemap, robots.txt, and legal pages...')
    with open(os.path.join(SRC, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(build_sitemap())
    with open(os.path.join(SRC, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write(build_robots())
    total += 2

    # 8. Contact, Privacy, Terms, Sitemap HTML
    print('\n[8/10] Contact, Privacy, Terms, and HTML Sitemap...')
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

    # 9. Blog / Learn section
    print('\n[9/10] Blog / Learn section...')
    html = build_learn_index()
    page('learn', html)
    total += 1
    print('  /learn/ done')
    for art in BLOG_ARTICLES:
        html = build_article_page(art)
        page('learn/{}'.format(art['slug']), html)
        total += 1
        print('  /learn/{}/ done'.format(art['slug']))

    # 10. Translated homepages (zh, de, es, fr)
    print('\n[10/10] Translated homepages...')
    for lang in SUPPORTED_LANGS:
        html = build_translated_homepage(lang)
        if html:
            page(lang, html)
            total += 1
            print('  /{}/ done'.format(lang))
        else:
            print('  /{}/ SKIPPED'.format(lang))

    print('\n=== Done: {} files generated ==='.format(total))


if __name__ == '__main__':
    main()
