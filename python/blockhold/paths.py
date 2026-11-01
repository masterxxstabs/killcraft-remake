"""Where the game finds its files, and where it is allowed to write.

Running from source (python main.py): everything lives in the python/ folder
next to the code, exactly like before.

Installed (the BLOCKHOLD.exe built with PyInstaller): the program folder may be
read-only (C:\\Program Files...), so caches, maps you make, your own sounds and
downloaded 3D models go in your user folder instead (~/.blockhold, which on
Windows is C:\\Users\\<you>\\.blockhold). The maps that ship with the game are
still read from the program folder.
"""
import sys
from pathlib import Path

FROZEN = bool(getattr(sys, 'frozen', False))          # True inside the .exe

# read-only game files: VERSION, CHANGELOG.md, maps/, sounds/README.txt ...
APP_DIR = Path(getattr(sys, '_MEIPASS', '.')).resolve() if FROZEN else Path(__file__).resolve().parent.parent

# your settings and records (this was always here)
USER_DIR = Path.home() / '.blockhold'

VERSION_FILE = APP_DIR / 'VERSION'
CHANGELOG_FILE = APP_DIR / 'CHANGELOG.md'

BUNDLED_MAPS = APP_DIR / 'maps'
USER_MAPS = USER_DIR / 'maps' if FROZEN else BUNDLED_MAPS

_PACKAGE = Path(__file__).resolve().parent
SOUND_CACHE = (USER_DIR / 'cache' / 'sounds') if FROZEN else _PACKAGE / '_generated_sounds'
TEXTURE_CACHE = (USER_DIR / 'cache' / 'textures') if FROZEN else _PACKAGE / '_generated_textures'

# your own sound effects (see sounds/README.txt): user folder first when installed
CUSTOM_SOUND_DIRS = [USER_DIR / 'sounds', APP_DIR / 'sounds'] if FROZEN else [APP_DIR / 'sounds']

# downloaded 3D gun models (tools/sketchfab_guns.py)
MODELS_DIR = USER_DIR / 'models' if FROZEN else APP_DIR / 'models'
