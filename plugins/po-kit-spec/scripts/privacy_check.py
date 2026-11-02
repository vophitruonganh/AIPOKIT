#!/usr/bin/env python3
"""Pre-delivery privacy check. Usage: privacy_check.py <file.docx|file.pdf|md_dir> [term ...]
Flags: document author/last-modified-by properties that are not empty, e-mail addresses, phone-like numbers (start with 0 or +country code, 9-12 digits),
and every extra term given (person names, test account names, organization or customer names...). Exit 1 when anything is found."""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import pokit_env; pokit_env.ensure()
import sys, re, os, glob, zipfile
def read(path):
    if os.path.isdir(path):
        return {f: open(f, encoding='utf-8').read() for f in glob.glob(os.path.join(path, '*.md'))}, []
    if path.endswith('.docx'):
        from docx import Document
        d = Document(path); cp = d.core_properties; props = []
        for k in ('author', 'last_modified_by', 'comments'):
            if getattr(cp, k): props.append('%s=%r' % (k, getattr(cp, k)))
        from docx.oxml.ns import qn
        return {path: ' '.join(t.text or '' for t in d.element.body.iter(qn('w:t')))}, props
    if path.endswith('.pdf'):
        import pymupdf
        d = pymupdf.open(path); props = ['%s=%r' % (k, v) for k, v in d.metadata.items() if k in ('author', 'creator') and v and 'Writer' not in v]
        return {path: '\n'.join(p.get_text() for p in d)}, props
    return {path: open(path, encoding='utf-8').read()}, []
texts, props = read(sys.argv[1]); terms = sys.argv[2:]
bad = ['property ' + p for p in props]
for name, t in texts.items():
    for m in re.finditer(r'[\w.+-]+@[\w-]+\.[\w.-]+', t): bad.append('%s: email %s' % (os.path.basename(name), m.group(0)))
    for m in re.finditer(r'(?<![\w.-])(?:\+\d{1,3}[\s.-]?|0)\d(?:[\s.-]?\d){7,10}(?![\w-])', t): bad.append('%s: phone-like %s' % (os.path.basename(name), m.group(0).strip()))
    for term in terms:
        n = len(re.findall(re.escape(term), t, re.I))
        if n: bad.append('%s: term %r x%d' % (os.path.basename(name), term, n))
print('\n'.join(bad) if bad else 'privacy check: clean'); sys.exit(1 if bad else 0)
