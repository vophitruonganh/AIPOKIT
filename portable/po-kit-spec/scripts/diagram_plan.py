#!/usr/bin/env python3
"""Plan the diagrams of a spec from its content (po-kit-spec v1.5).
Usage: diagram_plan.py <md_dir> [config.json] [--json out.json]
Prints one line per candidate: level, type, scope, used or not, satisfied or missing, reason.
Candidates marked 'agent' + 'missing' are the ```diagram``` blocks the spec-diagrammer must write."""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pokit_env; pokit_env.ensure()
import sys, json, os
import diagrams as D

def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    md = a[0]; cfg = json.load(open(a[1], encoding='utf-8')) if len(a) > 1 else {}
    spec = D.load_spec(md, cfg.get('files'))
    P = D.plan(spec, cfg)
    sg = D.signals(spec, cfg)['doc']
    print('profile %s | modules %d, features %d, roles %d, external systems %d, screens %d, entities %d, cross-module links %d'
          % (P[0]['profile'] if P else '-', sg['modules'], sg['features'], sg['roles'], sg['ext'], sg['screens'], sg['entities'], sg['cross_links']))
    for c in P:
        print('%-6s %-11s %-14s %-4s %-7s %-8s %s' % (c['level'], c['type'], c['scope'].replace('feature:', 'f:').replace('module:', 'm:'),
              'use' if c['use'] else 'skip', 'agent' if not c['auto'] else 'auto', 'ok' if c['satisfied'] else 'MISSING', c['reason']))
    used = [c for c in P if c['use']]
    miss = [c for c in used if not c['satisfied']]
    print('\n%d planned, %d used, %d to write (agent)' % (len(P), len(used), len(miss)))
    if '--json' in sys.argv:
        json.dump(P, open(sys.argv[sys.argv.index('--json') + 1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

if __name__ == '__main__': main()
