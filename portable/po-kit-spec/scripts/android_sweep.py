#!/usr/bin/env python3
"""Element sweep for the android driver (references/drivers.md).
Usage: android_sweep.py <uiautomator dump.xml>
Prints one line per interactive or labelled element: kind | text or content-desc | resource id (last part) | bounds centre.
Kinds: button, tab, input, checkbox, switch, list, text (labelled non-interactive text is kept so column headers and titles are not lost)."""
import sys, re
import xml.etree.ElementTree as ET

def kind(n):
    c = n.get('class', '')
    if 'EditText' in c: return 'input'
    if 'Switch' in c or 'Toggle' in c: return 'switch'
    if n.get('checkable') == 'true' or 'CheckBox' in c or 'RadioButton' in c: return 'checkbox'
    if 'Tab' in c: return 'tab'
    if n.get('scrollable') == 'true': return 'list'
    if n.get('clickable') == 'true' or n.get('long-clickable') == 'true': return 'button'
    return 'text'

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    raw = open(sys.argv[1], encoding='utf-8', errors='replace').read()
    raw = raw[raw.find('<?xml'):] if '<?xml' in raw else raw[raw.find('<hierarchy'):]
    raw = raw[:raw.rfind('</hierarchy>') + len('</hierarchy>')]
    seen, out = set(), []
    for n in ET.fromstring(raw).iter('node'):
        label = (n.get('text') or n.get('content-desc') or '').strip()
        k = kind(n)
        if k == 'text' and not label: continue
        if n.get('password') == 'true': label = '[password field]'
        rid = (n.get('resource-id') or '').split('/')[-1]
        m = re.findall(r'\d+', n.get('bounds', ''))
        c = '%d,%d' % ((int(m[0]) + int(m[2])) // 2, (int(m[1]) + int(m[3])) // 2) if len(m) == 4 else ''
        key = (k, label, rid)
        if key in seen: continue
        seen.add(key); out.append('%s | %s | %s | %s' % (k, re.sub(r'\s+', ' ', label)[:60], rid, c))
    print('\n'.join(out)); print('elements: %d' % len(out))

if __name__ == '__main__': main()
