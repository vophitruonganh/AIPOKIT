#!/usr/bin/env python3
"""PO loop step 1: export a question sheet (.xlsx) for the Product Owner.
Usage: po_sheet_export.py <md_dir> <out.xlsx> [config.json] [--all]
       po_sheet_export.py <md_dir> --count   (no file: counts used to decide whether the optional PO loop is worth it)
Rows: every unanswered open question (TBD-<feature>.<n>) and every business rule still labelled "PO proposal".
--all also lists rows already answered (read-only reference). The PO fills Decision / Answer / Decided by / Date,
then po_sheet_import.py loads the sheet back. Hidden column `key` matches rows even if ids shift."""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pokit_env; pokit_env.ensure()
import sys, os, json, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import po_loop as P
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation

TXT = {
 'vi': dict(sheet='Câu hỏi', guide='Hướng dẫn', summary='Tổng hợp',
   hdr=['Mã', 'Module', 'Tính năng', 'Loại', 'Nội dung cần chốt', 'Giả định / đề xuất hiện tại', 'Người trả lời', 'Ưu tiên',
        'Quyết định', 'Câu trả lời / nội dung chốt', 'Người chốt', 'Ngày chốt', 'key'],
   q='Câu hỏi mở', p='Quy tắc đề xuất', done='Đã trả lời',
   choices=['Đồng ý', 'Sửa', 'Từ chối', 'Kiểm trên app'],
   guide_rows=['Mỗi dòng là một điểm cần PO chốt. Lọc theo cột "Người trả lời" hoặc "Ưu tiên".',
     'Cột "Quyết định": Đồng ý = chấp nhận giả định hoặc đề xuất hiện tại; Sửa = ghi nội dung đúng vào cột "Câu trả lời"; '
     'Từ chối = không áp dụng (ghi lý do nếu có); Kiểm trên app = chuyển QA kiểm trên app trước khi chốt.',
     'Bỏ trống cột "Quyết định" nếu chưa trả lời; dòng đó giữ nguyên trong spec.',
     'Không sửa cột "Mã" và cột ẩn "key". Có thể thêm dòng ghi chú ở sheet khác.',
     'Gửi lại file này để nạp vào spec bằng po_sheet_import.py; spec sẽ tăng phiên bản và có danh sách thay đổi.'],
   sum_hdr=['Người trả lời', 'Câu hỏi mở', 'Quy tắc đề xuất', 'Tổng']),
 'en': dict(sheet='Questions', guide='How to', summary='Summary',
   hdr=['ID', 'Module', 'Feature', 'Kind', 'Point to decide', 'Current assumption / proposal', 'Owner', 'Priority',
        'Decision', 'Answer / decided text', 'Decided by', 'Date', 'key'],
   q='Open question', p='Proposed rule', done='Answered',
   choices=['Accept', 'Change', 'Reject', 'Check on app'],
   guide_rows=['Each row is one point for the PO to decide. Filter by "Owner" or "Priority".',
     'Decision: Accept = keep the current assumption or proposal; Change = write the right text in "Answer"; '
     'Reject = does not apply (add a reason); Check on app = QA checks on the app before deciding.',
     'Leave "Decision" empty when not answered; the row stays open in the spec.',
     'Do not edit "ID" or the hidden "key" column.',
     'Send the file back to load it with po_sheet_import.py; the spec gets a new version and a change list.'],
   sum_hdr=['Owner', 'Open questions', 'Proposed rules', 'Total']),
}

def collect(md_dir, include_done=False):
    rows = []
    for f in P.parse_spec(md_dir):
        mod = P.module_title(f['file'])
        for q in f['oq']:
            qs, asm, owner, prio, ans = q['cells'][:5]
            done = bool(P.ANSWERED.match(ans))
            if done and not include_done: continue
            rows.append(dict(id='TBD-%s.%d' % (f['id'], q['n']), module=mod, feature='%s %s' % (f['id'], f['title']), kind='q',
                             text=qs, current=asm, owner=owner, prio=prio, done=done, answer=ans if done else '', key='q:' + P.key(qs)))
        for bid, body in f['br'].items():
            if 'PO proposal' in body and 'PO decided' not in body:
                rows.append(dict(id=bid, module=mod, feature='%s %s' % (f['id'], f['title']), kind='p', text=body,
                                 current='', owner='PO', prio='', done=False, answer='', key='p:' + bid))
    return rows

def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if '--count' in sys.argv and a:
        rows = [r for r in collect(a[0]) if not r['done']]
        hi = sum(1 for r in rows if r['kind'] == 'q' and str(r['prio']).strip().lower() in ('high', 'cao', 'haute'))
        print('open questions=%d (high=%d), proposed rules=%d, owners=%d' % (sum(1 for r in rows if r['kind'] == 'q'), hi,
              sum(1 for r in rows if r['kind'] == 'p'), len({r['owner'] for r in rows})))
        return
    if len(a) < 2: print(__doc__); sys.exit(2)
    md, out = a[0], a[1]
    cfg = json.load(open(a[2], encoding='utf-8')) if len(a) > 2 else {}
    T = TXT.get(cfg.get('lang', 'vi'), TXT['en'])
    rows = collect(md, '--all' in sys.argv)
    wb = Workbook(); ws = wb.active; ws.title = T['sheet']
    ws.append(T['hdr'])
    for c in ws[1]: c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='1F4E79'); c.alignment = Alignment(wrap_text=True, vertical='top')
    for r in rows:
        ws.append([r['id'], r['module'], r['feature'], T['done'] if r['done'] else (T['q'] if r['kind'] == 'q' else T['p']), r['text'], r['current'],
                   r['owner'], r['prio'], '', r['answer'], '', '', r['key']])
    widths = [12, 18, 26, 14, 60, 40, 16, 9, 14, 50, 14, 12, 4]
    for i, w in enumerate(widths): ws.column_dimensions[chr(65 + i)].width = w
    ws.column_dimensions['M'].hidden = True
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment = Alignment(wrap_text=True, vertical='top')
        for c in row[8:12]: c.fill = PatternFill('solid', fgColor='FFF2CC')
    dv = DataValidation(type='list', formula1='"%s"' % ','.join(T['choices']), allow_blank=True)
    ws.add_data_validation(dv); dv.add('I2:I%d' % max(2, len(rows) + 1))
    dvd = DataValidation(type='date', allow_blank=True); ws.add_data_validation(dvd); dvd.add('L2:L%d' % max(2, len(rows) + 1))
    ws.freeze_panes = 'E2'; ws.auto_filter.ref = 'A1:L%d' % (len(rows) + 1)
    g = wb.create_sheet(T['guide'])
    g.append([cfg.get('product', ''), 'v' + str(cfg.get('version', '')), datetime.date.today().isoformat()])
    for t in T['guide_rows']: g.append([t])
    g.column_dimensions['A'].width = 120
    s = wb.create_sheet(T['summary']); s.append(T['sum_hdr'])
    agg = {}
    for r in rows:
        if r['done']: continue
        o = agg.setdefault(r['owner'] or '—', [0, 0]); o[0 if r['kind'] == 'q' else 1] += 1
    for o, (q, p) in sorted(agg.items(), key=lambda kv: -sum(kv[1])): s.append([o, q, p, q + p])
    s.column_dimensions['A'].width = 30
    wb.save(out)
    nq = sum(1 for r in rows if r['kind'] == 'q' and not r['done']); np_ = sum(1 for r in rows if r['kind'] == 'p')
    print('wrote %s | open questions=%d, proposed rules=%d, owners=%d' % (out, nq, np_, len(agg)))

if __name__ == '__main__': main()
