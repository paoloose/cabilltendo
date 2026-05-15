#!/bin/bash

# -- Systemd activation

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
log() { echo "[systemd]  $*" | tee -a "${SETUP_LOG}"; }

log "Reloading systemd …"
systemctl daemon-reload

log "Enabling services …"
systemctl enable bootsplash.service
systemctl enable cavilltendo.service
systemctl enable cavilltendo-remote.service

log "All services enabled."
