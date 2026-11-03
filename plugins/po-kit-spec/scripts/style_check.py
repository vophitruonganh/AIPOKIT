#!/usr/bin/env python3
"""Wording, format and page-layout gate.

Usage:
  style_check.py <md_dir> <config.json>                       wording checks on the spec (W1-W12), before the build
  style_check.py --srs <file.docx> <file.pdf> <md_dir> <config.json>
                                                              format (F1-F12) and layout (L1-L14) checks on the export
  style_check.py --fix <md_dir> <config.json>                 the same, after fixing what has one right answer (quotes, tone marks, "trên dev")
Options: --csv out.csv   write every finding;  --rules .po-kit/standards.md  (optional overrides, see below)

Each finding: level (FAIL / WARN), code, place, text, hint. Exit 1 when any FAIL.
Overrides in standards.md (all optional), one per line:
  style.banned: <phrase>            extra banned phrase (W1)
  style.allow: <phrase>             a phrase that is never reported
  style.off: W7                     switch a check off
  style.fail: W5                    raise a WARN check to FAIL
  style.max_words: 35               sentence length limit (W7)
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pokit_env; pokit_env.ensure()
import re, sys, os, glob, json, csv, collections

# ------------------------------------------------------------------ rules
BANNED_META = [   # W1: how the survey was done
    r'khảo sát chỉ đọc', r'tài khoản khảo sát', r'Chrome của người dùng', r'số bản ghi TEST',
    r'quan sát môi trường', r'(?:lúc|ngày|tháng|khi|chưa) khảo sát', r'theo brief', r'read-only survey',
    r'mở chỉ đọc', r'(?-i:(?:^|(?<=\. ))Không (?:bấm|lưu|gửi|đặt|gọi) ["“][^.;|]*, không )', r'được khảo sát', r'bị chặn khi', r'[Cc]hỉ khảo sát', r'cấm gửi dữ liệu', r'trong brief', r'phạm vi brief', r'^## (?:Appendix|Phụ lục) \w — (?:Environment|Môi trường)', r'Quan sát ngày [^,]*, chỉ đọc', r'chưa đối chiếu mã nguồn', r'`source/', r'kiểm chứng trên môi trường', r'test account', r"user's Chrome", r'TEST records created', r'at survey time', r'during the survey',
    r'\b(?:chưa|không) (?:bấm|bấm thử)\b(?! được)(?! vào được)', r'\bchưa thử\b', r'vì chưa gửi', r'TEST booking', r'\bbrief\b(?! description)', r'không xem được hộp thư', r'\bnot clicked\b', r'did not click', r'not tried']
TESTDATA = r'ngân sách TEST|(?:trên |với |dùng )?(?:hồ sơ|bản ghi|bookmark|lịch khám|lịch) TEST\b'   # W1 outside test cases and acceptance criteria (test data is fine there)
UIFRAMEWORK = r'\b(?:nz|ant|mat|mui|chakra|el)-[a-z]+(?:-[a-z]+)*\b'   # W13: class names of a UI framework (implementation detail)
BANNED_STATUS = [  # W2: document status / audience
    r'as-is', r'bản để PO xác nhận', r'để PO xác nhận', r'chưa phải spec', r'draft for the PO', r'not yet a spec']
PLACEHOLDER = r'(?-i:\b(?:TODO|TBD|FIXME|XXX)\b(?!-))|\?\?\?|lorem ipsum'
HOST = r'\b(?:[a-z0-9-]+\.)*(?:[a-z0-9-]*(?:dev|staging|stg|uat|test|sandbox|local)[a-z0-9-]*)\.(?:[a-z]{2,}\.)?(?!(?:txt|pdf|png|jpe?g|csv|json|md|docx?|xlsx?|svg|zip)\b)[a-z]{2,}\b|\b\d{1,3}(?:\.\d{1,3}){3}\b|localhost'
LOCALPATH = r'(?<![\w/])/(?:mnt|Users|home|tmp)/[\w./-]+'
ENVWORD = r'(?i)\btrên dev\b|hiện trạng dev|(?:host|route|dữ liệu|cấu hình|ở lại) dev\b|môi trường dev|\b(?:app|api|site|form) dev\b|\btừ dev\b|(?<!Status )\bon dev\b|dev environment'
ENDPOINT = r'\b(?:GET|POST|PUT|PATCH|DELETE)\s+/|/api/|\bcis/v\d'
LEGAL = r'\b(Nghị định|Thông tư|Luật|Decree|Circular)\b'
TONE = {'óa': 'oá', 'òa': 'oà', 'ỏa': 'oả', 'õa': 'oã', 'ọa': 'oạ', 'óe': 'oé', 'òe': 'oè', 'ỏe': 'oẻ', 'õe': 'oẽ', 'ọe': 'oẹ',
        'úy': 'uý', 'ùy': 'uỳ', 'ủy': 'uỷ', 'ũy': 'uỹ', 'ụy': 'uỵ'}
LEVEL = {'W1': 'FAIL', 'W2': 'FAIL', 'W3': 'FAIL', 'W4': 'FAIL', 'W5': 'WARN', 'W6': 'FAIL', 'W7': 'WARN', 'W8': 'WARN',
         'W9': 'WARN', 'W10': 'FAIL', 'W11': 'WARN', 'W12': 'WARN', 'W13': 'WARN',
         'F1': 'FAIL', 'F2': 'FAIL', 'F3': 'FAIL', 'F4': 'FAIL', 'F5': 'FAIL', 'F6': 'WARN', 'F7': 'FAIL', 'F8': 'FAIL', 'F9': 'FAIL',
         'F10': 'FAIL', 'F11': 'FAIL', 'F12': 'FAIL', 'F13': 'WARN', 'F14': 'FAIL',
         'L1': 'FAIL', 'L2': 'FAIL', 'L3': 'FAIL', 'L4': 'WARN', 'L5': 'FAIL', 'L6': 'FAIL', 'L7': 'FAIL', 'L9': 'FAIL',
         'L10': 'WARN', 'L11': 'WARN', 'L12': 'WARN', 'L13': 'FAIL', 'L14': 'WARN', 'L15': 'WARN', 'L16': 'WARN'}
OPT = {'max_words': 35, 'off': set(), 'allow': [], 'banned': []}
OUT = []


def add(code, place, text, hint=''):
    if code in OPT['off']: return
    if any(a.lower() in text.lower() for a in OPT['allow']): return
    OUT.append((LEVEL.get(code, 'WARN'), code, place, text.strip()[:160], hint))


def load_rules(path):
    if not path or not os.path.exists(path): return
    for l in open(path, encoding='utf-8'):
        m = re.match(r'\s*style\.(\w+):\s*(.+?)\s*$', l)
        if not m: continue
        k, v = m.groups()
        if k == 'banned': OPT['banned'].append(re.escape(v))
        elif k == 'allow': OPT['allow'].append(v)
        elif k == 'off': OPT['off'].add(v.upper())
        elif k == 'fail': LEVEL[v.upper()] = 'FAIL'
        elif k == 'max_words': OPT['max_words'] = int(v)


# ------------------------------------------------------------------ md (wording)
def sections(text):
    """yield (kind, title, body): kind = feature | appendix | other"""
    parts = re.split(r'^(## .*)$', text, flags=re.M)
    yield 'other', '', parts[0]
    for i in range(1, len(parts), 2):
        h = parts[i][3:].strip(); b = parts[i + 1] if i + 1 < len(parts) else ''
        kind = 'feature' if re.match(r'\d+\.\d+ ', h) else 'appendix' if re.match(r'(Appendix|Phụ lục)', h, re.I) else 'other'
        yield kind, h, b


def tone_norm(s):
    s = s.lower()
    for old, new in TONE.items(): s = s.replace(old, new)
    return s


def inventory_labels(md_dir):
    inv = os.path.join(os.path.dirname(os.path.abspath(md_dir.rstrip('/'))), 'inventory.md')
    labels = set()
    if os.path.exists(inv):
        rows = [l for l in open(inv, encoding='utf-8') if l.startswith('|')]
        if rows:
            head = [c.strip().lower() for c in rows[0].strip('|\n').split('|')]
            k = head.index('label') if 'label' in head else None
            for r in rows[2:]:
                cells = [c.strip() for c in r.strip('|\n').split('|')]
                if k is not None and k < len(cells):
                    for q in re.findall(r'"([^"]+)"', cells[k]) or [cells[k]]: labels.add(q.strip())
    return labels


def label_mask(md_dir):
    """Regex matching inventory labels whose tone marks differ between old (hóa) and new (hoá) style: the app spells them its own way
    and inventory_check needs them verbatim, so W12 neither counts nor rewrites them."""
    ls = [l for l in inventory_labels(md_dir) if any(o in l.lower() or n in l.lower() for o, n in TONE.items())]
    return re.compile('|'.join(re.escape(l) for l in sorted(ls, key=len, reverse=True))) if ls else None


def check_md(md_dir, cfg):
    LM = label_mask(md_dir)
    files = sorted(glob.glob(os.path.join(md_dir, '*.md')))
    texts = {os.path.basename(f): open(f, encoding='utf-8').read() for f in files}
    labels = inventory_labels(md_dir)
    actors = [a for a in cfg.get('actors', []) if a[:1].isupper() and ' ' not in a.strip() or len(a.split()) <= 3]
    glossary_bad = []
    tone_seen = collections.defaultdict(lambda: collections.Counter())
    for name, t in texts.items():
        # glossary "do not use" column, if the spec has one
        for m in re.finditer(r'^\|(.+)\|\s*$', t, re.M):
            pass
        g = re.search(r'^## (Standard glossary|Thuật ngữ chuẩn).*?(?=^## )', t, re.M | re.S)
        if g:
            rows = [l for l in g.group(0).split('\n') if l.startswith('|')]
            if rows:
                head = [c.strip().lower() for c in rows[0].strip('|').split('|')]
                for key in ('do not use', 'không dùng'):
                    if key in head:
                        k = head.index(key)
                        for r in rows[2:]:
                            c = r.strip('|').split('|')
                            if k < len(c): glossary_bad += [x.strip() for x in re.split(r'[,;/]', c[k]) if x.strip()]
    for key in ('cover_lines', 'revisions', 'purpose', 'date_line', 'product', 'out_of_scope', 'references', 'assumptions', 'constraints', 'dependencies', 'ui_layout', 'external_actors_note'):
        flat = json.dumps(cfg.get(key, ''), ensure_ascii=False)
        for p in BANNED_META + BANNED_STATUS + OPT['banned'] + [ENVWORD, r'[Kk]hảo sát', r'tài khoản (?:bệnh nhân|Admin|test)']:
            for m in re.finditer(p, flat, re.I): add('W1', 'config.json:' + key, flat, 'bìa và lịch sử thay đổi không nói cách khảo sát')
        for m in re.finditer(HOST + '|' + LOCALPATH, flat, re.I): add('W3', 'config.json:' + key, m.group(0), 'không ghi host / đường dẫn máy')
    quotes = collections.Counter()
    for name, t in texts.items():
        lines = t.split('\n')
        quotes['"'] += t.count('"'); quotes['“'] += t.count('“')
        sec_of_line = []
        cur = ('other', '')
        for l in lines:
            if l.startswith('## '):
                h = l[3:].strip()
                cur = ('feature' if re.match(r'\d+\.\d+ ', h) else 'appendix' if re.match(r'(Appendix|Phụ lục)', h, re.I) else 'other', h)
            sec_of_line.append(cur)
        in_code = False
        for i, l in enumerate(lines):
            if l.startswith('```'): in_code = not in_code; continue
            if in_code: continue
            place = '%s:%d' % (name, i + 1)
            kind, h = sec_of_line[i]
            for p in BANNED_META + OPT['banned']:
                for m in re.finditer(p, l, re.I): add('W1', place, '«%s» | %s' % (m.group(0), l[max(0, m.start() - 60):m.end() + 40]), 'bỏ câu mô tả cách khảo sát')
            for p in BANNED_STATUS:
                for m in re.finditer(p, l, re.I): add('W2', place, l, 'bỏ câu về trạng thái tài liệu')
            if not re.match(r'(?:\| TC-|- AC-|\| AC-)', l):
                for m in re.finditer(TESTDATA, l, re.I): add('W1', place, '«%s» | %s' % (m.group(0), l[max(0, m.start() - 60):m.end() + 40]), 'bỏ câu mô tả dữ liệu dùng khi khảo sát')
            for m in re.finditer(UIFRAMEWORK, re.sub(r'`[^`]*`', '', l)): add('W13', place, '«%s» | %s' % (m.group(0), l[max(0, m.start() - 60):m.end() + 30]), 'tên class của thư viện giao diện: mô tả hành vi bằng lời')
            for m in re.finditer(HOST, l, re.I):
                if kind == 'feature': add('W3', place, m.group(0) + ' | ' + l, 'viết đường dẫn dạng /route, bỏ host')
                else:
                    OUT.append(('WARN', 'W3', place, (m.group(0) + ' | ' + l)[:160], 'host môi trường trong bảng thành phần / phụ lục'))
            for m in re.finditer(LOCALPATH, l): add('W3', place, m.group(0), 'đường dẫn máy cục bộ không được vào spec')
            for m in re.finditer(ENVWORD, l): add('W3', place, m.group(0) + ' | ' + l, 'không nhắc môi trường; viết "app cùng môi trường" hoặc bỏ')
            for w in glossary_bad:
                if re.search(r'(?<!\w)%s(?!\w)' % re.escape(w), l) and not l.startswith('|'): add('W4', place, w + ' | ' + l, 'dùng thuật ngữ chuẩn')
            for m in (re.finditer(ENDPOINT, l) if kind == 'feature' else []): add('W6', place, '«%s» | %s' % (m.group(0), l[max(0, m.start() - 60):m.end() + 50]), 'tên endpoint chỉ ghi ở Phụ lục A'); break
            if re.search(PLACEHOLDER, l, re.I) and 'Unverified' not in l: add('W10', place, l, 'điền nội dung hoặc chuyển thành câu hỏi mở')
            if re.search(LEGAL, l) and not re.search(r'Observed|Inferred|PO proposal|PO decided|LEGAL REVIEW|Unverified', l):
                add('W11', place, l, 'gắn nhãn nguồn hoặc [LEGAL REVIEW NEEDED]')
            if kind == 'feature' and labels:
                for m in re.finditer(r'(?:[Bb]ấm|[Cc]lick|[Tt]ap|[Pp]ress)\s+"([^"]{2,40})"', l):
                    q = m.group(1)
                    if re.search(r'Inferred|Unverified|PO proposal|[Vv]erified|Cannot verify', l): continue   # label read from code, proposed, or an answer note: not in the inventory
                    nq = tone_norm(q)
                    if not any(nq in tone_norm(x) or tone_norm(x) in nq for x in labels if len(x) > 2):
                        add('W5', place, '"%s"' % q, 'nhãn không có trong inventory; kiểm lại chữ hoa, dấu')
            if not l.startswith('|') and not l.startswith('#'):
                body = re.sub(r'"[^"]*"|“[^”]*”', 'Q', re.sub(r'`[^`]*`|\([^)]*\)', '', l.lstrip('-* 0123456789.')))   # quoted UI text counts as one word
                for s in re.split(r'(?<=[.!?])\s+', body):
                    n = len(s.split())
                    if s.count('→') >= 4: n -= sum(len(x.split()) for x in s.split('→')[1:])   # a step chain counts as one item
                    elif s.count(',') >= 5: n -= sum(len(x.split()) for x in s.split(':', 1)[-1].split(',')[1:])   # an enumeration counts as one item
                    if n > OPT['max_words']: add('W7', place, s, 'câu %d từ, tách thành câu ngắn (≤%d)' % (n, OPT['max_words']))
            if kind == 'feature' and re.match(r'\d+\. ', l):   # the actor that starts a flow step is written as in the role table
                for a in actors:
                    if a[:1].isupper() and len(a) > 3:
                        for m in re.finditer(r'^\d+\. %s(?!\w)' % re.escape(a.lower()), l):
                            add('W8', place, l, 'viết tên vai trò đúng như bảng vai trò: "%s"' % a)
            for w in re.findall(r'\w+', re.sub(r'"[^"]*"|“[^”]*”|`[^`]*`', ' ', LM.sub(' ', l) if LM else l)):
                lw = w.lower()
                for old, new in TONE.items():
                    if old in lw: tone_seen[lw.replace(old, new)]['old:' + lw] += 1
                    elif new in lw: tone_seen[lw]['new:' + lw] += 1
    if quotes['"'] and quotes['“']: add('W9', md_dir, 'trộn " (%d) và “ (%d)' % (quotes['"'], quotes['“']), 'dùng một kiểu ngoặc kép')
    for base, c in tone_seen.items():
        if len(c) > 1: add('W12', md_dir, ' / '.join('%s (%d)' % (k.split(':', 1)[1], v) for k, v in c.items()), 'thống nhất một cách bỏ dấu')
    return texts


# ------------------------------------------------------------------ srs (format + layout)
def _xtext(el):   # visible text of an XML element (w:t only; itertext repeats text on these elements)
    return ''.join(x.text or '' for x in el.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))

_TB = {}
def _tables(doc, i, where=None):
    """tables of page i from the ruled lines (tablefind, a few ms per page); cached"""
    if i not in _TB:
        import tablefind
        _TB[i] = tablefind.tables(doc[i])
    return _TB[i]


def check_srs(docx_path, pdf_path, md_dir, cfg):
    from docx import Document
    from docx.shared import Emu
    from docx.oxml.ns import qn
    import pymupdf
    doc = Document(docx_path); pdf = pymupdf.open(pdf_path)
    sec = doc.sections[-1]
    PT = 12700
    lm, rm, tm, bm = (sec.left_margin / PT, sec.right_margin / PT, sec.top_margin / PT, sec.bottom_margin / PT)
    pw, ph = sec.page_width / PT, sec.page_height / PT
    text_w = pw - lm - rm
    # ---------------- F1 heading numbering
    heads = []
    for p in doc.paragraphs:
        s = p.style.name if p.style is not None else ''
        if s.startswith('Heading'):
            m = re.match(r'(\d+(?:\.\d+)*)[\s\t]', p.text)
            heads.append((int(s.split()[-1]) if s.split()[-1].isdigit() else 1, p.text.strip(), m.group(1) if m else None))
    prev = []
    for lvl, t, num in heads:
        if not num: continue
        parts = [int(x) for x in num.split('.')]
        if prev:
            ok = False
            for k in range(min(len(prev), len(parts))):
                if parts[:k] == prev[:k] and parts[k] == prev[k] + 1 and len(parts) == k + 1: ok = True
            if len(parts) == len(prev) + 1 and parts[:-1] == prev and parts[-1] == 1: ok = True
            if not ok and len(parts) <= len(prev) + 1:
                k = len(parts) - 1
                if parts[:k] == prev[:k] and parts[k] == prev[k] + 1: ok = True
            if not ok and len(parts) == 1 and parts[0] == prev[0] + 1: ok = True
            if not ok: add('F1', 'heading', '%s sau %s' % (num, '.'.join(map(str, prev))), 'đánh số mục bị nhảy hoặc lặp')
        prev = parts
    # ---------------- F2 captions
    meta_p = docx_path + '.meta.json'
    caps = json.load(open(meta_p))['captions'] if os.path.exists(meta_p) else {}
    for t, pt in (json.load(open(meta_p)).get('small_text', []) if os.path.exists(meta_p) else []):
        add('L16', t[:60], 'chữ trong hình chỉ còn %.1f pt khi in' % pt, 'tách hình hoặc rút gọn nhãn (diagram_check: ≤25 nút)')
    for kind, lst in caps.items():
        seen = collections.defaultdict(list)
        for c in lst:
            m = re.match(r'\S+ (\d+)-(\d+):', c)
            if m: seen[int(m.group(1))].append(int(m.group(2)))
            else: add('F2', kind, c, 'chú thích sai mẫu')
        for ch, ns in seen.items():
            if ns != list(range(1, len(ns) + 1)): add('F2', kind, 'chương %d: %s' % (ch, ns[:12]), 'số hình/bảng không liên tục')
    # ---------------- page texts, printed numbers
    pages = [p.get_text('text') for p in pdf]
    def printed(i):
        ls = [x.strip() for x in pages[i].strip().split('\n') if x.strip()]
        return ls[-1] if ls and ls[-1].isdigit() else None
    def pg(i):   # the page number printed in the footer (what the reader sees), else the pdf page
        return 'trang %s' % printed(i) if printed(i) else 'trang pdf %d' % (i + 1)
    # ---------------- F3/F4 toc lines and links
    toc_pages = [i for i, t in enumerate(pages[:15]) if re.search(r'\.{5,}\s*\d+|\.{5,}\s*00', t)]
    for i in toc_pages:
        if re.search(r'\.{3,}\s*00\b', pages[i]): add('F3', pg(i), 'còn số trang "00" trong mục lục', 'chạy pages.py rồi build lại')
        for l in pdf[i].get_links():
            if l.get('kind') != 1: continue
            tgt = l.get('page'); r = l['from']
            line = pdf[i].get_textbox(r).replace('\n', ' ').strip()
            m = re.match(r'(.*?)\s*\.{3,}\s*(\d+)\s*$', line) or re.match(r'(.*?)\s+(\d+)\s*$', line)
            if not m: continue
            label, num = m.group(1).strip(), m.group(2)
            key = re.sub(r'\s+', ' ', label)[:28]
            tgt_text = re.sub(r'\s+', ' ', pages[tgt]) if 0 <= tgt < len(pages) else ''
            if key[:20] not in tgt_text: add('F4', pg(i), '%s → trang pdf %d' % (label[:60], tgt + 1), 'link không trỏ tới đúng mục')
            elif printed(tgt) and printed(tgt) != num: add('F3', pg(i), '%s: mục lục ghi %s, thật là %s' % (label[:60], num, printed(tgt)), 'cập nhật số trang')
    if toc_pages and not any(pdf[i].get_links() for i in toc_pages): add('F4', 'mục lục', 'không có link nào', 'mục lục chưa bấm được')
    # ---------------- F5/L8 images
    for p in doc.inline_shapes:
        w, h = p.width / 360000, p.height / 360000
        if w > text_w * 2.54 / 72 + 0.05: add('F5', 'ảnh', 'rộng %.1f cm > vùng chữ %.1f cm' % (w, text_w * 2.54 / 72), 'thu nhỏ ảnh')
        if h > (ph - tm - bm) * 2.54 / 72 - 1.0: add('F5', 'ảnh', 'cao %.1f cm, quá một trang' % h, 'thu nhỏ hoặc tách sơ đồ')
    # ---------------- F6 empty cells
    empty = 0
    for t in doc.tables:
        for r in t.rows[1:]:
            cells = [_xtext(tc).strip() for tc in r._tr.tc_lst]   # text of nested tables counts
            if len(cells) > 1 and cells[0] and any(not c for c in cells[1:]): empty += 1
    if empty: add('F6', 'bảng', '%d dòng bảng có ô trống' % empty, 'điền hoặc ghi "Không áp dụng"')
    # ---------------- F7 markdown leaks
    for i, t in enumerate(pages):
        for m in re.finditer(r'\*\*[^*\n…]{2,40}\*\*|^#{1,4} |\]\(|<br\s*/?>|\\\|', t, re.M):
            add('F7', pg(i), m.group(0), 'ký hiệu markdown lọt ra bản xuất')
    # ---------------- F9 / L2 / L3 style
    st = doc.styles['Normal']
    want_font = cfg.get('doc_font') or {'slate': 'Inter', 'navy': 'Inter', 'mint': 'Inter', 'legacy': 'Times New Roman'}.get(cfg.get('doc_style') or ('legacy' if cfg.get('template') == 'classic' else 'slate'))
    if st.font.name != want_font: add('F9', 'style Normal', 'font %s, cần %s' % (st.font.name, want_font), 'kiểm tra doc_style')
    size = st.font.size.pt if st.font.size else None
    if not size or size < 10.5 or size > 13: add('L3', 'style Normal', 'cỡ chữ %s pt' % size, 'thân văn 11 pt (legacy 13)')
    ls = st.paragraph_format.line_spacing
    if ls and isinstance(ls, float) and not (1.0 <= ls <= 1.3): add('L3', 'style Normal', 'giãn dòng %s' % ls, '1.15')
    for k in (1, 2, 3):
        h = doc.styles['Heading %d' % k].paragraph_format
        b = h.space_before.pt if h.space_before else 0; a = h.space_after.pt if h.space_after else 0
        if b <= a: add('L2', 'Heading %d' % k, 'trước %.0f pt, sau %.0f pt' % (b, a), 'khoảng trước phải lớn hơn khoảng sau')
        if not h.keep_with_next: add('L6', 'Heading %d' % k, 'thiếu "giữ với đoạn sau"', 'bật keep_with_next')
    # ---------------- F10 cover
    cover = pages[0]
    for p in [r'Nguồn:', r'môi trường', r'tài khoản (?:test|bệnh nhân|Admin|khảo sát)', r'\bdev\b', r'as-is', r'xác nhận', r'Source:', r'environment']:
        if re.search(p, cover, re.I): add('F10', 'bìa', re.search(p, cover, re.I).group(0), 'bìa chỉ có tên tài liệu, sản phẩm, phiên bản, ngày')
    # ---------------- F8 environment words in the export
    for i, tx in enumerate(pages):
        for m in re.finditer(r'(?i)\btrên dev\b|\bon dev\b|môi trường dev|dev environment|\bstaging\b', tx):
            add('F8', pg(i), m.group(0), 'không nhắc môi trường trong SRS')
    # ---------------- F14 dangling references ("xem ở .", "use case ;", empty brackets)
    for i, tx in enumerate(pages):
        for m in re.finditer(r'\b(?:ở|tại|xem|see|in|use case)\s+[.;,]|\(\s*\)', tx.replace('\n', ' ')):
            add('F14', pg(i), tx.replace('\n', ' ')[max(0, m.start() - 50):m.end()], 'tham chiếu bị trống (thiếu giá trị trong config hoặc md)')
    # ---------------- F11 codes
    md_text = '\n'.join(open(f, encoding='utf-8').read() for f in glob.glob(os.path.join(md_dir, '*.md')))
    defined = set(re.findall(r'^- ((?:BR|AC)-\d+\.\d+\.\d+)', md_text, re.M)) | set(re.findall(r'^\| (TC-\d+\.\d+\.\d+)', md_text, re.M))
    defined |= {'UC-' + x for x in re.findall(r'^## (\d+\.\d+) ', md_text, re.M)}
    full = '\n'.join(pages)
    external = set(re.findall(r'SRS [^.;()]{1,60}?\b((?:BR|AC|TC)-\d+\.\d+\.\d+|UC-\d+\.\d+)', full.replace('\n', ' ')))   # codes of another document
    for code in sorted(set(re.findall(r'\b((?:BR|AC|TC)-\d+\.\d+\.\d+|UC-\d+\.\d+)\b', full)) - external):
        if code not in defined: add('F11', 'tài liệu', code, 'mã được nhắc nhưng không có định nghĩa')
    # ---------------- F12 privacy (same rules as privacy_check.py)
    ROLE_BOX = r'^(cskh|support|info|contact|hotro|lienhe|hello|sales|admin|noreply|no-reply|help|privacy|legal)@'
    for e in sorted(set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', full))):
        if re.search(r'example\.|@b\.co', e) or re.match(ROLE_BOX, e, re.I): continue
        add('F12', 'tài liệu', e, 'email cá nhân trong bản xuất (kiểm lại với privacy_check.py)')
    # ---------------- layout on the pdf
    H1 = {t for lvl, t, n in heads if lvl == 1}
    heading_set = {re.sub(r'\s+', ' ', t)[:40] for lvl, t, n in heads}
    body_top, body_bot = tm, ph - bm
    usable = body_bot - body_top
    cap_re = re.compile(r'^(Hình|Bảng|Figure|Table) \d+-\d+:')
    for i, page in enumerate(pdf):
        if i == 0: continue
        d = page.get_text('dict')
        lines = []
        for b in d['blocks']:
            if b.get('type') == 0:
                for l in b['lines']:
                    txt = ''.join(s['text'] for s in l['spans']).strip()
                    if txt: lines.append((l['bbox'], txt, max(s['size'] for s in l['spans'])))
        imgs = [im['bbox'] for im in page.get_image_info()]
        content = [x for x in lines if not (x[1].isdigit() and x[0][1] > body_bot - 5)]
        # L1 margins
        for bb, txt, sz in content:
            if bb[0] < lm - 6 or bb[2] > pw - rm + 6: add('L1', pg(i), txt, 'nội dung tràn lề'); break
        for bb in imgs:
            if bb[0] < lm - 3 or bb[2] > pw - rm + 3 or bb[3] > body_bot + 3: add('L1', pg(i), 'ảnh tràn lề', 'thu nhỏ ảnh'); break
        if not content and not imgs: continue
        ordered = sorted(content, key=lambda x: (round(x[0][1]), x[0][0]))
        if sum(1 for x in content if re.search(r'\.{5,}\s*\d+$', x[1])) > 3: continue   # contents / list of figures
        # L6 heading at page bottom
        for k, (bb, txt, sz) in enumerate(ordered):
            if re.sub(r'\s+', ' ', txt)[:40] in heading_set and sz >= 11.5:
                after = [x for x in ordered[k + 1:] if x[0][1] > bb[3] - 1]
                below_img = any(im[1] > bb[3] - 1 for im in imgs)
                if len(after) < 2 and not below_img and i < len(pdf) - 1:
                    add('L6', pg(i), txt, 'tiêu đề đứng một mình cuối trang')
        if i < len(pdf) - 1:
            import tablefind as _tf
            lab = _tf.lone_label(pdf[i], pdf[i + 1])
            if lab: add('L6', pg(i), lab, 'dòng dẫn của bảng đứng một mình cuối trang')
        # L7 caption without its figure / table
        for k, (bb, txt, sz) in enumerate(ordered):
            if cap_re.match(txt) and k == 0 and not any(im[3] <= bb[1] + 2 for im in imgs) and txt.startswith(('Hình', 'Figure')):
                add('L7', pg(i), txt, 'chú thích bị tách khỏi hình')
        # L13 chapter starts a page
        for k, (bb, txt, sz) in enumerate(ordered):
            if txt in H1 and re.match(r'\d+\.?\s', txt) and k > 0 and sz >= 14:
                add('L13', pg(i), txt, 'chương chính phải bắt đầu trang mới')
        # L12 nearly empty page
        if len(content) <= 2 and not imgs and i < len(pdf) - 1:
            add('L12', pg(i), ' / '.join(x[1] for x in content)[:80], 'trang chỉ có 1–2 dòng')
        # L11 large gap at page bottom
        bottoms = [x[0][3] for x in content] + [b[3] for b in imgs]
        gap = body_bot - max(bottoms) if bottoms else usable
        if gap > 0.35 * usable and i + 1 < len(pdf):
            nxt = sorted([l for b in pdf[i + 1].get_text('dict')['blocks'] if b.get('type') == 0 for l in b['lines']], key=lambda l: l['bbox'][1])
            first = ''.join(s['text'] for s in nxt[0]['spans']).strip() if nxt else ''
            nimg = sorted(pdf[i + 1].get_image_info(), key=lambda im: im['bbox'][1])
            # unavoidable: the next page opens with a figure taller than the gap (figures never split)
            fig_first = nimg and nimg[0]['bbox'][1] < body_top + 140 and (nimg[0]['bbox'][3] - body_top) + 40 > gap   # with the heading or lead-in above it
            if fig_first: continue
            ntab = _tables(pdf, i + 1, 'top')
            if ntab and ntab[0].bbox[1] < body_top + 60 and (ntab[0].bbox[3] - ntab[0].bbox[1]) + 60 > gap and ntab[0].row_count <= 10:
                continue   # a short table kept whole is taller than the gap
            if first not in H1 and not re.match(r'(Mục lục|Danh mục|Contents|List of)', first) and not (pages[i + 1].strip() == ''):
                why = 'hình hoặc bảng ở trang sau không vừa' if pdf[i + 1].get_image_info() else ''
                add('L11', pg(i), 'trống %.0f%% cuối trang' % (100 * gap / usable), why or 'dồn nội dung hoặc thu nhỏ khối trang sau')
        # L14 use case table starting at the very bottom
        for bb, txt, sz in ordered:
            if txt in ('Mã Use case', 'Use case code', 'Code') and body_bot - bb[1] < 5 * 16:
                add('L14', pg(i), txt, 'bảng use case bắt đầu sát cuối trang')
    # L9 / L10 table rows (docx properties) + split short tables (pdf)
    nosplit = 0; nohead = 0
    def all_tables(tables):
        for t in tables:
            yield t
            for r in t.rows:
                for c in r.cells: yield from all_tables(c.tables)
    for t in all_tables(doc.tables):
        for r in t.rows:
            trPr = r._tr.trPr
            tall = r._tr.find('.//' + qn('w:tbl')) is not None or len(_xtext(r._tr)) > 700
            if not tall and (trPr is None or trPr.find(qn('w:cantSplit')) is None): nosplit += 1
        if len(t.rows) > 8 and t.rows[0].cells[0].text.strip() not in ('Mã Use case', 'Use case code', 'Code de cas', 'Code'):
            trPr = t.rows[0]._tr.trPr
            if trPr is None or trPr.find(qn('w:tblHeader')) is None: nohead += 1
    narrow = 0
    for tb in all_tables(doc.tables):
        grid = [int(g.get(qn('w:w')) or 0) / 567 for g in tb._tbl.findall('.//' + qn('w:tblGrid') + '/' + qn('w:gridCol'))]
        if not grid or len(tb.columns) != len(grid): continue
        for j, col_w in enumerate(grid):
            try: words = [w for c in tb.columns[j].cells for w in c.text.split()]
            except Exception: break
            longest = max((len(w) for w in words if not re.search(r'[/_`=?]', w)), default=0)
            fs = 9 / 10.5 if len(grid) >= 7 else 1.0
            if longest and col_w + 0.05 < 0.23 * fs * min(longest, 12) + 0.4: narrow += 1; break
    if (cfg.get('lang') or 'vi') == 'vi':   # F13: English column names left in a Vietnamese document
        try:
            import po_transform; eng = set(po_transform.HDR) - {'Module', 'File'}
        except Exception: eng = set()
        left = sorted({c.text.strip() for tb in all_tables(doc.tables) for c in tb.rows[0].cells if c.text.strip() in eng})
        tagre = r'Permissions by action|UI states|Edge cases & error handling|Module links|Notifications, audit log|Open questions|& assumptions|\bUnknown\b|Inferred from code|Inferred from API|Safety-blocked|Needs role|Needs data|real-world effect|other role needed|(?:Product|Eng|Legal)(?:/\w+)? decision|\bWorks\b|\bBroken\b'
        for i, tx in enumerate(pages):
            for m in re.finditer(tagre, tx): add('F13', pg(i), m.group(0), 'nhãn tiếng Anh trong tài liệu tiếng Việt')
        if left: add('F13', 'bảng', 'tiêu đề cột tiếng Anh: ' + ', '.join(left), 'dịch tiêu đề cột (po_transform.HDR)')
    if narrow: add('L15', 'bảng', '%d bảng có cột hẹp hơn từ dài nhất (chữ bị ngắt giữa từ)' % narrow, 'chia lại độ rộng cột')
    if nosplit: add('L9', 'bảng', '%d dòng bảng có thể bị cắt ngang trang' % nosplit, 'bật "không tách dòng" (cantSplit)')
    if nohead: add('L9', 'bảng', '%d bảng dài không lặp dòng tiêu đề' % nohead, 'bật lặp tiêu đề')
    for i in range(1, len(pdf) - 1):
        a = _tables(pdf, i, 'bot')
        if not a: continue
        b = _tables(pdf, i + 1, 'top')
        if not a or not b: continue
        ta, tb = a[-1], b[0]
        above = [l for bl in pdf[i + 1].get_text('dict')['blocks'] if bl.get('type') == 0 for l in bl['lines'] if l['bbox'][3] <= tb.bbox[1] + 1 and ''.join(s['text'] for s in l['spans']).strip()]
        nested = ta.bbox[0] > lm + 20 or tb.bbox[0] > lm + 20
        uc_words = ('Luồng sự kiện', 'Hậu điều kiện', 'Trạng thái hiện', 'Main flow', 'Postcondition', 'Alternate flow')
        try: cells = ' '.join(str(c) for tt in (ta, tb) for row in tt.extract() for c in row if c)
        except Exception: cells = ''
        if any(w in cells.replace('\n', ' ') for w in uc_words): continue
        try:
            if not (tb.extract()[0][0] or '').strip(): continue   # first column empty: the rows continue a merged label cell
        except Exception: pass   # a use case table continues over pages by design
        if (ta.bbox[3] - ta.bbox[1]) + (tb.bbox[3] - tb.bbox[1]) > 0.35 * usable: continue   # a tall table may split
        if not above and not nested and ta.bbox[3] > body_bot - 30 and tb.bbox[1] < body_top + 30 and ta.row_count + tb.row_count <= 8:
            add('L10', pg(i) + '–' + (printed(i + 1) or str(i + 2)), 'bảng %d dòng bị chia 2 trang' % (ta.row_count + tb.row_count), 'giữ bảng ngắn trên một trang')


def fix_md(md_dir):
    """--fix: rewrite only what has one right answer. Quoted UI text and code are never touched (labels stay verbatim).
    W9 curly quotes -> straight; W12 old tone placement (hóa) -> new (hoá); W3 " trên dev" and "QA (app dev)" -> removed / "QA"."""
    n = collections.Counter()
    LM = label_mask(md_dir)
    def plain(seg):
        if 'W12' not in OPT['off']:
            keep = []
            if LM:   # inventory labels keep the app's own spelling
                seg = LM.sub(lambda m: keep.append(m.group(0)) or '\x00%d\x00' % (len(keep) - 1), seg)
            for old, new in TONE.items():
                k = seg.count(old) + seg.count(old.upper())
                if k: seg = seg.replace(old, new).replace(old.upper(), new.upper()); n['W12'] += k
            if keep: seg = re.sub('\x00(\\d+)\x00', lambda m: keep[int(m.group(1))], seg)
        if 'W3' not in OPT['off']:
            seg, k = re.subn(r'QA \(app dev\)', 'QA', seg); n['W3'] += k
            seg, k = re.subn(r'\s+trên dev\b', '', seg); n['W3'] += k
        return seg
    for f in sorted(glob.glob(os.path.join(md_dir, '*.md'))):
        t = open(f, encoding='utf-8').read(); o = t
        if 'W9' not in OPT['off']:
            k = t.count('“') + t.count('”'); t = t.replace('“', '"').replace('”', '"'); n['W9'] += k
        out, code = [], False
        for line in t.split('\n'):
            if line.startswith('```'): code = not code
            if code or line.startswith('```'): out.append(line); continue
            parts = re.split(r'("[^"\n]*"|`[^`\n]*`)', line)
            out.append(''.join(x if i % 2 else plain(x) for i, x in enumerate(parts)))
        t = '\n'.join(out)
        if t != o: open(f, 'w', encoding='utf-8').write(t)
    print('style_check --fix: ' + (', '.join('%s %d' % kv for kv in sorted(n.items()) if kv[1]) or 'nothing to fix'))


def main():
    a = sys.argv[1:]
    out_csv = None
    if '--csv' in a: k = a.index('--csv'); out_csv = a[k + 1]; del a[k:k + 2]
    if '--rules' in a: k = a.index('--rules'); load_rules(a[k + 1]); del a[k:k + 2]
    do_fix = '--fix' in a
    if do_fix: a.remove('--fix')
    if a and a[0] == '--srs':
        docx_p, pdf_p, md_dir, cfg_p = a[1:5]
        cfg = json.load(open(cfg_p, encoding='utf-8'))
        load_rules(os.path.join(os.path.dirname(os.path.abspath(cfg_p)), '.po-kit', 'standards.md'))
        check_srs(docx_p, pdf_p, md_dir, cfg)
    elif len(a) >= 2:
        md_dir, cfg_p = a[0], a[1]
        cfg = json.load(open(cfg_p, encoding='utf-8'))
        load_rules(os.path.join(os.path.dirname(os.path.abspath(cfg_p)), '.po-kit', 'standards.md'))
        if do_fix: fix_md(md_dir)
        check_md(md_dir, cfg)
    else:
        print(__doc__); sys.exit(2)
    c = collections.Counter((lv, code) for lv, code, *_ in OUT)
    for lv, code, place, text, hint in OUT:
        print('%-4s %-4s %-28s %s%s' % (lv, code, place[:28], text, ('  → ' + hint) if hint else ''))
    fails = sum(v for (lv, _), v in c.items() if lv == 'FAIL'); warns = sum(v for (lv, _), v in c.items() if lv == 'WARN')
    print('style_check: FAIL %d, WARN %d | %s' % (fails, warns, ', '.join('%s %s %d' % (k[1], k[0], v) for k, v in sorted(c.items(), key=lambda x: x[0][1]))))
    if out_csv:
        with open(out_csv, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(['level', 'code', 'place', 'text', 'hint']); w.writerows(OUT)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
