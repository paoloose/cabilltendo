# Console emulator :3

## Native build

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
