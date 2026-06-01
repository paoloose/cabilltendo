#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

# Activate the project venv
source "${VENV_DIR}/bin/activate"

export SDL_VIDEODRIVER=x11
export SDL_AUDIODRIVER=alsa
export IS_RASPBERRY=true

exec python3 "${CABILLTENDO_ROOT}/launcher.py"
