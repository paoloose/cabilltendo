#!/bin/bash

# Template deployer
# -----------------
# Reads templates/ files, replaces {{VAR}} with environment-variable values,
# writes the result to the target destination.
# Any leftover {{…}} causes a hard abort.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
TEMPLATES_DIR="${CABILLTENDO_ROOT}/templates"

# --- Helper
log() { echo "[deploy]   $*" | tee -a "${SETUP_LOG}"; }
abort() { log "ABORT: $*"; exit 1; }

# --- Template engine
process_template() {
    local content="$1"
    local varname

    while IFS= read -r varname; do
        content="${content//\{\{$varname\}\}/${!varname}}"
    done < <(compgen -v 2>/dev/null | grep -E '^[A-Z][A-Z0-9_]+$' || true)

    local leftovers
    leftovers=$(echo "$content" | { grep -o '\{\{[A-Z_][A-Z0-9_]*\}\}' || true; } | sort -u)
    if [ -n "$leftovers" ]; then
        log "ERROR  Unresolved placeholders:"
        printf '%s\n' "$leftovers" | while read -r p; do log "       $p"; done
        abort "Template substitution failed - see above"
    fi

    echo "$content"
}

# --- Single-file deploy
deploy_one() {
    local tmpl_name="$1"
    local dest="$2"
    local exec_flag="${3:-0}"

    local src="${TEMPLATES_DIR}/${tmpl_name}"
    [ -f "$src" ] || abort "Template not found: $src"

    local raw content
    raw="$(<"$src")"
    content="$(process_template "$raw")" || exit 1

    local dir; dir="$(dirname "$dest")"
    mkdir -p "$dir"

    echo "$content" > "$dest"
    chmod 644 "$dest"

    if [ "$exec_flag" = "1" ]; then
        chmod +x "$dest"
        log "Created (exec)  $dest"
    else
        log "Created         $dest"
    fi
}

# --- Deploy all (built-in mapping)
deploy_all() {
    log "▸ Template directory: $TEMPLATES_DIR"
    log "▸ Target prefix:      $CABILLTENDO_ROOT"

    deploy_one "mednafen.cfg"               "$MEDNAFEN_CFG"                                          0
    deploy_one "bootsplash.service"         "/etc/systemd/system/bootsplash.service"                  0
    deploy_one "cavilltendo.service"        "/etc/systemd/system/cavilltendo.service"                 0
    deploy_one "cavilltendo-remote.service" "/etc/systemd/system/cavilltendo-remote.service"      0
}

# --- Entry point----
case "${1:-all}" in
    all)    deploy_all ;;
    one)    deploy_one "$2" "$3" "${4:-0}" ;;
    *)      abort "Usage: deploy.sh [all | one <name> <dest> [exec]]" ;;
esac
