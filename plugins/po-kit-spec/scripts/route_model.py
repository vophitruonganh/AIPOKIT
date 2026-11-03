#!/usr/bin/env python3
"""Pick a model tier and effort for one task from measurable complexity. No model name is hardcoded here.
Usage: route_model.py <tool> <task> [key=value ...]
  tool : claude-code | codex | chatgpt | <any key in models.json> (unknown -> default)
  task : recon | write | deepen | review | verify | diagram | fix | reword | export | translate
  keys : screens fields roles states api rules defects_prev   (numbers)
         has_writes no_test_data money_or_legal independent_review   (0/1)
Prints one JSON line: score, tier, effort, model, why. Reads models.json next to this script,
overridden by .po-kit/models.json in the working folder when present.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, 'models.json'), encoding='utf-8'))
team = os.path.join('.po-kit', 'models.json')
if os.path.exists(team):
    over = json.load(open(team, encoding='utf-8'))
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k].update(v)
        else:
            cfg[k] = v

def route(tool, task, m):
    base = cfg['task_base'].get(task)
    if base is None:
        raise SystemExit('unknown task %r; choose from %s' % (task, ', '.join(cfg['task_base'])))
    score, why = float(base), ['base %s=%d' % (task, base)]
    for k, w in cfg['weights'].items():
        v = min(float(m.get(k, 0)), cfg['caps'][k])
        if v:
            score += v * w; why.append('%s=%g*%g' % (k, v, w))
    for k, w in cfg['flags'].items():
        if m.get(k):
            score += w; why.append('%s%+d' % (k, w))
    score = max(0, min(100, round(score)))
    tier = 'light'
    for t in ('standard', 'deep'):
        if score >= cfg['tier_cuts'][t]: tier = t
    order = ['light', 'standard', 'deep']
    if task in ('recon', 'verify') and m.get('has_writes') and tier == 'light':
        tier = 'standard'; why.append('floor: browser task with writes')
    if task in ('export', 'translate', 'fix'):
        tier = 'light'
    if task == 'reword' and tier == 'light':
        tier = 'standard'; why.append('floor: rewording must keep the meaning')
    effort = 'low'
    for e in ('medium', 'high'):
        if score >= cfg['effort_cuts'][e]: effort = e
    t = cfg['tools'].get(tool, cfg['tools']['default'])
    model = t.get(tier, 'inherit')
    return {'tool': tool if tool in cfg['tools'] else 'default', 'task': task, 'score': score, 'tier': tier,
            'effort': effort if t.get('supports_effort') else 'n/a (set in the tool UI: ' + effort + ')',
            'model': model, 'why': ', '.join(why)}

if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    m = {}
    for a in sys.argv[3:]:
        k, _, v = a.partition('=')
        m[k] = float(v)
    print(json.dumps(route(sys.argv[1], sys.argv[2], m), ensure_ascii=False))
