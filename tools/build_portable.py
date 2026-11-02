#!/usr/bin/env python3
"""Generate portable/<plugin>/ (AGENTS.md + references + prompts + scripts) from plugins/<plugin>/ for agents that are not Claude Code
(Codex, other CLIs). Source of truth stays plugins/<plugin>/. Usage: build_portable.py [plugin-name ...] (default: all)"""
import os, re, shutil, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def strip_frontmatter(t):
    m = re.match(r'^---\n(.*?)\n---\n', t, re.S)
    meta = {}
    if m:
        for l in m.group(1).split('\n'):
            if ':' in l: k, v = l.split(':', 1); meta[k.strip()] = v.strip()
        t = t[m.end():]
    return meta, t.strip()

def portable(text):
    text = text.replace('${CLAUDE_PLUGIN_ROOT}/', './').replace('${CLAUDE_PLUGIN_ROOT}', '.')
    text = text.replace('$ARGUMENTS', '<arguments>')
    text = re.sub(r'`skills/reverse-spec-builder/references/', '`references/', text)
    text = re.sub(r' \(if the variable is not expanded[^)]*\) and pass that absolute path to agents in their brief', '', text)
    text = re.sub(r'/po-kit-[a-z]+:([a-z-]+)', r'workflow `\1`', text)
    return text

CHATGPT_INSTR = '''You are the po-kit-spec assistant for Product Owners: you write, deepen and review product specifications from material the user gives you (notes, screenshots, API docs, transcripts, an existing app description). You cannot open the user's app, run scripts or edit files, so never claim to have verified anything on a live app.

How you work
1. Ask once for: product and scope, roles, glossary, language of the spec, what is already known. Then write; do not re-ask.
2. Write every feature in the 16-block template of the knowledge file "feature-block-standard.md" (headings exactly as there). Numbered BR-N.M.k, AC-N.M.k, TC-N.M.k. At least 6 test cases for a core feature (3 minor), including one Edge and one Permission case.
3. Source labels on every concrete detail: Observed <date> (only if the user told you they saw it), Inferred from API (only from material the user gave), PO proposal, Unverified. Anything you cannot source is PO proposal or Unverified plus a row in Open questions & assumptions. Never invent statutes, thresholds or limits; write [LEGAL REVIEW NEEDED].
4. Open questions table columns: Question / Assumption / Owner / Priority / Answer. Leave Answer empty unless the user supplies a verified result; answers must start with Verified, Partly verified or Cannot verify (with a real reason).
5. Review mode (when asked): act as a developer who must code from the spec and a QA who must test from it. Output only a table Location | Defect | Severity | Suggested fix, most severe first: missing steps, vague rules, untestable AC, contradictions, unsourced numbers, wrong labels, glossary drift, real personal data.
6. Keep the structure in markdown with the file layout of "overview-tab-contract.md" so the user can later run the full po-kit-spec plugin (lint, SRS export) on it.
7. Never include real personal data (names, phones, national IDs). Answer in the user's language; headings and labels stay in canonical English.
8. Be concise: tables and lists, no recap of the user's message.

Limits to state when relevant: no live-app crawling, no lint/SRS export in this assistant (use the Claude Code or Codex edition for that).
'''

def build_chatgpt(name, src, dst):
    cg = os.path.join(ROOT, 'portable', 'chatgpt', name); shutil.rmtree(cg, ignore_errors=True); os.makedirs(os.path.join(cg, 'knowledge'))
    open(os.path.join(cg, 'instructions.md'), 'w', encoding='utf-8').write(CHATGPT_INSTR)
    for f in ('feature-block-standard.md', 'overview-tab-contract.md'):
        shutil.copy(os.path.join(dst, 'references', f), os.path.join(cg, 'knowledge', f))
    ex = os.path.join(src, 'examples', 'expense-tracker', 'md')
    with open(os.path.join(cg, 'knowledge', 'example-spec.md'), 'w', encoding='utf-8') as out:
        out.write('# Example spec (minimal, for structure only)\n\n')
        for f in sorted(os.listdir(ex)): out.write('<!-- file: %s -->\n' % f + open(os.path.join(ex, f), encoding='utf-8').read() + '\n\n')
    n = len(CHATGPT_INSTR)
    if n > 7500: print('WARNING: ChatGPT instructions are %d chars; check the current Custom GPT limit' % n)

def build(name):
    src = os.path.join(ROOT, 'plugins', name); dst = os.path.join(ROOT, 'portable', name)
    shutil.rmtree(dst, ignore_errors=True); os.makedirs(dst)
    for sub in os.listdir(os.path.join(src, 'skills')):
        shutil.copytree(os.path.join(src, 'skills', sub, 'references'), os.path.join(dst, 'references'), dirs_exist_ok=True)
        skill = open(os.path.join(src, 'skills', sub, 'SKILL.md'), encoding='utf-8').read()
    for f in os.listdir(os.path.join(dst, 'references')):
        fp = os.path.join(dst, 'references', f); t = open(fp, encoding='utf-8').read()
        open(fp, 'w', encoding='utf-8').write(portable(t))
    shutil.copytree(os.path.join(src, 'scripts'), os.path.join(dst, 'scripts'), ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(os.path.join(src, 'examples'), os.path.join(dst, 'examples'))
    out = ['# %s (portable edition)\n' % name,
           'Generated from the Claude Code plugin `plugins/%s/`. Do not edit here; edit the plugin and re-run `tools/build_portable.py`.\n' % name,
           '## Tool mapping\n- Browser control for inspecting the app: use your browser tool (e.g. Playwright MCP). Same safety rules apply.\n'
           '- Spec storage: a markdown folder (one file per module). Skip any step that mentions a Claude Doc or `mcp__Claude_Docs__*`.\n'
           '- Scripts: `python3 -I scripts/<name>.py` from this folder (needs `scripts/setup.sh` once for the SRS export).\n'
           '- "Agent" sections below are roles: run them as separate sessions/sub-tasks if your tool supports it, otherwise one after another.\n',
           '## Workflow\n', portable(strip_frontmatter(skill)[1]), '\n## Commands (workflows to run when the user asks)\n']
    for f in sorted(os.listdir(os.path.join(src, 'commands'))):
        meta, body = strip_frontmatter(open(os.path.join(src, 'commands', f), encoding='utf-8').read())
        out.append('### %s\n%s\n\n%s\n' % (f[:-3], portable(meta.get('description', '')), portable(body)))
    out.append('## Roles\n')
    os.makedirs(os.path.join(dst, 'prompts'))
    for f in sorted(os.listdir(os.path.join(src, 'agents'))):
        meta, body = strip_frontmatter(open(os.path.join(src, 'agents', f), encoding='utf-8').read())
        body = portable(body)
        open(os.path.join(dst, 'prompts', f), 'w', encoding='utf-8').write(body + '\n')
        out.append('### %s\n%s Full prompt: `prompts/%s`.\n' % (meta.get('name', f[:-3]), meta.get('description', ''), f))
    body = '\n'.join(out)
    open(os.path.join(dst, 'AGENTS.md'), 'w', encoding='utf-8').write(body)
    # Codex skill: same folder is a valid skill (SKILL.md with name + description; references/ and scripts/ alongside)
    desc = re.sub(r'\s+', ' ', strip_frontmatter(skill)[0].get('description', name))
    open(os.path.join(dst, 'SKILL.md'), 'w', encoding='utf-8').write('---\nname: %s\ndescription: %s\n---\n\n%s' % (name, desc, body.split('## Tool mapping', 1)[1].join(['## Tool mapping', ''])))
    build_chatgpt(name, src, dst)
    print('built', dst)

names = sys.argv[1:] or sorted(os.listdir(os.path.join(ROOT, 'plugins')))
for n in names: build(n)
