#!/usr/bin/env python3
"""Reconcile public Apple identification facts with local historical SMBIOS data.

Requires requests and beautifulsoup4. Network refresh is explicit; cached HTML is
kept outside the published documentation. No Apple images or proprietary inputs.
"""
import argparse
import ast
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PAGES = {'MacBook Pro': '108052', 'MacBook Air': '102869', 'Mac mini': '102852',
         'iMac': '108054', 'Mac Pro': '102887', 'Mac Studio': '102231', 'MacBook': '103257'}
OS_URL = 'https://www.apple.com/os/macos/'
ID_RE = re.compile(r'(?:MacBookPro|MacBookAir|MacBook|Macmini|iMacPro|iMac|MacPro|Mac|Xserve)\d+,\d+')
NAME_RE = re.compile(r'^(?:MacBook Pro|MacBook Air|MacBook|Mac mini|Mac Pro|Mac Studio|iMac Pro|iMac)\s*\(')
SILICON_IDS = {'MacBookAir10,1', 'MacBookPro17,1', 'MacBookPro18,1', 'MacBookPro18,2',
               'MacBookPro18,3', 'MacBookPro18,4', 'Macmini9,1', 'iMac21,1', 'iMac21,2'}


def architecture(identifier):
    return 'apple-silicon' if identifier in SILICON_IDS or re.fullmatch(r'Mac\d+,\d+', identifier) else 'intel'


def source(url, label):
    return {'label': label, 'url': url}


def family_of(identifier):
    for prefix, family in [('MacBookPro', 'MacBook Pro'), ('MacBookAir', 'MacBook Air'),
                           ('MacBook', 'MacBook'), ('Macmini', 'Mac mini'), ('iMacPro', 'iMac Pro'),
                           ('iMac', 'iMac'), ('MacPro', 'Mac Pro'), ('Xserve', 'Xserve')]:
        if identifier.startswith(prefix):
            return family
    return None


def primitive(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        return [primitive(item) for item in node.elts]
    # Enum spellings remain source claims, never interpreted as measured hardware.
    return ast.unparse(node)


def repository_records():
    path = ROOT / 'opencore_legacy_patcher/datasets/smbios_data.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    dictionary = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                      and any(getattr(t, 'id', '') == 'smbios_dictionary' for t in n.targets))
    records, excluded = {}, []
    for key, val in zip(dictionary.keys, dictionary.values):
        key = key.value
        identifier = re.sub(r'_v\d+$', '', key)
        if not ID_RE.fullmatch(identifier):
            excluded.append(key)
            continue
        fields = {k.value: primitive(v) for k, v in zip(val.keys, val.values)}
        records.setdefault(identifier, []).append({'dataset_key': key, 'name': fields.get('Marketing Name'),
            'cpu_generation': fields.get('CPU Generation'), 'stock_gpus': fields.get('Stock GPUs'),
            'stock_storage': fields.get('Stock Storage'), 'screen_inches': fields.get('Screen Size'),
            'wireless': fields.get('Wireless Model'), 'bluetooth': fields.get('Bluetooth Model'),
            'ethernet': fields.get('Ethernet Chipset'), 'uga_graphics': fields.get('UGA Graphics')})
    return records, excluded, hashlib.sha256(path.read_bytes()).hexdigest()


def parse_page(family, url, html):
    soup = BeautifulSoup(html, 'html.parser')
    groups, current = [], None
    for element in soup.select('h2,h3,p'):
        text = ' '.join(element.get_text(' ', strip=True).split())
        if NAME_RE.match(text) and len(text) < 110 and not text.startswith('MacBook Pro models'):
            if current:
                groups.append(current)
            current = {'name': text, 'texts': [], 'links': []}
        elif current:
            current['texts'].append(text)
            current['links'].extend((a.get_text(' ', strip=True), urljoin(url, a['href']))
                                    for a in element.select('a[href]'))
    if current:
        groups.append(current)
    results = []
    for g in groups:
        id_lines = [line for line in g['texts'] if re.match(r'Model Identifiers?:', line, re.I)]
        identifiers = list(dict.fromkeys(ID_RE.findall(' '.join(id_lines))))
        if not identifiers:
            continue
        year = re.search(r'\b(19\d{2}|20\d{2})\b', g['name'])
        for line in g['texts']:
            if line.startswith('Year introduced:'):
                year = re.search(r'\b(20\d{2})\b', line)
        os_line = next((x.split(':', 1)[1].strip() for x in g['texts']
                        if x.lower().startswith('newest compatible operating system:')), None)
        facts = {}
        for field in ['Chip', 'Ports', 'Front ports', 'Colors', 'Colours']:
            value = next((x.split(':', 1)[1].strip() for x in g['texts']
                          if x.lower().startswith(field.lower() + ':')), None)
            if value:
                facts[field.lower().replace(' ', '_')] = value
        specs = list(dict.fromkeys(link for label, link in g['links'] if 'spec' in label.lower()))
        results.append({'name': g['name'], 'family': 'iMac Pro' if g['name'].startswith('iMac Pro') else family,
                        'year': int(year.group(1)) if year else None, 'identifiers': identifiers,
                        'latest_macos': os_line, 'facts': facts, 'technical_specs_urls': specs, 'source_url': url})
    extracted = set(i for v in results for i in v['identifiers'])
    listed = set(ID_RE.findall(' '.join(p.get_text(' ', strip=True) for p in soup.select('p')
                                      if re.match(r'Model Identifiers?:', p.get_text(' ', strip=True), re.I))))
    if not results or listed != extracted:
        raise ValueError(f'{family}: missing identifiers {listed - extracted}; empty={not results}')
    return results


def validate(data):
    models = data['models']
    assert len({m['id'] for m in models}) == len(models)
    ids = [i for m in models for i in m['identifiers']]
    assert len(set(ids)) == len(ids)
    assert len(models) >= 175, 'Unexpected model coverage regression'
    assert all(m['nextcore']['status'] == 'unverified' and m['nextcore']['evidence_url'] is None for m in models)
    assert all(m['sources'] and m['architecture'] in ('intel', 'apple-silicon', 'powerpc', 'm68k', 'unknown') for m in models)
    assert all(m['apple_support']['macos_27']['status'] == ('eligible' if m['architecture'] == 'apple-silicon' else 'unknown' if m['architecture'] == 'unknown' else 'ineligible') for m in models)
    for expected in ('MacBook1,1', 'MacPro5,1', 'Xserve3,1', 'MacBookAir10,1', 'Mac14,8', 'Mac17,9'):
        assert expected in ids, f'Missing sentinel {expected}'
    names = {m['name'] for m in models}
    for expected in ('Macintosh 128K', 'Macintosh 512K', 'Macintosh Plus', 'Macintosh SE',
                     'Macintosh SE/30', 'Macintosh II', 'Macintosh IIci', 'Macintosh Portable',
                     'Macintosh IIfx', 'Macintosh Color Classic II'):
        assert expected in names, f'Missing historical sentinel {expected}'
    return {'models': len(models), 'identifiers': len(ids), 'families': dict(Counter(m['family'] for m in models)),
            'architectures': dict(Counter(m['architecture'] for m in models))}


def spec_facts(url, cache, refresh):
    """Extract numeric configuration facts, not prose or an individual machine's configuration."""
    path = cache / ('spec-' + hashlib.sha256(url.encode()).hexdigest()[:16] + '.html')
    try:
        if refresh or not path.exists():
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            path.write_text(response.text, encoding='utf-8')
        html = path.read_text(encoding='utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        sections = {}
        for heading in soup.select('h2,h3,h4'):
            name = heading.get_text(' ', strip=True).lower()
            parts = []
            for sibling in heading.next_siblings:
                if getattr(sibling, 'name', None) in ('h2', 'h3', 'h4'):
                    break
                if hasattr(sibling, 'get_text'):
                    parts.append(sibling.get_text(' ', strip=True))
            sections[name] = ' '.join(parts)
        def text_for(prefixes):
            return ' '.join(text for key, text in sections.items() if any(key.startswith(p) for p in prefixes))
        def capacities(text):
            return sorted(set(re.findall(r'\b\d+(?:\.\d+)?\s*(?:GB|TB|MB)\b(?!/s)', text))) or None
        chips = text_for(('chip', 'processor', 'processing'))
        return {'source_url': url, 'status': 'parsed-public-specification',
                'sha256': hashlib.sha256(html.encode()).hexdigest(),
                'memory_capacity_mentions': capacities(text_for(('memory',))),
                'storage_capacity_mentions': capacities(text_for(('storage', 'hard drive'))),
                'processor_mentions': sorted(set(re.findall(r'(?:Intel\s+(?:Core\s+(?:i[3579]|2\s+Duo|Duo)|Xeon)|(?:Apple\s+)?M[1-9](?:\s+(?:Pro|Max|Ultra))?|A18\s+Pro)', chips))) or None,
                'scope': 'Specification-page configuration mentions; may span several model identifiers. Not measured installed hardware.'}
    except requests.RequestException as exc:
        return {'source_url': url, 'status': 'unavailable', 'error': type(exc).__name__}


def legacy_records(cache, refresh):
    """Traverse Apple's historical directories; keep product names separate from SMBIOS IDs."""
    failures, receipts, excluded_accessories = [], [], []
    def page(url):
        path = cache / ('legacy-' + hashlib.sha256(url.encode()).hexdigest()[:16] + '.html')
        if refresh or not path.exists():
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            path.write_text(r.text, encoding='utf-8')
        html = path.read_text(encoding='utf-8')
        return BeautifulSoup(html, 'html.parser'), hashlib.sha256(html.encode()).hexdigest()
    index_url = 'https://support.apple.com/en-us/docs/mac'
    index, index_hash = page(index_url)
    directories = {'https://support.apple.com/en-us/docs/mac/' + key for key in ('pp210', 'pp201', 'pp212')}
    for a in index.select('a[href]'):
        label = a.get_text(' ', strip=True)
        if (label.startswith(('Power Mac ', 'PowerBook', 'iBook', 'eMac', 'iMac G5'))
            or label in ('iMac', 'iMac (Early 2001)', 'iMac (Summer 2001)', 'iMac (Summer 2000)',
                         'iMac (17 inch, Flat Panel)', 'iMac (17-inch 1GHz)', 'iMac (266 MHz)',
                         'iMac (333 GHz)', 'iMac (Flat Panel)', 'iMac (Slot Loading)', 'iMac (USB 2.0)',
                         'Mac mini', 'Mac mini (Late 2005)')):
            directories.add(a['href'])
    def links(url):
        try:
            soup, digest = page(url)
            urls = {a['href'] for a in soup.select('a[href]')
                    if ('technical specifications' in a.get_text().lower() or a.get_text(strip=True) == 'Tech Specs')
                    and re.fullmatch(r'https://support.apple.com/en-us/\d+', a['href'])}
            return url, urls, digest
        except requests.RequestException as exc:
            failures.append({'url': url, 'error': type(exc).__name__})
            return url, set(), None
    # Additional public Apple search results cover named models absent from the
    # inspected directory's first list; these are observed URLs, not guessed IDs.
    supplemental_specs = ('112184', '112154', '112195', '112315', '112318',
                          '112188', '112196', '112201', '112247', '112189',
                          '112192', '112193', '112200', '112241')
    spec_urls = {'https://support.apple.com/en-us/' + p for p in supplemental_specs}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for url, urls, digest in pool.map(links, sorted(directories)):
            spec_urls.update(urls)
            receipts.append({'url': url, 'sha256': digest, 'linked_specifications': len(urls)})
    def record(url):
        try:
            soup, digest = page(url)
            title = soup.find('h1').get_text(' ', strip=True)
            name = re.sub(r'\s*[:\-]\s*(?:Technical Specifications|Tech Specs).*$', '', title, flags=re.I)
            if 'Dock' in name:
                excluded_accessories.append({'name': name, 'source_url': url})
                return None
            text = soup.get_text('\n', strip=True)
            match = re.search(r'Processor(?::|/Speed)\s*([^\n]+)', text)
            cpu = match.group(1).strip() if match else None
            arch = 'm68k' if cpu and re.search(r'68(?:LC)?0[02346]0', cpu) else 'powerpc' if (cpu and re.search(r'\b(?:60[134]|603e|604e|G[345])\b', cpu)) or 'PowerPC' in text else 'unknown'
            if arch == 'unknown' and re.search(r'\bG[345]\b', name):
                arch = 'powerpc'
            introduced = re.search(r'Introduced:\s*\d+/\d+/(\d{4})', text)
            name_year = re.search(r'\b(19\d{2}|200[0-5])\b', name)
            year = int((introduced or name_year).group(1)) if introduced or name_year else None
            family = next((f for f in ('PowerBook', 'iBook', 'eMac', 'iMac', 'Mac mini', 'Xserve',
                                      'Power Mac', 'Performa', 'Quadra', 'Centris', 'LC') if f in name), 'Macintosh')
            if name.startswith('Twentieth Anniversary'):
                family = 'Twentieth Anniversary Macintosh'
            def field(pattern):
                m = re.search(pattern, text)
                return m.group(1).strip() if m else None
            return {'id': 'legacy-' + url.rsplit('/', 1)[-1], 'name': name, 'family': family,
                    'catalog_level': 'named-model', 'year': year, 'identifiers': [], 'architecture': arch,
                    'era': 'PowerPC' if arch == 'powerpc' else '68k' if arch == 'm68k' else 'Legacy (architecture unverified)',
                    'apple_support': {'status': 'official-historical-specification', 'latest_macos': None,
                        'source_url': url, 'verified_at': str(date.today()), 'macos_27': {
                            'status': 'unknown' if arch == 'unknown' else 'ineligible', 'source_url': OS_URL,
                            'basis': 'macOS 27 lists Apple silicon Macs; this historical architecture is outside that list.'}},
                    'nextcore': {'status': 'unverified', 'architecture_support': 'not-implemented',
                        'summary': 'Historical catalog entry. No Nextcore implementation or physical macOS boot evidence for this architecture.', 'evidence_url': None},
                    'sources': [source(url, 'Apple historical technical specifications'), source(index_url, 'Apple Mac documentation index'), source(OS_URL, 'Apple macOS 27 eligibility')],
                    'variants': [], 'repository_hardware': [], 'technical_specifications': [],
                    'source_sha256': digest,
                    'details': {'cpu': cpu, 'memory': field(r'Min - Max RAM:\s*([^\n]+)'),
                                'storage': field(r'Min\. Int HD Size:\s*([^\n]+)'), 'graphics': None, 'ports': None},
                    'notes': ['Named historical model or configuration from an Apple specification page; not a modern SMBIOS identifier.',
                              'No claim of complete sales-SKU or legacy-model coverage. Null fields are unverified.',
                              'Historical source may contain typographical errors; ambiguous values are not converted into boot contracts.']}
        except (requests.RequestException, AttributeError) as exc:
            failures.append({'url': url, 'error': type(exc).__name__})
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        models = [r for r in pool.map(record, sorted(spec_urls)) if r]
    return models, {'index_url': index_url, 'index_sha256': index_hash, 'directories': receipts,
                    'supplemental_specification_urls': ['https://support.apple.com/en-us/' + p for p in supplemental_specs],
                    'directory_pagination_observation': 'No next/load-more link or button was present in the inspected public directory HTML. Some lists contain 50 specifications; this is not proof of all historical models.',
                    'specifications_discovered': len(spec_urls), 'records': len(models),
                    'excluded_accessories': sorted(excluded_accessories, key=lambda x: x['source_url']),
                    'failures': sorted(failures, key=lambda x: x['url'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = ROOT / 'docs/data/mac-models.json'
    if args.check:
        print(json.dumps(validate(json.loads(output.read_text(encoding='utf-8'))), indent=2))
        return
    if args.cache is None:
        parser.error('--cache outside the public tree is required when generating')
    if args.cache.resolve().is_relative_to(ROOT):
        parser.error('--cache must be outside the repository to keep source HTML out of publication')
    args.cache.mkdir(parents=True, exist_ok=True)
    os_cache = args.cache / 'macos-eligibility.html'
    if args.refresh or not os_cache.exists():
        response = requests.get(OS_URL, timeout=30)
        response.raise_for_status()
        os_cache.write_text(response.text, encoding='utf-8')
    os_html = os_cache.read_text(encoding='utf-8')
    os_text = ' '.join(BeautifulSoup(os_html, 'html.parser').get_text(' ', strip=True).split())
    eligibility = re.search(r'macOS 27 is compatible with these devices\.(.*?)(?:Developers|$)', os_text)
    if not eligibility or not all(name in eligibility.group(1) for name in
            ('MacBook Neo', 'MacBook Air with Apple silicon', 'MacBook Pro with Apple silicon',
             'iMac with Apple silicon', 'Mac mini with Apple silicon', 'Mac Studio', 'Mac Pro with Apple silicon')):
        raise ValueError('Apple eligibility page changed; manually reconcile the policy before regeneration')
    def fetch(pair):
        family, page = pair
        url = 'https://support.apple.com/en-us/' + page
        path = args.cache / (page + '.html')
        if args.refresh or not path.exists():
            response = requests.get(url, timeout=45)
            response.raise_for_status()
            path.write_text(response.text, encoding='utf-8')
        return family, url, path.read_text(encoding='utf-8')
    variants, receipts = [], []
    with ThreadPoolExecutor(max_workers=7) as pool:
        for family, url, html in pool.map(fetch, PAGES.items()):
            parsed = parse_page(family, url, html)
            variants.extend(parsed)
            receipts.append({'url': url, 'sha256': hashlib.sha256(html.encode()).hexdigest(),
                             'variant_count': len(parsed), 'identifier_count': len({i for v in parsed for i in v['identifiers']})})
    spec_urls = sorted({u for v in variants for u in v['technical_specs_urls']})
    with ThreadPoolExecutor(max_workers=8) as pool:
        specifications = dict(zip(spec_urls, pool.map(lambda u: spec_facts(u, args.cache, args.refresh), spec_urls)))
    historic, excluded, digest = repository_records()
    by_identifier = {}
    for v in variants:
        for identifier in v['identifiers']:
            by_identifier.setdefault(identifier, []).append(v)
    models = []
    repo_url = 'https://github.com/26x86/26x86/blob/main/opencore_legacy_patcher/datasets/smbios_data.py'
    for identifier in sorted(set(historic) | set(by_identifier)):
        official = by_identifier.get(identifier, [])
        legacy = historic.get(identifier, [])
        best = official[0] if official else {}
        name = best.get('name') or next((v['name'] for v in legacy if v['name']), identifier)
        arch = architecture(identifier)
        family = best.get('family') or family_of(identifier) or ('Mac Studio' if identifier in ('Mac13,1', 'Mac13,2') else 'MacBook Pro')
        year = best.get('year')
        if year is None and not official:
            match = re.search(r'\b(19\d{2}|20\d{2})\b', name)
            year = int(match.group(1)) if match else None
        urls = list(dict.fromkeys(v['source_url'] for v in official))
        sources = [source(u, 'Apple model identification') for u in urls]
        sources += [source(u, 'Apple technical specifications') for u in dict.fromkeys(u for v in official for u in v['technical_specs_urls'])]
        if legacy:
            sources.append(source(repo_url, 'Repository historical SMBIOS dataset (not independently verified hardware)'))
        sources.append(source(OS_URL, 'Apple macOS 27 eligibility'))
        models.append({'id': identifier.lower().replace(',', '-'), 'name': name, 'family': family,
                       'year': year, 'identifiers': [identifier], 'architecture': arch,
                       'era': 'Apple silicon' if arch == 'apple-silicon' else 'Intel',
                       'apple_support': {'status': 'official-identification' if official else 'repository-only',
                           'latest_macos': best.get('latest_macos'), 'source_url': urls[0] if urls else None,
                           'verified_at': str(date.today()), 'macos_27': {'status': 'eligible' if arch == 'apple-silicon' else 'ineligible',
                               'source_url': OS_URL, 'basis': 'Apple lists only the specified Apple silicon Mac families.'}},
                       'nextcore': {'status': 'unverified', 'summary': 'No model-specific physical installed macOS reboot and desktop evidence.', 'evidence_url': None},
                       'sources': sources, 'variants': official, 'repository_hardware': legacy,
                       'technical_specifications': [specifications[u] for u in dict.fromkeys(u for v in official for u in v['technical_specs_urls'])],
                       'details': {'cpu': best.get('facts', {}).get('chip'), 'memory': None, 'storage': None,
                                   'graphics': None, 'ports': best.get('facts', {}).get('ports') or best.get('facts', {}).get('front_ports')},
                       'notes': ['Model identifiers may cover multiple releases and hardware configurations.',
                                 'Unknown configuration values remain null; technical specifications links are authoritative.',
                                 'Apple OS eligibility does not establish Nextcore compatibility.']})
    neo_url = 'https://www.apple.com/macbook-neo/specs/'
    models.append({'id': 'macbook-neo-2026', 'name': 'MacBook Neo (2026)', 'family': 'MacBook Neo',
                   'year': 2026, 'identifiers': [], 'architecture': 'apple-silicon', 'era': 'Apple silicon',
                   'apple_support': {'status': 'official-product-specification', 'latest_macos': None,
                       'source_url': neo_url, 'verified_at': str(date.today()),
                       'macos_27': {'status': 'eligible', 'source_url': OS_URL, 'basis': 'Explicitly listed by Apple.'}},
                   'nextcore': {'status': 'unverified', 'summary': 'No model-specific physical installed macOS reboot and desktop evidence.', 'evidence_url': None},
                   'sources': [source(neo_url, 'Apple technical specifications'), source(OS_URL, 'Apple macOS 27 eligibility')],
                   'variants': [], 'repository_hardware': [], 'technical_specifications': [],
                   'details': {'cpu': 'Apple A18 Pro; 6 CPU cores', 'memory': '8 GB unified memory',
                       'storage': '256 GB or 512 GB SSD', 'graphics': '5-core GPU; 2408 x 1506 internal display',
                       'ports': 'USB 3 (USB-C), USB 2 (USB-C), 3.5 mm headphone'},
                   'notes': ['Name-based catalog entry: exact model identifier is unverified, not invented.',
                             'Apple OS eligibility does not establish Nextcore compatibility.']})
    for model in models:
        model['catalog_level'] = 'model-identifier' if model['identifiers'] else 'named-model'
    legacy, legacy_coverage = legacy_records(args.cache, args.refresh)
    models.extend(legacy)
    data = {'schema': 'nextcore.mac-model-catalog.v1', 'updated_at': str(date.today()), 'models': models,
            'coverage': {'unit': 'catalog record: model identifier or source-named model', 'apple_pages': receipts,
                         'eligibility_source': {'url': OS_URL, 'sha256': hashlib.sha256(os_html.encode()).hexdigest()},
                         'repository_source_sha256': digest, 'excluded_dataset_keys': excluded,
                         'repository_only_identifiers': sorted(set(historic) - set(by_identifier)),
                         'legacy': legacy_coverage,
                         'gaps': ['No claim of all regional sales SKUs or build-to-order configurations.',
                                  'PowerPC and 68k entries cover discovered Apple specification pages, not every historical variant. Some directory pages expose only a limited initial list.',
                                  'MacBook Neo has a name-based record; its exact model identifier awaits a checked official identification source.',
                                  'Specification capacity mentions span configuration options; exhaustive CPU/GPU/ports and regional SKU normalization remains incomplete.'],
                         'specification_pages': len(specifications),
                         'specification_fetch_failures': [u for u, v in specifications.items() if v['status'] == 'unavailable']}}
    data['coverage']['counts'] = validate(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=True) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(data['coverage']['counts'], indent=2))


if __name__ == '__main__':
    main()
