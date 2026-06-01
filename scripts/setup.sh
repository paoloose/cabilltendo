#!/bin/bash

# ---------------------------
# Cabilltendo: main setup script
#
# Run from the repo root:
#    sudo bash scripts/setup.sh
#
# Override any config variable via environment:
#    CABILLTENDO_ROOT=/custom/path sudo bash scripts/setup.sh
#
# Templates live in   ../templates/   (relative to this script)
# Config defaults in  config.sh
# ---------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export CABILLTENDO_ROOT="${CABILLTENDO_ROOT:-$(dirname "$SCRIPT_DIR")}"
source "${SCRIPT_DIR}/config.sh"

log() { echo "[setup]    $*" | tee -a "${SETUP_LOG}"; }
abort() { log "ABORT: $*"; exit 1; }

if [ "$(id -u)" -ne 0 ]; then abort "This script must be run as root."; fi

touch "${SETUP_LOG}"
log " ▗▄▄▖▗▞▀▜▌▗▖   ▄ █ █    ■  ▗▞▀▚▖▄▄▄▄     ▐▌ ▄▄▄  "
log "▐▌   ▝▚▄▟▌▐▌   ▄ █ █ ▗▄▟▙▄▖▐▛▀▀▘█   █    ▐▌█   █ "
log "▐▌        ▐▛▀▚▖█ █ █   ▐▌  ▝▚▄▄▖█   █ ▗▞▀▜▌▀▄▄▄▀ "
log "▝▚▄▄▖     ▐▙▄▞▘█ █ █   ▐▌             ▝▚▄▟▌      "
log "                       ▐▌                        "
log "                                                 "
log " Cabilltendo Setup"
log "   root     = $CABILLTENDO_ROOT"
log ""

# ---------------------------
# 1.  INSTALL DEPENDENCIES
# ---------------------------
log "── Installing dependencies ──"
apt-get update -qq
apt-get install -y -qq \
    nodm \
    mednafen \
    python3-venv \
    python3-pygame \
    python3-evdev \
    python3-pyudev \
    python3-flask \
    pmount \
    fonts-freefont-ttf \
    > /dev/null 2>&1 || abort "Failed to install dependencies."
log "  Dependencies installed."

# ---------------------------
# 1b. PYTHON VENV
# ---------------------------
log "── Setting up Python venv ──"
if [ ! -d "${VENV_DIR}" ]; then
    sudo -u "${USER_NAME}" python3 -m venv --system-site-packages "${VENV_DIR}"
    log "  Created venv at ${VENV_DIR}"
else
    log "  Venv already exists at ${VENV_DIR}"
fi

# ---------------------------
# 2.  DEPLOY  (render templates)
# ---------------------------
log "── Deploying templates ──"
bash "${SCRIPT_DIR}/deploy.sh" all

# ---------------------------
# 2.  INSTALL SERVICES
# ---------------------------
log "── Installing services ──"
bash "${SCRIPT_DIR}/install_services.sh"

# ---------------------------
# 3.  PERMISSIONS
# ---------------------------
log "── Setting ownership ──"
chown -R "${USER_NAME}:${USER_NAME}" "${CABILLTENDO_ROOT}"
usermod -aG plugdev,video,input,tty "${USER_NAME}"

log "============================================================"
log " Cabilltendo setup completed!"
log ""
log "   Project   : ${CABILLTENDO_ROOT}"
log "   ROMs      : ${ROMS_DIR}"
log "   Frontend  : ${CABILLTENDO_ROOT}/launcher.py"
log "   Remote    : http://<pi-ip>:${REMOTE_PORT}"
log "   Log       : ${SETUP_LOG}"
log ""
log "   Reboot to start"
log "============================================================"
