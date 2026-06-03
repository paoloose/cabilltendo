# Cavilltendo

```txt
Developed by:
Adrián Gutiérrez Carbajal
Paolo Luis Flores Cóngora
Juárez Andrade Axel Yael
```

Mednafen-based console emulator for the Raspberry Pi 4 🍓

<https://github.com/user-attachments/assets/ae103b7e-595c-459e-a63b-a1d0573e3775>

## Quick start

First, install a minimal Raspberry Pi 4 OS in your Raspberry Pi. I recommend
using the official [Imager](https://www.raspberrypi.com/documentation/computers/getting-started.html#imager-install) and choosing the Raspberry Pi OS Lite.
No desktop environment is required for this emulator to work.

Once installed, login into your Raspberry, and clone this entire repository. A recommended choice
is `/opt/cavilltendo/repo`.

```bash
# Assuming your user is "pi"
sudo mkdir -p /opt/cavilltendo/repo
sudo chown pi /opt/cavilltendo/repo
sudo chgrp pi /opt/cavilltendo/repo

cd /opt/cavilltendo/repo
git clone https://github.com/paoloose/cavilltendo.git .
```

And finally, run the setup script:

```bash
sudo ./setup_raspberrypi4.sh
```

Once this script is finished, no internet connection or root is required.

In a nutshell, the script:

1. Installs system dependencies (`mednafen`, `xinit`, `python3-venv`, `pmount`, etc.)
2. Creates a Python virtual environment and install the Cavilltendo dependencies
3. Deploys rendered templates (mednafen config, systemd services)
4. Copies a full Mednafen configuration for gamepad support
5. Enables and starts the `cavilltendo` systemd service
6. Sets user groups for display, input, and USB access

**Note**: template files are filled with the variables in `config.sh`. You can customize these
variables, but they have sane defaults so you don't need to do so.

After reboot, the Pi boots directly into the game launcher with a branded splash screen.

## Clean boot (no logs)

First, enable auto-login on the virtual TTY using `raspi-config`:

```bash
sudo raspi-config
# System Options → Boot / Auto Login → Console Autologin
```

Then suppress kernel logs, systemd status lines, and the blinking cursor
to give the Pi a consumer-appliance boot experience:

**`/boot/firmware/cmdline.txt`** (append to the single line):

```txt
console=tty3 quiet silent splash loglevel=0 logo.nologo
vt.global_cursor_default=0 systemd.show_status=false
rd.udev.log_level=0 udev.log_priority=0
```

**`/boot/firmware/config.txt`**:

```txt
disable_splash=1
```

Finally, redirect the login prompt away from tty1 and clear the
welcome banners:

```bash
sudo systemctl mask getty@tty1.service
sudo systemctl unmask getty@tty2.service
sudo systemctl enable getty@tty2.service
sudo truncate -s 0 /etc/issue
sudo truncate -s 0 /etc/issue.net
sudo systemctl daemon-reload
```

## System dependencies

| Package              | Purpose                                     |
| -------------------- | ------------------------------------------- |
| `mednafen`           | Multi-system emulator (NES, SNES, GBA)      |
| `xinit`              | Minimal X server to run the Pygame launcher |
| `python3-venv`       | Python virtual environment                  |
| `pmount`             | Mounts USB drives without root privileges   |
| `fonts-freefont-ttf` | Fallback system fonts                       |

## Controls

### Raspberry Pi (gamepad only)

| Button                      | Action                   |
| --------------------------- | ------------------------ |
| D-Pad Up / Down             | Navigate ROM list        |
| A / B (Button 0 / 1)        | Launch selected game     |
| Select + Start (hold 0.5 s) | Exit launcher            |
| L1 + R1 (hold 0.5 s)        | Pause / unpause emulator |

**In-game keyboard shortcuts** (Mednafen defaults):

| Key      | Action           |
| -------- | ---------------- |
| F12      | Exit game        |
| Pause    | Pause / unpause  |
| F5 / F7  | Save / Load state |

### Desktop development (keyboard fallback)

When running the launcher directly on a desktop (without `IS_RASPBERRY`), keyboard
input is automatically enabled:

| Key     | Action               |
| ------- | -------------------- |
| Up/Down | Navigate ROM list    |
| Enter   | Launch selected game |
| Escape  | Exit launcher        |

## USB ROM auto-copy

Insert a USB stick containing ROM files and the system automatically:

1. Mounts the drive (no root required, via `pmount`)
2. Recursively scans for `.nes`, `.sfc`, `.smc`, `.gba` files
3. Copies new ROMs into the local library (`roms/from_usb/`)
4. Skips duplicates via MD5 hash comparison

If a game is running, Mednafen is briefly paused during the copy.  The launcher
refreshes the game list immediately after.

## Testing in Linux desktop distros

When testing this launcher in a full blown desktop distro **DO NOT** run the installation scripts.
They are intended for the Raspberry Pi only.

It is enough to install mednafen

```bash
sudo apt install mednafen
```

And the Python dependencies in a virtual environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install pygame evdev pyudev
```

Then start the launcher:

```bash
python3 launcher.py
```

When `IS_RASPBERRY` is not set (the default on desktop), keyboard input is
enabled as described above.
