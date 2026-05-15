#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
export SDL_VIDEODRIVER=kmsdrm
export SDL_AUDIODRIVER=alsa
exec "${PYTHON_BIN}" "${CABILLTENDO_ROOT}/launcher.py"
