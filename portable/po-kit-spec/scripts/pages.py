import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pokit_env; pokit_env.ensure()
import pymupdf, json, sys, re, collections
d = pymupdf.open(sys.argv[1]); meta = json.load(open(sys.argv[2])); out = {}
toc = d.get_toc()

_TB = {}
def _tables(doc, i, where=None):
    """tables of page i from the ruled lines (tablefind, a few ms per page); cached"""
    if i not in _TB:
        import tablefind
        _TB[i] = tablefind.tables(doc[i])
    return _TB[i]
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
# short tables that the renderer split over two pages: the next build starts them on a new page.
# Kept from earlier runs so the layout converges (build, convert, pages.py: run the loop until nothing new is found)
try: _pj = json.load(open(sys.argv[3]))
except Exception: _pj = {}
prev = _pj.get('table_breaks', [])
dropped = set(_pj.get('table_breaks_dropped', []))   # dropped once: if it is needed again it stays (no oscillation)
breaks = list(prev); n_drop = n_add = 0
pw, ph = d[0].rect.width, d[0].rect.height
def _key(row):   # letters of the first data row, sorted (pdf text order differs from the docx); same as build_srs
    return ''.join(sorted(re.sub(r'\W', '', ''.join(str(c or '') for c in row))))
_OCC = {}
def _occ():   # every table start in page order -> its key with the occurrence number, as build_srs counts them
    if _OCC: return
    seen = collections.Counter()
    for i in range(d.page_count):
        for t in _tables(d, i):
            rows = t.extract()
            if len(rows) < 2 or t.bbox[0] > 100: continue
            k = _key(rows[1]); _OCC[(i, t.bbox)] = k + '#%d' % seen[k]; seen[k] += 1
def tkey(i, t):
    _occ(); return _OCC.get((i, t.bbox), '')
def _bottom(pg):   # lowest content on a page, page number excluded
    ys = [ln['bbox'][3] for b in pg.get_text('dict')['blocks'] if b.get('type') == 0 for ln in b['lines']
          if ''.join(s['text'] for s in ln['spans']).strip() and not (''.join(s['text'] for s in ln['spans']).strip().isdigit() and ln['bbox'][1] > ph - 80)]
    ys += [im['bbox'][3] for im in pg.get_image_info()]
    return max(ys) if ys else 0
# a break that is no longer needed (the table would now fit on the page before) is dropped
for i in range(body_start, d.page_count):
    ts = _tables(d, i, 'top')
    if not ts or ts[0].bbox[1] > 130: continue
    rows = ts[0].extract()
    if len(rows) < 2: continue
    key = tkey(i, ts[0])
    if key in breaks and key not in dropped and (ph - 57 - _bottom(d[i - 1])) > (ts[0].bbox[3] - ts[0].bbox[1]) + 60:
        breaks.remove(key); dropped.add(key); n_drop += 1
for i in range(body_start - 1, d.page_count - 1):
    a = _tables(d, i, 'bot')
    if not a: continue
    b = _tables(d, i + 1, 'top')
    if not a or not b: continue
    ta, tb = a[-1], b[0]
    if ta.bbox[0] > 100 or tb.bbox[0] > 100: continue                       # nested (flow steps): may continue
    if ta.bbox[3] < ph - 120 or tb.bbox[1] > 110: continue
    if ta.row_count + tb.row_count > 10: continue
    if (ta.bbox[3] - ta.bbox[1]) + (tb.bbox[3] - tb.bbox[1]) > 0.35 * ph: continue
    rows = ta.extract()
    if len(rows) < 2: continue
    # same rules as style_check L10: text above the next-page part means it is another table; use case tables continue by design
    above = [ln for bl in d[i + 1].get_text('dict')['blocks'] if bl.get('type') == 0 for ln in bl['lines']
             if ln['bbox'][3] <= tb.bbox[1] + 1 and ''.join(s['text'] for s in ln['spans']).strip()]
    if above: continue
    try: nxt = tb.extract()
    except Exception: nxt = []
    cells = ' '.join(str(c) for r in rows + nxt for c in r if c).replace('\n', ' ')
    if any(w in cells for w in ('Luồng sự kiện', 'Hậu điều kiện', 'Trạng thái hiện', 'Main flow', 'Postcondition', 'Alternate flow')): continue
    if nxt and not (nxt[0][0] or '').strip(): continue
    key = tkey(i, ta)
    if key and key not in breaks: breaks.append(key); n_add += 1
# a block label or lead-in line left alone at a page bottom, its table on the next page: the next build starts the label with the table
import tablefind as _tf
for i in range(body_start - 1, d.page_count - 1):
    if _tf.lone_label(d[i], d[i + 1]):
        nt = _tables(d, i + 1)
        key = tkey(i + 1, nt[0]) if nt else ''
        if key and key not in breaks: breaks.append(key); n_add += 1
out['table_breaks'] = breaks
out['table_breaks_dropped'] = sorted(dropped)
# headings left alone at the bottom of a page (fewer than 2 lines after them): the next build starts them on a new page
try: hprev = json.load(open(sys.argv[3])).get('heading_breaks', [])
except Exception: hprev = []
hb = list(hprev)
for l, t, p in toc:
    if p < body_start or p >= d.page_count: continue
    pg = d[p - 1]; key = re.sub(r'\s+', ' ', t).strip()
    lines = sorted([ln for b in pg.get_text('dict')['blocks'] if b.get('type') == 0 for ln in b['lines']
                    if ''.join(s['text'] for s in ln['spans']).strip()], key=lambda ln: ln['bbox'][1])
    hit = [ln for ln in lines if re.sub(r'\s+', ' ', ''.join(s['text'] for s in ln['spans'])).strip()[:30] == key[:30]]
    if not hit: continue
    y = hit[0]['bbox'][3]
    below = [ln for ln in lines if ln['bbox'][1] > y - 1 and not (''.join(s['text'] for s in ln['spans']).strip().isdigit() and ln['bbox'][1] > ph - 80)]
    imgs = [im for im in pg.get_image_info() if im['bbox'][1] > y - 1]
    if len(below) < 2 and not imgs and y > ph * 0.6 and key not in hb: hb.append(key)
out['heading_breaks'] = hb
missing = [c for c in caps if 'c:' + c.split(':')[0] not in out]
moved = sum(1 for k, v in out.items() if not k.startswith('table_breaks') and k != 'heading_breaks' and _pj.get(k) != v)   # page numbers that changed since the last build
json.dump(out, open(sys.argv[3], 'w'), ensure_ascii=False)
print('pages', d.page_count, 'missing captions', len(missing), missing[:3], 'lof', out.get('lof'), 'table breaks', len(breaks), '(+%d)' % n_add if not n_drop else '(+%d -%d)' % (n_add, n_drop), 'heading breaks', len(hb), '(+%d)' % (len(hb) - len(hprev)), 'moved', moved)
