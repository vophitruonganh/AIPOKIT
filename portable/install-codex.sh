#!/usr/bin/env bash
# Install po-kit-<tool> as a Codex skill.
# Usage: install-codex.sh <tool> [--global | <repo dir>]     e.g. install-codex.sh po-kit-spec --global
# Codex reads skills from ~/.agents/skills (global) or <repo>/.agents/skills (per repo), and AGENTS.md from the repo root.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
TOOL="${1:?tool name, e.g. po-kit-spec}"; TARGET="${2:---global}"
[ -d "$HERE/$TOOL" ] || { echo "unknown tool: $TOOL"; exit 1; }
if [ "$TARGET" = "--global" ]; then DEST="$HOME/.agents/skills"; else DEST="$TARGET/.agents/skills"; fi
mkdir -p "$DEST"; rm -rf "$DEST/$TOOL"; cp -r "$HERE/$TOOL" "$DEST/$TOOL"
echo "Installed skill $TOOL to $DEST/$TOOL"
echo
echo "Next steps"
echo "1. Browser tool for crawling the app: add to ~/.codex/config.toml (or use Settings > MCP servers in the desktop app):"
echo "   [mcp_servers.playwright]"
echo "   command = \"npx\""
echo "   args = [\"-y\", \"@playwright/mcp\"]"
echo "2. SRS export needs Python, Graphviz, LibreOffice: bash \"$DEST/$TOOL/scripts/setup.sh\""
echo "3. Start Codex in your working folder and say: use the $TOOL skill to build a spec for <app URL>"
