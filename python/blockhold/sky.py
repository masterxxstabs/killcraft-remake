"""The sky: a dome with a colour gradient, drifting clouds and stars (all drawn by
a shader, no textures), and a ring of dark mountains far outside the arena."""
import math
import random
from panda3d.core import LVecBase3f
from ursina import Entity, Shader, Vec3, camera, scene
from .lowpoly import LowPoly
from .render import node, hex_rgb

SKY_SHADER = Shader(name='blockhold_sky', language=Shader.GLSL, vertex='''
#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
out vec3 dir;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    dir = p3d_Vertex.xyz;
}
''', fragment='''
#version 130
uniform vec3 sky_top;
uniform vec3 sky_horizon;
uniform vec3 cloud_col;
uniform float cloud_amt;
uniform float stars;
uniform float time;
in vec3 dir;
out vec4 color;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}
float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) { v += a * noise(p); p = p * 2.03 + vec2(11.7, 3.1); a *= 0.5; }
    return v;
}
void main() {
    vec3 d = normalize(dir);
    float h = d.y;
    vec3 c = mix(sky_horizon, sky_top, smoothstep(-0.02, 0.6, h));
    if (h > 0.0) {
        vec2 uv = d.xz / (h + 0.18) * 1.6 + vec2(time * 0.012, time * 0.004);
        float n = fbm(uv);
        float cl = smoothstep(0.42, 0.78, n) * cloud_amt * smoothstep(0.0, 0.22, h);
        vec2 sp = floor(d.xz / (h + 0.35) * 260.0);
        float star = step(0.9965, hash(sp)) * stars * (1.0 - cl * 1.4) * smoothstep(0.06, 0.35, h);
        star *= 0.55 + 0.45 * sin(time * 2.0 + hash(sp + 7.0) * 40.0);
        c = mix(c, cloud_col * (0.75 + 0.5 * n), cl);
        c += vec3(max(star, 0.0)) * 0.85;
    }
    color = vec4(c, 1.0);
}
''')

MOUNTAIN_COLOURS = ['#26262e', '#2c2c35', '#22232a', '#30303a']


def mountain_mesh(seed=7):
    lp = LowPoly(seed=seed, variation=0.08)
    rnd = random.Random(seed)
    n = 34
    for i in range(n):
        a = i / n * math.tau + rnd.random() * 0.12
        r = 165 + rnd.random() * 50
        x, z = math.cos(a) * r, math.sin(a) * r
        h = 12 + rnd.random() * 22
        w = 26 + rnd.random() * 26
        colour = rnd.choice(MOUNTAIN_COLOURS)
        lp.cylinder((x, -2, z), w, h, colour, sides=5 + rnd.randrange(3), top_radius=w * (0.08 + rnd.random() * 0.15))
        if rnd.random() < 0.6:                      # a lower shoulder next to the peak
            b = a + (rnd.random() - 0.5) * 0.12
            lp.cylinder((math.cos(b) * (r - 12), -2, math.sin(b) * (r - 12)), w * 0.8, h * 0.55,
                        rnd.choice(MOUNTAIN_COLOURS), sides=5, top_radius=w * 0.2)
    return lp.mesh()


class Sky:
    def __init__(self):
        self.dome = Entity(parent=scene, model='sphere', scale=700, shader=SKY_SHADER, double_sided=True)
        self.dome.setBin('background', 0)
        self.dome.setDepthWrite(False)
        self.dome.setShaderInput('time', 0.0)
        self.mountains = node(scene)
        self.mountains.model = mountain_mesh()
        self.t = 0.0
        self.set_style(dict(clouds='#3a302d', cloud_amt=0.8, stars=0.3))
        self.set_colours((0.1, 0.1, 0.1), (0.2, 0.2, 0.2), 60)

    def set_style(self, a):
        self.dome.setShaderInput('cloud_col', LVecBase3f(*hex_rgb(a['clouds'])))
        self.dome.setShaderInput('cloud_amt', float(a['cloud_amt']))
        self.dome.setShaderInput('stars', float(a['stars']))

    def set_colours(self, top, horizon, fog_far, dark=0.55):
        self.dome.setShaderInput('sky_top', LVecBase3f(*top))
        self.dome.setShaderInput('sky_horizon', LVecBase3f(*horizon))
        # the mountains get their own, longer fog that fades to a darker colour than the
        # horizon, so they show up as dark silhouettes against the glow of the sky
        self.mountains.setShaderInput('fog_range', float(fog_far * 0.8), float(fog_far * 3.4))
        self.mountains.setShaderInput('fog_color', float(horizon[0] * dark), float(horizon[1] * dark),
                                      float(horizon[2] * dark), 1.0)

    def set_arena(self, half):
        k = max(0.6, half / 34)
        self.mountains.scale = k
        camera.clip_plane_far = max(1000, 260 * k)     # the mountain ring has to stay inside the view

    def show(self, on):
        self.dome.enabled = on
        self.mountains.enabled = on

    def update(self, dt):
        self.t += dt
        self.dome.position = camera.world_position
        self.dome.setShaderInput('time', self.t)
