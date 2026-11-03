"""A faster version of Ursina's per-frame loop.

Every frame Ursina visits *every* entity in the scene (over a thousand: each zombie
limb, coin, particle and label is one) and for each one walks up its parents to see
if any is switched off, just to find the handful that have an update() to run. That
alone cost about 10 ms a frame with 40 zombies around.

This keeps a list of only the entities that need something every frame (an update(),
scripts, or shader inputs that change) and runs exactly what Ursina would run for
those, in the same order. The list is rebuilt whenever entities are created or
destroyed, and every half second in case something got an update() later on.
"""
import __main__
from ursina import application, camera, mouse, scene
from ursina import main as ursina_main
from panda3d.core import ClockObject

REFRESH_FRAMES = 30
_clock = ClockObject.getGlobalClock()


def _needs_frames(e):
    if callable(getattr(e, 'update', None)):
        return True
    if getattr(e, 'scripts', None):
        return True
    sh = getattr(e, 'shader', None)
    if sh is None or not getattr(sh, 'continuous_input', None):
        return False
    # Ursina's default shader feeds the 3D camera position (for fog) to every entity every frame,
    # including the 2D UI, where it does nothing: skip those
    return not e.has_ancestor(camera.ui)


def install(app):
    if getattr(app, '_blockhold_fastloop', False):
        return
    app._blockhold_fastloop = True
    state = dict(key=None, frame=0, list=[])

    def candidates():
        ents = scene.entities
        key = (len(ents), id(ents[-1]) if ents else 0)
        state['frame'] += 1
        if key != state['key'] or state['frame'] % REFRESH_FRAMES == 0:
            state['key'] = key
            state['list'] = [e for e in ents if _needs_frames(e)]
        return state['list']

    def fast_update(task=None):
        if application.calculate_dt:
            t = ursina_main.time                     # (Ursina keeps dt on the time module)
            t.dt_unscaled = _clock.getDt()
            t.dt = t.dt_unscaled * application.time_scale
        mouse.update()
        if hasattr(__main__, 'update') and __main__.update and not application.paused:
            __main__.update()
        for seq in application.sequences:
            seq.update()
        if scene._entities_marked_for_removal:
            scene.entities = [e for e in scene.entities if e not in scene._entities_marked_for_removal]
            scene._entities_marked_for_removal.clear()
        removed = scene._entities_marked_for_removal
        for e in candidates():
            if e in removed or not e:
                continue
            if not e.enabled or e.ignore:
                continue
            if application.paused and e.ignore_paused is False:
                continue
            if e.has_disabled_ancestor():
                continue
            if callable(getattr(e, 'update', None)):
                e.update()
            if not e:
                continue
            for script in getattr(e, 'scripts', ()):
                if script.enabled and callable(getattr(script, 'update', None)):
                    script.update()
            if not e:
                continue
            if e.shader and getattr(e.shader, 'continuous_input', None):
                for k, value in e.shader.continuous_input.items():
                    e.set_shader_input(k, value())
        ursina_main._audio_manager.update()
        return ursina_main.Task.cont

    app.taskMgr.remove(app._update_task)
    app._update_task = app.taskMgr.add(fast_update, 'update')
