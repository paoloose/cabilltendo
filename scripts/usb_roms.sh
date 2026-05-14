#!/bin/bash

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
DEVICE="/dev/$1"

echo "[$(date)] USB inserted: $DEVICE" >> "$USB_LOG"

mkdir -p "$USB_MOUNT"
mount -o ro "$DEVICE" "$USB_MOUNT" 2>>"$USB_LOG" || exit 1

pkill -STOP mednafen 2>/dev/null || true

declare -A EXT_MAP=([nes]="NES" [sfc]="SNES" [smc]="SNES" [gba]="GBA")
COPIED=0

for ext in "${!EXT_MAP[@]}"; do
    sys="${EXT_MAP[$ext]}"
    dest_dir="$ROMS_DIR/$sys"
    mkdir -p "$dest_dir"
    while IFS= read -r -d '' rom; do
        fname="$(basename "$rom")"
        dest="$dest_dir/$fname"
        if [ -f "$dest" ]; then
            src_hash="$(md5sum "$rom"  | cut -d' ' -f1)"
            dst_hash="$(md5sum "$dest" | cut -d' ' -f1)"
            if [ "$src_hash" = "$dst_hash" ]; then
                echo "SKIP (dup): $fname" >> "$USB_LOG"
                continue
            fi
            dest="$dest_dir/${fname%.*}_new.$ext"
        fi
        cp "$rom" "$dest"
        echo "COPIED [$sys]: $fname" >> "$USB_LOG"
        COPIED=$((COPIED + 1))
    done < <(find "$USB_MOUNT" -iname "*.$ext" -print0)
done

umount "$USB_MOUNT" 2>/dev/null || true
touch "$USB_FLAG"
pkill -CONT mednafen 2>/dev/null || true
echo "Done. Copied: $COPIED" >> "$USB_LOG"
