# Cabilltendo

Mednafen-based console emulator for the Raspberry Pi 4 🍓

https://github.com/user-attachments/assets/ae103b7e-595c-459e-a63b-a1d0573e3775

## Quick start

Install a simple Raspberry Pi OS that is shipped with `apt` and `systemd`.
No desktop environment is required for this emulator to work.
See <https://www.raspberrypi.com/software/operating-systems/>.

Then login in your Raspberry, copy out this entire repository, and execute

```bash
./setup_raspberrypi4.sh
```

Once this script is finished, no internet connection is required

## Using a custom embedded OS

I also developed a Docker script on top of [buildroot](https://buildroot.org/) to compile
your own embedded Linux kernel with only the specific requirements of this project.

<!--
However, this will require you to modify important parts of the setup script, specifically
the installation of dependencies (which your distro will already include), and the
deployment of `systemd` services (as you probably will be using a lightweight alternative).
-->

Take a look at the repo! <https://github.com/paoloose/buildroot>

## Controls

### Raspberry Pi (gamepad only)

| Button                      | Action                   |
| --------------------------- | ------------------------ |
| D-Pad Up / Down             | Navigate ROM list        |
| A / B (Button 0 / 1)        | Launch selected game     |
| Select + Start (hold 0.5 s) | Exit launcher            |
| L1 + R1 (hold 0.5 s)        | Pause / unpause emulator |

## Testing in Linux desktop distros

If you are trying to run this launcher in your mainstream Linux distribution, well you can!

Just **don't** run the installation scrips, are they are intended for the Raspberry Pi only.

```bash
sudo apt install build-essential pkg-config libasound2-dev libsdl2-dev libflac-dev zlib1g-dev
```

```bash
cd mednafen-git
./configure --prefix=$(pwd)/.local
touch aclocal.m4 configure Makefile.in src/Makefile.in src/drivers/Makefile.in
make -j$(nproc)
make install-strip
```

## Cross-compiling for Raspberry Pi 4 (aarch64)

```bash
sudo dpkg --add-architecture arm64 && sudo apt update
sudo apt install libsdl2-dev:arm64 libasound2-dev:arm64 libflac-dev:arm64 \
  zlib1g-dev:arm64 gettext:arm64 libgettextpo-dev:arm64 pkg-config
```

```bash
cd mednafen-git
./configure --host=aarch64-linux-gnu --prefix=$(pwd)/.local \
  CC=aarch64-linux-gnu-gcc CXX=aarch64-linux-gnu-g++
touch aclocal.m4 configure Makefile.in src/Makefile.in src/drivers/Makefile.in
make -j$(nproc)
make install-strip
```

The binary ends up in `.local/bin/mednafen`. Copy it and its runtime deps to the Raspberry Pi.
