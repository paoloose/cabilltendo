#!/usr/bin/env python3
import os

IS_RASPBERRY = 'IS_RASPBERRY' in os.environ
if IS_RASPBERRY: os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
os.environ.setdefault('SDL_AUDIODRIVER', 'alsa')

import pygame
import subprocess
import signal
import select
import threading
import time
import hashlib
import shutil
import pyudev
from os import environ, path
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple
from evdev import InputDevice, ecodes, list_devices

# -- Config (env vars with relative-path fallbacks) ----------
SCRIPT_DIR = path.dirname(path.abspath(__file__))

MEDNAFEN_BIN   = environ.get('MEDNAFEN_BIN', path.join(SCRIPT_DIR, 'mednafen/src/mednafen'))
MEDNAFEN_CFG   = environ.get('MEDNAFEN_CFG', '')
ROMS_DIR       = environ.get('ROMS_DIR', path.join(SCRIPT_DIR, 'roms'))
FONT_PIXEL     = environ.get('PIXEL_FONT', path.join(SCRIPT_DIR, 'assets/fonts/Pixelitta-Regular.ttf'))
FONT_DIGITAL   = environ.get('DIGITAL_FONT', path.join(SCRIPT_DIR, 'assets/fonts/Digital808.ttf'))
CONSOLE_LOGO   = environ.get('LOGO_IMAGE', path.join(SCRIPT_DIR, 'assets/henry.png'))
SELECTOR_IMAGE = environ.get('SELECTOR_IMAGE', path.join(SCRIPT_DIR, 'assets/selector.png'))
THUMBNAILS_DIR = environ.get('THUMBNAILS_DIR', path.join(SCRIPT_DIR, 'thumbnails'))
USB_LOG_FILE  = environ.get('USB_LOG', '/tmp/usb_roms.log')

# -- Console definitions -------------------

@dataclass(frozen=True)
class ConsoleInfo:
    label: str
    color: Tuple[int, int, int]
    thumbnail_folder: str
    extensions: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def folder_name(self) -> str:
        return self.thumbnail_folder


_CONSOLE_DATA = {
    'NES':  ConsoleInfo('NES',  (151, 67, 37),  'Nintendo_-_Nintendo_Entertainment_System', ('.nes',)),
    'SNES': ConsoleInfo('SNES', (110, 53, 156), 'Nintendo_-_Super_Nintendo_Entertainment_System', ('.sfc', '.smc')),
    'GBA':  ConsoleInfo('GBA',  (73, 107, 53),  'Nintendo_-_Game_Boy_Advance', ('.gba',)),
}

EXT_TO_CONSOLE: dict[str, ConsoleInfo] = {}
for info in _CONSOLE_DATA.values():
    for ext in info.extensions:
        EXT_TO_CONSOLE[ext] = info

UNKNOWN_CONSOLE = ConsoleInfo('???', (100, 100, 100), 'Unknown', ())
ROM_EXTENSIONS = {ext for info in _CONSOLE_DATA.values() for ext in info.extensions}

# -- UI strings -------------------
WINDOW_TITLE  = 'Cabilltendo | Sistemas Embebidos'
LOGO_TITLE    = 'CABILLTENDO'
LOGO_SUBTITLE = 'Henry Cavill Entertainment'
SECTION_TITLE = 'GAME SELECT'
NO_ROMS_MSG   = 'No ROMs found'
HINT_DPAD     = 'D-PAD = SELECT'
HINT_START    = 'START = OK'

# -- Theme -------------------
BG_DARK       = (10,  10,  15)
GOLD          = (200, 162, 60)
RED_TITLE     = (232, 64,  64)
DARK_BLUE     = (26,  26,  110)
WHITE         = (255, 255, 255)
PANEL_BG      = (0,   0,   0)
PREVIEW_BG    = (17,  17,  17)
BOTTOM_BAR    = (204, 34,  34)
ARROW_BLUE    = (68,  136, 255)
GOLD_TITLE    = (224, 192, 104)
MUTED         = (136, 136, 136)
INFO_BAR      = (5,   5,   12)
SEL_BG        = (30,  30,  60)
SEP_GRAY      = (34,  34,  34)
SCROLL_TRACK  = (60,  60,  60)

# -- Timing (mostly ms) -------------------

PATTERN_ALPHA   = 100
PATTERN_SPEED   = 0.4
BLINK_PERIOD_MS = 700
AXIS_DELAY_MS   = 180
AXIS_RATE_MS    = 80
AXIS_DEADZONE  = 0.5

HOTKEY_HOLD_S  = 0.5
HOTKEY_SELECT   = {ecodes.BTN_SELECT}
HOTKEY_START    = {ecodes.BTN_START}
HOTKEY_L1       = {ecodes.BTN_TL}
HOTKEY_R1       = {ecodes.BTN_TR}

# -- Data ---------------------

@dataclass
class RomEntry:
    name: str
    path: str
    ext: str
    console: ConsoleInfo

    @property
    def color(self) -> Tuple[int, int, int]:
        return self.console.color


@dataclass
class Thumbnails:
    title: Optional[pygame.Surface] = None
    logo: Optional[pygame.Surface] = None


def scan_roms(base_dir: str) -> list[RomEntry]:
    entries: list[RomEntry] = []
    base = Path(base_dir)
    if not base.is_dir():
        return entries
    for ext in sorted(ROM_EXTENSIONS):
        for p in sorted(base.rglob(f'*{ext}')):
            if p.name.startswith('._'):
                continue
            console = EXT_TO_CONSOLE.get(ext, UNKNOWN_CONSOLE)
            entries.append(RomEntry(p.stem, str(p), ext, console))
    return entries


# -- Layout -------------------

class Layout:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h

        self.header_y    = int(h * 0.035)
        self.box_w       = int(w * 0.42)
        self.box_h       = int(h * 0.13)

        self.panel_w     = int(w * 0.80)
        self.panel_h     = int(h * 0.62)
        self.panel_x     = (w - self.panel_w) // 2
        self.panel_y     = int(h * 0.22)
        self.radius      = max(6, int(h * 0.018))

        self.list_w      = self.panel_w // 2
        self.list_x      = self.panel_x
        self.list_y      = self.panel_y
        self.list_pad    = max(12, int(w * 0.03))
        self.item_h      = max(24, int(h * 0.048))

        self.pv_w        = self.panel_w // 2
        self.pv_x        = self.panel_x + self.list_w
        self.pv_y        = self.panel_y
        self.pv_pad      = max(10, int(w * 0.02))

        self.bottom_h    = max(40, int(h * 0.08))
        self.bottom_x    = self.panel_x
        self.bottom_y    = self.panel_y + self.panel_h
        self.bottom_w    = self.panel_w

        self.tile_sz     = max(32, int(h * 0.12))

        self.font_label  = max(10, int(h * 0.024))
        self.font_title  = max(20, int(h * 0.065))
        self.font_sub    = max(12, int(h * 0.032))
        self.font_section= max(14, int(h * 0.038))
        self.font_game   = max(13, int(h * 0.032))
        self.font_pub_lbl= max(8,  int(h * 0.016))
        self.font_pub_nm = max(10, int(h * 0.028))
        self.font_hint   = max(10, int(h * 0.024))


# -- Hotkey monitor
#    runs in a separate thread and watch for keys

class _GamepadHotkey:
    """Background thread that reads gamepad input via evdev while mednafen
    owns the display. pygame events are unavailable during emulation, so
    we read /dev/input devices directly using evdev.

    Hotkey combos (hold for ≥ 0.5 s):
      Select + Start → SIGTERM mednafen (exit game, return to launcher)
      L1 + R1        → SIGSTOP/SIGCONT mednafen (pause / unpause game)

    InputDevice file descriptors are closed on thread exit
    """

    def __init__(self, pid: int):
        self.pid = pid
        self._paused = False
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    def join(self):
        self._thread.join(timeout=3)

    @staticmethod
    def _open_gamepads():
        """Scan /dev/input for devices with key events and open them."""
        pads = []
        for p in list_devices():
            try:
                d = InputDevice(p)
                if ecodes.EV_KEY in d.capabilities(verbose=False):
                    pads.append(d)
                else:
                    d.close()
            except Exception:
                continue
        return pads

    def _run(self):
        pads = self._open_gamepads()
        if not pads:
            return

        sel = start = l1 = r1 = False
        exit_t = pause_t = 0.0

        try:
            while not self._stop.is_set():
                try:
                    os.kill(self.pid, 0)
                except ProcessLookupError:
                    return
                try:
                    fds = [p.fd for p in pads]
                    r, _, _ = select.select(fds, [], [], 0.1)
                except (OSError, ValueError):
                    break
                for fd in r:
                    for pad in pads:
                        if pad.fd != fd:
                            continue
                        try:
                            events = pad.read()
                        except Exception:
                            continue
                        for ev in events:
                            if ev.type != ecodes.EV_KEY:
                                continue
                            if ev.code in HOTKEY_SELECT:
                                sel = ev.value != 0
                            elif ev.code in HOTKEY_START:
                                start = ev.value != 0
                            elif ev.code in HOTKEY_L1:
                                l1 = ev.value != 0
                            elif ev.code in HOTKEY_R1:
                                r1 = ev.value != 0

                            now = time.monotonic()
                            if sel and start:
                                if exit_t == 0:
                                    exit_t = now
                                elif now - exit_t >= HOTKEY_HOLD_S:
                                    try:
                                        os.kill(self.pid, signal.SIGTERM)
                                    except ProcessLookupError:
                                        pass
                                    return
                            else:
                                exit_t = 0.0

                            if l1 and r1:
                                if pause_t == 0:
                                    pause_t = now
                                elif now - pause_t >= HOTKEY_HOLD_S:
                                    try:
                                        if self._paused:
                                            os.kill(self.pid, signal.SIGCONT)
                                        else:
                                            os.kill(self.pid, signal.SIGSTOP)
                                    except ProcessLookupError:
                                        pass
                                    self._paused = not self._paused
                                    pause_t = 0.0
                                    time.sleep(0.3)
                            else:
                                pause_t = 0.0
        finally:
            for pad in pads:
                try:
                    pad.close()
                except Exception:
                    pass


class _USBMonitor:
    """Background thread that watches for USB mass-storage devices using
    pyudev and automatically copies new ROMs to the local library.

    When a USB partition is added:
      1. Mounts it with pmount (no root required)
      2. Scans for ROM files recursively (skipping macOS resource forks)
      3. Copies new ROMs with MD5 dedup into ROMS_DIR/<console>/
      4. Unmounts with pumount
      5. Sets roms_dirty so the main loop refreshes the game list

    If mednafen is running, it is paused/resumed around the copy
    to prevent filesystem conflicts.
    """

    def __init__(self, roms_dir: str, log_path: str = ''):
        self.roms_dir = roms_dir
        self.log_path = log_path
        self.roms_dirty = False
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    def join(self):
        self._thread.join(timeout=3)

    @staticmethod
    def _md5(filepath: str) -> str:
        h = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()

    def _log(self, msg: str) -> None:
        if not self.log_path:
            return
        try:
            with open(self.log_path, 'a') as f:
                f.write(f'[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n')
        except OSError:
            pass

    def _find_mount(self, device_node: str) -> Optional[str]:
        try:
            result = subprocess.run(
                ['findmnt', '-unl', '-S', device_node],
                capture_output=True, text=True, timeout=5,
            )
            if result.stdout:
                return result.stdout.split()[0]
        except Exception:
            pass
        return None

    def _copy_roms(self, mount_point: str) -> int:
        copied = 0
        for root, dirs, files in os.walk(mount_point):
            for fname in files:
                if fname.startswith('._'):
                    continue
                ext = os.path.splitext(fname)[1].lower()
                console_info = EXT_TO_CONSOLE.get(ext)
                if console_info is None:
                    continue
                dest_dir = path.join(self.roms_dir, console_info.label)
                os.makedirs(dest_dir, exist_ok=True)
                src = path.join(root, fname)
                dest = path.join(dest_dir, fname)
                if path.isfile(dest):
                    if self._md5(src) == self._md5(dest):
                        continue
                    base, _ = os.path.splitext(fname)
                    dest = path.join(dest_dir, f'{base}_new{ext}')
                try:
                    shutil.copy2(src, dest)
                    copied += 1
                except OSError:
                    continue
        return copied

    def _handle_device(self, device_node: str) -> None:
        self._log(f'USB inserted: {device_node}')
        try:
            subprocess.run(
                ['pmount', device_node],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,
            )
        except Exception:
            self._log(f'pmount failed for {device_node}')
            return

        time.sleep(1)
        mount_point = self._find_mount(device_node)
        if not mount_point:
            self._log(f'No mount point for {device_node}')
            try:
                subprocess.run(
                    ['pumount', device_node],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,
                )
            except Exception:
                pass
            return

        try:
            subprocess.run(
                ['pkill', '-STOP', 'mednafen'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            copied = self._copy_roms(mount_point)
            self._log(f'Copied {copied} ROM(s) from {device_node}')
            if copied > 0:
                self.roms_dirty = True
        finally:
            subprocess.run(
                ['pkill', '-CONT', 'mednafen'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ['pumount', device_node],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,
            )
            self._log(f'Unmounted {device_node}')

    def _run(self) -> None:
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='block', device_type='partition')
        monitor.start()

        while not self._stop.is_set():
            try:
                device = monitor.poll(timeout=1)
            except Exception:
                continue
            if device is None:
                continue
            if device.action != 'add':
                continue
            device_node = device.device_node
            if not device_node:
                continue
            self._handle_device(device_node)


# -- Helpers -------------------------------------------------------------------

def _load_image(path: str) -> Optional[pygame.Surface]:
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception:
        return None


def _scale_fit(img: pygame.Surface, max_w: int, max_h: int) -> pygame.Surface:
    iw, ih = img.get_size()
    s = min(max_w / iw, max_h / ih)
    return pygame.transform.smoothscale(img, (int(iw * s), int(ih * s)))


# -- Launcher ------------------------------------------------------------------

class Launcher:
    def __init__(self) -> None:
        pygame.init()
        pygame.joystick.init()
        pygame.mouse.set_visible(False)

        info = pygame.display.Info()
        self.W = max(info.current_w, 800)
        self.H = max(info.current_h, 600)

        self.screen = pygame.display.set_mode((self.W, self.H), pygame.FULLSCREEN)
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        L = self.layout = Layout(self.W, self.H)

        # --- fonts ---
        self.font_label   = pygame.font.Font(FONT_PIXEL,   L.font_label)
        self.font_title   = pygame.font.Font(FONT_DIGITAL, L.font_title)
        self.font_sub     = pygame.font.Font(FONT_PIXEL,   L.font_sub)
        self.font_section = pygame.font.Font(FONT_DIGITAL, L.font_section)
        self.font_game    = pygame.font.Font(FONT_DIGITAL, L.font_game)
        self.font_pub_lbl = pygame.font.Font(FONT_PIXEL,   L.font_pub_lbl)
        self.font_pub_nm  = pygame.font.Font(FONT_DIGITAL, L.font_pub_nm)
        self.font_hint    = pygame.font.Font(FONT_PIXEL,   L.font_hint)

        # --- pattern background ---
        self.tile: Optional[pygame.Surface] = None
        self.pattern_surface: Optional[pygame.Surface] = None
        self.console_logo_img: Optional[pygame.Surface] = None
        if raw := _load_image(CONSOLE_LOGO):
            self.console_logo_img = _scale_fit(raw, int(L.panel_w * 0.35), int(L.panel_h * 0.35))
            self.tile = pygame.transform.smoothscale(raw, (L.tile_sz, L.tile_sz))
            self.tile.set_alpha(PATTERN_ALPHA)
            self._build_pattern()

        # --- selector cursor ---
        self.selector_img: Optional[pygame.Surface] = None
        raw_sel = _load_image(SELECTOR_IMAGE)
        if raw_sel:
            sel_sz = int(L.item_h * 0.8)
            self.selector_img = pygame.transform.smoothscale(raw_sel, (sel_sz, sel_sz))

        # --- ROMs ---
        self.roms = scan_roms(ROMS_DIR)
        self.thumbnails: dict[str, Thumbnails] = {}
        self._load_thumbnails()
        self.selected = 0
        self.scroll_offset = 0

        # --- animation state ---
        self.blink_timer = 0.0
        self.blink_visible = True
        self.pattern_offset = 0.0

        # --- input state ---
        self._select_held = False
        self._start_held = False
        self.joy_up_ms = 0
        self.joy_down_ms = 0
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

        self.running = True

        self.usb_monitor = _USBMonitor(ROMS_DIR, USB_LOG_FILE)
        self.usb_monitor.start()

    # -- thumbnails --------------------------------------------------------

    def _build_pattern(self) -> None:
        ts = self.layout.tile_sz
        pw, ph = self.W + ts * 2, self.H + ts * 2
        self.pattern_surface = pygame.Surface((pw, ph))
        self.pattern_surface.fill(BG_DARK)
        for x in range(0, pw, ts):
            for y in range(0, ph, ts):
                self.pattern_surface.blit(self.tile, (x, y))

    def _load_thumbnails(self) -> None:
        if not path.isdir(THUMBNAILS_DIR):
            return
        for rom in self.roms:
            folder = rom.console.thumbnail_folder
            if not folder:
                continue
            title_p = path.join(THUMBNAILS_DIR, folder, 'Named_Titles', f'{rom.name}.png')
            logo_p = path.join(THUMBNAILS_DIR, folder, 'Named_Logos', f'{rom.name}.png')
            thumb = Thumbnails()
            if path.isfile(title_p):
                thumb.title = _load_image(title_p)
            if path.isfile(logo_p):
                thumb.logo = _load_image(logo_p)
            if thumb.title or thumb.logo:
                self.thumbnails[rom.path] = thumb

    def _refresh_roms(self) -> None:
        self.roms = scan_roms(ROMS_DIR)
        self.thumbnails = {}
        self._load_thumbnails()
        self.selected = 0
        self.scroll_offset = 0

    # -- navigation --------------------------------------------------------

    @property
    def _visible_count(self) -> int:
        L = self.layout
        usable = L.panel_h - L.list_pad * 2 - self.font_section.get_height() - max(6, int(L.h * 0.012))
        return max(1, usable // L.item_h)

    def ensure_visible(self) -> None:
        max_vis = self._visible_count
        if self.selected < self.scroll_offset:
            self.scroll_offset = self.selected
        elif self.selected >= self.scroll_offset + max_vis:
            self.scroll_offset = self.selected - max_vis + 1

    def _navigate(self, delta: int) -> None:
        n = self.selected + delta
        if 0 <= n < len(self.roms):
            self.selected = n
            self.ensure_visible()

    def _axis_nav(self, axis_val: float, timer: int) -> int:
        """Return updated timer (ms) after handling axis navigation."""
        if abs(axis_val) < AXIS_DEADZONE:
            return 0
        now = pygame.time.get_ticks()
        if now - timer < AXIS_DELAY_MS:
            return timer
        self._navigate(-1 if axis_val < 0 else 1)
        return now

    # -- drawing ----------

    def _draw_bg(self) -> None:
        if self.pattern_surface is None:
            self.screen.fill(BG_DARK)
            return
        ts = self.layout.tile_sz
        dx = int(self.pattern_offset) % ts
        dy = int(self.pattern_offset) % ts
        self.screen.blit(self.pattern_surface, (-dx, -dy))

    def _draw_header(self) -> None:
        L = self.layout
        cx = self.W // 2
        y = L.header_y

        box_r = pygame.Rect(cx - L.box_w // 2, y, L.box_w, L.box_h)
        bw = max(2, int(L.h * 0.007))
        pygame.draw.rect(self.screen, GOLD, box_r, width=bw, border_radius=L.radius)
        inner = box_r.inflate(-int(L.w * 0.012), -int(L.h * 0.012))
        pygame.draw.rect(self.screen, BG_DARK, inner,
                         border_radius=max(4, L.radius - 4))

        ts = self.font_title.render(LOGO_TITLE, True, RED_TITLE)
        shadow = self.font_title.render(LOGO_TITLE, True, DARK_BLUE)
        tx = cx - ts.get_width() // 2
        ty = box_r.y + max(2, int(L.h * 0.008))
        self.screen.blit(shadow, (tx + 2, ty + 2))
        self.screen.blit(ts, (tx, ty))

        sub = self.font_title.render(LOGO_SUBTITLE, True, GOLD)
        self.screen.blit(sub, (cx - sub.get_width() // 2,
                                ty + ts.get_height()))

    def _draw_panel(self) -> None:
        L = self.layout
        r = pygame.Rect(L.panel_x, L.panel_y, L.panel_w, L.panel_h)
        pygame.draw.rect(self.screen, PANEL_BG, r, border_radius=L.radius)
        sep_x = L.panel_x + L.list_w
        pygame.draw.line(self.screen, SEP_GRAY,
                         (sep_x, L.panel_y + 8), (sep_x, L.panel_y + L.panel_h - 8), 2)

    def _draw_game_list(self) -> None:
        L = self.layout
        x = L.list_x + L.list_pad
        y = L.list_y + L.list_pad

        sec = self.font_section.render(SECTION_TITLE, True, GOLD_TITLE)
        self.screen.blit(sec, (x, y))
        y += sec.get_height() + max(6, int(L.h * 0.012))

        if not self.roms:
            self.screen.blit(
                self.font_game.render(NO_ROMS_MSG, True, MUTED), (x, y))
            return

        max_vis = self._visible_count
        visible = self.roms[self.scroll_offset:self.scroll_offset + max_vis]
        for i, rom in enumerate(visible):
            idx = self.scroll_offset + i
            iy = y + i * L.item_h
            is_sel = idx == self.selected

            if is_sel:
                sel_r = pygame.Rect(
                    x - 6, iy - 2, L.list_w - L.list_pad * 2 + 12, L.item_h)
                pygame.draw.rect(self.screen, SEL_BG, sel_r, border_radius=4)

            self._draw_selector(x, iy, L.item_h, is_sel)

            ns = self.font_game.render(rom.name, True, WHITE)
            max_w = L.list_x + L.list_w - L.list_pad - (x + 60) - 4
            if ns.get_width() > max_w and max_w > 0:
                ns = ns.subsurface((0, 0, max_w, ns.get_height()))
            self.screen.blit(ns, (x + 60,
                                  iy + (L.item_h - ns.get_height()) // 2))

        # --- scrollbar ---
        total = len(self.roms)
        if total > max_vis:
            scroll_top = y
            scroll_bot = L.list_y + L.panel_h - L.list_pad
            scroll_area = scroll_bot - scroll_top
            track_h = max(30, int(max_vis / total * scroll_area))
            track_y = scroll_top + int(self.scroll_offset / total * scroll_area)
            bar_x = L.panel_x + L.list_w - 10
            pygame.draw.rect(self.screen, SCROLL_TRACK,
                             (bar_x, track_y, 5, track_h), border_radius=2)
            thumb_h = max(14, int(max_vis / total * track_h))
            pygame.draw.rect(self.screen, GOLD,
                             (bar_x, track_y, 5, thumb_h), border_radius=2)

    def _draw_selector(self, x: int, iy: int, item_h: int, is_sel: bool) -> None:
        if not is_sel:
            return
        if self.selector_img:
            sel_y = iy + (item_h - self.selector_img.get_height()) // 2
            cpy = self.selector_img.copy()
            cpy.set_alpha(255 if self.blink_visible else 60)
            self.screen.blit(cpy, (x, sel_y))
        elif self.blink_visible:
            pts = [(x + 2, iy + item_h // 2 - 5),
                   (x + 10, iy + item_h // 2),
                   (x + 2, iy + item_h // 2 + 5)]
            pygame.draw.polygon(self.screen, ARROW_BLUE, pts)

    def _draw_preview(self) -> None:
        L = self.layout
        px = L.pv_x + L.pv_pad
        py = L.pv_y + L.pv_pad
        pw = L.pv_w - L.pv_pad * 2
        ph = L.panel_h - L.pv_pad * 2

        pygame.draw.rect(self.screen, PREVIEW_BG,
                         pygame.Rect(px, py, pw, ph), border_radius=6)

        if not self.roms:
            ns = self.font_game.render(NO_ROMS_MSG, True, MUTED)
            self.screen.blit(ns, (px + pw // 2 - ns.get_width() // 2,
                                   py + ph // 2 - ns.get_height() // 2))
            return

        rom = self.roms[self.selected]
        thumbs = self.thumbnails.get(rom.path, Thumbnails())

        info_h   = int(ph * 0.18)
        info_y   = py + ph - info_h
        img_area = info_y - py

        iw = int(pw * 0.92)
        ix = px + (pw - iw) // 2
        iy = py + int(L.h * 0.01)

        if thumbs.title:
            scaled = _scale_fit(thumbs.title, iw, int(img_area * 0.93))
            sw, sh = scaled.get_size()
            self.screen.blit(scaled, (ix + (iw - sw) // 2,
                                       iy + int(img_area * 0.93 - sh) // 2))
        elif self.console_logo_img:
            la = pygame.Rect(ix, iy, iw, int(img_area * 0.93))
            pygame.draw.rect(self.screen, rom.color, la, border_radius=4)
            pygame.draw.rect(self.screen, (85, 85, 85), la, width=2, border_radius=4)
            lw, lh = self.console_logo_img.get_size()
            self.screen.blit(self.console_logo_img,
                             (ix + (iw - lw) // 2, iy + int(img_area * 0.93 - lh) // 2))
        else:
            la = pygame.Rect(ix, iy, iw, int(img_area * 0.93))
            pygame.draw.rect(self.screen, rom.color, la, border_radius=4)

        # --- info bar (logo + text, Netflix-style)
        pygame.draw.rect(self.screen, INFO_BAR,
                         pygame.Rect(px, info_y, pw, info_h))

        pad = int(pw * 0.05)
        text_x = px + pad
        if thumbs.logo:
            logo_scaled = _scale_fit(thumbs.logo, int(pw * 0.38), int(info_h * 0.85))
            lw, lh = logo_scaled.get_size()
            lx = px + pad
            ly = info_y + (info_h - lh) // 2
            self.screen.blit(logo_scaled, (lx, ly))
            text_x = lx + lw + int(pw * 0.04)

        parts = [
            self.font_section.render(rom.console.label, True, GOLD_TITLE),
            self.font_game.render(rom.name, True, WHITE),
        ]
        max_text_w = px + pw - pad - text_x
        line_h = max(s.get_height() for s in parts)
        total_h = sum(line_h for _ in parts) + 6
        ty = info_y + (info_h - total_h) // 2
        for s in parts:
            if s.get_width() > max_text_w:
                s = s.subsurface((0, 0, max_text_w, s.get_height()))
            self.screen.blit(s, (text_x, ty))
            ty += line_h + 3

    def _draw_bottom_bar(self) -> None:
        L = self.layout
        br = pygame.Rect(L.bottom_x, L.bottom_y, L.bottom_w, L.bottom_h)
        pygame.draw.rect(self.screen, BOTTOM_BAR, br, border_radius=L.radius)

        pad = max(16, int(L.w * 0.03))
        hint_y = L.bottom_y + (L.bottom_h - int(L.h * 0.03)) // 2
        icon_sz = max(10, int(L.h * 0.025))

        lx = L.bottom_x + pad
        pygame.draw.rect(self.screen, WHITE, (lx, hint_y + 2, icon_sz, icon_sz))
        pygame.draw.rect(self.screen, BOTTOM_BAR,
                         (lx + icon_sz * 0.3, hint_y, icon_sz * 0.4, icon_sz + 4))
        pygame.draw.rect(self.screen, BOTTOM_BAR,
                         (lx, hint_y + icon_sz * 0.35, icon_sz, icon_sz * 0.4))
        h1 = self.font_game.render(HINT_DPAD, True, WHITE)
        self.screen.blit(h1, (lx + icon_sz + 10,
                              hint_y + (icon_sz + 4 - h1.get_height()) // 2))

        rx = L.bottom_x + L.bottom_w - pad
        cx = rx - int(L.w * 0.07)
        pygame.draw.circle(self.screen, WHITE, (cx, hint_y + icon_sz // 2 + 2),
                           icon_sz // 2 + 1)
        h2 = self.font_game.render(HINT_START, True, WHITE)
        self.screen.blit(h2, (cx + icon_sz // 2 + 8,
                              hint_y + (icon_sz + 4 - h2.get_height()) // 2))

    def draw(self) -> None:
        self._draw_bg()
        self._draw_header()
        self._draw_panel()
        self._draw_game_list()
        self._draw_preview()
        self._draw_bottom_bar()

    # -- input ------------------

    def _launch_current(self) -> None:
        if not self.roms:
            return
        rom = self.roms[self.selected]
        if not path.isfile(MEDNAFEN_BIN):
            return
        pygame.display.quit()
        cmd = [MEDNAFEN_BIN]
        if MEDNAFEN_CFG and path.isfile(MEDNAFEN_CFG):
            cmd += ['-cfgfile', MEDNAFEN_CFG]
        cmd.append(rom.path)
        proc = subprocess.Popen(cmd)
        hotkey = _GamepadHotkey(proc.pid)
        hotkey.start()
        try:
            proc.wait()
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
        hotkey.stop()
        hotkey.join()
        self.screen = pygame.display.set_mode((self.W, self.H), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)

    def handle_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.JOYHATMOTION:
                if event.value in ((0, 1), (0, -1)):
                    self._navigate(1 if event.value == (0, -1) else -1)

            elif event.type == pygame.JOYAXISMOTION:
                if event.axis == 1:
                    if event.value < -AXIS_DEADZONE:
                        self.joy_up_ms = self._axis_nav(event.value, self.joy_up_ms)
                    elif event.value > AXIS_DEADZONE:
                        self.joy_down_ms = self._axis_nav(event.value, self.joy_down_ms)
                    else:
                        self.joy_up_ms = self.joy_down_ms = 0

            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button in (0, 1):
                    self._launch_current()
                elif event.button in (6, 8):
                    self._select_held = True
                elif event.button in (7, 9):
                    self._start_held = True

            elif event.type == pygame.JOYBUTTONUP:
                if event.button in (6, 8):
                    self._select_held = False
                elif event.button in (7, 9):
                    self._start_held = False

        if self._select_held and self._start_held:
            self.running = False

        if self.joystick:
            now = pygame.time.get_ticks()
            try:
                av = self.joystick.get_axis(1)
                if av < -AXIS_DEADZONE and now - self.joy_up_ms > AXIS_RATE_MS:
                    self._navigate(-1)
                    self.joy_up_ms = now
                elif av > AXIS_DEADZONE and now - self.joy_down_ms > AXIS_RATE_MS:
                    self._navigate(1)
                    self.joy_down_ms = now
            except Exception:
                pass

    # -- main loop ------------------

    def run(self) -> None:
        while self.running:
            dt = self.clock.get_time()
            self.blink_timer += dt
            if self.blink_timer >= BLINK_PERIOD_MS:
                self.blink_timer = 0.0
                self.blink_visible = not self.blink_visible

            self.pattern_offset = (
                self.pattern_offset + PATTERN_SPEED * dt / 16.0) % 10000.0

            if self.usb_monitor.roms_dirty:
                self.usb_monitor.roms_dirty = False
                self._refresh_roms()

            self.handle_input()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        self.usb_monitor.stop()
        self.usb_monitor.join()
        pygame.quit()


if __name__ == '__main__':
    Launcher().run()
