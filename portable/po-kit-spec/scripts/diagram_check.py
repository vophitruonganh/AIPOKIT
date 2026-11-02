#!/usr/bin/env python3
"""Gate for the diagrams of a spec (Phase 4b, before export).
Usage: diagram_check.py <md_dir> [config.json]
FAIL: a used Must diagram that needs a ```diagram``` block is missing; a block with a syntax problem or > 25 nodes.
WARN: a used Should diagram is missing; a block whose labels are long. Exit 1 when any FAIL."""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pokit_env; pokit_env.ensure()
import sys, json
import diagrams as D

def main():
    md = sys.argv[1]; cfg = json.load(open(sys.argv[2], encoding='utf-8')) if len(sys.argv) > 2 else {}
    spec = D.load_spec(md, cfg.get('files'))
    P = D.plan(spec, cfg)
    fails = warns = 0
    for c in P:
        if c['use'] and not c['satisfied']:
            lvl = 'FAIL' if c['level'] == 'Must' else 'WARN'
            fails += lvl == 'FAIL'; warns += lvl == 'WARN'
            print('%s  missing %s block for %s (%s)' % (lvl, c['type'], c['scope'], c['reason']))
    for d in D.all_diagram_blocks(spec):
        for p in D.block_problems(d):
            lvl = 'WARN' if p.startswith('label over') else 'FAIL'
            fails += lvl == 'FAIL'; warns += lvl == 'WARN'
            print('%s  %s "%s" in %s: %s' % (lvl, d['type'], d['title'], d['scope'], p))
    print('diagrams: %d planned, %d used | FAIL: %d, WARN: %d' % (len(P), sum(c['use'] for c in P), fails, warns))
    sys.exit(1 if fails else 0)

if __name__ == '__main__': main()
