# ArchClean

![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?logo=arch-linux&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![GTK4](https://img.shields.io/badge/GTK-4-4A86CF?logo=gtk&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

**ArchClean** is a lightweight system cleaner for Arch Linux, built with Python, GTK 4, and Libadwaita.

It helps identify and remove unnecessary files to free up disk space through a simple graphical interface.

## Features

- **Pacman Cache** — Remove cached package archives.
- **User Cache** — Clean application caches in `~/.cache`.
- **System Logs** — Clean eligible system log files.
- **System Journal** — Remove old systemd journal entries.
- **Orphan Packages** — Find packages that are no longer required.
- **Browser Cache** — Clean supported Firefox, Chrome, Chromium, and Brave caches.

### Interface

- Modern GTK 4 and Libadwaita design.
- Automatic dark and light theme support.
- Scan and clean controls with progress indicators.
- Selected file size display.
- Confirmation dialogs and notifications.
- Individual category cleaning.
- **Scan All** and **Clean All** options.

### Security

- Uses Polkit authentication for privileged system operations.
- Separates user-level and system-level cleanup.
- Requires confirmation before deleting selected items.

## Requirements

- Arch Linux or an Arch-based distribution
- Python 3.10+
- GTK 4
- Libadwaita
- PyGObject

Install the required dependencies:

```bash
sudo pacman -S python python-gobject gtk4 libadwaita
```

## Installation

### Option 1: Install with pipx

Install pipx:

```bash
sudo pacman -S python-pipx
```

Clone the repository and install ArchClean:

```bash
git clone https://github.com/salih-ari/ArchClean.git
cd ArchClean
pipx install --system-site-packages .
```

Launch the application:

```bash
archclean
```

### Option 2: Build with PKGBUILD

```bash
git clone https://github.com/salih-ari/ArchClean.git
cd ArchClean
makepkg -si
```

### Option 3: Run from source

```bash
git clone https://github.com/salih-ari/ArchClean.git
cd ArchClean
PYTHONPATH=. python -m archclean.main
```

## Usage

1. Launch ArchClean.
2. Select a cleanup category.
3. Click **Scan** to find removable files.
4. Review the results and deselect anything you want to keep.
5. Click **Clean** and confirm the operation.
6. Authenticate when prompted for privileged operations.

Use **Scan All** or **Clean All** to process all supported categories.

## Project Structure

```text
ArchClean/
├── archclean/
│   ├── __init__.py
│   ├── main.py
│   ├── ui/
│   │   └── main_window.py
│   ├── cleaner/
│   │   ├── base.py
│   │   ├── cache.py
│   │   ├── logs.py
│   │   ├── packages.py
│   │   └── browser.py
│   └── utils/
│       ├── pacman.py
│       └── elevate.py
├── data/
│   └── archclean.desktop
├── tests/
├── PKGBUILD
├── setup.py
├── pyproject.toml
└── README.md
```

## Testing

Run the cleaner tests:

```bash
PYTHONPATH=. python tests/test_cleaners.py
```

## Contributing

Contributions, bug reports, and feature requests are welcome.

Please open an issue to report bugs or suggest improvements. Pull requests are welcome, and relevant tests should be included with code changes.

## License

This project is licensed under the [MIT License](LICENSE).

## Disclaimer

Deleting system files can cause problems if performed incorrectly. Review selected items carefully before cleaning and back up important data when necessary.

