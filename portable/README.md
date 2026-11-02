# Portable editions (generated, do not edit)
Built by `python3 tools/build_portable.py` from `plugins/<tool>/`. Edit the plugin, re-run the script, commit both.

## Codex (CLI, IDE extension, desktop app)
Codex reads skills from `~/.agents/skills` (global) or `<repo>/.agents/skills`, and `AGENTS.md` from the repo root (per OpenAI's Codex customization docs). `po-kit-spec/` is a valid skill folder (`SKILL.md` + `references/` + `scripts/`).
```
bash portable/install-codex.sh po-kit-spec --global          # or: ... po-kit-spec /path/to/repo
```
Then add a browser tool so Codex can inspect your app (`~/.codex/config.toml`, or Settings > MCP servers):
```
[mcp_servers.playwright]
command = "npx"
args = ["-y", "@playwright/mcp"]
```
Start Codex in your working folder: "use the po-kit-spec skill to build a spec for <app URL>". There are no slash commands; the commands in `AGENTS.md` are workflows you ask for by name ("run the lint workflow on ./spec").
Status: not tested on Codex. The skill structure and paths follow OpenAI's docs; the Codex plugin format is not used because its file format was not documented where checked.

## ChatGPT (Custom GPT or Project)
`chatgpt/po-kit-spec/` holds `instructions.md` (paste into the GPT's Instructions, or the Project's instructions) and `knowledge/` (upload the 3 files). This edition writes and reviews specs from material you provide. It cannot crawl your app, run the lint or export an SRS; it says so in its instructions. Keep the markdown it produces: the Claude Code or Codex edition can lint and export it later.
Status: not tested in ChatGPT. OpenAI's help page lists up to 20 knowledge files per GPT; check current limits for instructions length.
