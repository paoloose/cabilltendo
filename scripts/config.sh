#!/bin/bash

# Sourced by systemd by wrapper script
# Every variable respects the environment:  export VAR="${VAR:-default}"

export CABILLTENDO_ROOT="${CABILLTENDO_ROOT:-$(dirname "$(dirname "${BASH_SOURCE[0]}")")}"
export PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"

# --- Paths used by launcher.py at runtime
export MEDNAFEN_BIN="${MEDNAFEN_BIN:-mednafen}"
export ROMS_DIR="${ROMS_DIR:-${CABILLTENDO_ROOT}/roms}"
export THUMBNAILS_DIR="${THUMBNAILS_DIR:-${CABILLTENDO_ROOT}/thumbnails}"
export PIXEL_FONT="${PIXEL_FONT:-${CABILLTENDO_ROOT}/assets/fonts/Pixelitta-Regular.ttf}"
export DIGITAL_FONT="${DIGITAL_FONT:-${CABILLTENDO_ROOT}/assets/fonts/Digital808.ttf}"
export LOGO_IMAGE="${LOGO_IMAGE:-${CABILLTENDO_ROOT}/assets/console_logo.png}"
export SELECTOR_IMAGE="${SELECTOR_IMAGE:-${CABILLTENDO_ROOT}/assets/selector.png}"
export USB_FLAG="${USB_FLAG:-/tmp/roms_updated}"

# --- Paths used by the deploy step (templates)
export SCRIPTS_DIR="${SCRIPTS_DIR:-${CABILLTENDO_ROOT}/scripts}"
export REMOTE_DIR="${REMOTE_DIR:-${CABILLTENDO_ROOT}/remote}"
export MEDNAFEN_CFG="${MEDNAFEN_CFG:-${CABILLTENDO_ROOT}/mednafen_cfg/mednafen.cfg}"
export USB_SCRIPT="${USB_SCRIPT:-${SCRIPTS_DIR}/usb_roms.sh}"
export INJECT_SCRIPT="${INJECT_SCRIPT:-${SCRIPTS_DIR}/inject_input.py}"
export REMOTE_SERVER="${REMOTE_SERVER:-${REMOTE_DIR}/server.py}"
export BOOT_SOUND="${BOOT_SOUND:-${CABILLTENDO_ROOT}/assets/boot.ogg}"

# --- Runtime paths (used by usb_roms.sh)
export USB_MOUNT="${USB_MOUNT:-/mnt/retro_usb}"
export USB_LOG="${USB_LOG:-/tmp/usb_roms.log}"

# --- Networking & user
export REMOTE_PORT="${REMOTE_PORT:-8080}"
export USER_NAME="${USER_NAME:-pi}"
export SCREEN_WIDTH="${SCREEN_WIDTH:-1920}"
export SCREEN_HEIGHT="${SCREEN_HEIGHT:-1080}"

export SETUP_LOG="${SETUP_LOG:-/tmp/cavilltendo_setup.log}"
