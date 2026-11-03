#!/usr/bin/env bash
# One-time setup for pokit-browser (headless recon/verify). macOS or Linux. Safe to run again (finished steps are skipped).
# Installs Playwright and its Chromium into ~/.po-kit/browser (nothing global, no sudo), then runs the doctor.
# Progress: every step prints "[n/5] ..." with its time, the full log goes to ~/.po-kit/browser/setup.log, and the current
# step is kept in ~/.po-kit/browser/setup.status (one line), so an agent or a second terminal can follow it:
#   cat ~/.po-kit/browser/setup.status
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PKHOME="${POKIT_HOME:-$HOME/.po-kit}"
DEPS="$PKHOME/browser"
PW_VERSION="${POKIT_PW_VERSION:-1.63.0}"
mkdir -p "$DEPS"; LOG="$DEPS/setup.log"; STATUS="$DEPS/setup.status"; : > "$LOG"
T0=$(date +%s); N=0; TOTAL=5
step() { N=$((N+1)); S0=$(date +%s); echo "[$N/$TOTAL] $1 ..."; echo "step $N/$TOTAL: $1 (started $(date +%H:%M:%S))" > "$STATUS"; }
done_() { echo "      ok ($(( $(date +%s) - S0 )) s) ${1:-}"; }
fail() { echo "      FAILED: $1"; echo "      Log: $LOG"; echo "failed at step $N/$TOTAL: $1" > "$STATUS"; exit 1; }
# a dot every 5 s while a long command runs, so a silent download never looks frozen
run() { "$@" >> "$LOG" 2>&1 & local p=$!; while kill -0 $p 2>/dev/null; do sleep 5; kill -0 $p 2>/dev/null && printf '      ... %s s\n' $(( $(date +%s) - S0 )); done; wait $p; }

step "Check Node.js 18+"
# a non-interactive shell does not load nvm / fnm / volta / Homebrew paths: look for an existing Node before installing one
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" >/dev/null 2>&1
command -v fnm >/dev/null 2>&1 && eval "$(fnm env 2>/dev/null)"
for d in "$HOME/.volta/bin" /opt/homebrew/bin /usr/local/bin; do [ -d "$d" ] && PATH="$PATH:$d"; done
need_node() { command -v node >/dev/null 2>&1 && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 18 ]; }
if need_node; then done_ "node $(node -v)"
elif command -v brew >/dev/null 2>&1; then echo "      installing Node.js with Homebrew (1 to 3 min)"; run brew install node || fail "brew install node"; need_node || fail "Node.js still not on PATH: open a new terminal and run again"; done_ "node $(node -v)"
else fail "Node.js 18+ is missing. Install the LTS from https://nodejs.org, then run this script again"; fi

step "Install Playwright $PW_VERSION into $DEPS"
[ -f "$DEPS/package.json" ] || echo '{"private":true,"name":"pokit-browser-deps"}' > "$DEPS/package.json"
HAVE="$(node -p "try{require('$DEPS/node_modules/playwright/package.json').version}catch(e){''}")"
if [ "$HAVE" = "$PW_VERSION" ]; then done_ "already installed"
else run npm install --prefix "$DEPS" --no-audit --no-fund --loglevel=error "playwright@$PW_VERSION" || fail "npm install playwright (network? see log)"; done_; fi

step "Download Chromium for Playwright (about 150 MB the first time)"
if node "$DEPS/node_modules/playwright/cli.js" install --dry-run chromium 2>/dev/null | grep -q "Install location" && \
   [ -n "$(node -e "const p=require('$DEPS/node_modules/playwright');try{require('fs').existsSync(p.chromium.executablePath())&&console.log(1)}catch(e){}")" ]; then done_ "already installed"
elif run node "$DEPS/node_modules/playwright/cli.js" install chromium; then done_
else echo "      Chromium download failed (blocked network?). The runner will use the Google Chrome or Edge installed here, in a separate profile."; fi

step "Check the setup (doctor)"
node "$HERE/pokit-browser.mjs" doctor ${1:+--url "$1"} | sed 's/^/      /'; done_

step "Done"
echo "setup finished in $(( $(date +%s) - T0 )) s" > "$STATUS"; done_ "total $(( $(date +%s) - T0 )) s"
echo
echo "Next: sign in once (a window opens, you type the password yourself):"
echo "  node \"$HERE/pokit-browser.mjs\" login --url https://your-app.example.com"
