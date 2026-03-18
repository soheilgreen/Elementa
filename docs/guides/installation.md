# Installation

## Requirements

| Requirement | Version |
|------------|---------|
| Python | 3.10 – 3.12 |
| Operating System | Windows 10+, macOS 12+, Linux (Ubuntu 22.04+) |

!!! note "System dependencies"
    `gmsh` ships as a self-contained Python wheel on all major platforms — no separate gmsh installation is required.

---

## Install from PyPI (recommended)

```bash
pip install elementa
```

Verify the installation:

```bash
elementa --version   # prints version and exits (if supported)
python -c "import elementa; print(elementa.__version__)"
```

---

## Install from Source

```bash
git clone https://github.com/soheilgreen/elementa.git
cd elementa
pip install -e ".[dev]"
```

The `[dev]` extra installs `ruff` and `pytest` for development.

---

## Virtual Environment (recommended)

=== "Linux / macOS"

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install elementa-fem
    ```

=== "Windows"

    ```bat
    python -m venv .venv
    .venv\Scripts\activate
    pip install elementa-fem
    ```

---

## Platform Notes

### Linux

On headless servers, a virtual display is required for the Qt GUI:

```bash
sudo apt-get install libgl1-mesa-glx libglib2.0-0
# If no display server is available:
pip install PyVirtualDisplay
```

### macOS

On Apple Silicon, install Rosetta 2 if the gmsh wheel does not yet have a native arm64 build:

```bash
softwareupdate --install-rosetta
```

### Windows

Ensure you are using a 64-bit Python distribution. The Microsoft Visual C++ redistributable is required (usually already present).

---

## Upgrading

```bash
pip install --upgrade elementa
```

---

## Uninstalling

```bash
pip uninstall elementa
```
