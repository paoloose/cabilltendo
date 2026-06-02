#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

# Activate the project venv
source "${VENV_DIR}/bin/activate"

export SDL_VIDEODRIVER=x11
export SDL_AUDIODRIVER=alsa
export IS_RASPBERRY=true

# Clean X environment: black background, no cursor blink, no screensaver
xsetroot -solid black 2>/dev/null || true
xset s off -dpms 2>/dev/null || true

"${PYTHON_BIN}" "${CAVILLTENDO_ROOT}/bootsplash.py" || true
exec "${PYTHON_BIN}" "${CAVILLTENDO_ROOT}/launcher.py"
