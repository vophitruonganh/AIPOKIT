#!/usr/bin/env python3
"""PO loop step 2: load the Product Owner's answered sheet back into the spec.
Usage: po_sheet_import.py <md_dir> <answers.xlsx> [config.json] [--dry-run]
For each row with a Decision:
  open question  Accept/Change/Reject -> Answer cell "PO decided <date> (<who>): <text>"; Check on app -> owner "QA", stays open
  proposed rule  Accept -> label becomes "PO decided <date>"; Change -> rule text replaced; Reject -> rule marked not applicable
Before writing, the current md folder is copied to <spec dir>/versions/v<version>/md. Then it writes, next to the md folder:
  po-apply.md   decided points whose feature text (flows, fields, AC, TC) a spec-writer must now align
  po-verify.md  rows sent back to QA for a check on the app (Phase 4)
  changes-v<old>-v<new>.md   change list (spec_diff)
and bumps `version` + adds a `revisions` row in config.json. Rows are matched by the hidden key, so edited ids do not break it."""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pokit_env; pokit_env.ensure()
import sys, os, re, json, shutil, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import po_loop as P, spec_diff
from openpyxl import load_workbook

CHOICE = {'đồng ý': 'accept', 'accept': 'accept', 'sửa': 'change', 'change': 'change', 'từ chối': 'reject', 'reject': 'reject',
          'kiểm trên app': 'check', 'check on app': 'check'}
REJECT = {'vi': 'Không áp dụng', 'en': 'Not applicable'}
REV = {'vi': 'PO chốt %d điểm (%d câu hỏi, %d quy tắc), %d chuyển QA kiểm trên app.', 'en': 'PO decided %d points (%d questions, %d rules); %d sent to QA.'}

def bump(v):
    parts = str(v or '0.1').split('.')
    try: parts[-1] = str(int(parts[-1]) + 1)
    except ValueError: parts.append('1')
    return '.'.join(parts)

def esc(s): return re.sub(r'\s+', ' ', str(s or '')).replace('|', '/').strip()

def read_sheet(path):
    ws = load_workbook(path, data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(h or '').strip() for h in rows[0]]
    col = lambda *names: next(i for i, h in enumerate(hdr) if h in names)
    ix = dict(id=col('Mã', 'ID'), dec=col('Quyết định', 'Decision'), ans=col('Câu trả lời / nội dung chốt', 'Answer / decided text'),
              who=col('Người chốt', 'Decided by'), date=col('Ngày chốt', 'Date'), key=col('key'))
    out = []
    for r in rows[1:]:
        d = CHOICE.get(str(r[ix['dec']] or '').strip().lower())
        if not d: continue
        dt = r[ix['date']]
        dt = dt.date().isoformat() if isinstance(dt, datetime.datetime) else (dt.isoformat() if isinstance(dt, datetime.date) else (str(dt).strip() if dt else datetime.date.today().isoformat()))
        out.append(dict(id=str(r[ix['id']] or ''), dec=d, ans=esc(r[ix['ans']]), who=esc(r[ix['who']]) or 'PO', date=dt, key=str(r[ix['key']] or '')))
    return out

def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if len(a) < 2: print(__doc__); sys.exit(2)
    md, sheet = os.path.abspath(a[0]), a[1]; cfgp = a[2] if len(a) > 2 else None
    cfg = json.load(open(cfgp, encoding='utf-8')) if cfgp else {}
    lang = cfg.get('lang', 'vi'); dry = '--dry-run' in sys.argv
    rows = read_sheet(sheet)
    feats = P.parse_spec(md)
    byq = {}; byid = {}
    for f in feats:
        for q in f['oq']:
            byq['q:' + P.key(q['cells'][0])] = (f, q); byid['TBD-%s.%d' % (f['id'], q['n'])] = (f, q)
    files = {}
    def lines_of(p):
        if p not in files: files[p] = open(p, encoding='utf-8').read().split('\n')
        return files[p]
    apply, verify, miss = [], [], []; nq = nr = 0
    for r in rows:
        if r['key'].startswith('p:') or (not r['key'] and re.match(r'^BR-', r['id'])):
            bid = r['key'][2:] if r['key'] else r['id']
            f = next((x for x in feats if bid in x['br']), None)
            if not f: miss.append(r['id']); continue
            if r['dec'] == 'check': verify.append((f, bid, f['br'][bid])); continue
            L = lines_of(f['file'])
            i = next(k for k, l in enumerate(L) if re.match(r'^- %s[:.]' % re.escape(bid), l))
            body = re.sub(r'^- %s[:.]\s*' % re.escape(bid), '', L[i])
            tag = 'PO decided %s' % r['date']
            if r['dec'] == 'accept': new = body.replace('PO proposal (differs from current)', tag).replace('PO proposal', tag)
            elif r['dec'] == 'change': new = '%s (%s)' % (r['ans'] or body, tag)
            else:
                plain = re.sub(r'PO proposal(?: \(differs from current\))?[;,:]?\s*', '', body)
                plain = re.sub(r'\s*\(\s*\)', '', plain).strip()
                new = '%s: %s (%s%s)' % (REJECT.get(lang, REJECT['en']), plain, tag, ('; ' + r['ans']) if r['ans'] else '')
            L[i] = '- %s: %s' % (bid, new); nr += 1
            apply.append((f, bid, r['dec'], new))
        else:
            hit = byq.get(r['key']) or byid.get(r['id'])
            if not hit: miss.append(r['id']); continue
            f, q = hit; L = lines_of(f['file']); cells = list(q['cells'])
            if P.ANSWERED.match(cells[4]): continue
            if r['dec'] == 'check':
                cells[2] = 'QA'; verify.append((f, 'TBD-%s.%d' % (f['id'], q['n']), cells[0]))
            else:
                txt = cells[1] if r['dec'] == 'accept' else (r['ans'] if r['dec'] == 'change' else '%s. %s' % (REJECT.get(lang, REJECT['en']), r['ans']))
                cells[4] = 'PO decided %s (%s): %s' % (r['date'], r['who'], esc(txt)); nq += 1
                apply.append((f, 'TBD-%s.%d' % (f['id'], q['n']), r['dec'], cells[0] + ' → ' + esc(txt)))
            L[q['line_no']] = '| ' + ' | '.join(cells[:5]) + ' |'
    spec_dir = os.path.dirname(md); old_v = str(cfg.get('version', '0')); new_v = bump(old_v)
    print('rows with a decision: %d | questions decided: %d | rules decided: %d | to QA: %d | not found: %s' % (len(rows), nq, nr, len(verify), ', '.join(miss) or 'none'))
    if dry: return
    snap = os.path.join(spec_dir, 'versions', 'v' + old_v, 'md')
    if not os.path.exists(snap): shutil.copytree(md, snap)
    for p, L in files.items(): open(p, 'w', encoding='utf-8').write('\n'.join(L))
    with open(os.path.join(spec_dir, 'po-apply.md'), 'w', encoding='utf-8') as o:
        o.write('# PO decisions to align in the feature text (v%s)\n\nFor each row, update Main flow, Business rules, Field specification, Acceptance criteria and Test cases of the feature so they match the decision; keep the `PO decided` label.\n\n| Feature | ID | Decision | Text |\n| --- | --- | --- | --- |\n' % new_v)
        for f, i, d, t in apply: o.write('| %s | %s | %s | %s |\n' % (f['id'], i, d, esc(t)))
    with open(os.path.join(spec_dir, 'po-verify.md'), 'w', encoding='utf-8') as o:
        o.write('# Sent to QA for a check on the app (Phase 4)\n\n| Feature | ID | Point |\n| --- | --- | --- |\n')
        for f, i, t in verify: o.write('| %s | %s | %s |\n' % (f['id'], i, esc(t)))
    text, tot = spec_diff.diff(snap, md, lang)
    cp = os.path.join(spec_dir, 'changes-v%s-v%s.md' % (old_v, new_v)); open(cp, 'w', encoding='utf-8').write(text)
    if cfgp:
        cfg['version'] = new_v
        cfg.setdefault('revisions', []).append([new_v, datetime.date.today().isoformat(), REV.get(lang, REV['en']) % (nq + nr, nq, nr, len(verify))])
        json.dump(cfg, open(cfgp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('version %s -> %s | snapshot %s | wrote po-apply.md, po-verify.md, %s' % (old_v, new_v, snap, os.path.basename(cp)))

if __name__ == '__main__': main()
