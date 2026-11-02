#!/usr/bin/env python3
"""Content-driven diagrams for the SRS (po-kit-spec v1.5).

One library used by build_srs.py, diagram_plan.py and diagram_check.py:
  load_spec(md_dir)        -> lightweight model of the spec (modules, features, blocks, diagram blocks)
  signals(spec, cfg)       -> measurable signals per document / module / feature
  plan(spec, cfg)          -> candidate diagrams scored Must / Should / Could, filtered by profile and budget
  render_*(...)            -> Graphviz renderers (PNG for Word, SVG next to it for the web reader)
Diagram blocks written by the spec-diagrammer agent live in the md files as fenced code:
    ```diagram <type>: <title>
    ...
    ```
Types and syntax: references/diagrams.md. Nothing here is specific to one product."""
import os, re, json, glob, subprocess, collections
HERE = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, HERE)
import langpack as L

# ------------------------------------------------------------------ catalog
TYPES = ['context', 'uc_overview', 'uc_module', 'process', 'linkmap', 'state', 'activity', 'sequence',
         'screen_map', 'flow', 'erd', 'decision', 'perm_matrix', 'timeline']
AGENT_TYPES = {'process', 'sequence', 'flow', 'erd', 'decision', 'timeline'}   # need understanding: written as ```diagram``` blocks
BLOCK_TYPES = {'context', 'process', 'journey', 'state', 'sequence', 'flow', 'erd', 'decision', 'timeline'}
ALIAS = {'journey': 'process', 'wizard': 'flow'}
# document profiles: which types are used and the per-feature cap (figures + diagram tables)
PROFILES = {
    'full':    {'types': set(TYPES), 'per_feature': 3, 'levels': {'Must', 'Should', 'Could'}},
    'classic': {'types': {'context', 'uc_overview', 'uc_module', 'process', 'state', 'activity', 'sequence', 'erd', 'decision'},
                'per_feature': 2, 'levels': {'Must', 'Should'}},
    'po':      {'types': {'context', 'uc_overview', 'process', 'linkmap', 'state', 'screen_map', 'flow', 'perm_matrix'},
                'per_feature': 1, 'levels': {'Must', 'Should'}},
    'dev':     {'types': {'context', 'state', 'sequence', 'erd', 'decision', 'activity', 'timeline', 'perm_matrix'},
                'per_feature': 3, 'levels': {'Must', 'Should', 'Could'}},
}
UNVERIFIED = re.compile(r'Unverified|PO proposal|Inferred|Chưa xác minh|Đề xuất PO|Suy ra|Non vérifié|Proposition PO', re.I)
SRC_LABEL = re.compile(r'\s*\((?:[^()]*?(?:Observed|Unverified|PO proposal|Inferred|Verified|Quan sát|Chưa xác minh|Đề xuất)[^()]*)\)', re.I)
COND_WORDS = re.compile(r'\b(và|hoặc|nếu|khi|trừ khi|and|or|if|when|unless|et|ou|si)\b', re.I)
TIME_RE = re.compile(r'\b\d+\s*(phút|giờ|ngày|tuần|tháng|năm|minutes?|hours?|days?|weeks?|months?|years?|h|min)\b', re.I)
DEADLINE = re.compile(r'hết hạn|hạn|quá hạn|trước khi|trước giờ|sau khi|tự động|tự huỷ|tự hủy|giữ chỗ|nhắc|expire|deadline|before|after|within|automatic|remind|hold|délai|avant|après|expir', re.I)
STEP_RE = re.compile(r'\b(?:bước|step|étape)\s*(\d+)', re.I)

# ------------------------------------------------------------------ spec model
def _table(lines, i):
    rows = []
    while i < len(lines) and lines[i].startswith('|'):
        cells = [c.strip() for c in re.split(r'(?<!\\)\|', lines[i].strip().strip('|'))]
        if not all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c): rows.append(cells)
        i += 1
    return rows, i

def parse_diagram_blocks(text):
    """fenced ```diagram <type>: <title> blocks -> list of dicts"""
    out = []
    for m in re.finditer(r'^```diagram[ \t]+([A-Za-z_]+)[ \t]*:?[ \t]*([^\n]*)\n(.*?)^```[ \t]*$', text, re.M | re.S):
        t = m.group(1).lower(); t = ALIAS.get(t, t)
        out.append({'type': t, 'title': m.group(2).strip(), 'body': m.group(3).rstrip('\n'), 'raw_type': m.group(1).lower()})
    return out

def strip_fences(text):
    return re.sub(r'^```.*?^```[ \t]*$', '', text, flags=re.M | re.S)

def _blocks_of_feature(body):
    """canonical block key -> raw text of that block"""
    out = collections.OrderedDict(); cur = '_'; buf = []
    for l in body.split('\n'):
        m = re.match(r'^\*\*([^*]+?)\*\*\s*(?:[—:-]\s*(.*))?$', l)
        if m:
            out[cur] = '\n'.join(buf); cur = L.match('blocks', m.group(1).strip()) or m.group(1).strip(); buf = [m.group(2) or '']
        else: buf.append(l)
    out[cur] = '\n'.join(buf)
    return out

def load_spec(md_dir, files=None):
    paths = [os.path.join(md_dir, f + '.md') for f in files] if files else sorted(glob.glob(os.path.join(md_dir, '[0-9]*.md')))
    spec = {'dir': md_dir, 'overview': None, 'modules': []}
    for p in paths:
        if not os.path.exists(p): continue
        text = open(p, encoding='utf-8').read()
        base = os.path.basename(p)[:-3]
        num = int(re.match(r'\d+', base).group(0))
        if num == 0:
            secs = re.split(r'^## ', text, flags=re.M)
            spec['overview'] = {'file': base, 'text': text, 'diagrams': parse_diagram_blocks(text),
                                'sections': {s.split('\n', 1)[0].strip(): s.split('\n', 1)[1] if '\n' in s else '' for s in secs[1:]}}
            continue
        title = (re.search(r'^# (.*)', text, re.M) or [None, base])[1]
        mod = {'file': base, 'num': num, 'name': re.sub(r'^\d+\.\s*', '', title), 'features': [], 'map': {},
               'diagrams': [], 'text': text}
        parts = re.split(r'^## ', text, flags=re.M)
        for s in parts[1:]:
            head, _, body = s.partition('\n')
            mm = re.match(r'(\d+\.\d+)\s+(.*)', head)
            if mm:
                fid, fname = mm.group(1), re.sub(r'\s*`[^`]+`', '', mm.group(2)).strip()
                bl = _blocks_of_feature(strip_fences(body))
                mod['features'].append({'id': fid, 'name': fname, 'body': body, 'blocks': bl,
                                        'diagrams': parse_diagram_blocks(body)})
            else:
                key = L.match('module_sections', head.strip())
                if key == 'feature_map':
                    rows, _ = _table(body.split('\n'), next((k for k, l in enumerate(body.split('\n')) if l.startswith('|')), 0))
                    for r in rows[1:]:
                        if r and re.match(r'^\d+\.\d+$', r[0]):
                            roles = [x.strip() for x in re.split(r',|/', re.sub(r'[*`]', '', r[3] if len(r) > 3 else '')) if x.strip()]
                            mod['map'][r[0]] = {'name': r[1] if len(r) > 1 else '', 'screen': r[2] if len(r) > 2 else '', 'roles': roles}
                mod['diagrams'] += parse_diagram_blocks(body)
        spec['modules'].append(mod)
    spec['root'] = os.path.dirname(os.path.abspath(md_dir.rstrip('/')))
    return spec

def all_diagram_blocks(spec):
    out = []
    if spec['overview']:
        for d in spec['overview']['diagrams']: out.append(dict(d, scope='doc'))
    for m in spec['modules']:
        for d in m['diagrams']: out.append(dict(d, scope='module:%d' % m['num']))
        for f in m['features']:
            for d in f['diagrams']: out.append(dict(d, scope='feature:' + f['id']))
    return out

# ------------------------------------------------------------------ helpers
def clean(s, n=None):
    """drop markdown and source-label parentheses; shorten at a word boundary"""
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s); s = re.sub(r'`([^`]+)`', r'\1', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s); s = re.sub(r'\\([<>*\[\]_`|#])', r'\1', s)
    s = SRC_LABEL.sub('', s).strip()
    s = re.sub(r'\s+', ' ', s)
    if n and len(s) > n:
        cut = s[:n].rsplit(' ', 1)[0].rstrip(',;:–-')
        s = cut + '…'
    return s

def external_systems(cfg, spec=None):
    """[(name, note)] from config `external_systems`, else the list after ':' in external_actors_note, else a ```diagram context``` block"""
    out = []
    for x in cfg.get('external_systems', []):
        if isinstance(x, dict): out.append((x.get('name', ''), x.get('note', '')))
        else: out.append((str(x), ''))
    if not out and cfg.get('external_actors_note'):
        note = cfg['external_actors_note']
        tail = note.split(':', 1)[1] if ':' in note else note
        for x in re.split(r',(?![^()]*\))|;|\band\b|\bvà\b', tail.rstrip('. ')):
            x = x.strip(' .')
            if not x: continue
            mm = re.match(r'^(.*?)\s*\((.*)\)\s*$', x)
            n, nt = (mm.group(1), mm.group(2)) if mm else (x, '')
            out.append((n[:1].upper() + n[1:], nt))
    return [(n, nt) for n, nt in out if n]

def human_actors(cfg):
    sys_names = {p.get('system_actor') for p in L.PACKS.values()}
    return [a for a in cfg.get('actors', []) if a not in sys_names]

# ------------------------------------------------------------------ signals
def feature_signals(f, mod, ext_names):
    bl = f['blocks']
    steps = len(re.findall(r'^\d+\.\s', bl.get('main_flow', ''), re.M))
    alts = len(re.findall(r'^[-*]\s|^\d+\.\s', bl.get('alt_flow', ''), re.M))
    lc_rows = [r for r in _rows_in(bl.get('lifecycle', '')) if len(r) >= 2]
    transitions = len(lc_rows)
    text = f['body']
    flows = (bl.get('main_flow', '') + '\n' + bl.get('alt_flow', '')).lower()
    ext = sorted({n for n in ext_names if n and n.lower() in flows})
    brs = _rows_in(bl.get('business_rules', ''))
    br_conds = max([len(COND_WORDS.findall(' '.join(r))) for r in brs] or [0])
    # a time limit counts only in a rule about a deadline (expiry, hold, before/after, automatic), not a duration such as a 30-minute slot
    timers = sum(len(TIME_RE.findall(l)) for l in bl.get('business_rules', '').split('\n') if DEADLINE.search(l))
    steps_mentioned = len(set(STEP_RE.findall(text)))
    money = bool(re.search(r'money_or_legal|thanh toán|payment|paiement|hoàn tiền|refund', text, re.I))
    links = sorted(set(re.findall(r'\b(\d+\.\d+)\b', bl.get('module_links', ''))) - {f['id']})
    roles = (mod['map'].get(f['id']) or {}).get('roles', [])
    return {'steps': steps, 'alts': alts, 'transitions': transitions, 'ext': ext, 'br_conds': br_conds,
            'timers': timers, 'wizard_steps': steps_mentioned, 'money': money, 'links': links, 'roles': roles,
            'blocks': [d['type'] for d in f['diagrams']]}

def _rows_in(text):
    lines = text.split('\n'); i = next((k for k, l in enumerate(lines) if l.startswith('|')), None)
    if i is None: return []
    rows, _ = _table(lines, i)
    return rows[1:]

def entity_count(spec):
    """data entities visible in the spec folder: CMS content model headings, else distinct API resources"""
    root = spec['root']
    cm = os.path.join(root, 'source', 'content-model.md')
    if os.path.exists(cm):
        return len(re.findall(r'^#{2,3} ', open(cm, encoding='utf-8').read(), re.M))
    api = os.path.join(root, 'source', 'api.md')
    if os.path.exists(api):
        res = set()
        for p in re.findall(r'(?:GET|POST|PUT|PATCH|DELETE)?\s*`?(/[A-Za-z0-9_\-/{}:.]+)', open(api, encoding='utf-8').read()):
            segs = [s for s in p.split('/') if s and not re.match(r'^(v\d+|api|admin|[{:].*|\d+)$', s)]
            if segs: res.add(segs[-1].rstrip('s'))
        return len(res)
    return 0

def screens(spec):
    out = collections.OrderedDict()
    for m in spec['modules']:
        for fid, mp in m['map'].items():
            sc = clean(mp.get('screen', ''))
            if sc: out.setdefault(sc, []).append((m['num'], m['name'], fid))
    return out

def signals(spec, cfg):
    ext = external_systems(cfg, spec)
    names = [n for n, _ in ext]
    doc = {'ext': len(ext), 'roles': len(human_actors(cfg)), 'modules': len(spec['modules']),
           'features': sum(len(m['features']) for m in spec['modules']), 'screens': len(screens(spec)),
           'entities': entity_count(spec), 'blocks': [d['type'] for d in (spec['overview'] or {}).get('diagrams', [])]}
    cross = 0
    feats = {}
    for m in spec['modules']:
        for f in m['features']:
            s = feature_signals(f, m, names); feats[f['id']] = s
            cross += sum(1 for x in s['links'] if x.split('.')[0] != f['id'].split('.')[0])
    doc['cross_links'] = cross
    return {'doc': doc, 'features': feats}

# ------------------------------------------------------------------ planner
def plan(spec, cfg):
    """list of candidates: {type, scope, level, auto, reason, satisfied}"""
    prof_name = (cfg.get('diagrams') or {}).get('profile') or ('classic' if cfg.get('template') == 'classic' else 'full')
    prof = PROFILES.get(prof_name, PROFILES['full'])
    inc = set((cfg.get('diagrams') or {}).get('include', [])); exc = set((cfg.get('diagrams') or {}).get('exclude', []))
    sg = signals(spec, cfg); d = sg['doc']
    blocks = all_diagram_blocks(spec)
    have = collections.Counter((b['type'], b['scope']) for b in blocks)
    have_type = collections.Counter(b['type'] for b in blocks)
    C = []
    def add(t, scope, level, reason, auto=None, satisfied=None):
        C.append({'type': t, 'scope': scope, 'level': level, 'reason': reason,
                  'auto': (t not in AGENT_TYPES) if auto is None else auto,
                  'satisfied': satisfied if satisfied is not None else (t not in AGENT_TYPES)})
    if d['ext'] >= 1: add('context', 'doc', 'Must', '%d external system(s) in config' % d['ext'])
    add('uc_overview', 'doc', 'Must', 'every SRS (section 2.3)')
    for m in spec['modules']:
        add('uc_module', 'module:%d' % m['num'], 'Must', 'template section 2.4')
    if d['modules'] >= 3 and d['cross_links'] >= 3:
        add('process', 'doc', 'Must', '%d cross-module links: section 2.5 needs an end-to-end process' % d['cross_links'],
            satisfied=have_type['process'] > 0)
        add('linkmap', 'doc', 'Should', 'module links between %d modules' % d['modules'])
    elif have_type['process']:
        add('process', 'doc', 'Should', 'process block present', satisfied=True)
    seen_states = set()
    for m in spec['modules']:
        for f in m['features']:
            s = sg['features'][f['id']]; sc = 'feature:' + f['id']
            if s['transitions'] >= 2 or 'state' in s['blocks']:
                key = _state_key(f)
                if key in seen_states:
                    C.append({'type': 'state', 'scope': sc, 'level': 'Could', 'reason': 'same states as an earlier feature: referenced, not redrawn',
                              'auto': True, 'satisfied': True, 'dup': True})
                else:
                    seen_states.add(key); add('state', sc, 'Must', '%d transitions in State lifecycle' % s['transitions'])
            if s['steps'] >= 5 or s['alts'] >= 2:
                lvl = 'Must' if (s['money'] or s['steps'] >= 8) else 'Should'
                add('activity', sc, lvl, '%d main steps, %d alternate flows' % (s['steps'], s['alts']))
            if s['ext']:
                add('sequence', sc, 'Must' if s['money'] else 'Should', 'flow reaches %s' % ', '.join(s['ext']),
                    satisfied=have[('sequence', sc)] > 0)
            if s['wizard_steps'] >= 3:
                add('flow', sc, 'Should', 'wizard with %d numbered steps' % s['wizard_steps'], satisfied=have[('flow', sc)] > 0)
            if s['br_conds'] >= 3:
                add('decision', sc, 'Could', 'a business rule combines %d conditions' % s['br_conds'], satisfied=have[('decision', sc)] > 0)
            if s['timers'] >= 2:
                add('timeline', sc, 'Could', '%d time limits in business rules' % s['timers'], satisfied=have[('timeline', sc)] > 0)
            for b in f['diagrams']:   # blocks the agent wrote without a signal still count
                if not any(c['type'] == b['type'] and c['scope'] == sc for c in C):
                    add(b['type'], sc, 'Should', 'diagram block in the spec', satisfied=True)
    if d['screens'] >= 5: add('screen_map', 'doc', 'Should', '%d distinct screens' % d['screens'])
    if d['entities'] >= 3:
        add('erd', 'doc', 'Should', '%d data entities in the spec folder' % d['entities'], satisfied=have_type['erd'] > 0)
    if d['roles'] >= 2: add('perm_matrix', 'doc', 'Should', '%d roles' % d['roles'])
    # profile, include/exclude and per-feature budget
    order = {'Must': 0, 'Should': 1, 'Could': 2}
    per = collections.Counter()
    for c in sorted(C, key=lambda c: (order[c['level']], c['scope'])):
        key = c['type'] + ':' + c['scope'].split(':')[-1]
        use = (c['type'] in prof['types'] and c['level'] in prof['levels']) or c['type'] in inc or key in inc
        if c['type'] in exc or key in exc: use = False
        if use and c['scope'].startswith('feature:') and not c.get('dup'):
            if per[c['scope']] >= prof['per_feature'] and c['level'] != 'Must' and key not in inc: use = False
            else: per[c['scope']] += 1
        c['use'] = use
        c['profile'] = prof_name
    return C

def _state_key(f):
    rows = _rows_in(f['blocks'].get('lifecycle', ''))
    return tuple(sorted({clean(r[0], 40) for r in rows} | {clean(r[1], 40) for r in rows if len(r) > 1}))

def wanted(P, t, scope):
    return any(c['use'] and c['type'] == t and c['scope'] == scope for c in P)

# ------------------------------------------------------------------ rendering
# Themes: config.json -> "diagrams": {"theme": "modern" | "classic"}; build_srs calls set_theme().
THEMES = {
    'modern': {
        'fonts': ['Inter', 'Helvetica Neue', 'Segoe UI', 'Arial', 'Liberation Sans', 'DejaVu Sans'],
        'ink': '#0F172A', 'text': '#334155', 'muted': '#64748B', 'edge': '#64748B', 'edge_soft': '#CBD5E1',
        'primary': '#4F46E5', 'primary_ink': '#FFFFFF', 'primary_soft': '#EEF2FF', 'primary_line': '#A5B4FC',
        'node_fill': '#FFFFFF', 'node_line': '#C7D2FE', 'pen': '1.3',
        'uc_fill': '#EEF2FF', 'uc_line': '#818CF8',
        'boundary_fill': '#F8FAFC', 'boundary_line': '#CBD5E1',
        'ext_fill': '#F1F5F9', 'ext_line': '#94A3B8',
        'unv_fill': '#FFFBEB', 'unv_line': '#F59E0B',
        'alt_fill': '#FAF5FF', 'alt_line': '#C4B5FD', 'alt_ink': '#6D28D9',
        'row_alt': '#F8FAFC',
        # lanes / groups: (background, border, title colour)
        'lanes': [('#F5F7FF', '#E0E7FF', '#4338CA'), ('#F0FDFA', '#CCFBF1', '#0F766E'), ('#FFF7ED', '#FED7AA', '#C2410C'),
                  ('#FDF2F8', '#FBCFE8', '#BE185D'), ('#F8FAFC', '#E2E8F0', '#334155')],
        'arrow': 'vee', 'arrowsize': '0.7', 'actor': 'actor_modern.png',
    },
    'classic': {
        'fonts': ['Liberation Sans', 'Arial', 'DejaVu Sans'],
        'ink': '#000000', 'text': '#000000', 'muted': '#555555', 'edge': '#333333', 'edge_soft': '#999999',
        'primary': '#FFFFCC', 'primary_ink': '#000000', 'primary_soft': '#FFFFCC', 'primary_line': '#8a7a2a',
        'node_fill': '#FFFFCC', 'node_line': '#8a7a2a', 'pen': '1.0',
        'uc_fill': '#FFFFCC', 'uc_line': '#8a7a2a',
        'boundary_fill': '#FFFFFF', 'boundary_line': '#555555',
        'ext_fill': '#FFFFFF', 'ext_line': '#555555',
        'unv_fill': '#FFFFCC', 'unv_line': '#8a7a2a',
        'alt_fill': '#FFFFFF', 'alt_line': '#8a7a2a', 'alt_ink': '#000000',
        'row_alt': '#FFFFFF',
        'lanes': [('#F4F4F4', '#777777', '#000000'), ('#EAF4FB', '#777777', '#000000'), ('#FBF3EA', '#777777', '#000000'),
                  ('#EEF8EE', '#777777', '#000000'), ('#F6EEF8', '#777777', '#000000')],
        'arrow': 'normal', 'arrowsize': '0.8', 'actor': 'actor.png',
    },
}
T = {}
FONT = 'Liberation Sans'
ACTOR_IMG = os.path.join(HERE, 'actor.png')

def _font(cands):
    try:
        have = subprocess.run(['fc-list', ':', 'family'], capture_output=True, text=True).stdout
        fams = {x.strip() for l in have.splitlines() for x in l.split(',')}
        for c in cands:
            if c in fams: return c
    except Exception: pass
    return cands[-1]

def set_theme(name='modern'):
    global T, FONT, ACTOR_IMG
    T = dict(THEMES.get(name) or THEMES['modern'])
    FONT = _font(T['fonts'])
    ACTOR_IMG = os.path.join(HERE, T['actor'])
    if not os.path.exists(ACTOR_IMG): ACTOR_IMG = os.path.join(HERE, 'actor.png')

def esc(s): return s.replace('\\', '\\\\').replace('"', '\\"')
def hesc(s): return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
def wrap(s, n=24):
    words = s.split(); lines = []; cur = ''
    for w in words:
        if len(cur) + len(w) + 1 > n and cur: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    if cur: lines.append(cur)
    return lines
def wl(s, n=24): return '\\n'.join(esc(x) for x in wrap(s, n))
def hw(s, n=24): return '<BR/>'.join(hesc(x) for x in wrap(s, n))

def render(dot_src, out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, name)
    open(p + '.dot', 'w', encoding='utf-8').write(dot_src)
    for extra in ([], ['-Gsplines=polyline'], ['-Gsplines=line']):   # graphviz routing can fail on dense clusters
        eng = ['neato', '-n2'] if dot_src.startswith('// engine=neato') else ['dot']
        r = subprocess.run(eng + ['-Tpng', '-Gdpi=170'] + extra + ['-o', p + '.png', p + '.dot'], capture_output=True)
        if r.returncode == 0: break
    else: raise RuntimeError('graphviz failed on %s: %s' % (name, r.stderr.decode(errors='replace')[-300:]))
    subprocess.run(eng + ['-Tsvg'] + extra + ['-o', p + '.svg', p + '.dot'], check=True, capture_output=True)
    return p + '.png'

def head():
    """graph-wide defaults of the current theme"""
    return ('bgcolor="white"; pad=0.25; fontname="%(f)s"; fontcolor="%(ink)s";\n'
            'node [fontname="%(f)s", fontsize=11, fontcolor="%(text)s", penwidth=%(pen)s, margin="0.16,0.07"];\n'
            'edge [fontname="%(f)s", fontsize=9, fontcolor="%(muted)s", color="%(edge)s", penwidth=1.1, arrowhead=%(arrow)s, arrowsize=%(arrowsize)s];'
            % dict(T, f=FONT))
def box(fill=None, line=None, extra=''):
    return 'node [shape=box, style="rounded,filled", fillcolor="%s", color="%s"%s];' % (fill or T['node_fill'], line or T['node_line'], extra)
def unv(): return 'style="rounded,filled,dashed", fillcolor="%s", color="%s"' % (T['unv_fill'], T['unv_line'])
def lane_style(li):
    bg, bd, ti = T['lanes'][li % len(T['lanes'])]
    return 'label=<<B>%%s</B>>; fontname="%s"; fontsize=11.5; fontcolor="%s"; style="rounded,filled"; fillcolor="%s"; color="%s"; penwidth=1.2; margin=14;' % (FONT, ti, bg, bd)
def start_end():
    return ['start [shape=circle, label="", width=0.2, style=filled, fillcolor="%s", color="%s"];' % (T['primary'], T['primary'] if T['primary'] != '#FFFFCC' else 'black'),
            'end [shape=doublecircle, label="", width=0.14, style=filled, fillcolor="%s", color="%s"];' % (T['primary'], T['primary'] if T['primary'] != '#FFFFCC' else 'black')]

def actor_node(nid, label):
    return ('%s [shape=none, margin=0, label=<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">'
            '<TR><TD FIXEDSIZE="TRUE" WIDTH="44" HEIGHT="58"><IMG SRC="%s" SCALE="TRUE"/></TD></TR>'
            '<TR><TD><FONT POINT-SIZE="11" COLOR="%s"><B>%s</B></FONT></TD></TR></TABLE>>];' % (nid, ACTOR_IMG, T['ink'], hw(label, 16)))

def uc_dot(actors, ucs, edges, title):
    s = ['digraph G {', 'rankdir=LR; nodesep=0.25; ranksep=1.1; splines=true; newrank=true;', head(),
         'edge [arrowhead=none, color="%s"];' % T['edge']]
    left = actors[:(len(actors) + 1) // 2]; right = actors[(len(actors) + 1) // 2:]
    for i, a in enumerate(actors): s.append(actor_node('a%d' % i, a))
    s.append('subgraph cluster_sys { label=<<B>%s</B>>; fontname="%s"; fontsize=12.5; fontcolor="%s"; style="rounded,filled"; fillcolor="%s"; color="%s"; penwidth=1.2; margin=16;'
             % (hesc(title), FONT, T['ink'], T['boundary_fill'], T['boundary_line']))
    for j, u in enumerate(ucs):
        s.append('u%d [shape=ellipse, style=filled, fillcolor="%s", color="%s", fontcolor="%s", label="%s", width=2.2];' % (j, T['uc_fill'], T['uc_line'], T['ink'], wl(u, 24)))
    s.append('}')
    for (i, j) in edges:
        s.append(('a%d -> u%d;' if actors[i] in left else 'u%d -> a%d;') % ((i, j) if actors[i] in left else (j, i)))
    if left: s.append('{rank=same; %s}' % ' '.join('a%d' % actors.index(a) for a in left))
    if right: s.append('{rank=same; %s}' % ' '.join('a%d' % actors.index(a) for a in right))
    s.append('}')
    return '\n'.join(s)

def context_dot(product, actors, systems):
    """systems: [(name, note)]"""
    s = ['digraph G {', 'rankdir=LR; nodesep=0.4; ranksep=1.4; splines=true;', head(),
         'sys [shape=box, style="rounded,filled", fillcolor="%s", color="%s", fontcolor="%s", penwidth=2, fontsize=13.5, label=<<B>%s</B>>, width=2.6, height=1.1];'
         % (T['primary'], T['primary'] if T['primary'] != '#FFFFCC' else T['node_line'], T['primary_ink'], hw(product, 20))]
    for i, a in enumerate(actors):
        s.append(actor_node('a%d' % i, a)); s.append('a%d -> sys [arrowhead=none];' % i)
    for j, (n, note) in enumerate(systems):
        s.append('x%d [shape=box, style="rounded,filled", fillcolor="%s", color="%s", fontcolor="%s", label="%s", width=1.9];' % (j, T['ext_fill'], T['ext_line'], T['ink'], wl(n, 22)))
        s.append('sys -> x%d [dir=both, arrowtail=%s%s];' % (j, T['arrow'], ', label="%s"' % wl(note, 22) if note else ''))
    s.append('}')
    return '\n'.join(s)

def activity_dot(rows, alts=()):
    """rows: [(lane, text, dashed)]; alts: [(after_index, condition, lane, text)]"""
    lanes = []
    for a, _, _ in rows:
        if a not in lanes: lanes.append(a)
    for _, _, a, _ in alts:
        if a not in lanes: lanes.append(a)
    s = ['digraph G {', 'rankdir=TB; nodesep=0.3; ranksep=0.34; newrank=true; compound=true;', head(),
         box(extra=', fontsize=10')] + start_end()
    for li, lane in enumerate(lanes):
        s.append('subgraph cluster_%d { %s' % (li, lane_style(li) % hesc(lane)))
        for k, (a, t, dsh) in enumerate(rows):
            if a == lane: s.append('n%d [label="%s", width=2.6%s];' % (k, wl(t, 32), (', ' + unv()) if dsh else ''))
        for k, (_, cond, a, t) in enumerate(alts):
            if a == lane: s.append('x%d [label=<<FONT POINT-SIZE="8.5" COLOR="%s"><B>%s</B></FONT><BR/>%s>, width=2.4, style="rounded,filled,dashed", fillcolor="%s", color="%s"];'
                                   % (k, T['alt_ink'], hw(cond, 34), hw(t, 32), T['alt_fill'], T['alt_line']))
        if li == 0: s.append('start;')
        s.append('}')
    if rows:
        s.append('start -> n0;')
        for k in range(len(rows) - 1): s.append('n%d -> n%d;' % (k, k + 1))
        s.append('n%d -> end;' % (len(rows) - 1))
    for k, (i, cond, _, _) in enumerate(alts):
        s.append('d%d [shape=diamond, label="", width=0.28, height=0.28, style=filled, fillcolor="%s", color="%s"];' % (k, T['alt_fill'], T['alt_line']))
        s.append('n%d -> d%d [style=dashed, arrowhead=none, color="%s"];' % (min(i, len(rows) - 1), k, T['alt_line']))
        s.append('d%d -> x%d [style=dashed, color="%s"];' % (k, k, T['alt_line']))
    s.append('}')
    return '\n'.join(s)

def state_dot(rows):
    """rows: [(from, to, label, dashed)]; '(none)'/'[*]'/empty from = start"""
    START = re.compile(r'^(\[\*\]|\(.*chưa có.*\)|\(none\)|\(new\)|—|-|start|bắt đầu)$', re.I)
    ids = {}
    def nid(x):
        if x not in ids: ids[x] = 's%d' % len(ids)
        return ids[x]
    s = ['digraph G {', 'rankdir=TB; nodesep=0.55; ranksep=0.5;', head(),
         box(T['primary_soft'], T['primary_line'], ', fontsize=11, fontcolor="%s", height=0.5' % T['ink'])] + start_end()
    edges = []; has_end = False
    for a, b, lab, dsh in rows:
        a0 = 'start' if (not a or START.match(a)) else nid(a)
        if b == '[*]': b0 = 'end'; has_end = True
        else: b0 = nid(b)
        edges.append('%s -> %s [label="%s"%s];' % (a0, b0, wl(lab, 26), ', style=dashed, color="%s"' % T['unv_line'] if dsh else ''))
    for x, i in ids.items(): s.append('%s [label=<<B>%s</B>>];' % (i, hw(x, 20)))
    if not has_end: s = [x for x in s if not x.startswith('end ')]
    s += edges; s.append('}')
    return '\n'.join(s)

def sequence_dot(parts, msgs):
    """parts: [name]; msgs: [(src, dst, label, dashed)] — fixed coordinates (neato -n2): straight lifelines and level arrows"""
    n = len(parts); P = {p: i for i, p in enumerate(parts)}
    longest = max([len(x) for _, _, lab, _ in msgs for x in wrap(lab, 26)] + [12])
    W = max(150, int(longest * 5.6) + 50); STEP = 46; TOP = 0
    act = T['primary'] if T['primary'] != '#FFFFCC' else T['edge']
    s = ['// engine=neato', 'digraph G {', 'splines=line; outputorder=edgesfirst;', head(),
         'node [shape=point, width=0.01, height=0.01, color="%s", label=""];' % T['edge_soft']]
    ys = []; y = TOP - 48
    for a_, b_, _, _ in msgs:
        ys.append(y); y -= STEP + (24 if a_ == b_ else 0)
    bottom = y + STEP - 30
    for i, p in enumerate(parts):
        x = i * W
        s.append('p%d [shape=box, style="rounded,filled", fillcolor="%s", color="%s", fontcolor="%s", fontsize=10.5, width=1.45, height=0.42, label=<<B>%s</B>>, pos="%d,%d"];'
                 % (i, T['primary_soft'], T['primary_line'], T['ink'], hw(p, 18), x, TOP))
        s.append('b%d [pos="%d,%d"];' % (i, x, bottom))
        s.append('p%d -> b%d [style=dashed, arrowhead=none, color="%s", penwidth=1.0];' % (i, i, T['edge_soft']))
    for r, (a, b, lab, dsh) in enumerate(msgs):
        y = ys[r]; ia, ib = P[a], P[b]; st = ', style=dashed' if dsh else ''
        if ia == ib:
            x = ia * W
            s.append('s%d_0 [pos="%d,%d"]; s%d_1 [pos="%d,%d"]; s%d_2 [pos="%d,%d"]; s%d_3 [pos="%d,%d"];' % (r, x, y, r, x + 34, y, r, x + 34, y - 22, r, x, y - 22))
            s.append('s%d_0 -> s%d_1 [arrowhead=none, color="%s"%s]; s%d_1 -> s%d_2 [arrowhead=none, color="%s"%s]; s%d_2 -> s%d_3 [color="%s"%s];'
                     % (r, r, act, st, r, r, act, st, r, r, act, st))
            ln = wrap(lab, 22)
            s.append('t%d [shape=box, style=filled, fillcolor=white, color=white, margin="0.03,0.01", width=0, height=0, fontsize=9.5, fontcolor="%s", label="%s", pos="%d,%d"];' % (r, T['text'], wl(lab, 22), x + 44 + 3 * max(len(l) for l in ln), y - 11))
        else:
            s.append('a%d [pos="%d,%d"]; c%d [pos="%d,%d"];' % (r, ia * W, y, r, ib * W, y))
            s.append('a%d -> c%d [color="%s"%s];' % (r, r, act, st))
            nl = len(wrap(lab, 26))
            s.append('t%d [shape=box, style=filled, fillcolor=white, color=white, margin="0.03,0.01", width=0, height=0, fontsize=9.5, fontcolor="%s", label="%s", pos="%d,%d"];' % (r, T['text'], wl(lab, 26), (ia + ib) * W / 2, y + 5 + 6 * nl))
    s.append('}')
    return '\n'.join(s)

def erd_dot(entities, rels):
    """entities: {name: [fields]}; rels: [(a, card_a, card_b, b, label)]"""
    s = ['digraph G {', 'rankdir=LR; nodesep=0.5; ranksep=1.0; splines=true;', head(), 'node [shape=plain];',
         'edge [arrowhead=none, color="%s"];' % T['edge']]
    ids = {}
    hdr_bg = T['primary'] if T['primary'] != '#FFFFCC' else T['node_fill']
    for k, (e, fields) in enumerate(entities.items()):
        ids[e] = 'e%d' % k
        rows = ''.join('<TR><TD ALIGN="LEFT" BGCOLOR="%s"><FONT POINT-SIZE="9.5" COLOR="%s">%s</FONT></TD></TR>'
                       % (T['row_alt'] if i % 2 else '#FFFFFF', T['text'], hesc(clean(f, 40))) for i, f in enumerate(fields[:12]))
        if len(fields) > 12: rows += '<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="9.5" COLOR="%s">… +%d</FONT></TD></TR>' % (T['muted'], len(fields) - 12)
        s.append('%s [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="5" COLOR="%s" STYLE="ROUNDED">'
                 '<TR><TD BGCOLOR="%s"><FONT COLOR="%s"><B>%s</B></FONT></TD></TR>%s</TABLE>>];'
                 % (ids[e], T['primary_line'], hdr_bg, T['primary_ink'], hw(e, 24), rows))
    for a, ca, cb, b, lab in rels:
        s.append('%s -> %s [taillabel="%s", headlabel="%s", label="%s", labeldistance=1.6, labelfontcolor="%s"];' % (ids[a], ids[b], esc(ca), esc(cb), wl(lab, 20), T['primary'] if T['primary'] != '#FFFFCC' else T['ink']))
    s.append('}')
    return '\n'.join(s)

def tree_dot(root, groups):
    """screen map: root -> group -> leaves; groups: [(group, [leaf])]"""
    s = ['digraph G {', 'rankdir=LR; nodesep=0.12; ranksep=0.7; splines=true;', head(), box(extra=', fontsize=10'),
         'edge [arrowhead=none, color="%s"];' % T['edge_soft'],
         'r [label=<<B>%s</B>>, fillcolor="%s", color="%s", fontcolor="%s", fontsize=12];' % (hw(root, 18), T['primary'] if T['primary'] != '#FFFFCC' else T['node_fill'], T['primary'] if T['primary'] != '#FFFFCC' else T['node_line'], T['primary_ink'])]
    k = 0
    for gi, (g, leaves) in enumerate(groups):
        bg, bd, ti = T['lanes'][gi % len(T['lanes'])]
        s.append('g%d [label=<<B>%s</B>>, fillcolor="%s", color="%s", fontcolor="%s"];' % (gi, hw(g, 22), bg, bd, ti)); s.append('r -> g%d;' % gi)
        for lf in leaves:
            s.append('l%d [label="%s", fillcolor="white", color="%s"];' % (k, wl(lf, 30), bd)); s.append('g%d -> l%d;' % (gi, k)); k += 1
    s.append('}')
    return '\n'.join(s)

def linkmap_dot(mods, edges):
    """module-level link map. mods: [(num, name, [(fid, fname)])]; edges: [(fid_a, fid_b)] grouped per module pair"""
    s = ['digraph G {', 'rankdir=LR; nodesep=0.4; ranksep=1.0;', head(), box(extra=', fontsize=10.5')]
    for k, (num, name, feats) in enumerate(mods):
        bg, bd, ti = T['lanes'][k % len(T['lanes'])]
        s.append('m%d [label=<<B>%s</B>>, fillcolor="%s", color="%s", fontcolor="%s"];' % (num, hw('%d. %s' % (num, name), 20), bg, bd, ti))
    pairs = collections.OrderedDict()
    own = {fid: num for num, _, feats in mods for fid, _ in feats}
    for a, b in edges:
        if a not in own or b not in own: continue
        ma, mb = own[a], own[b]
        pairs.setdefault((ma, mb), []).append('%s→%s' % (a, b))
    for (ma, mb), lst in pairs.items():
        lab = ', '.join(lst) if len(lst) <= 2 else '%d' % len(lst)
        s.append('m%d -> m%d [label="%s", fontsize=8.5, penwidth=%.1f];' % (ma, mb, wl(lab, 18), min(3.0, 0.9 + 0.3 * len(lst))))
    s.append('}')
    return '\n'.join(s)

def timeline_dot(points):
    s = ['digraph G {', 'rankdir=LR; nodesep=0.3; ranksep=0.45;', head(), box(T['primary_soft'], T['primary_line'], ', fontsize=10'),
         'edge [color="%s", penwidth=2.2, arrowhead=none];' % (T['primary_line'])]
    for k, (when, what) in enumerate(points):
        s.append('t%d [label=<<FONT COLOR="%s"><B>%s</B></FONT><BR/>%s>];' % (k, T['primary'] if T['primary'] != '#FFFFCC' else T['ink'], hesc(when), hw(what, 20)))
        if k: s.append('t%d -> t%d;' % (k - 1, k))
    s.append('}')
    return '\n'.join(s)

set_theme('modern')

# ------------------------------------------------------------------ block parsers (syntax: references/diagrams.md)
ARROW = re.compile(r'^(.+?)\s*(-->|->)\s*(.+?)\s*(?::\s*(.*))?$')
def parse_flow(body):
    """'Lane | step' lines; '? condition -> Lane | text' adds a branch after the previous step"""
    rows, alts = [], []
    for l in body.split('\n'):
        l = l.strip()
        if not l or l.startswith('#'): continue
        dsh = bool(UNVERIFIED.search(l))
        if l.startswith('?'):
            cond, _, rest = l[1:].partition('->')
            lane, _, txt = rest.partition('|') if '|' in rest else ('', '', rest)
            alts.append((max(len(rows) - 1, 0), clean(cond, 60), clean(lane) or (rows[-1][0] if rows else ''), clean(txt, 90)))
        else:
            lane, _, txt = l.partition('|') if '|' in l else ('', '', l)
            rows.append((clean(lane) or (rows[-1][0] if rows else ''), clean(txt, 90), dsh))
    return rows, alts

def parse_sequence(body):
    parts, msgs = [], []
    for l in body.split('\n'):
        l = l.strip()
        if not l or l.startswith('#'): continue
        m = ARROW.match(l)
        if not m: continue
        a, arrow, b, lab = clean(m.group(1)), m.group(2), clean(m.group(3)), clean(m.group(4) or '', 70)
        for x in (a, b):
            if x not in parts: parts.append(x)
        msgs.append((a, b, lab, arrow == '-->' or bool(UNVERIFIED.search(l))))
    return parts, msgs

def parse_state(body):
    rows = []
    for l in body.split('\n'):
        m = ARROW.match(l.strip())
        if m: rows.append((clean(m.group(1)), clean(m.group(3)), clean(m.group(4) or '', 50), m.group(2) == '-->' or bool(UNVERIFIED.search(l))))
    return rows

CARD = re.compile(r'^(.+?)\s+([01n*N]|0\.\.1|1\.\.n|0\.\.n|1\.\.\*|0\.\.\*)\s*--\s*([01n*N]|0\.\.1|1\.\.n|0\.\.n|1\.\.\*|0\.\.\*)\s+(.+?)(?:\s*:\s*(.*))?$')
def parse_erd(body):
    ents = collections.OrderedDict(); rels = []
    for l in body.split('\n'):
        l = l.strip()
        if not l or l.startswith('#'): continue
        m = CARD.match(l)
        if m:
            a, ca, cb, b, lab = clean(m.group(1)), m.group(2), m.group(3), clean(m.group(4)), clean(m.group(5) or '')
            ents.setdefault(a, []); ents.setdefault(b, []); rels.append((a, ca, cb, b, lab)); continue
        if ':' in l:
            e, _, fs = l.partition(':')
            ents.setdefault(clean(e), []).extend([x.strip() for x in fs.split(',') if x.strip()])
    return ents, rels

def parse_context(body):
    out = []
    for l in body.split('\n'):
        l = l.strip()
        if not l or l.startswith('#'): continue
        n, _, note = l.partition('|') if '|' in l else l.partition(':')
        out.append((clean(n), clean(note, 60)))
    return out

def parse_timeline(body):
    out = []
    for l in body.split('\n'):
        l = l.strip()
        if '|' in l:
            a, _, b = l.partition('|'); out.append((clean(a), clean(b, 60)))
    return out

def lifecycle_rows(f):
    rows = []
    for r in _rows_in(f['blocks'].get('lifecycle', '')):
        if len(r) < 2: continue
        who = clean(r[2], 20) if len(r) > 2 else ''
        act = clean(r[3], 40) if len(r) > 3 else ''
        lab = act if not who else '%s: %s' % (who, act)
        rows.append((clean(r[0], 40), clean(r[1], 40), lab, bool(UNVERIFIED.search(' '.join(r[3:4] + r[5:6])))))
    return rows

def node_count(d):
    t = d['type']; b = d['body']
    if t in ('process', 'flow'): r, a = parse_flow(b); return len(r) + len(a)
    if t == 'sequence': p, m = parse_sequence(b); return len(p) + len(m)
    if t == 'state': return len({x for r in parse_state(b) for x in r[:2]})
    if t == 'erd': e, _ = parse_erd(b); return len(e)
    if t == 'timeline': return len(parse_timeline(b))
    if t == 'context': return len(parse_context(b))
    return 0

def block_problems(d):
    """syntax problems of one ```diagram``` block"""
    t = d['type']; b = d['body']; out = []
    if t not in BLOCK_TYPES and d.get('raw_type') not in BLOCK_TYPES: out.append('unknown diagram type "%s"' % d.get('raw_type', t))
    if not d['title']: out.append('no title after the type')
    n = node_count(d)
    if t != 'decision' and n == 0: out.append('no parsable line (see references/diagrams.md)')
    if n > 25: out.append('%d nodes (> 25): split it' % n)
    for l in b.split('\n'):
        txt = re.sub(r'^[^|:>]*[|:>]', '', l)
        if len(clean(txt)) > 90: out.append('label over 90 characters: "%s…"' % clean(txt)[:40])
    if t == 'decision' and not re.search(r'^\|', b, re.M): out.append('decision block needs a markdown table')
    return out
