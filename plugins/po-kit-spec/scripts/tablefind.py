"""Fast table finder for the SRS PDF (about 200x faster than PyMuPDF find_tables).

The SRS tables are drawn with ruled borders and filled header cells, so a table is a block of ruling lines.
Row edges are the horizontal rules that start at the table's left edge; cell edges are the vertical rules
inside a row. A nested table (flow steps inside a use case row) is part of the block of its outer table.

Returns objects with .bbox (x0, y0, x1, y1), .row_count and .extract() (rows of cell texts),
the same three things the layout checks read from find_tables.
"""


class _T:
    def __init__(self, page, bbox, ys, vlines):
        self.page, self.bbox, self._ys, self._v = page, bbox, ys, vlines
        self.row_count = max(len(ys) - 1, 1)
        self._rows = None

    def extract(self):
        if self._rows is None:
            words = self.page.get_text('words', clip=self.bbox)
            rows = []
            for k in range(len(self._ys) - 1):
                y0, y1 = self._ys[k], self._ys[k + 1]
                xs = sorted({round(x) for x, a, b in self._v if a <= (y0 + y1) / 2 <= b} | {round(self.bbox[0]), round(self.bbox[2])})
                cells = [''] * max(len(xs) - 1, 1)
                for w in words:
                    cy = (w[1] + w[3]) / 2; cx = (w[0] + w[2]) / 2
                    if not (y0 <= cy <= y1): continue
                    j = next((n for n in range(len(xs) - 1) if xs[n] <= cx <= xs[n + 1]), None)
                    if j is not None: cells[j] = (cells[j] + ' ' + w[4]).strip()
                rows.append(cells)
            self._rows = rows
        return self._rows


def tables(page):
    h, v = [], []          # horizontal (x0, x1, y), vertical (x, y0, y1)
    boxes = []
    for d in page.get_drawings():
        for it in d['items']:
            if it[0] == 'l':
                p, q = it[1], it[2]
                if abs(p.y - q.y) < 1 and abs(p.x - q.x) > 8: h.append((min(p.x, q.x), max(p.x, q.x), (p.y + q.y) / 2))
                elif abs(p.x - q.x) < 1 and abs(p.y - q.y) > 4: v.append(((p.x + q.x) / 2, min(p.y, q.y), max(p.y, q.y)))
            elif it[0] == 're':
                r = it[1]
                if r.height < 1.5 and r.width > 8: h.append((r.x0, r.x1, (r.y0 + r.y1) / 2))
                elif r.width < 1.5 and r.height > 4: v.append(((r.x0 + r.x1) / 2, r.y0, r.y1))
                elif r.width > 8 and r.height > 4: boxes.append((r.x0, r.y0, r.x1, r.y1))
    segs = [(a, y, b, y) for a, b, y in h] + [(x, a, x, b) for x, a, b in v] + boxes
    if not segs: return []
    segs.sort(key=lambda s: s[1])
    blocks = []
    for s in segs:   # merge into blocks: touching in x and in y
        for b in blocks:
            if s[0] <= b[2] + 2 and s[2] >= b[0] - 2 and s[1] <= b[3] + 3 and s[3] >= b[1] - 3:
                b[0], b[1], b[2], b[3] = min(b[0], s[0]), min(b[1], s[1]), max(b[2], s[2]), max(b[3], s[3]); break
        else:
            blocks.append(list(s))
    merged = True
    while merged:    # blocks that grew into each other
        merged = False
        for i in range(len(blocks)):
            for j in range(i + 1, len(blocks)):
                a, b = blocks[i], blocks[j]
                if a[0] <= b[2] + 2 and a[2] >= b[0] - 2 and a[1] <= b[3] + 3 and a[3] >= b[1] - 3:
                    a[:] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    del blocks[j]; merged = True; break
            if merged: break
    out = []
    for b in blocks:
        if b[2] - b[0] < 60 or b[3] - b[1] < 8: continue
        ys = sorted({round(y, 0) for a, c, y in h if b[1] - 1 <= y <= b[3] + 1 and abs(a - b[0]) < 3}
                    | {round(y, 0) for x0, y0, x1, y1 in boxes if abs(x0 - b[0]) < 3 and b[1] - 1 <= y0 <= b[3] + 1 for y in (y0, y1)})
        ys = [y for k, y in enumerate(ys) if k == 0 or y - ys[k - 1] > 2]
        if len(ys) < 2: ys = [b[1], b[3]]
        vl = [(x, a, c) for x, a, c in v if b[0] - 1 <= x <= b[2] + 1 and a >= b[1] - 1 and c <= b[3] + 1]
        out.append(_T(page, tuple(b), ys, vl))
    out.sort(key=lambda t: t.bbox[1])
    return out


def lone_label(page, nxt, foot=80):
    """The last line of `page` is a short bold label (block label, lead-in sentence ending with ':')
    and `nxt` opens with a table: the label was left alone at the bottom. Returns the label text or ''."""
    h = page.rect.height
    lines = [(ln['bbox'], ''.join(s['text'] for s in ln['spans']).strip(), ln['spans'])
             for b in page.get_text('dict')['blocks'] if b.get('type') == 0 for ln in b['lines']]
    lines = [x for x in lines if x[1] and not (x[1].isdigit() and x[0][1] > h - foot)]
    if not lines: return ''
    bb, txt, spans = max(lines, key=lambda x: x[0][3])
    if any(im['bbox'][3] > bb[3] for im in page.get_image_info()): return ''
    if any(t.bbox[3] > bb[3] for t in tables(page)): return ''
    bold = all((s['flags'] & 16) or 'Bold' in s['font'] for s in spans if s['text'].strip())
    if not (len(txt) <= 90 and (bold or txt.endswith(':')) and not txt.endswith('.')): return ''
    ts = tables(nxt)
    if not ts or ts[0].bbox[1] > 110: return ''
    above = [1 for b in nxt.get_text('dict')['blocks'] if b.get('type') == 0 for ln in b['lines']
             if ln['bbox'][3] <= ts[0].bbox[1] + 1 and ''.join(s['text'] for s in ln['spans']).strip()]
    return '' if above else txt
