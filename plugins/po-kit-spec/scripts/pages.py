import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pokit_env; pokit_env.ensure()
import pymupdf, json, sys, re
d = pymupdf.open(sys.argv[1]); meta = json.load(open(sys.argv[2])); out = {}
toc = d.get_toc()
body_start = min(p for l, t, p in toc)  # physical page of first heading
for l, t, p in toc: out.setdefault('h:' + re.sub(r'\s+', ' ', t).strip(), p - 1)
kinds = list(meta['captions'])                      # localized caption words, e.g. Figure / Table
caps = [c for k in kinds for c in meta['captions'][k]]
cap_re = re.compile(r'^((%s) \d+-\d+:)' % '|'.join(map(re.escape, kinds)))
for i in range(body_start - 1, d.page_count):
    for line in d[i].get_text().split('\n'):
        m = cap_re.match(line.strip())
        if m and ('c:' + m.group(1)[:-1]) not in out: out['c:' + m.group(1)[:-1]] = i
lof = meta.get('lof_title', '')
for i in range(0, body_start):
    for b in d[i].get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                if s['size'] > 15 and lof and lof in s['text'] and 'lof' not in out: out['lof'] = i
missing = [c for c in caps if 'c:' + c.split(':')[0] not in out]
json.dump(out, open(sys.argv[3], 'w'), ensure_ascii=False)
print('pages', d.page_count, 'missing captions', len(missing), missing[:3], 'lof', out.get('lof'))
