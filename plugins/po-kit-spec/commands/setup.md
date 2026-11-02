---
description: Check and install the tools the Word/PDF export needs (graphviz, LibreOffice, Python modules in ~/.po-kit/venv). Usage - /po-kit-spec:setup
allowed-tools: Bash
---
1. Run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/check_env.sh`. If it prints "Environment OK", say so and stop.
2. Otherwise tell the user in one line what is missing and that `scripts/setup.sh` installs it (Homebrew on macOS, apt on Linux with sudo, Python modules in a private venv at `~/.po-kit/venv`, nothing system-wide for Python). Run it after the user says yes, then run `check_env.sh` again and report.
