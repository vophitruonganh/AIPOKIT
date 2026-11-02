#!/usr/bin/env python3
"""Detect a diagram style (theme, palette, font) from a reference Word file (.docx / .dotx).

Usage: python3 -I style_detect.py <file.docx>        prints the detected style as JSON

What is read (no text content, only formatting):
  - table cell shading (w:shd fill)          strongest signal: what the reader sees on every table
  - heading / run colours, hyperlink colour  (w:color)
  - theme accents and fonts                  (word/theme/theme1.xml)
Colours that are near white, near black or grey are ignored; the rest are grouped by hue,
ranked by use, and deepened to ink strength. No usable colour -> theme "mono" (greys).
"""
import colorsys, json, re, sys, zipfile
from collections import Counter

SANS_HINT = re.compile(r'sans|arial|helvet|calibri|segoe|inter|roboto|open|lato|verdana|tahoma|aptos|noto sans|source sans|montserrat|nunito', re.I)


def _rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _hls(h):
    return colorsys.rgb_to_hls(*_rgb(h))


def usable(h):
    _, l, s = _hls(h)
    return s >= 0.18 and 0.08 <= l <= 0.95


def deep(h, light=0.34, sat=0.62):
    hue, l, s = _hls(h)
    # keep a colour that is already ink-strong; deepen pale shades
    if l <= 0.45 and s >= 0.35:
        return '#' + h.lstrip('#').upper()
    return '#%02X%02X%02X' % tuple(int(x * 255) for x in colorsys.hls_to_rgb(hue, light, max(sat, min(s, 0.75))))


def _hue_dist(a, b):
    d = abs(_hls(a)[0] - _hls(b)[0]) * 360
    return min(d, 360 - d)


def detect(path):
    out = {'source': path, 'theme': 'modern', 'palette': None, 'alt': None, 'font': None, 'signals': {}}
    try:
        z = zipfile.ZipFile(path)
    except Exception as e:
        out['error'] = 'cannot open: %s' % e
        return out
    names = set(z.namelist())
    read = lambda n: z.read(n).decode('utf-8', 'ignore') if n in names else ''
    doc = read('word/document.xml')
    for n in names:
        if re.match(r'word/(header|footer)\d*\.xml$', n): doc += read(n)
    hexre = r'([0-9A-Fa-f]{6})'
    weights = Counter()
    # only formatting the reader actually sees: direct formatting in the body, plus styles the body uses
    used = set(re.findall(r'<w:(?:pStyle|rStyle|tblStyle) w:val="([^"]+)"', doc))
    styles = read('word/styles.xml')
    used |= set(re.findall(r'<w:style [^>]*w:default="1"[^>]*w:styleId="([^"]+)"', styles))
    used |= set(re.findall(r'<w:style [^>]*w:styleId="([^"]+)"[^>]*w:default="1"', styles))
    sty = ''.join(m.group(0) for m in re.finditer(r'<w:style [^>]*w:styleId="([^"]+)".*?</w:style>', styles, re.S) if m.group(1) in used)
    for src, k in ((doc, 1), (sty, 4)):
        for c in re.findall(r'<w:shd [^>]*w:fill="' + hexre + '"', src): weights[c.upper()] += 3 * k
        for c in re.findall(r'<w:color [^>]*w:val="' + hexre + '"', src): weights[c.upper()] += 1 * k
    theme = read('word/theme/theme1.xml')
    accents = re.findall(r'<a:accent\d>\s*<a:srgbClr val="' + hexre + '"', theme)
    hlink = re.findall(r'<a:hlink>\s*<a:srgbClr val="' + hexre + '"', theme)
    if '<w:hyperlink' in doc:                                # theme accents are often unused defaults: only the link colour, and only if links exist
        for c in hlink: weights[c.upper()] += 2
    out['signals'] = {'colours': weights.most_common(12), 'theme_accents': accents, 'link': hlink}
    # group by hue, keep the strongest of each group
    groups = []
    for c, w in weights.most_common():
        if not usable(c): continue
        for g in groups:
            if _hue_dist(g['c'], c) < 28:
                g['w'] += w
                break
        else:
            groups.append({'c': c, 'w': w})
    groups.sort(key=lambda g: -g['w'])
    # amber/orange/red are reserved for "unverified": a warm colour does not lead when a cool one is used too
    warm = lambda c: _hue_dist(c, 'F59E0B') < 35 or _hue_dist(c, 'DC2626') < 20
    cool = [g for g in groups if not warm(g['c'])]
    if groups and warm(groups[0]['c']) and cool and cool[0]['w'] * 6 >= groups[0]['w']:
        groups.remove(cool[0]); groups.insert(0, cool[0])
    if groups:
        pal = [deep(g['c']) for g in groups[:3]]
        out['palette'] = pal
        alts = [c for c in pal[1:] if not warm(c)]
        out['alt'] = alts[0] if alts else (pal[1] if len(pal) > 1 else None)
    else:
        out['theme'] = 'mono'
        out['palette'] = ['#334155', '#475569', '#64748B']
    fonts = re.findall(r'<a:(?:minor|major)Font>\s*<a:latin typeface="([^"]+)"', theme)
    defaults = ''.join(re.findall(r'<w:docDefaults>.*?</w:docDefaults>', styles, re.S))
    rfonts = Counter(re.findall(r'w:ascii="([^"]+)"', sty + doc + defaults))
    cand = [f for f, _ in rfonts.most_common()] or fonts
    cand = [f for f in cand if not re.search(r'mono|courier', f, re.I)] or cand
    sans = [f for f in cand if SANS_HINT.search(f)]
    out['font'] = sans[0] if sans else None      # serif document: diagrams keep the default sans for legibility
    out['signals']['fonts'] = cand[:5]
    return out


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    print(json.dumps(detect(sys.argv[1]), ensure_ascii=False, indent=1))
