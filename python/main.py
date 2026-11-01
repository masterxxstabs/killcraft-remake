"""BLOCKHOLD - a blocky first-person wave survival game.

Run it with:            python main.py
Update it with:         python main.py --update
Skip the update check:  python main.py --offline
Check an install:       BLOCKHOLD.exe --selftest   (exit code 0 = everything is there)
Render check:           BLOCKHOLD.exe --autotest   (plays a few seconds, saves ~/.blockhold/autotest.png)
"""
import sys
import traceback
from pathlib import Path

FROZEN = bool(getattr(sys, 'frozen', False))       # True inside the BLOCKHOLD.exe build
USER_DIR = Path.home() / '.blockhold'


class Tee:
    """Writes to a log file and (if there is one) the console."""

    def __init__(self, path, stream):
        self.file = open(path, 'w', buffering=1, encoding='utf-8', errors='replace')
        self.stream = stream

    def write(self, text):
        self.file.write(text)
        if self.stream is not None:
            try:
                self.stream.write(text)
            except Exception:
                pass
        return len(text)

    def flush(self):
        self.file.flush()
        if self.stream is not None:
            try:
                self.stream.flush()
            except Exception:
                pass


def setup_frozen():
    """The .exe has no console window: keep a log file, and point Panda3D at its bundled plugins."""
    USER_DIR.mkdir(parents=True, exist_ok=True)
    name = 'selftest.log' if '--selftest' in sys.argv else 'log.txt'
    sys.stdout = Tee(USER_DIR / name, sys.__stdout__)
    sys.stderr = sys.stdout
    from panda3d.core import Filename, load_prc_file_data
    bundle = Path(sys._MEIPASS)
    plugins = Filename.from_os_specific(str(bundle / 'panda3d')).get_fullpath()
    load_prc_file_data('blockhold', f'plugin-path {plugins}\n')


def show_error(message):
    """Tell the player something went wrong (a message box on Windows, the log everywhere)."""
    print(message, flush=True)
    if FROZEN and sys.platform == 'win32' and not ({'--selftest', '--autotest'} & set(sys.argv)):
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message[-1500:], 'BLOCKHOLD crashed', 0x10)
        except Exception:
            pass


def selftest():
    """Check that everything the game needs is in this install, without opening a window."""
    import importlib
    import pkgutil
    import blockhold
    for m in pkgutil.walk_packages(blockhold.__path__, 'blockhold.'):
        importlib.import_module(m.name)
    from blockhold import maps, paths, sounds, world_textures
    print('BLOCKHOLD', paths.VERSION_FILE.read_text().strip(), '| frozen:', paths.FROZEN, '| data:', paths.APP_DIR)
    names = [stem for stem, _ in maps.list_maps()]
    assert {'village', 'forest_camp'} <= set(names), f'bundled maps missing: {names}'
    for stem in names:
        maps.load_map(stem)
    for name in world_textures.GENERATORS:
        world_textures.image(name)
    sounds.ensure_generated()
    import ursina
    fonts = Path(ursina.__file__).resolve().parent / 'fonts'
    assert (fonts / 'OpenSans-Regular.ttf').exists(), f'ursina fonts missing in {fonts}'
    from panda3d.core import GraphicsPipeSelection
    pipe = GraphicsPipeSelection.get_global_ptr().make_default_pipe()
    assert pipe is not None, 'no Panda3D display plugin found'
    print('display:', pipe.get_interface_name(), '| maps:', names, '| caches:', paths.SOUND_CACHE.parent)
    print('SELFTEST OK')


def main():
    if FROZEN:
        setup_frozen()
    if '--selftest' in sys.argv:
        try:
            selftest()
        except Exception:
            traceback.print_exc()
            print('SELFTEST FAILED')
            sys.exit(1)
        sys.exit(0)
    if '--update' in sys.argv:
        from blockhold.updater import run_cli
        run_cli()
        sys.exit()

    from ursina import Ursina, window

    from panda3d.core import Filename
    from blockhold.paths import APP_DIR
    icon = APP_DIR / 'installer' / 'blockhold.ico'
    extra = {'icon': Filename.from_os_specific(str(icon)).get_fullpath()} if icon.exists() else {}
    app = Ursina(title='BLOCKHOLD', development_mode=False, editor_ui_enabled=False, borderless=False, **extra)
    window.fps_counter.enabled = False
    window.exit_button.visible = False

    from blockhold.game import Game  # (needs the window to exist first)

    game = Game(check_updates='--offline' not in sys.argv and '--autotest' not in sys.argv)
    if '--autotest' in sys.argv:
        autotest(game)
    app.run()


def autotest(game):
    """Build check: start a game, save a screenshot to ~/.blockhold/autotest.png and quit."""
    import faulthandler
    import time
    from ursina import Entity, application, invoke
    from panda3d.core import Filename
    log = getattr(sys.stdout, 'file', None) or sys.__stderr__
    if log is not None:
        faulthandler.dump_traceback_later(150, exit=True, file=log)   # stuck? say where, then quit
    start = time.time()
    frames = [0]

    def count():
        frames[0] += 1
        if frames[0] in (1, 10) or frames[0] % 60 == 0:
            print(f'AUTOTEST frame {frames[0]} at {time.time() - start:.1f}s', flush=True)
    Entity(update=count)

    def shot():
        path = USER_DIR / 'autotest.png'
        application.base.win.saveScreenshot(Filename.from_os_specific(str(path)))
        took = time.time() - start
        print(f'AUTOTEST screenshot {path} after {frames[0]} frames ({frames[0] / max(took, 0.01):.1f} fps)', flush=True)
        application.quit()
    invoke(game.start_game, delay=1)
    invoke(shot, delay=6)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        show_error('BLOCKHOLD ran into a problem and has to close.\n\n' + traceback.format_exc() +
                   f'\nA log is saved in {USER_DIR / "log.txt"}')
        sys.exit(1)
