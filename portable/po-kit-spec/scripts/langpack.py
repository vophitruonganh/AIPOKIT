"""Language packs for the spec toolkit.
Authoring uses the canonical (English) headings and labels. Every pack in lang/ is accepted as an alias when
parsing, so specs written in another pack (e.g. the legacy Vietnamese headings) still lint and build.
The pack chosen with `lang` in config.json only controls the language of the generated document."""
import json, os, glob
HERE = os.path.dirname(os.path.abspath(__file__))
PACKS = {}
for _f in sorted(glob.glob(os.path.join(HERE, 'lang', '*.json'))):
    _p = json.load(open(_f, encoding='utf-8')); PACKS[_p['code']] = _p
CANON = PACKS['en']

def pack(code):
    return PACKS.get(code or 'en', CANON)

def aliases(group, key):
    """all strings (any pack) meaning `key` in `group`, longest first"""
    out = []
    for p in PACKS.values():
        v = p.get(group, {}).get(key)
        if v and v not in out: out.append(v)
    return sorted(out, key=len, reverse=True)

def match(group, text, **_):
    """canonical key of the first alias that `text` starts with, else None"""
    for key in CANON[group]:
        for a in aliases(group, key):
            if text.startswith(a): return key
    return None

def any_of(group, key):
    return aliases(group, key)

def find_section(sections, key, cfg_override=None):
    """name of the first section in `sections` (iterable of names) that matches overview `key`"""
    names = [cfg_override] if cfg_override else aliases('overview', key)
    for n in sections:
        for a in names:
            if n.startswith(a): return n
    return None
