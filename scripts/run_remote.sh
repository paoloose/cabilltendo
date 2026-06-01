#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

# Activate the project venv
source "${VENV_DIR}/bin/activate"

exec python3 "${REMOTE_DIR}/server.py"
