#!/usr/bin/env python3
"""Verification coverage table: per feature, how many open questions are verified / partial / cannot-verify / still assumptions.
Usage: spec_stats.py <md_dir> <out.md> [lang]   (lang = language pack of the table text, default en)"""
import re, sys, glob, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import langpack as L
d, outp = sys.argv[1], sys.argv[2]
S = L.pack(sys.argv[3] if len(sys.argv) > 3 else 'en')['stats']
A = lambda k: '|'.join(re.escape(a) for a in L.aliases('answers', k))
RE_PART, RE_CAN, RE_VER, RE_DEC = (re.compile(r'(?<![A-Za-z])(%s)' % A(k)) for k in ('partial', 'cannot', 'verified', 'decided'))
OQ = re.compile(r'\*\*(%s)\*\*(.*?)(?=\n\*\*|\Z)' % '|'.join(re.escape(a) for a in L.aliases('blocks', 'open_questions')), re.S)
QCOLS = tuple('| ' + p['question_col'] for p in L.PACKS.values())
out = [S['title'] + '\n', S['legend'] + '\n', '| ' + ' | '.join(S['hdr']) + ' |', '| ' + ' | '.join(['---'] * len(S['hdr'])) + ' |']
T = [0] * 7
for f in sorted(glob.glob(os.path.join(d, '[1-9]*.md'))):
    t = open(f, encoding='utf-8').read()
    for s in re.split(r'^## (?=\d+\.\d+ )', t, flags=re.M)[1:]:
        title = re.sub(r'\s*`[^`]*`.*$', '', s.split('\n', 1)[0]).strip()
        body = s.split('\n## ')[0]
        m = OQ.search(body)
        rows = [r for r in (m.group(2) if m else '').split('\n') if r.startswith('|') and not r.startswith('| ---') and not r.startswith(QCOLS)]
        mp = sum(bool(RE_PART.search(r)) for r in rows)
        dx = sum(bool(RE_VER.search(r)) and not RE_PART.search(r) for r in rows)
        ck = sum(bool(RE_CAN.search(r)) and not RE_VER.search(r) for r in rows)
        dc = sum(bool(RE_DEC.search(r)) and not (RE_VER.search(r) or RE_CAN.search(r)) for r in rows)
        tc = len(re.findall(r'^\| TC-', body, re.M))
        v = [len(rows), dx, mp, ck, dc, len(rows) - dx - mp - ck - dc, tc]
        T = [a + b for a, b in zip(T, v)]
        out.append('| %s | %s |' % (title, ' | '.join(map(str, v))))
out.append('| **%s** | %s |' % (S['total'], ' | '.join('**%d**' % x for x in T)))
open(outp, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('wrote %s | ' % outp + ', '.join('%s=%d' % (h, v) for h, v in zip(S['hdr'][1:], T)))
