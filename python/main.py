"""BLOCKHOLD - a blocky first-person wave survival game.

Run it with:   python main.py
"""
from ursina import Ursina, window

app = Ursina(title='BLOCKHOLD', development_mode=False, editor_ui_enabled=False, borderless=False)
window.fps_counter.enabled = False
window.exit_button.visible = False

from blockhold.game import Game  # noqa: E402  (needs the window to exist first)

game = Game()
app.run()
