"""BLOCKHOLD - a blocky first-person wave survival game.

Run it with:            python main.py
Update it with:         python main.py --update
Skip the update check:  python main.py --offline
"""
import sys

if '--update' in sys.argv:
    from blockhold.updater import run_cli
    run_cli()
    sys.exit()

from ursina import Ursina, window

app = Ursina(title='BLOCKHOLD', development_mode=False, editor_ui_enabled=False, borderless=False)
window.fps_counter.enabled = False
window.exit_button.visible = False

from blockhold.game import Game  # noqa: E402  (needs the window to exist first)

game = Game(check_updates='--offline' not in sys.argv)
app.run()
