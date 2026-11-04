# PyInstaller recipe for BLOCKHOLD.exe (and the Linux build).
#
#   cd python
#   pip install -r requirements-build.txt
#   pyinstaller blockhold.spec --noconfirm
#
# The game ends up in dist/BLOCKHOLD/ (run BLOCKHOLD.exe there). installer/blockhold.iss
# turns that folder into a Windows installer. GitHub Actions does all of this for every
# release (.github/workflows/release.yml).
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = [], [], []
# the engine and its helpers carry fonts, shaders, models and native plugins: take all of it
for package in ('ursina', 'panda3d', 'direct', 'gltf', 'simplepbr', 'screeninfo', 'pyperclip'):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h
hiddenimports += collect_submodules('blockhold')

# game files read at run time (see blockhold/paths.py)
datas += [
    ('VERSION', '.'),
    ('CHANGELOG.md', '.'),
    ('DEVLOG.md', '.'),
    ('README.md', '.'),
    ('maps/*.json', 'maps'),
    ('assets/models', 'assets/models'),
    ('sounds/README.txt', 'sounds'),
    ('installer/blockhold.ico', 'installer'),
    ('installer/blockhold.png', 'installer'),
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=['tkinter', 'numpy', 'pytest'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BLOCKHOLD',
    icon='installer/blockhold.ico',
    console=False,              # a game: no black console window (errors go to ~/.blockhold/log.txt)
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name='BLOCKHOLD', upx=False)
