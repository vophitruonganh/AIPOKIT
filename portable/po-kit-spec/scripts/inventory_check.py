#!/usr/bin/env python3
"""Coverage gate: checks the Phase 1 inventory (references/coverage-rules.md) and, with --md, that the spec covers it.
Usage: inventory_check.py <inventory.md> [--md <md_dir>] [--csv out.csv]
Checks:
  - table header has ID | Screen | Path | Kind | Label | Role | Status | Feature
  - every row: unique ID, known Kind, valid Status (no "Not explored"; "Removed: <version>" keeps the id of an element gone from the app), Feature = N.M or "global"
  - with --md: every row's feature exists as "## N.M" in the module files; every feature has >= 1 row;
    every row's Label appears in its feature section (global rows: in 0-*.md or any module file)
Exit 1 on any FAIL. WARN rows do not fail."""
import re, sys, glob, os, csv, collections, unicodedata

KINDS = set('menu submenu tab subtab view filter search button link dropdown option-list column row-action bulk-action '
            'pagination modal drawer form-field detail widget state header footer'.split())
STATUS = re.compile(r'^(Explored|Opened read-only|Safety-blocked:\s*\S.*|Needs data|Needs role:\s*\S.*|Broken:\s*\S.*|Removed:\s*\S.*)$', re.I)
COLS = ['id', 'screen', 'path', 'kind', 'label', 'role', 'status', 'feature']

def norm(s):
    s = unicodedata.normalize('NFC', s).lower()
    s = re.sub(r'[`"“”‘’*]', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def read_rows(path):
    rows, header = [], None
    for ln, line in enumerate(open(path, encoding='utf-8'), 1):
        line = line.strip()
        if not line.startswith('|'): continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if header is None:
            if [norm(c) for c in cells[:8]] == COLS: header = cells
            continue
        if all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c): continue
        if len(cells) < 8: rows.append((ln, None)); continue
        rows.append((ln, dict(zip(COLS, cells[:8]))))
    return header, rows

def sections(md_dir):
    feats, every = {}, ''
    for f in sorted(glob.glob(os.path.join(md_dir, '*.md'))):
        t = open(f, encoding='utf-8').read(); every += '\n' + t
        for sec in re.split(r'^## (?=\d+\.\d+ )', t, flags=re.M)[1:]:
            m = re.match(r'(\d+\.\d+)', sec)
            feats[m.group(1)] = norm(sec.split('\n## Appendix')[0])
    return feats, norm(every)

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    inv = sys.argv[1]; md = out = None
    if '--md' in sys.argv: md = sys.argv[sys.argv.index('--md') + 1]
    if '--csv' in sys.argv: out = sys.argv[sys.argv.index('--csv') + 1]
    header, rows = read_rows(inv)
    res = []  # (level, where, message)
    if header is None:
        print('FAIL  header: table with columns %s not found' % ' | '.join(c.title() for c in COLS)); sys.exit(1)
    ids = collections.Counter(r['id'] for _, r in rows if r)
    feats, every = sections(md) if md else ({}, '')
    used = collections.Counter(); per_status = collections.Counter(); per_screen = collections.Counter()
    for ln, r in rows:
        where = 'line %d' % ln
        if r is None: res.append(('FAIL', where, 'row has fewer than 8 cells')); continue
        where = '%s (line %d)' % (r['id'] or '?', ln)
        if not r['id']: res.append(('FAIL', where, 'empty ID'))
        elif ids[r['id']] > 1: res.append(('FAIL', where, 'duplicate ID'))
        if r['kind'].lower() not in KINDS: res.append(('FAIL', where, 'unknown Kind "%s"' % r['kind']))
        if not r['label']: res.append(('FAIL', where, 'empty Label'))
        if not r['screen']: res.append(('WARN', where, 'empty Screen'))
        st = r['status']
        if not STATUS.match(st): res.append(('FAIL', where, 'Status "%s" is not allowed (never "Not explored"; reasons required after ":")' % st))
        per_status[st.split(':')[0].strip() or '(empty)'] += 1; per_screen[r['screen']] += 1
        ft = r['feature'].strip()
        if ft.lower() != 'global' and not re.fullmatch(r'\d+\.\d+', ft):
            res.append(('FAIL', where, 'Feature "%s" must be N.M or global' % ft)); continue
        if st.lower().startswith('removed'): continue   # gone from the app in a later version: kept for stable ids, not described
        used[ft] += 1
        if md:
            lab = norm(r['label'])
            if ft.lower() == 'global':
                if lab and lab not in every: res.append(('FAIL', where, 'label "%s" (global) not found anywhere in the spec' % r['label']))
            elif ft not in feats: res.append(('FAIL', where, 'feature %s has no "## %s" section' % (ft, ft)))
            elif lab and lab not in feats[ft]: res.append(('FAIL', where, 'label "%s" not described in feature %s' % (r['label'], ft)))
    for ft in sorted(feats, key=lambda x: tuple(map(int, x.split('.')))):
        if not used[ft]: res.append(('FAIL', 'feature ' + ft, 'no inventory row: the feature was not walked, or the inventory is incomplete'))
    for lvl, where, msg in res: print('%-5s %s: %s' % (lvl, where, msg))
    n = sum(1 for _, r in rows if r)
    print('\nRows: %d | screens: %d | %s' % (n, len(per_screen), ', '.join('%s %d' % kv for kv in per_status.most_common())))
    fails = sum(1 for x in res if x[0] == 'FAIL')
    print('FAIL: %d, WARN: %d' % (fails, sum(1 for x in res if x[0] == 'WARN')))
    if out:
        with open(out, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(['level', 'where', 'message']); w.writerows(res)
    sys.exit(1 if fails or n == 0 else 0)

if __name__ == '__main__': main()
