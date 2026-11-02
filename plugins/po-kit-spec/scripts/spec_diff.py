#!/usr/bin/env python3
"""Change list between two versions of a spec (markdown module folders).
Usage: spec_diff.py <old_md_dir> <new_md_dir> <out.md> [lang]
Compares features (by N.M), business rules and acceptance criteria (by id and text), test cases (by id),
open questions (matched by question text) and reports what was added, removed, changed, decided or answered."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import po_loop as P

W = {'vi': dict(title='# Thay đổi giữa hai phiên bản spec', sum='Tóm tắt', feat_add='Tính năng mới', feat_del='Tính năng bị bỏ',
                feat='Tính năng', br='Quy tắc', ac='Tiêu chí', tc='Test case', added='thêm', removed='bỏ', changed='sửa',
                decided='PO chốt', answered='Câu hỏi đã có trả lời', q_add='Câu hỏi mới', q_del='Câu hỏi bị bỏ', none='Không có thay đổi.',
                old='Cũ', new='Mới'),
     'en': dict(title='# Changes between two spec versions', sum='Summary', feat_add='New features', feat_del='Removed features',
                feat='Feature', br='Rules', ac='Criteria', tc='Test cases', added='added', removed='removed', changed='changed',
                decided='decided by PO', answered='Questions answered', q_add='New questions', q_del='Removed questions', none='No changes.',
                old='Old', new='New')}

def cut(s, n=160):
    s = re.sub(r'\s+', ' ', s).strip()
    return s if len(s) <= n else s[:n - 1] + '…'

def diff(old_dir, new_dir, lang='vi'):
    T = W.get(lang, W['en'])
    old = {f['id']: f for f in P.parse_spec(old_dir)}; new = {f['id']: f for f in P.parse_spec(new_dir)}
    order = lambda ids: sorted(ids, key=lambda x: tuple(map(int, x.split('.'))))
    out, tot = [T['title'], ''], dict(fa=0, fd=0, ch=0, dec=0, ans=0)
    fa = order(set(new) - set(old)); fd = order(set(old) - set(new))
    if fa: out += ['## ' + T['feat_add'], ''] + ['- %s %s' % (i, new[i]['title']) for i in fa] + ['']
    if fd: out += ['## ' + T['feat_del'], ''] + ['- %s %s' % (i, old[i]['title']) for i in fd] + ['']
    tot['fa'], tot['fd'] = len(fa), len(fd)
    for fid in order(set(old) & set(new)):
        o, n = old[fid], new[fid]; lines = []
        for k in ('br', 'ac'):
            for rid in sorted(set(o[k]) | set(n[k]), key=lambda x: [int(p) for p in re.findall(r'\d+', x)]):
                a, b = o[k].get(rid), n[k].get(rid)
                if a == b: continue
                if a is None: lines.append('- %s %s: %s' % (rid, T['added'], cut(b)))
                elif b is None: lines.append('- %s %s: %s' % (rid, T['removed'], cut(a)))
                elif 'PO decided' in b and 'PO decided' not in a:
                    lines.append('- %s %s: %s' % (rid, T['decided'], cut(b))); tot['dec'] += 1
                else: lines.append('- %s %s: %s **%s** %s → **%s** %s' % (rid, T['changed'], '', T['old'], cut(a, 100), T['new'], cut(b, 100)))
        ta, td = set(n['tc']) - set(o['tc']), set(o['tc']) - set(n['tc'])
        tchg = [t for t in set(o['tc']) & set(n['tc']) if P.norm(o['tc'][t]) != P.norm(n['tc'][t])]
        if ta or td or tchg:
            lines.append('- %s: %s %d, %s %d, %s %d' % (T['tc'], T['added'], len(ta), T['removed'], len(td), T['changed'], len(tchg)))
        oq = {P.key(q['cells'][0]): q for q in o['oq']}; nq = {P.key(q['cells'][0]): q for q in n['oq']}
        for k_, q in nq.items():
            if k_ not in oq: lines.append('- %s: %s' % (T['q_add'], cut(q['cells'][0])))
            elif P.ANSWERED.match(q['cells'][4]) and not P.ANSWERED.match(oq[k_]['cells'][4]):
                lines.append('- TBD-%s.%d %s: %s → %s' % (fid, q['n'], T['answered'].lower(), cut(q['cells'][0], 90), cut(q['cells'][4], 120)))
                tot['ans'] += 1
        for k_, q in oq.items():
            if k_ not in nq: lines.append('- %s: %s' % (T['q_del'], cut(q['cells'][0])))
        if lines:
            tot['ch'] += 1; out += ['## %s %s' % (fid, n['title']), ''] + lines + ['']
    head = '%s: %s %d, %s %d, %s %d, %s %d, %s %d.' % (T['sum'], T['feat_add'].lower(), tot['fa'], T['feat_del'].lower(), tot['fd'],
            T['feat'].lower() + ' ' + T['changed'], tot['ch'], T['decided'], tot['dec'], T['answered'].lower(), tot['ans'])
    out.insert(2, head); out.insert(3, '')
    if not (tot['fa'] or tot['fd'] or tot['ch']): out.append(T['none'])
    return '\n'.join(out) + '\n', tot

if __name__ == '__main__':
    if len(sys.argv) < 4: print(__doc__); sys.exit(2)
    text, tot = diff(sys.argv[1], sys.argv[2], sys.argv[4] if len(sys.argv) > 4 else 'vi')
    open(sys.argv[3], 'w', encoding='utf-8').write(text)
    print('wrote %s | %s' % (sys.argv[3], ', '.join('%s=%d' % kv for kv in tot.items())))
