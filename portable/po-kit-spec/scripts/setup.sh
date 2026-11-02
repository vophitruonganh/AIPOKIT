#!/usr/bin/env bash
# One-time setup for the SRS export step. Linux (apt) or macOS (Homebrew).
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="${POKIT_VENV:-$HOME/.po-kit/venv}"
if command -v apt-get >/dev/null; then
  sudo apt-get update && sudo apt-get install -y python3-pip python3-venv graphviz libreoffice fonts-liberation
elif command -v brew >/dev/null; then
  command -v dot >/dev/null || brew install graphviz
  command -v soffice >/dev/null || brew install --cask libreoffice
else
  echo "Install graphviz and LibreOffice with your package manager, then re-run."
fi
# Python modules go into a private venv; the scripts switch to it by themselves (scripts/pokit_env.py).
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --no-cache-dir --upgrade pip
"$VENV/bin/pip" install -q --no-cache-dir -r "$DIR/requirements.txt"
echo "Setup done. Python modules are in $VENV"
