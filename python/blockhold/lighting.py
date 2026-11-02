"""Point lights for the world shader.

The shader can draw MAX_LIGHTS lights at once. Every frame the closest ones to
the camera are picked from: the torch the local player carries, short flashes
(muzzle flashes, explosions) and steady lights (lamp posts, campfires, crystal
nodes, power-ups...). Steady lights come from "providers": any object with a
lights() method returning [(position, (r, g, b), radius, strength), ...].

Lighting is presentation only: every client works out its own lights.
"""
import math
from panda3d.core import LVecBase3f, LVecBase4f
from ursina import Vec3, camera, scene
from .data.atmosphere import TORCH_COLOUR
from .render import MAX_LIGHTS, init_light_inputs


class Lighting:
    def __init__(self, game):
        self.game = game
        self.pos, self.col = init_light_inputs(scene)
        self.ambient = (1.0, 1.0, 1.0)
        self.torch = 0.0              # strength of the player's torch
        self.torch_radius = 0.0
        self.strength = 1.0           # multiplier for every other light
        self.flashes = []             # dicts: pos, rgb, radius, strength, life, max
        self.t = 0.0

    def set_atmosphere(self, a):
        self.torch, self.torch_radius, self.strength = a['torch'], a['torch_radius'], a['lights']

    def set_ambient(self, rgb):
        self.ambient = tuple(rgb)
        scene.setShaderInput('ambient', LVecBase3f(*self.ambient))

    def flash(self, pos, rgb, radius, strength=1.5, life=0.07):
        """A light that fades out quickly (muzzle flash, explosion)."""
        if self.strength <= 0:
            return
        self.flashes.append(dict(pos=Vec3(pos), rgb=rgb, radius=radius, strength=strength, life=life, max=life))
        del self.flashes[:-6]

    def clear(self):
        self.flashes = []

    def providers(self):
        g = self.game
        out = [g.world]
        for name in ('mining', 'powerups', 'projectiles', 'quest', 'drops'):
            obj = getattr(g, name, None)
            if obj is not None and hasattr(obj, 'lights'):
                out.append(obj)
        return out

    def update(self, dt):
        self.t += dt
        g = self.game
        cam = Vec3(camera.world_position)
        chosen = []
        # 1) the local player's torch, held a little in front and below the eyes
        p = getattr(g, 'player', None)
        if self.torch > 0 and g.state in ('playing', 'paused', 'dead') and p is not None and not p.dead:
            fwd = Vec3(camera.forward)
            flicker = 1 + 0.05 * math.sin(self.t * 13) + 0.035 * math.sin(self.t * 31 + 1.7)
            pos = cam + Vec3(fwd.x, 0, fwd.z) * 0.5 + Vec3(0, -0.35, 0)
            chosen.append((pos, TORCH_COLOUR, self.torch_radius, self.torch * flicker))
        # 2) flashes
        for f in list(self.flashes):
            f['life'] -= dt
            if f['life'] <= 0:
                self.flashes.remove(f)
                continue
            k = f['life'] / f['max']
            chosen.append((f['pos'], f['rgb'], f['radius'] * (0.6 + 0.4 * k), f['strength'] * k * self.strength))
        # 3) the closest steady lights
        if self.strength > 0:
            steady = []
            for prov in self.providers():
                try:
                    for pos, rgb, radius, strength in prov.lights():
                        d = (pos - cam).length() - radius
                        if d < 70:
                            steady.append((d, pos, rgb, radius, strength))
                except Exception as e:          # a broken provider must never stop the game
                    print('light provider failed:', e)
            steady.sort(key=lambda s: s[0])
            for _, pos, rgb, radius, strength in steady[:MAX_LIGHTS - len(chosen)]:
                chosen.append((pos, rgb, radius, strength * self.strength))
        for i in range(MAX_LIGHTS):
            if i < len(chosen):
                pos, rgb, radius, strength = chosen[i]
                self.pos[i] = LVecBase4f(pos.x, pos.y, pos.z, radius)
                self.col[i] = LVecBase4f(rgb[0] * strength, rgb[1] * strength, rgb[2] * strength, 0)
            else:
                self.pos[i] = LVecBase4f(0, 0, 0, 0)
        scene.setShaderInput('cam_pos', LVecBase3f(cam.x, cam.y, cam.z))


def flicker_light(pos, rgb, radius, strength, t, seed=0.0, amount=0.12):
    """A steady light that wavers like a flame."""
    k = 1 + amount * (math.sin(t * 9 + seed) * 0.6 + math.sin(t * 23 + seed * 2.3) * 0.4)
    return (pos, rgb, radius * (0.97 + 0.03 * k), strength * k)

