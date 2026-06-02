#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

# Activate the project venv
source "${VENV_DIR}/bin/activate"

export SDL_VIDEODRIVER=x11
export SDL_AUDIODRIVER=alsa
export IS_RASPBERRY=true

"${PYTHON_BIN}" "${CABILLTENDO_ROOT}/bootsplash.py"
exec "${PYTHON_BIN}" "${CABILLTENDO_ROOT}/launcher.py"
