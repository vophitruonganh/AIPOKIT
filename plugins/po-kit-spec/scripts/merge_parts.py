#!/usr/bin/env python3
"""Merge split-module parts: replaces the line `<!-- PART-B -->` in md/N-*.md with md/_parts/N-b.md, then moves the part to _parts/done/.
Usage: merge_parts.py <md dir>"""
import sys, os, re, glob, shutil
md = sys.argv[1].rstrip('/')
for part in sorted(glob.glob(os.path.join(md, '_parts', '*-b.md'))):
    n = os.path.basename(part).split('-')[0]
    target = glob.glob(os.path.join(md, n + '-*.md'))
    if not target: print('no module file for', part); continue
    t = open(target[0], encoding='utf-8').read()
    if '<!-- PART-B -->' not in t: print('marker missing in', target[0]); continue
    body = open(part, encoding='utf-8').read().strip('\n')
    open(target[0], 'w', encoding='utf-8').write(t.replace('<!-- PART-B -->', body, 1))
    os.makedirs(os.path.join(md, '_parts', 'done'), exist_ok=True)
    shutil.move(part, os.path.join(md, '_parts', 'done', os.path.basename(part)))
    print('merged', part, '->', target[0])
