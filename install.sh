#!/usr/bin/env bash
# AIPOKIT (po-kit) one-step installer for macOS and Linux.
#   1. unzip po-kit.zip anywhere   2. run:  bash po-kit/install.sh
# Re-run the same command with a newer po-kit.zip to update.
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
HOME_KIT="$HOME/.po-kit"; DEST="$HOME_KIT/po-kit"
echo "== po-kit installer"
command -v claude >/dev/null || { echo "Claude Code is not installed. Install it first: https://claude.com/claude-code"; exit 1; }
command -v python3 >/dev/null || { echo "python3 is missing. macOS: brew install python   Linux: sudo apt-get install python3"; exit 1; }

# 1. stable copy of the marketplace (so the unzipped folder can be deleted)
mkdir -p "$HOME_KIT"
if [ "$SRC" != "$DEST" ]; then rm -rf "$DEST.new"; cp -R "$SRC" "$DEST.new"; rm -rf "$DEST"; mv "$DEST.new" "$DEST"; fi
VER=$(python3 -c "import json;print(json.load(open('$DEST/plugins/po-kit-spec/.claude-plugin/plugin.json'))['version'])")
echo "== po-kit-spec $VER copied to $DEST"

# 2. Claude Code marketplace + plugin (user scope); a clean re-add so the marketplace always points at ~/.po-kit/po-kit
for M in aipokit po-kit; do   # po-kit = marketplace name before v1.4.4
  claude plugin uninstall "po-kit-spec@$M" >/dev/null 2>&1 || true
  claude plugin marketplace remove "$M" >/dev/null 2>&1 || true
done
claude plugin marketplace add "$DEST"
claude plugin install po-kit-spec@aipokit --scope user
claude plugin list 2>/dev/null | grep -A2 "po-kit-spec" || true

# 3. tools for the Word/PDF export (graphviz, LibreOffice, Python modules in ~/.po-kit/venv)
bash "$DEST/plugins/po-kit-spec/scripts/setup.sh"
bash "$DEST/plugins/po-kit-spec/scripts/check_env.sh" || true
echo
echo "== Done. Open a NEW Claude Code session and type /po-kit-spec:start"
