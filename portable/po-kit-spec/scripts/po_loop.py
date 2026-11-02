"""Shared parsing for the PO loop (po_sheet_export, po_sheet_import, spec_diff).
Reads module files `N-name.md` (canonical English blocks) and returns features with their business rules,
acceptance criteria, test cases and open-question rows. Question ids follow po_transform (TBD-<feature>.<n>);
rows are matched across versions by a key built from the normalized question text, so ids stay stable for the reader."""
import re, glob, os, hashlib, unicodedata

OQ = 'Open questions & assumptions'
SIMPLE = {'Business rules': 'br', 'Acceptance criteria': 'ac'}
OQ_COLS = ['Question', 'Assumption', 'Owner', 'Priority', 'Answer']

def norm(s):
    s = unicodedata.normalize('NFC', s or '').lower()
    s = re.sub(r'[`*"“”‘’]', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def key(question):
    return hashlib.sha1(norm(question).encode('utf-8')).hexdigest()[:10]

def split_row(line):
    return [c.strip() for c in re.split(r'(?<!\\)\|', line.strip().strip('|'))]

def module_files(md_dir):
    return sorted(glob.glob(os.path.join(md_dir, '[1-9]*.md')), key=lambda p: int(re.match(r'(\d+)', os.path.basename(p)).group(1)))

def parse_module(path):
    """-> list of features: {id, title, file, br:{id:text}, ac:{id:text}, tc:{id:row}, oq:[{n,line_no,cells}]}"""
    lines = open(path, encoding='utf-8').read().split('\n')
    feats, f, block = [], None, ''
    i = 0
    while i < len(lines):
        l = lines[i]
        m = re.match(r'^## (\d+\.\d+)\s+(.*)$', l)
        if m:
            f = {'id': m.group(1), 'title': re.sub(r'\s*`[^`]*`\s*$', '', m.group(2)).strip(), 'file': path,
                 'br': {}, 'ac': {}, 'tc': {}, 'oq': [], 'line': i}
            feats.append(f); block = ''; i += 1; continue
        if l.startswith('## '):
            f = None; block = ''; i += 1; continue
        m = re.match(r'^\*\*([^*\n]+)\*\*\s*$', l)
        if m:
            block = m.group(1).strip(); i += 1; continue
        if f is not None:
            if block in SIMPLE:
                mm = re.match(r'^- ([A-Z]+-[\d.]+)[:.]\s*(.*)$', l)
                if mm: f[SIMPLE[block]][mm.group(1)] = mm.group(2)
            elif block == 'Test cases':
                mm = re.match(r'^\|\s*(TC-[\d.]+)\s*\|', l)
                if mm: f['tc'][mm.group(1)] = l
            elif block == OQ and l.startswith('|') and not re.match(r'^\|\s*:?-{3}', l):
                cells = split_row(l)
                if cells and cells[0] not in ('Question',) and not (i + 1 < len(lines) and re.match(r'^\|\s*:?-{3}', lines[i + 1])):
                    while len(cells) < 5: cells.append('')
                    f['oq'].append({'n': len(f['oq']) + 1, 'line_no': i, 'cells': cells})
        i += 1
    return feats

def parse_spec(md_dir):
    out = []
    for p in module_files(md_dir): out.extend(parse_module(p))
    return out

def module_title(path):
    for l in open(path, encoding='utf-8'):
        if l.startswith('# '): return l[2:].strip()
    return os.path.basename(path)

ANSWERED = re.compile(r'^(Verified|Partly verified|Cannot verify|PO decided)\b')
