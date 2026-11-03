#!/usr/bin/env python3
"""Quality gate for a spec exported as markdown (one file per module tab).
Usage: spec_lint.py <md_dir> [--csv out.csv] [--bar]
  --open [N]  only list the unanswered open questions (file:line, feature, question), of module N if given,
              so a verifier reads those lines and no whole module file
  --bar  also list the features under the Phase 3 bar and the blocks to deepen (main flow < 5 steps, < 5 rules,
         no alternate flow, < 6 test cases), so the deepen step needs no reading or counting
Per feature section ("## N.M Title") checks:
  - the required blocks (references/feature-block-standard.md)
  - BR/AC/TC numbering (BR-N.M.k, AC-N.M.k, TC-N.M.k: present, sequential)
  - test-case mix (>=3 TC; at least one Edge and one Permission)
  - open-question table: every row answered
  - source labels and absolute claims without any label
Headings/labels may be in any shipped language pack (scripts/lang/*.json). Exit 1 when a hard check fails."""
import re, sys, glob, os, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import langpack as L

OPTIONAL = {'field_spec', 'lifecycle', 'formulas'}  # may be absent or "Not applicable"
REQUIRED = [k for k in L.CANON['blocks'] if k != 'formulas']
alt = lambda group, key: '|'.join(re.escape(a) for a in L.aliases(group, key))
TC_TYPES = '|'.join(re.escape(a) for k in L.CANON['tc_types'] for a in L.aliases('tc_types', k))
ANSWER = re.compile(r'(?<![A-Za-z])(%s)' % '|'.join(re.escape(a) for k in L.CANON['answers'] for a in L.aliases('answers', k)))
OQ_HEAD = re.compile(r'\*\*(%s)\*\*(.*?)(?=\n\*\*|\Z)' % alt('blocks', 'open_questions'), re.S)
Q_COLS = tuple("| " + p["question_col"] for p in L.PACKS.values())
CLAIM = re.compile('|'.join('(?:%s)' % p['claims_regex'] for p in L.PACKS.values()))
PROPOSAL_PREFIX = tuple(p['proposal_prefix'] for p in L.PACKS.values())
PROPOSAL_LABEL = tuple(L.aliases('labels', 'proposal'))

def label_count(body, key):
    return sum(len(re.findall(re.escape(a), body)) for a in L.aliases('labels', key))

def open_rows(d, mod=None):
    n = 0
    for f in sorted(glob.glob(os.path.join(d, '[1-9]*.md'))):
        if mod and not os.path.basename(f).startswith(mod + '-'): continue
        feat, inq = '', False
        for ln, line in enumerate(open(f, encoding='utf-8'), 1):
            m = re.match(r'^## (\d+\.\d+) ', line)
            if m: feat, inq = m.group(1), False; continue
            if line.startswith('**'): inq = bool(re.match(r'\*\*(%s)\*\*' % alt('blocks', 'open_questions'), line)); continue
            if inq and line.startswith('|') and not line.startswith('| ---') and not line.startswith(Q_COLS) and not ANSWER.search(line):
                n += 1; print('%s:%d  %s  %s' % (os.path.basename(f), ln, feat, line.strip('| \n').split('|')[0].strip()[:120]))
    print('%d open questions without an answer' % n)

def main():
    d = sys.argv[1]; out = None
    if '--open' in sys.argv:
        k = sys.argv.index('--open'); open_rows(d, sys.argv[k + 1] if len(sys.argv) > k + 1 and not sys.argv[k + 1].startswith('-') else None); sys.exit(0)
    if '--csv' in sys.argv: out = sys.argv[sys.argv.index('--csv') + 1]
    rows = []; fails = 0
    for f in sorted(glob.glob(os.path.join(d, '[1-9]*.md'))):
        t = open(f, encoding='utf-8').read()
        for sec in re.split(r'^## (?=\d+\.\d+ )', t, flags=re.M)[1:]:
            head = sec.split('\n', 1)[0]
            m = re.match(r'(\d+)\.(\d+)', head); mod, ft = m.group(1), m.group(2)
            body = sec.split('\n## ')[0]; pid = '%s.%s' % (mod, ft)
            problems = []
            present = {L.match('blocks', b) for b in re.findall(r'^\*\*([^*]+?)\*\*', body, re.M)}
            for r in REQUIRED:
                if r not in present and r not in OPTIONAL: problems.append('missing block: ' + L.CANON['blocks'][r])
            for kind in ('BR', 'AC', 'TC'):
                ids = re.findall(r'\b%s-%s\.%s\.(\d+)\b' % (kind, mod, ft), body)
                uniq = sorted({int(i) for i in ids})
                if not uniq: problems.append('no ' + kind); continue
                if uniq != list(range(1, uniq[-1] + 1)): problems.append(kind + ' numbering not continuous')
            tcs = re.findall(r'^\| (TC-[\d.]+) \|.*\| (%s) \|\s*$' % TC_TYPES, body, re.M)
            kinds = collections.Counter(k for _, k in tcs)
            has = lambda key: any(kinds[a] for a in L.aliases('tc_types', key))
            if len(tcs) < 3: problems.append('fewer than 3 test cases (%d)' % len(tcs))
            if not has('edge'): problems.append('no Edge test case')
            if not has('perm'): problems.append('no Permission test case')
            q = OQ_HEAD.search(body)
            qrows = [r for r in (q.group(2) if q else '').split('\n') if r.startswith('|') and not r.startswith('| ---') and not r.startswith(Q_COLS)]
            unanswered = sum(not ANSWER.search(r) for r in qrows)
            lab = {k: label_count(body, k) for k in L.CANON['labels']}
            tot = sum(lab.values()) or 1
            share_unverified = (lab['unverified'] + lab['proposal']) / tot
            unlabelled = [x for x in CLAIM.finditer(body) if not body[:x.start()].endswith(PROPOSAL_PREFIX + PROPOSAL_LABEL)]
            if unlabelled and not lab['observed'] and not lab['inferred']:
                problems.append('absolute/numeric claims but no source label')
            blocks = {}
            for bm in re.finditer(r'^\*\*([^*]+?)\*\*(.*?)(?=^\*\*[^*]+?\*\*|\Z)', body, re.M | re.S):
                blocks[L.match('blocks', bm.group(1))] = bm.group(2)
            under = []
            if len(re.findall(r'^\d+\. ', blocks.get('main_flow', ''), re.M)) < 5: under.append('main flow < 5 steps')
            if len(set(re.findall(r'\bBR-%s\.%s\.\d+' % (mod, ft), blocks.get('business_rules', '')))) < 5: under.append('rules < 5')
            if len([l for l in blocks.get('alt_flow', '').split('\n') if l.strip().lstrip('-* ')]) < 1: under.append('no alternate flow')
            if len(tcs) < 6: under.append('test cases < 6 (core feature)')
            fails += bool(problems)
            rows.append(dict(feature=pid, title=re.sub(r'\s*`.*$', '', head)[:50], tc=len(tcs), questions=len(qrows),
                             unanswered=unanswered, observed=lab['observed'], inferred=lab['inferred'],
                             proposal=lab['proposal'], unverified=lab['unverified'],
                             share_unverified=round(share_unverified, 2), problems='; '.join(problems), deepen='; '.join(under)))
    for r in rows:
        print('%s %-5s %-50s TC=%-2d Q=%-2d unanswered=%-2d OBS=%-3d PRO=%-3d UNV=%-3d %s' % (
            'FAIL' if r['problems'] else 'ok  ', r['feature'], r['title'], r['tc'], r['questions'], r['unanswered'],
            r['observed'], r['proposal'], r['unverified'], r['problems']))
    print('\n%d features, %d failing' % (len(rows), fails))
    if '--bar' in sys.argv:
        low = [r for r in rows if r['deepen']]
        print('\nunder the Phase 3 bar: %d' % len(low))
        for r in low: print('deepen %-5s %s' % (r['feature'], r['deepen']))
    if out and rows:
        with open(out, 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    sys.exit(1 if fails else 0)

if __name__ == '__main__':
    main()
