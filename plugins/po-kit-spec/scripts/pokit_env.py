"""Re-run the calling script with the po-kit venv (~/.po-kit/venv, made by setup.sh) when it exists and we are not in it.
Needed where the system Python is externally managed (macOS Homebrew, PEP 668) and `python3 -I` ignores user site-packages."""
import os, sys
VENV = os.environ.get('POKIT_VENV') or os.path.expanduser('~/.po-kit/venv')
def ensure():
    py = os.path.join(VENV, 'bin', 'python3')
    if os.path.exists(py) and os.path.realpath(sys.prefix) != os.path.realpath(VENV):
        os.execv(py, [py, '-I'] + sys.argv)
