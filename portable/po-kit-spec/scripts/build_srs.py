#!/usr/bin/env python3
"""Build an SRS (docx) in the IEEE-830 style template from the exported spec markdown.
Usage: build_srs.py <md_dir> <out.docx> [pages.json] [config.json]
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pokit_env; pokit_env.ensure()
import re, sys, os, json, subprocess, copy
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

MD, OUT = sys.argv[1], sys.argv[2]
PAGES = json.load(open(sys.argv[3])) if len(sys.argv) > 3 and os.path.exists(sys.argv[3]) else {}
CFG_PATH = sys.argv[4] if len(sys.argv) > 4 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
CFG = json.load(open(CFG_PATH, encoding='utf-8'))
VI_DOC = CFG.get('lang') == 'vi'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import langpack as L
PK = L.pack(CFG.get('lang', 'en')); SR = PK['srs']              # language of the generated document
SPK = L.pack(CFG.get('spec_lang', CFG.get('lang', 'en')))        # language of the spec text (actor/system wording)
SYS = SPK['system_actor']; USER = SPK['srs']['user']
def S(key, *a): return SR[key] % a if a else SR[key]
PRODUCT = CFG['product']
CLASSIC = CFG.get('template') == 'classic'   # strict classic SRS template: 3 parts, UC table + input data + notes only
VI = CFG.get('lang', 'en') == 'vi'
WHEN_WORD = {'vi': 'Khi', 'fr': 'Quand'}.get(CFG.get('spec_lang', CFG.get('lang', 'en')))
HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'srs_img'); os.makedirs(IMG, exist_ok=True)   # diagram images next to the output
FONT = 'Times New Roman'
GREEN = 'C6EFE0'; ORANGE = 'FBD4B4'; LIGHT = 'E8F7F0'
TEXT_W = 16.0  # cm

# ---------------------------------------------------------------- markdown
def parse_blocks(text):
    lines = text.split('\n'); i = 0; out = []
    while i < len(lines):
        l = lines[i]
        if not l.strip(): i += 1; continue
        m = re.match(r'^(#{1,6}) (.*)', l)
        if m: out.append(('h', len(m.group(1)), m.group(2).strip())); i += 1; continue
        if l.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                r = lines[i].strip()
                cells = [c.strip() for c in re.split(r'(?<!\\)\|', r.strip('|'))]
                if not all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c) or not any(cells):
                    rows.append(cells)
                i += 1
            out.append(('table', rows)); continue
        m = re.match(r'^(\s*)([-*]|\d+\.) (.*)', l)
        if m:
            kind = 'ol' if m.group(2)[0].isdigit() else 'ul'
            items = []
            while i < len(lines):
                mm = re.match(r'^(\s*)([-*]|\d+\.) (.*)', lines[i])
                if not mm: break
                ind = len(mm.group(1))
                if ind >= 2 and items: items[-1][1].append(mm.group(3))
                else:
                    k2 = 'ol' if mm.group(2)[0].isdigit() else 'ul'
                    if k2 != kind and items: break
                    items.append([mm.group(3), []])
                i += 1
            out.append((kind, items)); continue
        m = re.match(r'^\*\*([^*]+?)\*\*\s*(?:[—:-]\s*(.*))?$', l)
        if m and (m.group(2) is None or l.startswith('**' + m.group(1) + '** —')):
            out.append(('label', m.group(1).strip(), (m.group(2) or '').strip())); i += 1; continue
        para = [l]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||\s*[-*] |\s*\d+\. )', lines[i]):
            para.append(lines[i]); i += 1
        out.append(('p', ' '.join(para)))
    return out

def unesc(s):
    return re.sub(r'\\([<>*\[\]_`|#])', r'\1', s)

INLINE = re.compile(r'(\*\*(.+?)\*\*|(?<![\w*\\])\*(?!\s)(.+?)(?<![\s\\])\*(?!\w)|`([^`]+)`|\[([^\]]+)\]\(([^)]+)\))')
def drop_bug_refs(text):
    """classic template has no bug appendix: remove '(BUG-nn)', ', BUG-nn' references"""
    text = re.sub(r'\s*\((?:BUG-\d+(?:[,;]\s*)?)+\)', '', text)
    text = re.sub(r'[,;]\s*BUG-\d+', '', text)
    text = re.sub(r'\(\s*BUG-\d+[,;]\s*', '(', text)
    text = re.sub(r'\s*\bBUG-\d+\b', '', text)
    if VI_DOC: text = text.replace('(differs from current)', '(khác hiện trạng)').replace('differs from current', 'khác hiện trạng')
    return text

def runs(par, text, bold=False, italic=False, size=None):
    text = text.replace('<br>', '\n')
    if CFG.get('template') == 'classic': text = drop_bug_refs(text)
    pos = 0
    for m in INLINE.finditer(text):
        if m.start() > pos: _run(par, text[pos:m.start()], bold, italic, size)
        if m.group(2) is not None: runs(par, m.group(2), True, italic, size)
        elif m.group(3) is not None: runs(par, m.group(3), bold, True, size)
        elif m.group(4) is not None: _run(par, m.group(4), bold, italic, size, mono=True)
        else: _run(par, m.group(5), bold, italic, size, link=m.group(6))
        pos = m.end()
    if pos < len(text): _run(par, text[pos:], bold, italic, size)

def _run(par, t, bold, italic, size, mono=False, link=None):
    t = unesc(t)
    parts = t.split('\n')
    for k, s in enumerate(parts):
        r = par.add_run(s)
        if k < len(parts) - 1: r.add_break()
        r.bold = bold or None; r.italic = italic or None
        if size: r.font.size = Pt(size)
        if mono:
            r.font.name = 'Liberation Mono'; r.font.size = Pt((size or 13) - 2)
            r._element.rPr.rFonts.set(qn('w:hAnsi'), 'Liberation Mono')
        if link: r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x99); r.underline = True

def plain(s):
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s); s = re.sub(r'`([^`]+)`', r'\1', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s); s = re.sub(r'(?<!\w)\*(\S.*?)\*', r'\1', s)
    return unesc(s)

# ---------------------------------------------------------------- docx helpers
doc = Document()
st = doc.styles['Normal']; st.font.name = FONT; st.font.size = Pt(12 if CLASSIC else 13)
st.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
st.paragraph_format.space_after = Pt(6); st.paragraph_format.line_spacing = 1.15
for lvl, size, ital in ([(1, 14, False), (2, 13, True), (3, 13, False), (4, 12, False)] if CLASSIC else [(1, 16, False), (2, 14, True), (3, 13.5, False), (4, 13, False)]):
    h = doc.styles['Heading %d' % lvl]
    h.font.name = FONT; h.font.size = Pt(size); h.font.bold = lvl < 3 or (lvl == 4 and not CLASSIC); h.font.italic = ital
    h.font.color.rgb = RGBColor(0, 0, 0)
    rpr = h.element.get_or_add_rPr(); rf = rpr.find(qn('w:rFonts'))
    if rf is None: rf = OxmlElement('w:rFonts'); rpr.append(rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'): rf.set(qn(a), FONT)
    for a in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
        if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]
    h.paragraph_format.space_before = Pt(14 if lvl == 1 else 10); h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
sec = doc.sections[0]
if CLASSIC:   # US Letter, as in the classic template
    sec.page_height = Cm(27.94); sec.page_width = Cm(21.59)
    sec.left_margin = Cm(3.0); sec.right_margin = Cm(2.5); sec.top_margin = Cm(2.5); sec.bottom_margin = Cm(2.5)
else:
    sec.page_height = Cm(29.7); sec.page_width = Cm(21.0)
    sec.left_margin = Cm(3); sec.right_margin = Cm(2); sec.top_margin = Cm(2); sec.bottom_margin = Cm(2)

def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement('w:shd')
    s.set(qn('w:val'), 'clear'); s.set(qn('w:color'), 'auto'); s.set(qn('w:fill'), color); tcPr.append(s)

def set_borders(tbl):
    tblPr = tbl._tbl.tblPr; b = OxmlElement('w:tblBorders')
    for e in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        x = OxmlElement('w:' + e); x.set(qn('w:val'), 'single'); x.set(qn('w:sz'), '4'); x.set(qn('w:color'), '000000'); b.append(x)
    tblPr.append(b)

def set_widths(tbl, widths):
    tbl.autofit = False
    tblPr = tbl._tbl.tblPr
    lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tblPr.append(lay)
    grid = tbl._tbl.tblGrid
    for k, gc in enumerate(grid.findall(qn('w:gridCol'))):
        if k < len(widths): gc.set(qn('w:w'), str(int(widths[k] * 567)))
    for row in tbl.rows:
        for k, c in enumerate(row.cells):
            if k < len(widths): c.width = Cm(widths[k])

def cell_text(cell, text, bold=False, size=11, align=None, italic=False):
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1); p.paragraph_format.space_before = Pt(1); p.paragraph_format.line_spacing = 1.0
    if align: p.alignment = align
    runs(p, text, bold, italic, size)
    return p

def no_split(row):
    trPr = row._tr.get_or_add_trPr(); x = OxmlElement('w:cantSplit'); trPr.append(x)

def header_repeat(row):
    trPr = row._tr.get_or_add_trPr(); x = OxmlElement('w:tblHeader'); trPr.append(x)

def para(text='', style=None, align=None, bold=False, italic=False, size=None, space_after=None, indent=None):
    p = doc.add_paragraph(style=style)
    if align is not None: p.alignment = align
    elif style is None: p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if text: runs(p, text, bold, italic, size)
    if space_after is not None: p.paragraph_format.space_after = Pt(space_after)
    if indent is not None: p.paragraph_format.left_indent = Cm(indent)
    return p

HEADINGS = []   # (level, text)
def heading(text, level):
    if CLASSIC and re.match(r'^\d+(\.\d+)*\s', text):   # classic template: number, tab, title
        text = re.sub(r'"([^"]*)"', '\u201c\\1\u201d', text)
        num, rest = text.split(' ', 1)
        p = doc.add_heading('', level); p.paragraph_format.tab_stops.add_tab_stop(Cm(0.75 + 0.35 * (level - 1)))
        p.add_run(num + '\t' + rest)
        HEADINGS.append((level, text)); return p
    p = doc.add_heading(text, level)
    HEADINGS.append((level, text)); return p

CAPTIONS = {SR['fig']: [], SR['tbl']: []}
COUNT = {}
def caption(kind, chap, title):
    k = (kind, chap); COUNT[k] = COUNT.get(k, 0) + 1
    if CLASSIC: title = re.sub(r'"([^"]*)"', '\u201c\\1\u201d', title)
    label = '%s %d-%d: %s' % (kind, chap, COUNT[k], title)
    CAPTIONS[kind].append(label)
    p = para(label, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, space_after=10)
    return p

def generic_table(rows, chap=None, title=None, widths=None, size=10.5, header=True):
    if not rows: return
    ncol = max(len(r) for r in rows)
    rows = [r + [''] * (ncol - len(r)) for r in rows]
    t = doc.add_table(rows=len(rows), cols=ncol); set_borders(t)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    if widths is None: widths = auto_widths(rows)
    for i, r in enumerate(rows):
        for j, c in enumerate(r):
            cl = t.cell(i, j)
            cell_text(cl, c, bold=(header and i == 0), size=size,
                      align=WD_ALIGN_PARAGRAPH.CENTER if header and i == 0 else None)
            if header and i == 0: shade(cl, ORANGE)
    if header: header_repeat(t.rows[0])
    set_widths(t, widths)
    if title: caption(SR['tbl'], chap, title)
    else: para('', space_after=2)
    return t

def auto_widths(rows, total=TEXT_W):
    ncol = len(rows[0])
    lens = [max(min(len(plain(r[j])), 120) for r in rows) + 4 for j in range(ncol)]
    lens = [max(l, 8) for l in lens]
    s = sum(lens); w = [total * l / s for l in lens]
    # a column never gets narrower than its longest word (header or cell), so words do not break mid-word
    mins = [max(1.6, 0.26 * min(max((len(x) for r in rows for x in plain(r[j]).split()), default=1), 12) + 0.7) for j in range(ncol)]
    w = [max(x, m) for x, m in zip(w, mins)]; s = sum(w)
    return [x * total / s for x in w]

def render_blocks(blocks, chap=None, cap_tables=False, cap_prefix=''):
    for b in blocks:
        if b[0] == 'p': para(b[1])
        elif b[0] == 'label':
            p = para(b[1] + ('. ' if b[2] else ''), bold=True, italic=True, space_after=4)
            p.paragraph_format.keep_with_next = True
            if b[2]: runs(p, b[2])
        elif b[0] in ('ul', 'ol'):
            for k, (it, sub) in enumerate(b[1]):
                p = para(('%d. ' % (k + 1) if b[0] == 'ol' else '•  ') + it, indent=0.6)
                p.paragraph_format.first_line_indent = Cm(-0.5); p.paragraph_format.space_after = Pt(3)
                for s in sub:
                    q = para('–  ' + s, indent=1.2); q.paragraph_format.first_line_indent = Cm(-0.4)
                    q.paragraph_format.space_after = Pt(2)
        elif b[0] == 'table':
            generic_table(b[1], chap, (cap_prefix or None) if cap_tables else None)
        elif b[0] == 'h':
            p = para(b[2], bold=True, space_after=4); p.paragraph_format.keep_with_next = True

def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ---------------------------------------------------------------- load spec
FILES = CFG['files']  # first = overview tab, then module tabs in order
src = {f: open(os.path.join(MD, f + '.md')).read() for f in FILES}
# The spec keeps canonical English labels (the lint depends on them). The exported document is a PO view:
# statuses in a column, TBD ids, answers in the document language (see po_transform.py).
PO_MODE = CFG.get('po_mode', True)
if PO_MODE:
    import po_transform as PT
    src = {f: PT.transform(t, CFG.get('lang', 'en')) for f, t in src.items()}
# drop byline (date + author mention) under the title
src[FILES[0]] = re.sub(r'^[^\n]*@[^\n]*\n', '', src[FILES[0]], count=1, flags=re.M) if CFG.get('strip_byline', True) else src[FILES[0]]

def split_h2(text):
    secs = []; cur = None; title = None
    for l in text.split('\n'):
        if l.startswith('# '): title = l[2:].strip(); continue
        if l.startswith('## '):
            cur = [l[3:].strip(), []]; secs.append(cur); continue
        if cur is not None: cur[1].append(l)
    return title, [(a, '\n'.join(b)) for a, b in secs]

ROLE_MAP = CFG.get('role_map', {})
def norm_role(r):
    r = r.strip(); return ROLE_MAP.get(r, r)

modules = []
for f in FILES[1:]:
    title, secs = split_h2(src[f])
    num = int(re.match(r'\d+', f).group(0))
    m = {'num': num, 'title': title, 'name': re.sub(r'^\d+\.\s*', '', title), 'secs': secs, 'features': [], 'map': {}, 'appx': []}
    for name, body in secs:
        key = L.match('module_sections', name)
        if key == 'feature_map':
            m['map_blocks'] = parse_blocks(body)
            for b in m['map_blocks']:
                if b[0] == 'table':
                    for r in b[1][1:]:
                        if re.match(r'^\d+\.\d+$', r[0]):
                            m['map'][r[0]] = {'name': r[1], 'screen': r[2], 'roles': [norm_role(x) for x in re.split(r',|/', plain(r[3])) if x.strip()], 'status': r[4]}
        elif key == 'summary': m['summary'] = parse_blocks(body)
        elif key == 'roles': m['roles'] = parse_blocks(body)
        elif re.match(r'^\d+\.\d+ ', name):
            fid, fname = name.split(' ', 1)
            route = ''
            mr = re.search(r'\s*`([^`]+)`\s*$', fname)
            if mr: route = mr.group(1); fname = fname[:mr.start()].strip()
            mr2 = re.search(r'`([^`]+)`', fname)
            if mr2:
                route = route or mr2.group(1); fname = re.sub(r'\s*`[^`]+`', '', fname).strip()
            m['features'].append({'id': fid, 'name': fname, 'route': route, 'blocks': parse_blocks(body)})
        elif key == 'appendix': m['appx'].append((name, parse_blocks(body)))
        else: m.setdefault('other', []).append((name, parse_blocks(body)))
    modules.append(m)

ov_title, ov_secs = split_h2(src[FILES[0]])
class _OV(dict):
    def __missing__(self, k): return []   # tolerate sections the overview tab does not have
OV = _OV({n: parse_blocks(b) for n, b in ov_secs})
def OVK(key):
    """blocks of the overview section for canonical `key` (any language pack; config `sections` may override)"""
    ov = CFG.get('sections', {}).get(key) or (CFG.get('bugs_section') if key == 'bugs' else None)
    n = L.find_section([n for n, _ in ov_secs], key, ov)
    return OV[n] if n else []

# ---------------------------------------------------------------- use case derivation
ACTORS = sorted(CFG['actors'], key=lambda x: -len(x))  # longest first so 'Lab technician' wins over 'Technician'

def sentences(s):
    s = s.strip()
    toks = re.split(r'((?<=[.!?])\s+(?=\S)|;\s+(?=%s\b))' % re.escape(SYS), s)
    parts = [toks[0]]
    for i in range(1, len(toks), 2):          # split only before a capital letter, quote or parenthesis (or '; System')
        sep, nxt = toks[i], toks[i + 1]
        if sep.startswith(';') or nxt[:1].isupper() or nxt[:1] in '(“"': parts.append(nxt)
        else: parts[-1] += sep + nxt
    return [p.strip() for p in parts if p.strip()]

def detect_actor(s):
    pre = ''
    m = re.match(r'^(\([^)]*\)\s*)', s)
    if m: pre = m.group(1); s2 = s[m.end():]
    else: s2 = s
    for a in ACTORS:
        if s2.startswith(a + ' ') or s2.startswith(a + ',') or s2 == a or s2.startswith(a + '.'):
            rest = s2[len(a):].lstrip(' ,')
            rest = rest[:1].upper() + rest[1:] if rest else rest
            return norm_role(a), pre + rest
    if re.search(SPK['system_clause_regex'], s2): return SYS, s
    return None, s

def main_rows(items, primary):
    rows = []
    for it, sub in items:
        actor_prev = None
        for sn in sentences(it):
            a, txt = detect_actor(sn)
            if a is None: a = actor_prev or (rows[-1][0] if rows and rows[-1][0] != SYS else primary)
            if rows and rows[-1][0] == a and actor_prev is not None:
                rows[-1][1] += ' ' + txt
            else: rows.append([a, txt])
            actor_prev = a
        if sub: rows[-1][1] += '\n' + '\n'.join('– ' + x for x in sub)
    return rows

def alt_rows(items):
    rows = []
    for it, sub in items:
        if WHEN_WORD: it = re.sub(r'^When\s+', WHEN_WORD + ' ', it)
        txt = it
        if '→' in it:
            cond, res = [x.strip() for x in it.split('→', 1)]
            a, r2 = detect_actor(res)
            if a is None:
                pos = [(res.find(x), x) for x in ACTORS if res.find(x) >= 0]
                a = norm_role(min(pos)[1]) if pos else SYS
                r2 = res
            txt = cond.rstrip(':') + ': ' + r2[:1].lower() + r2[1:] if r2 and not r2[:2].isupper() else cond + ': ' + r2
        else:
            pos = [(it.find(x), x) for x in ACTORS if it.find(x) >= 0]
            a = norm_role(min(pos)[1]) if pos else SYS
        if sub: txt += '\n' + '\n'.join('– ' + x for x in sub)
        rows.append([a, txt])
    return rows

def group(blocks):
    """split feature blocks by bold labels -> ordered list of (label, intro, blocks)"""
    out = []; cur = ['_', '', []]
    for b in blocks:
        if b[0] == 'label':
            cur = [b[1], b[2], []]; out.append(cur)
        else: cur[2].append(b)
    if cur[0] == '_' and cur[2]: out.insert(0, cur)
    return out

FIELD_HDRS = [p['field_hdr'] for p in L.PACKS.values()]
def bkey(label):
    """canonical block key when `label` is exactly a heading of some language pack, else the raw label"""
    for k in L.CANON['blocks']:
        if label in L.aliases('blocks', k): return k
    return label

# ---------------------------------------------------------------- diagrams
def dot_render(src_dot, name):
    p = os.path.join(IMG, name)
    open(p + '.dot', 'w').write(src_dot)
    subprocess.run(['dot', '-Tpng', '-Gdpi=170', '-o', p + '.png', p + '.dot'], check=True)
    return p + '.png'

def esc(s): return s.replace('"', '\\"')
def wrap(s, n=22):
    words = s.split(); lines = []; cur = ''
    for w in words:
        if len(cur) + len(w) + 1 > n and cur: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    if cur: lines.append(cur)
    return '\\n'.join(esc(x) for x in lines)

ACTOR_IMG = os.path.join(HERE, 'actor.png')
def uc_diagram(name, actors, ucs, edges, title):
    s = ['digraph G {', 'rankdir=LR; nodesep=0.25; ranksep=1.1; splines=true; newrank=true;',
         'node [fontname="Liberation Sans", fontsize=11]; edge [arrowhead=none, color="#333333"];']
    left = actors[:(len(actors) + 1) // 2]; right = actors[(len(actors) + 1) // 2:]
    for i, a in enumerate(actors):
        s.append('a%d [shape=none, image="%s", label="%s", labelloc=b, height=1.6, width=1.4, imagescale=true, fixedsize=true];' % (i, ACTOR_IMG, wrap(a, 16)))
    s.append('subgraph cluster_sys { label="%s"; fontname="Liberation Sans"; fontsize=12; color="#555555"; style=solid;' % esc(title))
    for j, u in enumerate(ucs):
        s.append('u%d [shape=ellipse, style=filled, fillcolor="#FFFFCC", color="#8a7a2a", label="%s", width=2.2];' % (j, wrap(u, 24)))
    s.append('}')
    for (i, j) in edges:
        if actors[i] in left: s.append('a%d -> u%d;' % (i, j))
        else: s.append('u%d -> a%d;' % (j, i))
    s.append('{rank=same; %s}' % ' '.join('a%d' % actors.index(a) for a in left))
    if right: s.append('{rank=same; %s}' % ' '.join('a%d' % actors.index(a) for a in right))
    s.append('}')
    return dot_render('\n'.join(s), name)

def activity_diagram(name, rows, lanes_order):
    lanes = []
    for a, _ in rows:
        if a not in lanes: lanes.append(a)
    s = ['digraph G {', 'rankdir=TB; nodesep=0.3; ranksep=0.32; newrank=true; compound=true;',
         'node [fontname="Liberation Sans", fontsize=10, shape=box, style="rounded,filled", fillcolor="#FFFFCC", color="#8a7a2a"]; edge [color="#333333", arrowsize=0.7];',
         'start [shape=circle, label="", width=0.22, style=filled, fillcolor=black];',
         'end [shape=doublecircle, label="", width=0.16, style=filled, fillcolor=black];']
    for li, lane in enumerate(lanes):
        s.append('subgraph cluster_%d { label="%s"; fontname="Liberation Sans"; fontsize=11; style="filled"; fillcolor="%s"; color="#777777";' % (li, esc(lane), ['#F4F4F4', '#EAF4FB', '#FBF3EA', '#EEF8EE'][li % 4]))
        for k, (a, t) in enumerate(rows):
            if a == lane:
                s.append('n%d [label="%s", width=2.6];' % (k, wrap(plain(t).split('\n')[0][:150], 34)))
        if li == 0: s.append('start;')
        s.append('}')
    s.append('start -> n0;')
    for k in range(len(rows) - 1): s.append('n%d -> n%d;' % (k, k + 1))
    s.append('n%d -> end;' % (len(rows) - 1))
    s.append('}')
    return dot_render('\n'.join(s), name)

def state_diagram(name, lc):
    """lc: {states: {id: label}, edges: [[from,to,label,dashed?]], start: [ids], end: [ids]}"""
    g = ['digraph G { rankdir=TB; nodesep=0.5; ranksep=0.4;',
         'node [fontname="Liberation Sans", fontsize=10.5, shape=box, style="rounded,filled", fillcolor="#FFFFCC", color="#8a7a2a"];',
         'edge [fontname="Liberation Sans", fontsize=9, color="#333333", arrowsize=0.7];',
         'start [shape=circle, label="", width=0.2, style=filled, fillcolor=black];',
         'end [shape=doublecircle, label="", width=0.15, style=filled, fillcolor=black];']
    for sid, lab in lc['states'].items():
        extra = ', fillcolor="#F6D5D5"' if sid in lc.get('bad', []) else ''
        g.append('%s [label="%s"%s];' % (sid, esc(lab).replace('\\n', '\\n'), extra))
    for e in lc['edges']:
        a_, b_ = ('start' if e[0] == 'start' else e[0]), e[1]
        g.append('%s -> %s [label="%s"%s];' % (a_, b_, esc(e[2]) if len(e) > 2 else '', ', style=dashed' if len(e) > 3 and e[3] else ''))
    for sid in lc.get('end', []): g.append('%s -> end;' % sid)
    g.append('}')
    return dot_render('\n'.join(g), name)

def figure(path, chap, title, width=15.5):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    from PIL import Image
    w, h = Image.open(path).size
    wcm = min(width, w / 170 * 2.54); hcm = wcm * h / w
    if hcm > 21: wcm = wcm * 21 / hcm
    p.add_run().add_picture(path, width=Cm(wcm)); p.paragraph_format.keep_with_next = True
    caption(SR['fig'], chap, title)

# ================================================================= DOCUMENT
UCSEQ = {f['id']: n + 1 for n, f in enumerate(f for m in modules for f in m['features'])}
# ---- cover
for _ in range(2): para('')
p = para('', align=WD_ALIGN_PARAGRAPH.LEFT)
pPr = p._p.get_or_add_pPr(); bd = OxmlElement('w:pBdr'); bt = OxmlElement('w:bottom')
bt.set(qn('w:val'), 'single'); bt.set(qn('w:sz'), '36'); bt.set(qn('w:color'), '000000'); bd.append(bt); pPr.append(bd)
COV = WD_ALIGN_PARAGRAPH.RIGHT
if CLASSIC:
    para(S('cover_title'), align=COV, bold=True, size=22, space_after=4)
    para(S('cover_sub'), align=COV, bold=True, size=18, space_after=36)
    para(PRODUCT, align=COV, bold=True, size=22, space_after=4)
    for _l in CFG['cover_lines']: para(_l, align=COV, bold=True, size=22, space_after=4)
else:
    para(S('cover_title'), align=COV, bold=True, size=20, space_after=4)
    para(S('cover_sub'), align=COV, bold=True, size=15, space_after=60)
    para(PRODUCT, align=COV, bold=True, size=19, space_after=6)
    for _l in CFG['cover_lines']:
        para(_l, align=COV, bold=True, size=17, space_after=6)
para('', space_after=30)
if CLASSIC:
    para(S('version') + CFG['version'], align=COV, bold=True, size=16, space_after=30)
    para(CFG['source_line'], align=COV, bold=True, size=16, space_after=4)
    para(CFG['source_detail'], align=COV, bold=True, size=16, space_after=30)
    para(CFG['date_line'], align=COV, bold=True, size=16, space_after=150)
    if CFG.get('cover_footer'): para(CFG['cover_footer'], align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, italic=True, size=12)
else:
    para(S('version') + CFG['version'], align=COV, bold=True, size=14, space_after=30)
    para(CFG['source_line'], align=COV, bold=True, size=13, space_after=4)
    para(CFG['source_detail'], align=COV, size=12, space_after=40)
    para(CFG['date_line'], align=COV, bold=True, size=14)
if CFG.get('revisions') and not CLASSIC:   # change history: [[version, date, change], ...]
    _RH = {'vi': ('Lịch sử thay đổi', ['Phiên bản', 'Ngày', 'Nội dung thay đổi']), 'fr': ('Historique', ['Version', 'Date', 'Modification'])}.get(
        CFG.get('lang', 'en'), ('Revision history', ['Version', 'Date', 'Change']))
    para('', space_after=20)
    para(_RH[0], bold=True, size=12, space_after=4)
    generic_table([_RH[1]] + CFG['revisions'], None, None, widths=[3.0, 3.0, 10.0], size=10)

# ---- new section with page numbers
new = doc.add_section(WD_SECTION.NEW_PAGE)
new.footer.is_linked_to_previous = False
fp = new.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = fp.add_run()
for tag, txt in (('begin', None), (None, ' PAGE '), ('end', None)):
    if tag:
        fc = OxmlElement('w:fldChar'); fc.set(qn('w:fldCharType'), tag); r._r.append(fc)
    else:
        it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = txt; r._r.append(it)
pg = OxmlElement('w:pgNumType'); pg.set(qn('w:start'), '1'); new._sectPr.append(pg)
doc.sections[0].footer.is_linked_to_previous = False

# ---- TOC placeholders (filled in pass 2)
TOC_ANCHOR = para(S('toc'), align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16)
TOC_PARAS = []
def toc_line(text, level, page):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(3); p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.left_indent = Cm(0.5 * (level - 1)); p.paragraph_format.right_indent = Cm(0)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(TEXT_W), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    runs(p, text + '\t' + page, size=12)
    return p
# Body is built first; the TOC paragraphs are generated afterwards and moved after toc_marker.
toc_marker = doc.add_paragraph()
page_break_after_toc = doc.add_paragraph(); page_break_after_toc.add_run().add_break(WD_BREAK.PAGE)
lof_marker = para(S('lof'), align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16)
lof_anchor = doc.add_paragraph()
pb2 = doc.add_paragraph(); pb2.add_run().add_break(WD_BREAK.PAGE)

def bullet(t_, indent=0.6):
    p = para('•  ' + t_, indent=indent); p.paragraph_format.first_line_indent = Cm(-0.5); return p

# ================================================================= 1 INTRODUCTION
heading(S('h1'), 1)
heading(S('h1_1'), 2)
para(CFG['purpose'].replace('{product}', PRODUCT))
para(S('audience'))
heading(S('h1_2'), 2)
for b in OVK('product'):
    if b[0] == 'p' and b[1].startswith(CFG.get('scope_para_prefix', PRODUCT)):
        para(b[1]); break
para(S('scope_modules', len(modules), sum(len(m['features']) for m in modules),
       '; '.join(S('scope_item', m['num'], m['name'], len(m['features'])) for m in modules)))
para(CFG['out_of_scope'])

heading(S('h1_3'), 2)
rows = [SR['gloss_hdr']] + SR['gloss_rows']
for b in OVK('glossary'):
    if b[0] == 'table':
        for r in b[1][1:]:
            rows.append([r[0], r[1] + (S('not_used') + r[2] if len(r) > 2 and r[2] else '')])
generic_table(rows[1:] if CLASSIC else rows, 1, S('gloss_title'), widths=[5.2, 10.8], header=not CLASSIC)

heading(S('h1_4'), 2)
refs = ['IEEE Recommended Practice for Software Requirements Specifications, IEEE Std 830-1998.',
        'IEEE Guide for Developing System Requirements Specifications, IEEE Std 1233-1996.',
        ] + CFG['references']
for b in OVK('compliance'):
    if b[0] == 'table':
        legal = []
        for r in b[1][1:]:
            for x in re.split(r',\s*', plain(r[1])):
                x = re.sub(r'\s*\(.*?\)', '', x).strip()
                if x and x not in legal: legal.append(x)
        refs.append(S('legal_prefix') + '; '.join(legal + CFG.get('legal_extra', [])) + '.')
        break
for r_ in refs:
    if CLASSIC:
        q = para('', indent=1.0); q.paragraph_format.first_line_indent = Cm(-0.6); q.paragraph_format.line_spacing = 2.0
        rr = q.add_run('\u2B07  '); rr.font.color.rgb = RGBColor(0xC0, 0x30, 0x60); rr.font.size = Pt(10); runs(q, r_)
    else: bullet(r_)

heading(S('h1_5'), 2)
para(S('overview_intro').replace('bốn phần', 'ba phần').replace('four parts', 'three parts') if CLASSIC else S('overview_intro'))
for k, t in enumerate(SR['parts'][:3] if CLASSIC else SR['parts']):
    p = para('%d. %s' % (k + 1, t), indent=0.6); p.paragraph_format.first_line_indent = Cm(-0.5)
if not CLASSIC: para(S('uc_explain'))
if not PO_MODE and not CLASSIC:
    para(S('label_intro'), space_after=4)
    for b in OVK('conventions'):
        if b[0] == 'table':
            generic_table(b[1], 1, S('label_title')); break
for b in ([] if CLASSIC else OVK('reading')):
    if b[0] == 'ul':
        for it, _ in b[1]:
            if any(w in it for w in SR['skip_reading_contains']): continue
            bullet(it.replace(*SR['partial_replace']))
page_break()

# ================================================================= 2 FUNCTIONAL REQUIREMENTS
heading(S('h2'), 1)
heading(S('h2_1'), 2)
if CLASSIC:
    _rr = next((b[1][1:] for b in OVK('roles') if b[0] == 'table'), [])
    _names = [plain(r[0]) for r in _rr]
    _and = ' và ' if VI else ' and '
    _lst = ', '.join(_names[:-1]) + _and + _names[-1] if len(_names) > 1 else ''.join(_names)
    para(('Hệ thống gồm có các tác nhân là %s. ' if VI else 'The system has the actors %s. ') % _lst +
         ' '.join('%s: %s.' % (plain(r[0]), (lambda s: s if s[1:2].isupper() else s[:1].lower() + s[1:])(plain(r[1]))) for r in _rr))
else:
    para(S('actors_intro', CFG['uc_permissions'], CFG['external_actors_note']))
    for b in OVK('roles'):
        if b[0] == 'table':
            generic_table(b[1], 2, S('actors_title'), widths=[4.2, 7.8, 4.0]); break

heading(S('h2_2'), 2)
para(S('funcs_intro', len(modules)))
# optional dashboard/overview-screen description: heading '### 3.0 ...' inside the modules section of the overview tab
_dash = CFG.get('dashboard_heading_regex')
if _dash:
    _sec = next((b for n, b in ov_secs if n.startswith(L.aliases('overview', 'modules')[0])), '')
    _mm = re.search(_dash + r'[^\n]*\n(.*?)\n### ', _sec, re.S)
    if _mm:
        para(CFG.get('dashboard_title', S('dash_title')), bold=True, space_after=3)
        for b in parse_blocks(_mm.group(1)):
            if b[0] == 'ul':
                for it, _ in b[1]:
                    q = bullet(it, 1.0); q.paragraph_format.space_after = Pt(2)
for m in (modules if not CLASSIC else []):
    para('%d. %s: ' % (m['num'], m['name']), bold=True, space_after=3)
    summ = next((b[1] for b in m.get('summary', []) if b[0] == 'p'), '')
    para(summ)
    rows = [SR['uc_list_hdr']]
    for f in m['features']:
        mp = m['map'].get(f['id'], {})
        rows.append(['UC-' + f['id'], f['name'], mp.get('screen', f['route']), ', '.join(mp.get('roles', [])), mp.get('status', '')])
    generic_table(rows, 2, S('uc_list_title', m['num'], m['name']), widths=[1.9, 4.3, 4.0, 2.8, 3.0], size=10)
if CLASSIC:
    for m in modules:
        summ = next((b[1] for b in m.get('summary', []) if b[0] == 'p'), '')
        first = sentences(summ)[0] if summ else ''
        p = para('%d. %s: %s' % (m['num'], m['name'], first), indent=0.6); p.paragraph_format.first_line_indent = Cm(-0.5)
        p.paragraph_format.space_after = Pt(3)
para(S('diagram_intro'))

# ---- 2.3 overview diagram
heading(S('h2_3'), 2)
_ovc = CFG.get('overview_diagram', {})
ov_actors = list(_ovc.get('actors') or [])
if not ov_actors:
    for m in modules:
        for f in m['features']:
            for a_ in m['map'].get(f['id'], {}).get('roles', []):
                if a_ not in ov_actors: ov_actors.append(a_)
ov_ucs = _ovc.get('usecases') or ['%d. %s' % (m['num'], m['name']) for m in modules]
role_rows = next((b[1] for b in OVK('roles') if b[0] == 'table'), [[]])
edges = set()
amap = _ovc.get('role_alias', {})
for r in role_rows[1:]:
    a = amap.get(r[0], r[0])
    if a not in ov_actors: continue
    for n in re.findall(r'\b(\d+)\b', r[2]):
        if 1 <= int(n) <= len(ov_ucs): edges.add((ov_actors.index(a), int(n) - 1))
png = uc_diagram('uc_overview', ov_actors, ov_ucs, sorted(edges), PRODUCT)
figure(png, 2, S('ov_fig'), width=15.5)
para(S('ov_note'), italic=True, size=11)

# ---- 2.4 per module decomposition
heading(S('h2_4'), 2)
for k, m in enumerate(modules):
    heading(S('h2_4_n', k + 1, m['name']), 3)
    actors = []
    for f in m['features']:
        for a in m['map'].get(f['id'], {}).get('roles', []):
            if a not in actors: actors.append(a)
    ucs = ['UC-%s %s' % (f['id'], f['name']) for f in m['features']]
    ed = [(actors.index(a), j) for j, f in enumerate(m['features']) for a in m['map'].get(f['id'], {}).get('roles', [])]
    png = uc_diagram('uc_m%d' % m['num'], actors, ucs, ed, '%d. %s' % (m['num'], m['name']))
    figure(png, 2, S('mod_fig', m['name']), width=14.5)
    if m.get('roles') and not CLASSIC:
        para(S('roles_in_module'), bold=True, italic=True, space_after=4)
        render_blocks(m['roles'])

# ---- 2.5 processes
heading(S('h2_5'), 2)
_lc = CFG.get('lifecycle')
_off = 0
def lc_first(s): return s[:1].lower() + s[1:] if SPK['lower_first'] and not s[1:2].isupper() else s
if _lc:
    _off = 1
    heading('2.5.1 ' + _lc['title'], 3)
    m1 = modules[0]
    for b in m1.get('map_blocks', []):
        if b[0] == 'label' and b[1].startswith(_lc['label_prefix']):
            para(b[2].replace(S('lc_strip'), ''))
    png = state_diagram('state_main', _lc)
    figure(png, 2, S('state_fig') + _lc['object'], width=10)

def flow_rows_of(f, primary):
    for lab, intro, bl in group(f['blocks']):
        if bkey(lab) == 'main_flow':
            for b in bl:
                if b[0] == 'ol': return main_rows(b[1], primary)
    return []

for k, m in enumerate(modules):
    heading(S('h2_5_n', k + 1 + _off, lc_first(m['name'])), 3)
    summ = next((b[1] for b in m.get('summary', []) if b[0] == 'p'), '')
    if summ: para(summ)
    for b in m.get('map_blocks', []):
        if b[0] == 'label' and b[2] and not (_lc and b[1].startswith(_lc['label_prefix'])):
            para(b[1] + ': ' + b[2])
        elif b[0] == 'p': para(b[1])
    best = None   # the use case with the longest main flow
    for f in m['features']:
        prim = (m['map'].get(f['id'], {}).get('roles') or [USER])[0]
        rws = flow_rows_of(f, prim)
        if best is None or len(rws) > len(best[1]): best = (f, rws)
    if best and best[1]:
        f, rws = best
        rws = rws[:14]
        para(S('flow_intro', f['id'], f['name'], k + 1))
        png = activity_diagram('act_m%d' % m['num'], rws, None)
        figure(png, 2, S('act_fig', lc_first(f['name'])), width=15.5)

# ================================================================= 2.6 USE CASE SPECS
heading(S('h2_6'), 2)
if not CLASSIC: para(S('uc_intro'))

def uc_table(m, f):
    mp = m['map'].get(f['id'], {})
    roles = mp.get('roles') or [USER]
    g = group(f['blocks'])
    gd = {bkey(lab): (intro, bl) for lab, intro, bl in g}
    desc = gd.get('problem_value', ('', []))[0]
    if not desc:
        desc = ' '.join(b[1] for b in gd.get('problem_value', ('', []))[1] if b[0] == 'p')
    mrows = flow_rows_of(f, roles[0])
    arows = []
    for b in gd.get('alt_flow', ('', []))[1]:
        if b[0] in ('ul', 'ol'): arows += alt_rows(b[1])
        elif b[0] == 'p': arows.append([SYS, b[1]])
    if mrows and mrows[0][0] != SYS:
        trig = mrows[0][0] + ' ' + mrows[0][1][:1].lower() + mrows[0][1][1:]
        trig = sentences(trig)[0]
    else:
        trig = SPK['srs']['trigger_default'] + plain(mp.get('screen', f['route']))
    screen = plain(mp.get('screen', '') or f['route'])
    pre = CFG['precondition']
    dw = SPK['srs']['dialog_words']
    if any(w in screen for w in dw): pre += SPK['srs']['dialog_pre'] + screen.replace(SPK['srs']['dialog_strip'], '') + '.'
    post = ''
    for a, t in reversed(mrows):
        if a == SYS: post = t; break
    if not post and mrows: post = mrows[-1][1]

    t = doc.add_table(rows=0, cols=4); set_borders(t); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    def row_kv(label, value, merge=True):
        r = t.add_row(); c = r.cells
        cell_text(c[0], label, bold=True, size=10.5); shade(c[0], GREEN)
        mc = c[1].merge(c[3]) if merge else c[1]
        cell_text(mc, value, size=10.5); no_split(r)
        return mc
    r = t.add_row(); c = r.cells
    cell_text(c[0], S('r_code'), bold=True, size=10.5); shade(c[0], GREEN)
    cell_text(c[1], ('UC%03d' % UCSEQ[f['id']]) if CLASSIC else 'UC-' + f['id'], size=10.5)
    cell_text(c[2], S('r_name'), bold=True, size=10.5); shade(c[2], GREEN)
    cell_text(c[3], f['name'], size=10.5)
    row_kv(S('r_actor'), ', '.join(roles))
    row_kv(S('r_desc'), desc)
    if not CLASSIC: row_kv(S('r_screen'), screen)
    row_kv(S('r_trigger'), trig)
    row_kv(S('r_pre'), pre)
    def flow(label, rows, alt=False):
        r = t.add_row(); c = r.cells
        cell_text(c[0], label, bold=True, size=10.5); shade(c[0], GREEN)
        mc = c[1].merge(c[3])
        if not rows:
            cell_text(mc, S('none'), size=10.5); return
        inner = mc.add_table(rows=1, cols=3); set_borders(inner)
        for j, h in enumerate(SR['flow_hdr']):
            cell_text(inner.cell(0, j), h, bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER); shade(inner.cell(0, j), ORANGE)
        for k, (a, txt) in enumerate(rows):
            ir = inner.add_row(); ic = ir.cells
            cell_text(ic[0], ('A%d' % (k + 1)) if alt else ('%d.' % (k + 1)), size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
            cell_text(ic[1], a, size=10); cell_text(ic[2], txt, size=10); no_split(ir)
        set_widths(inner, [1.1, 2.4, 8.0])
        # drop the empty paragraph the merged cell keeps above the nested table
        ps = mc.paragraphs
        if ps and not ps[0].text: ps[0]._p.getparent().remove(ps[0]._p)
        _tp = OxmlElement('w:p'); mc._tc.append(_tp)
        if CLASSIC:   # keep the paragraph Word needs after a nested table as small as possible
            _pPr = OxmlElement('w:pPr'); _sp = OxmlElement('w:spacing'); _sp.set(qn('w:before'), '0'); _sp.set(qn('w:after'), '0'); _sp.set(qn('w:line'), '20'); _sp.set(qn('w:lineRule'), 'exact')
            _pPr.append(_sp); _rp = OxmlElement('w:rPr'); _sz = OxmlElement('w:sz'); _sz.set(qn('w:val'), '2'); _rp.append(_sz); _pPr.append(_rp); _tp.append(_pPr)
    flow(S('r_main'), mrows)
    flow(S('r_alt'), arows, alt=True)
    row_kv(S('r_post'), post)
    if not CLASSIC: row_kv(S('r_status'), plain(mp.get('status', S('status_default'))))
    set_widths(t, [3.6, 5.2, 2.6, 4.6])
    caption(SR['tbl'], 2, S('uc_table_title', f['name']))
    return g

CONSUMED = {'problem_value', 'main_flow', 'alt_flow'}
def classic_extras(f, g):
    """classic template: '* Dữ liệu đầu vào' table (STT, field, description, required, validation, example) + '*Ghi chú' with the business rules"""
    gd = {bkey(lab): (intro, bl) for lab, intro, bl in g}
    for tb in [b for b in gd.get('field_spec', ('', []))[1] if b[0] == 'table'][:1]:
        if len(tb[1][0]) < 6 or plain(tb[1][0][0]) not in ('Field', 'Trường', 'Champ', 'Trường dữ liệu'): continue
        para(S('input_intro'), space_after=4).paragraph_format.keep_with_next = True
        rows = [SR['input_hdr'][:5] + (['Ví dụ'] if VI else ['Example'])]
        for n, r in enumerate(tb[1][1:]):
            r = r + [''] * (7 - len(r))
            desc = r[1] + ((S('default_word') + r[4]) if r[4] and r[4] not in ('—', '-') else '')
            rows.append(['%d.' % (n + 1), r[0], desc, r[2], r[5], r[3] if r[3] not in ('—', '-') else ''])
        generic_table(rows, 2, S('input_title', f['name']), widths=[1.2, 2.6, 3.6, 1.6, 3.8, 3.2], size=9.5)
    brs = [b for b in gd.get('business_rules', ('', []))[1] if b[0] in ('table', 'ul')]
    if brs:
        items = []
        for b in brs:
            items += [(r[1], r[2] if len(r) > 2 else '') for r in b[1][1:]] if b[0] == 'table' else [(it, '') for it, _ in b[1]]
        prop = ('đề xuất', 'proposal', 'proposition')
        lines = [plain(x) + (' (%s)' % ('đề xuất' if VI else 'proposed') if any(w in st.lower() for w in prop) else '') for x, st in items]
        for n, ln in enumerate(lines):
            q = para(('*Ghi chú: ' if VI else '*Note: ') + ln if n == 0 else ln, indent=0 if n == 0 else 0.5)
            q.paragraph_format.space_after = Pt(2)
_ucn = 0
for k, m in enumerate(modules):
    if not CLASSIC:
        heading(S('h2_6_m', k + 1, m['num'], m['name']), 3)
        summ = next((b[1] for b in m.get('summary', []) if b[0] == 'p'), '')
        if summ: para(summ)
    for f in m['features']:
        _ucn += 1
        if CLASSIC: heading('2.6.%d %s' % (_ucn, f['name']), 3)
        else: heading(S('h2_6_f', k + 1, f['id'].split('.')[1], f['name'], f['id']), 4)
        g = uc_table(m, f)
        if CLASSIC:
            classic_extras(f, g); continue
        field_done = False
        for lab, intro, bl in g:
            key = bkey(lab)
            if key in CONSUMED: continue
            if key == 'field_spec' and not field_done:
                tb = next((b for b in bl if b[0] == 'table'), None)
                if tb and [plain(x) for x in tb[1][0]] in FIELD_HDRS:
                    field_done = True
                    para(S('input_intro'), space_after=4).paragraph_format.keep_with_next = True
                    rows = [SR['input_hdr']]
                    for n, r in enumerate(tb[1][1:]):
                        r = r + [''] * (7 - len(r))
                        desc = r[1]
                        if r[3] and r[3] not in ('—', '-'): desc += '; ' + r[3]
                        if r[4] and r[4] not in ('—', '-'): desc += S('default_word') + r[4]
                        rows.append(['%d.' % (n + 1), r[0], desc, r[2], r[5], r[6]])
                    generic_table(rows, 2, S('input_title', f['name']), widths=[1.0, 2.6, 3.6, 1.6, 4.0, 3.2], size=9.5)
                    if intro: para(intro)
                    for b in bl:
                        if b is not tb: render_blocks([b])
                    continue
            if lab == '_':
                render_blocks(bl); continue
            name = PK['rename'].get(key, lab)
            p = para(name + ('. ' if intro else ''), bold=True, italic=True, space_after=4)
            p.paragraph_format.keep_with_next = True
            if intro: runs(p, intro)
            render_blocks(bl)
    for name, bl in m.get('other', []):
        para(name, bold=True, italic=True); render_blocks(bl)
page_break()

# ================================================================= 3 NON-FUNCTIONAL
heading(S('h3'), 1)
heading(S('h3_1'), 2)
para(CFG['ui_layout'].replace('{product}', PRODUCT))
if CLASSIC:
    _nav = OVK('navigation'); _navt = next((b[1] for b in _nav if b[0] == 'table'), None)
    for b in _nav:
        if b[0] == 'p' and not b[1].rstrip().endswith(':'): para(b[1])
    if _navt:
        para('Các màn hình chính gồm có:' if VI else 'The main screens are:', space_after=3).paragraph_format.keep_with_next = True
        for r in _navt[1:]:
            q = bullet('%s (module %s)' % (plain(r[1]), plain(r[2])) if len(r) > 2 and plain(r[2]) else plain(r[1])); q.paragraph_format.space_after = Pt(2)
    _cv = [it for b in OVK('conventions') if b[0] == 'ul' for it, _ in b[1]]
    if _cv:
        para('Quy ước chung cho mọi màn hình:' if VI else 'Conventions for all screens:', space_after=3).paragraph_format.keep_with_next = True
        for it in _cv: q = bullet(it); q.paragraph_format.space_after = Pt(2)
    heading(S('h3_2'), 2)
    for b in OVK('compliance'):
        if b[0] == 'ul':
            for it, _ in b[1]: bullet(it)
        elif b[0] == 'p': para(b[1])
    para(S('perm_para') + CFG['uc_permissions'] + '.')
    heading(S('h3_3'), 2)
    for t_ in CFG['constraints'] + CFG.get('dependencies', []) + CFG.get('assumptions', []): bullet(t_)
for b in ([] if CLASSIC else OVK('navigation')):
    if b[0] == 'p': para(b[1])
    elif b[0] == 'table': generic_table(b[1], 3, S('nav_title'), widths=[3.2, 3.6, 5.2, 4.0], size=10)
if not CLASSIC:
    _sec3 = next((b for n, b in ov_secs if n.startswith(L.aliases('overview', 'modules')[0])), '')
    _first = _sec3.strip().split('\n')[0] if _sec3.strip() else ''
    if _first and not _first.startswith('#'):
        para(S('observed_conv') + re.sub(r'^' + re.escape(S('observed_conv_strip')) + r'\s*', '', _first))
    para(S('conv_intro'), bold=True, italic=True, space_after=4)
    conv = OVK('conventions')
    tabs = [b for b in conv if b[0] == 'table']
    if len(tabs) > 1: generic_table(tabs[1][1], 3, S('conv_title'), widths=[3.6, 12.4], size=10.5)
    for b in conv:
        if b[0] == 'p' and not b[1].startswith(S('conv_skip')): para(b[1])

if not CLASSIC: heading(S('h3_2'), 2)
for b in ([] if CLASSIC else OVK('compliance')):
    if b[0] == 'table': generic_table(b[1], 3, S('legal_title'), widths=[3.4, 3.4, 5.2, 4.0], size=10)
    else: render_blocks([b])
if not CLASSIC:
    para(S('perm_para') + CFG['uc_permissions'] + (', ' + CFG['audit_note'] if CFG.get('audit_note') else '') + '.')

    heading(S('h3_3'), 2)
    s1 = OVK('product')
    tabs = [b for b in s1 if b[0] == 'table']
    if tabs: para(S('components_intro'), bold=True, italic=True, space_after=4)
    if tabs: generic_table(tabs[0][1], 3, S('components_title'), widths=[5.0, 5.0, 6.0], size=10.5)
    _cn = tuple(CFG.get('components_note_prefixes', SR['components_note_prefixes']))
    for b in s1:
        if _cn and b[0] == 'p' and b[1].startswith(_cn): para(b[1])
    if len(tabs) > 1: para(S('plans_intro'), bold=True, italic=True, space_after=4)
    if len(tabs) > 1: generic_table(tabs[1][1], 3, CFG.get('plans_title', S('plans_title')), widths=[2.8, 2.8, 6.0, 4.4], size=10)
    _pn = tuple(CFG.get('plans_note_prefixes', SR['plans_note_prefixes']))
    for b in s1:
        if b[0] == 'p' and b[1].startswith(_pn): para(b[1])
    for t_ in CFG['constraints']: bullet(t_)
    _X = {'vi': ('Giả định', 'Phụ thuộc'), 'fr': ('Hypothèses', 'Dépendances')}.get(CFG.get('lang', 'en'), ('Assumptions', 'Dependencies'))
    for _key, _title in (('assumptions', _X[0]), ('dependencies', _X[1])):
        if CFG.get(_key):
            para(_title, bold=True, italic=True, space_after=4)
            for t_ in CFG[_key]: bullet(t_)
if not CLASSIC: page_break()

# ================================================================= 4 APPENDICES
if not CLASSIC:
    heading(S('h4'), 1)
    heading(S('h4_1'), 2)
    for b in OVK('bugs'):
        if b[0] == 'table': generic_table(b[1], 4, S('h4_1_title'), size=9.5)
        else: render_blocks([b])
    heading(S('h4_2'), 2)
    for b in OVK('gaps'):
        if b[0] == 'table': generic_table(b[1], 4, S('h4_2_title'), widths=[0.9, 10.1, 1.8, 3.2], size=10)
        else: render_blocks([b])
    for k, m in enumerate(modules):
        heading(S('h4_n', k + 3, m['name']), 2)
        for name, bl in m['appx']:
            para(re.sub(SR['appendix_strip'], '', name), bold=True, italic=True, space_after=4).paragraph_format.keep_with_next = True
            render_blocks(bl)

# ================================================================= TOC & LOF
def move_after(anchor, paras):
    ref = anchor._p
    for p in paras:
        ref.addnext(p._p); ref = p._p

toc = []
for lvl, text in HEADINGS:
    if lvl > 4: continue
    num = text.split(' ', 1)[0]
    rest = text.split(' ', 1)[1] if ' ' in text else ''
    pg_ = str(PAGES.get('h:' + text, '00'))
    toc.append(toc_line(num + ' ' + rest, lvl, pg_))
toc.insert(0, toc_line(S('lof'), 1, str(PAGES.get('lof', '00'))))
move_after(toc_marker, toc)
lof = []
for kind in (SR['fig'], SR['tbl']):
    for c in CAPTIONS[kind]:
        lof.append(toc_line(c, 1, str(PAGES.get('c:' + c.split(':')[0], '00'))))
    sp = doc.add_paragraph(); lof.append(sp)
move_after(lof_anchor, lof)

doc.core_properties.author = ''; doc.core_properties.last_modified_by = ''
doc.core_properties.title = S('doc_title') + PRODUCT
doc.core_properties.comments = ''
doc.save(OUT)
json.dump({'headings': HEADINGS, 'captions': CAPTIONS, 'lof_title': SR['lof']}, open(OUT + '.meta.json', 'w'), ensure_ascii=False)
print('ok', len(HEADINGS), sum(len(v) for v in CAPTIONS.values()))
