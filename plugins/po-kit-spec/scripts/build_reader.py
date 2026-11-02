#!/usr/bin/env python3
"""Build a single-file HTML reader (contents rail, search, collapsible blocks, TBD panel) from the spec markdown.
Usage: build_reader.py <md_dir> <config.json> <out.html>   (language and labels follow config.json, like build_srs.py)"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pokit_env; pokit_env.ensure()
import re, sys, os, json, html
import markdown
MD, CFGP, OUT = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import langpack as L
import po_transform as PT
CFG = json.load(open(CFGP, encoding='utf-8'))
PK = L.pack(CFG.get('lang', 'en')); EN = L.pack('en')
BLK = {EN['blocks'][k]: PK['blocks'][k] for k in EN['blocks']}
BLK['Open questions & assumptions'] = PK['blocks']['open_questions']
SEC = {'1. Product overview':'1. Tổng quan sản phẩm','Standard glossary':'Thuật ngữ','How to read this document':'Cách đọc tài liệu','User roles':'Vai trò người dùng','Common conventions for all screens':'Quy ước chung cho mọi màn hình','2. Navigation structure':'2. Cấu trúc điều hướng','4. Compliance & security':'4. Tuân thủ và bảo mật','Bugs and spec deviations found during recon':'Lỗi và sai lệch spec đã tìm thấy','5. Gaps and points to confirm':'5. Khoảng trống và điểm cần xác nhận','Summary': 'Tóm tắt', 'Roles & permissions': 'Vai trò và quyền', 'Feature map': 'Danh sách tính năng',
       'Appendix A — Integration & API': 'Phụ lục A: tích hợp và API'}
HDR = {'Role': 'Vai trò', 'Can do': 'Được làm', 'Cannot do': 'Không được làm', 'Feature': 'Tính năng', 'Screen': 'Màn hình',
       'Main role': 'Vai trò chính', 'Status on dev': 'Tình trạng trên dev', 'Question': 'Câu hỏi', 'Assumption': 'Giả định',
       'Owner': 'Người trả lời', 'Priority': 'Ưu tiên', 'Answer': 'Trả lời', 'Situation': 'Tình huống', 'Expected': 'Kỳ vọng',
       'Source': 'Nguồn', 'In/Out': 'Vào/Ra', 'Module': 'Module', 'Data': 'Dữ liệu', 'When': 'Khi nào', 'Precondition': 'Điều kiện trước',
       'Steps': 'Các bước', 'Type': 'Loại', 'Required': 'Bắt buộc', 'Format': 'Định dạng', 'Default': 'Mặc định',
       'Validation': 'Kiểm tra', 'Error message': 'Thông báo lỗi', 'Action': 'Hành động', 'Field': 'Trường', 'Note': 'Ghi chú',
       'Column': 'Cột', 'Button': 'Nút', 'Result': 'Kết quả', 'Enabled': 'Khi bật', 'From': 'Từ', 'To': 'Đến', 'Who': 'Ai',
       'Blocking condition': 'Điều kiện chặn', 'Effect': 'Hệ quả', 'Name': 'Tên', 'Purpose': 'Mục đích', 'Term': 'Thuật ngữ',
       'Meaning': 'Nghĩa', 'Route': 'Đường dẫn', 'Main tasks': 'Việc chính', 'Main module': 'Module chính', 'Label': 'Nhãn',
       'Observed': 'Quan sát', 'Severity': 'Mức độ', 'Features': 'Tính năng', 'File': 'File'}
lab = '|'.join(re.escape(PK['labels'][k]) for k in ('observed', 'inferred', 'proposal')) + '|Observed|Inferred from API|PO proposal'
dt = r'(?: \d{4}-\d{2}-\d{2})?'
def po(t):
    for en, loc in [(EN['answers'][k], PK['answers'][k]) for k in ('partial', 'cannot', 'verified')] + \
                   [(EN['labels'][k], PK['labels'][k]) for k in ('inferred', 'proposal', 'unverified', 'observed')]:
        t = re.sub(r'(?<![\w`])' + re.escape(en) + r'(?![\w`])', loc, t)
    t = re.sub(r'\s*\((?:%s)%s\)' % (lab, dt), '', t)
    t = re.sub(r'\((?:%s)%s[,;:] ?' % (lab, dt), '(', t)
    t = re.sub(r'\s*\((?:%s)%s\)' % (lab, dt), '', t)
    t = re.sub(r'(?<![\w`])%s(?=\s*[|\n])' % re.escape(PK['labels']['unverified']), 'Chưa xác nhận', t)
    return re.sub(r'(?<![\w`])%s(?![\w`])' % re.escape(PK['labels']['unverified']), 'chưa xác nhận', t)
def hdr_tr(t):
    out = []; L_ = t.split('\n')
    for i, l in enumerate(L_):
        if l.startswith('|') and i + 1 < len(L_) and re.match(r'^\|\s*:?-{3}', L_[i + 1]):
            l = '|' + '|'.join(' ' + HDR.get(c.strip(), c.strip()) + ' ' for c in l.strip().strip('|').split('|')) + '|'
        out.append(l)
    return '\n'.join(out)
mdr = markdown.Markdown(extensions=['tables', 'fenced_code', 'sane_lists'])
def render(t):
    mdr.reset(); h = mdr.convert(hdr_tr(t))
    h = re.sub(r'<table>', '<div class="tw"><table>', h); h = h.replace('</table>', '</table></div>')
    return h
def esc(s): return html.escape(s, quote=True)
files = CFG['files']; nav = []; body = []; stats = {'features': 0}
OPEN = {PK['blocks'][k] for k in ('problem_value', 'user_stories', 'main_flow', 'business_rules')}
for fi, f in enumerate(files):
    txt = PT.transform(open(os.path.join(MD, f + '.md'), encoding='utf-8').read(), CFG.get('lang', 'en'))
    m = re.match(r'#\s+(.+)', txt); title = po(m.group(1).strip()) if m else f
    parts = re.split(r'(?m)^## ', txt)[1:]
    mid = 'm%d' % fi; nav.append([mid, title, []]); sec_html = []
    for p in parts:
        head, _, rest = p.partition('\n'); head = po(head.strip())
        isfeat = bool(re.match(r'\d+\.\d+ ', head))
        head_txt = SEC.get(head, head)
        sid = 's%d_%d' % (fi, len(sec_html))
        if isfeat:
            stats['features'] += 1
            nav[-1][2].append([sid, re.sub(r'\s*`[^`]*`\s*$', '', head_txt)])
        elif fi == 0 or head in SEC:
            if fi == 0: nav[-1][2].append([sid, head_txt])
        bits = re.split(r'(?m)^\*\*([^*\n]+)\*\*\s*$', rest)
        inner = render(bits[0]) if bits[0].strip() else ''
        for j in range(1, len(bits), 2):
            name = BLK.get(bits[j].strip(), po(bits[j].strip())); content = bits[j + 1]
            cls = 'blk tbd' if name == PK['blocks']['open_questions'] else 'blk'
            op = ' open' if (name in OPEN or cls.endswith('tbd')) else ''
            inner += '<details class="%s"%s><summary>%s</summary>%s</details>' % (cls, op, esc(name), render(content))
        htitle = esc(head_txt)
        m2 = re.search(r'`([^`]+)`\s*$', head_txt)
        if m2: htitle = esc(head_txt[:m2.start()].strip()) + ' <code>%s</code>' % esc(m2.group(1))
        sec_html.append('<section id="%s" class="%s" data-text="%s"><h2>%s</h2>%s</section>' % (
            sid, 'feat' if isfeat else 'sec', esc(re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', inner))[:20000].lower()), htitle, inner))
    body.append('<div class="mod" id="%s"><h1>%s</h1>%s</div>' % (mid, esc(title), ''.join(sec_html)))
navh = ''
for mid, t, ch in nav:
    navh += '<div class="ng"><a class="nm" href="#%s">%s</a>%s</div>' % (mid, esc(t), ''.join('<a class="nf" href="#%s">%s</a>' % (i, esc(n)) for i, n in ch))
ptitle = CFG.get('product', 'SRS')
PAGE = open(os.path.join(HERE, 'reader_template.html'), encoding='utf-8').read()
PAGE = PAGE.replace('{{TITLE}}', esc(ptitle)).replace('{{SUB}}', esc(CFG.get('cover_lines', [''])[0])) \
           .replace('{{NAV}}', navh).replace('{{BODY}}', ''.join(body)).replace('{{META}}', esc(CFG.get('source_detail', '')))
open(OUT, 'w', encoding='utf-8').write(PAGE)
print('wrote', OUT, len(PAGE) // 1024, 'KB', stats)
