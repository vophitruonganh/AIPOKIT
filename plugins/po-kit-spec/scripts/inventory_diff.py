#!/usr/bin/env python3
"""Update run: merge a new recon inventory into the previous one so ids never change.
Usage: inventory_diff.py <old inventory.md> <new inventory.md> <out inventory.md> [version]
Rows match on Screen + Path + Kind + Label + Role (normalized). A matched row keeps its old ID and Feature;
a new row gets the next free INV id and keeps the Feature the recon gave it (new features: next free N.M in the module);
an old row missing from the new walk stays with Status "Removed: <version>". Prints added / removed / kept counts
and the features to rewrite (any feature with an added or removed row), so only those go back to Phase 2."""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inventory_check import read_rows, norm, COLS

def key(r): return tuple(norm(r[c]) for c in ('screen', 'path', 'kind', 'label', 'role'))

def main():
    a = sys.argv[1:]
    if len(a) < 3: print(__doc__); sys.exit(2)
    ver = a[3] if len(a) > 3 else 'new version'
    _, old = read_rows(a[0]); _, new = read_rows(a[1])
    old = [r for _, r in old if r]; new = [r for _, r in new if r]
    by_key = collections.defaultdict(list)
    for r in old: by_key[key(r)].append(r)
    nums = [int(m.group(1)) for r in old for m in [re.search(r'(\d+)$', r['id'])] if m]
    nxt = max(nums or [0]) + 1; width = max([len(str(n)) for n in nums] + [3])
    out, matched, added, touched = [], set(), 0, set()
    for r in new:
        o = by_key[key(r)].pop(0) if by_key.get(key(r)) else None
        if o:
            matched.add(o['id']); out.append(dict(r, id=o['id'], feature=o['feature']))
        else:
            out.append(dict(r, id='INV-%0*d' % (width, nxt))); nxt += 1; added += 1; touched.add(r['feature'])
    removed = 0
    for r in old:
        if r['id'] in matched: continue
        if r['status'].lower().startswith('removed'): out.append(r)
        else: out.append(dict(r, status='Removed: %s' % ver)); removed += 1; touched.add(r['feature'])
    out.sort(key=lambda r: int(re.search(r'(\d+)$', r['id']).group(1)) if re.search(r'(\d+)$', r['id']) else 0)
    with open(a[2], 'w', encoding='utf-8') as f:
        f.write('| ' + ' | '.join(c.title() for c in COLS).replace('Id', 'ID') + ' |\n|' + ' --- |' * len(COLS) + '\n')
        for r in out: f.write('| ' + ' | '.join(r[c] for c in COLS) + ' |\n')
    touched.discard('global')
    print('kept %d | added %d | removed %d | features to rewrite: %s' % (len(matched), added, removed,
          ', '.join(sorted(touched, key=lambda x: tuple(int(p) for p in re.findall(r'\d+', x)) or (0,))) or 'none'))

if __name__ == '__main__': main()
