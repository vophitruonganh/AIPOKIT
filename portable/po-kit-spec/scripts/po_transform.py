"""PO view of a spec: turns the author-facing markdown (English labels, inline source tags) into text a Product Owner reads.
Shared by build_srs.py and build_reader.py. Pure text in, text out.
 - Business rules and Acceptance criteria bullets become tables: ID | text | Status (status is derived from the source tag).
 - Open questions get an ID (TBD-<feature>.<n>), a completeness sentence and an empty 'Due' column; answers show in the document language.
 - Remaining source tags are removed; 'Unverified' in running text becomes plain words ('chưa xác nhận').
"""
import re
import langpack as L

BR_AC = ('Business rules', 'Acceptance criteria')
OQ = 'Open questions & assumptions'
STATUS = {
    'vi': {'decided': 'PO đã chốt', 'observed': 'Đã quan sát', 'inferred': 'Suy từ API', 'proposal': 'Đề xuất', 'unverified': 'Chờ xác nhận', 'none': '—'},
    'en': {'decided': 'PO decided', 'observed': 'Observed', 'inferred': 'Inferred from API', 'proposal': 'Proposed', 'unverified': 'To confirm', 'none': '—'},
    'fr': {'decided': 'Décidé par le PO', 'observed': 'Observé', 'inferred': "Déduit de l'API", 'proposal': 'Proposé', 'unverified': 'À confirmer', 'none': '—'},
}
WORDS = {  # status column header, id header, due header, unconfirmed (cell, inline), completeness template
    'vi': ('Trạng thái', 'Mã', 'Hạn chốt', ('Chưa xác nhận', 'chưa xác nhận'),
           'Mức hoàn chỉnh: %d/%d quy tắc và tiêu chí đã quan sát, suy ra từ API hoặc PO đã chốt; %d điểm cần xác nhận, %d đã có kết quả (kiểm trên app hoặc PO chốt).'),
    'en': ('Status', 'ID', 'Due', ('Unconfirmed', 'unconfirmed'),
           'Completeness: %d of %d rules and criteria observed, inferred from the API or decided by the PO; %d points to confirm, %d answered (checked on the app or decided by the PO).'),
    'fr': ('Statut', 'ID', 'Échéance', ('Non confirmé', 'non confirmé'),
           "Complétude : %d/%d règles et critères observés ou déduits de l'API ; %d points à confirmer, %d vérifiés sur l'application." ),
}
TC_HDR_NOTE = None
HDR = {'Role': 'Vai trò', 'Can do': 'Được làm', 'Cannot do': 'Không được làm', 'Feature': 'Tính năng', 'Screen': 'Màn hình',
       'Main role': 'Vai trò chính', 'Status on dev': 'Tình trạng hiện tại', 'Question': 'Câu hỏi', 'Assumption': 'Giả định',
       'Owner': 'Người trả lời', 'Priority': 'Ưu tiên', 'Answer': 'Trả lời', 'Situation': 'Tình huống', 'Expected': 'Kỳ vọng',
       'Source': 'Nguồn', 'In/Out': 'Vào/Ra', 'Module': 'Module', 'Data': 'Dữ liệu', 'When': 'Khi nào', 'Precondition': 'Điều kiện trước',
       'Steps': 'Các bước', 'Type': 'Loại', 'Required': 'Bắt buộc', 'Format': 'Định dạng', 'Default': 'Mặc định',
       'Validation': 'Kiểm tra', 'Error message': 'Thông báo lỗi', 'Action': 'Hành động', 'Field': 'Trường', 'Note': 'Ghi chú',
       'Column': 'Cột', 'Button': 'Nút', 'Result': 'Kết quả', 'Enabled': 'Khi bật', 'From': 'Từ', 'To': 'Đến', 'Who': 'Ai',
       'Blocking condition': 'Điều kiện chặn', 'Effect': 'Hệ quả', 'Name': 'Tên', 'Purpose': 'Mục đích', 'Term': 'Thuật ngữ',
       'Meaning': 'Nghĩa', 'Route': 'Đường dẫn', 'Main tasks': 'Việc chính', 'Main module': 'Module chính', 'Label': 'Nhãn',
       'Observed': 'Quan sát', 'Severity': 'Mức độ', 'Features': 'Tính năng', 'File': 'File', 'Point': 'Nội dung',
       'Why': 'Lý do', 'Kind': 'Loại', 'Path': 'Đường dẫn', 'Status': 'Trạng thái', 'Expected result': 'Kết quả mong đợi'}
GWT = {'vi': (('Given', 'Cho'), ('When', 'Khi'), ('Then', 'Thì')), 'fr': (('Given', 'Étant donné'), ('When', 'Quand'), ('Then', 'Alors'))}
TAG = {'decided': r'PO decided', 'observed': r'Observed', 'inferred': r'Inferred from API', 'proposal': r'PO proposal', 'unverified': r'Unverified'}
DT = r'(?: \d{4}-\d{2}-\d{2})?'

def _classify(t):
    if re.search(r'PO decided', t): return 'decided'
    if re.search(r'Unverified', t): return 'unverified'
    if re.search(r'PO proposal', t): return 'proposal'
    if re.search(r'Inferred from API', t): return 'inferred'
    if re.search(r'Observed', t): return 'observed'
    return 'none'

def _strip_tags(t):
    lab = r'PO decided|Observed|Inferred from API|PO proposal'
    t = re.sub(r'\s*\((?:%s)%s\)' % (lab, DT), '', t)
    t = re.sub(r'\((?:%s)%s[,;:] ?' % (lab, DT), '(', t)
    return re.sub(r'\s*\((?:%s)%s\)' % (lab, DT), '', t)

OQ_HDR = {'vi': {'Question': 'Câu hỏi', 'Assumption': 'Giả định', 'Owner': 'Người trả lời', 'Priority': 'Ưu tiên', 'Answer': 'Kết quả / quyết định'},
          'fr': {'Question': 'Question', 'Assumption': 'Hypothèse', 'Owner': 'Responsable', 'Priority': 'Priorité', 'Answer': 'Résultat'}}
NOT_CHECKED = {'vi': 'chưa kiểm', 'fr': 'non vérifié'}

def _answers(t, lang):
    pk, en = L.pack(lang), L.pack('en')
    for k in ('partial', 'cannot', 'verified', 'decided'):
        t = re.sub(r'(?<![\w`])' + re.escape(en['answers'][k]) + r'(?![\w`])', pk['answers'][k], t)
    if lang in NOT_CHECKED: t = re.sub(r'(?<![\w`])not checked(?![\w`])', NOT_CHECKED[lang], t)
    return t

def transform(text, lang='en', tests_to_appendix=True):
    lang = lang if lang in WORDS else 'en'
    st, (h_status, h_id, h_due, unc, tmpl) = STATUS[lang], WORDS[lang]
    lines = text.split('\n'); out = []; i = 0
    feat = ''; block = ''; counts = {}; qn = {}
    tcs = {}; titles = {}                # test cases moved to a module appendix
    while i < len(lines):
        l = lines[i]
        if l.startswith('## '): block = ''          # a new section (feature or appendix) closes the previous block
        m = re.match(r'^## (\d+\.\d+)\b', l)
        if m:
            feat = m.group(1); counts[feat] = [0, 0, 0, 0]; qn[feat] = 0; block = ''
            titles[feat] = re.sub(r'^\d+\.\d+\s+', '', re.sub(r'\s*`[^`]*`\s*$', '', l[3:]).strip())
        m = re.match(r'^\*\*([^*\n]+)\*\*\s*$', l)
        if m:
            block = m.group(1).strip()
            if tests_to_appendix and block == 'Test cases' and feat:
                i += 1; buf = []
                while i < len(lines) and not re.match(r'^\*\*[^*\n]+\*\*\s*$', lines[i]) and not lines[i].startswith('## '):
                    buf.append(lines[i]); i += 1
                tcs[feat] = '\n'.join(buf).strip(); block = 'Test cases'; continue
            out.append(l)
            if block == OQ and feat: out.append(''); out.append('@@COMPLETE:%s@@' % feat)
            i += 1; continue
        if block in BR_AC and feat and re.match(r'^- [A-Z][A-Z-]*[\d.]+[:.]', l):
            rows = []
            while i < len(lines) and re.match(r'^- [A-Z][A-Z-]*[\d.]+[:.]', lines[i]):
                mm = re.match(r'^- ([A-Z][A-Z-]*[\d.]+)[:.]\s*(.*)$', lines[i])
                body = mm.group(2); k = _classify(body)
                if block == 'Acceptance criteria' and lang in GWT:
                    for en_, loc_ in GWT[lang]: body = re.sub(r'\b%s\b' % en_, loc_, body)
                if k in ('observed', 'inferred', 'decided'): counts[feat][0] += 1
                counts[feat][1] += 1
                rows.append((mm.group(1), body, k)); i += 1
            out.append('| %s | %s | %s |' % (h_id, 'Content' if lang == 'en' else {'vi': 'Nội dung', 'fr': 'Contenu'}[lang], h_status))
            out.append('| --- | --- | --- |')
            for rid, body, k in rows:
                body = body.replace('|', '\\|')
                out.append('| %s | %s | %s |' % (rid, body, st[k]))
            continue
        if block == OQ and l.startswith('|') and i + 1 < len(lines) and re.match(r'^\|\s*:?-{3}', lines[i + 1]):
            hdr = [OQ_HDR.get(lang, {}).get(c.strip(), c.strip()) for c in l.strip().strip('|').split('|')]
            out.append('| ' + ' | '.join([h_id] + hdr + [h_due]) + ' |')
            out.append('| ' + ' | '.join(['---'] * (len(hdr) + 2)) + ' |'); i += 2
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                qn[feat] += 1; counts[feat][2] += 1
                ans = cells[-1] if cells else ''
                if re.match(r'^(Verified|Partly verified|Cannot verify|PO decided)\b', ans): counts[feat][3] += 1
                out.append('| ' + ' | '.join(['TBD-%s.%d' % (feat, qn[feat])] + cells + ['—']) + ' |'); i += 1
            continue
        out.append(l); i += 1
    if tcs:
        head = {'vi': 'Test case', 'fr': 'Cas de test'}.get(lang, 'Test cases')
        out.append(''); out.append('## Appendix E — ' + head); out.append('')
        for f, body in tcs.items():
            out.append('**UC-%s %s**' % (f, titles.get(f, ''))); out.append(''); out.append(body); out.append('')
    res = '\n'.join(out)
    if lang == 'vi':
        ls = res.split('\n')
        for n_, l_ in enumerate(ls):
            if l_.startswith('|') and n_ + 1 < len(ls) and re.match(r'^\|\s*:?-{3}', ls[n_ + 1]):
                ls[n_] = '|' + '|'.join(' ' + HDR.get(c.strip(), c.strip()) + ' ' for c in l_.strip().strip('|').split('|')) + '|'
        res = '\n'.join(ls)
    for f, c in counts.items():
        res = res.replace('@@COMPLETE:%s@@' % f, tmpl % (c[0], c[1], c[2], c[3]))
    res = re.sub(r'@@COMPLETE:[^@]*@@', '', res)
    res = _strip_tags(res)
    res = _answers(res, lang) if lang != 'en' else res
    if lang != 'en':   # tags left inside longer parentheses
        for k, w in (('decided', 'PO đã chốt'), ('observed', 'đã quan sát'), ('inferred', 'suy từ API'), ('proposal', 'đề xuất')):
            word = {'vi': w}.get(lang, STATUS[lang][k].lower())
            res = re.sub(r'(?<![\w`])' + TAG[k] + r'(?:' + DT + r')?(?![\w`])', word, res)
        res = res.replace('Open questions', L.pack(lang)['blocks']['open_questions'])
        res = re.sub(r'Appendix ([A-E])', lambda m_: {'vi': 'Phụ lục ', 'fr': 'Annexe '}.get(lang, 'Appendix ') + m_.group(1), res)
        res = res.replace('**' + OQ + '**', '**' + L.pack(lang)['blocks']['open_questions'] + '**')
    pk = L.pack(lang)
    res = re.sub(r'(?<![\w`])Unverified(?=\s*[|\n])', unc[0], res)
    return re.sub(r'(?<![\w`])Unverified(?![\w`])', unc[1], res)
