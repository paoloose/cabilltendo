# Console emulator :3

```bash
sudo apt install build-essential pkg-config libasound2-dev libsdl2-dev libflac-dev zlib1g-dev
```

```bash
cd mednafen

./configure --prefix=$(pwd)/.local
make -j$(nproc)
make install-strip
```
