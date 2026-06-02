#!/bin/bash

# Sourced by systemd by wrapper script
# Every variable respects the environment:  export VAR="${VAR:-default}"

export CAVILLTENDO_ROOT="${CAVILLTENDO_ROOT:-$(dirname "$(dirname "${BASH_SOURCE[0]}")")}"
export VENV_DIR="${VENV_DIR:-${CAVILLTENDO_ROOT}/.venv}"
export PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"

# --- Display (nodm / X11)
export DISPLAY="${DISPLAY:-:0}"

# --- Paths used by launcher.py at runtime
export MEDNAFEN_BIN="${MEDNAFEN_BIN:-mednafen}"
export ROMS_DIR="${ROMS_DIR:-${CAVILLTENDO_ROOT}/roms}"
export THUMBNAILS_DIR="${THUMBNAILS_DIR:-${CAVILLTENDO_ROOT}/thumbnails}"
export PIXEL_FONT="${PIXEL_FONT:-${CAVILLTENDO_ROOT}/assets/fonts/Pixelitta-Regular.ttf}"
export DIGITAL_FONT="${DIGITAL_FONT:-${CAVILLTENDO_ROOT}/assets/fonts/Digital808.ttf}"
export LOGO_IMAGE="${LOGO_IMAGE:-${CAVILLTENDO_ROOT}/assets/console_logo.png}"
export SELECTOR_IMAGE="${SELECTOR_IMAGE:-${CAVILLTENDO_ROOT}/assets/selector.png}"
export USB_LOG="${USB_LOG:-/tmp/usb_roms.log}"

# --- Paths used by the deploy step (templates)
export SCRIPTS_DIR="${SCRIPTS_DIR:-${CAVILLTENDO_ROOT}/scripts}"
export REMOTE_DIR="${REMOTE_DIR:-${CAVILLTENDO_ROOT}/remote}"
export MEDNAFEN_CFG="${MEDNAFEN_CFG:-${CAVILLTENDO_ROOT}/mednafen_cfg/mednafen.cfg}"
export INJECT_SCRIPT="${INJECT_SCRIPT:-${SCRIPTS_DIR}/inject_input.py}"
export REMOTE_SERVER="${REMOTE_SERVER:-${REMOTE_DIR}/server.py}"
export BOOT_SOUND="${BOOT_SOUND:-${CAVILLTENDO_ROOT}/assets/boot.ogg}"

# --- Networking & user
export REMOTE_PORT="${REMOTE_PORT:-8080}"
export USER_NAME="${USER_NAME:-pi}"
export SCREEN_WIDTH="${SCREEN_WIDTH:-1920}"
export SCREEN_HEIGHT="${SCREEN_HEIGHT:-1080}"

export SETUP_LOG="${SETUP_LOG:-/tmp/cavilltendo_setup.log}"
