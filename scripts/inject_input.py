#!/usr/bin/env python3
import sys
import os

try:
    from evdev import UInput, ecodes
except ImportError:
    sys.exit(0)

BTN = sys.argv[1] if len(sys.argv) > 1 else 'a'

MAP = {
    'up':    (ecodes.EV_KEY, ecodes.KEY_UP),
    'down':  (ecodes.EV_KEY, ecodes.KEY_DOWN),
    'left':  (ecodes.EV_KEY, ecodes.KEY_LEFT),
    'right': (ecodes.EV_KEY, ecodes.KEY_RIGHT),
    'a':     (ecodes.EV_KEY, ecodes.BTN_SOUTH),
    'b':     (ecodes.EV_KEY, ecodes.BTN_EAST),
    'start': (ecodes.EV_KEY, ecodes.BTN_START),
    'select':(ecodes.EV_KEY, ecodes.BTN_SELECT),
}

if BTN not in MAP:
    sys.exit(1)

cap = {ecodes.EV_KEY: [v[1] for v in MAP.values()]}
ui = UInput(cap, name='retro-remote')
ev_type, code = MAP[BTN]
ui.write(ev_type, code, 1)
ui.syn()
ui.write(ev_type, code, 0)
ui.syn()
ui.close()
