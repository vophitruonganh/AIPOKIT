#!/usr/bin/env bash
# Prints what is missing for the SRS export. Exit 1 if anything is missing.
miss=0
for c in python3 dot soffice; do command -v $c >/dev/null || { echo "MISSING: $c"; miss=1; }; done
V="${POKIT_VENV:-$HOME/.po-kit/venv}"; PY=python3; [ -x "$V/bin/python3" ] && PY="$V/bin/python3"
$PY - <<'EOF2' || miss=1
import importlib
bad = 0
for m in ("docx","fitz","PIL","openpyxl"):
    try: importlib.import_module(m)
    except Exception: print("MISSING python module:", m); bad = 1
raise SystemExit(bad)
EOF2
[ $miss = 0 ] && echo "Environment OK" || echo "Run: bash \"$(dirname "$0")/setup.sh\""
exit $miss
