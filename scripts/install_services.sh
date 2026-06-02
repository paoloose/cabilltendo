#!/bin/bash

# -- Systemd activation

set -exuo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
log() { echo "[systemd]  $*" | tee -a "${SETUP_LOG}"; }

log "Reloading systemd …"
systemctl daemon-reload

# Bootsplash is embedded in run_launcher.sh; disable standalone service if stale
systemctl disable --now bootsplash.service 2>/dev/null || true

log "Enabling services …"
systemctl enable cavilltendo.service

log "All services enabled."
