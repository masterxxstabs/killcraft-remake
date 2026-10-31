"""Rendering helpers: the world shader (texture * vertex colour * fog) and
cube meshes with Minecraft-style baked face shading."""
from ursina import Entity, Mesh, Shader, Vec2, Vec3, color as ucolor

MAX_LIGHTS = 8

WORLD_SHADER = Shader(name='blockhold_world', language=Shader.GLSL, vertex='''
#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat4 p3d_ModelMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
in vec4 p3d_Color;
uniform vec2 texture_scale;
uniform vec2 texture_offset;
out vec2 uvs;
out vec4 vcol;
out vec3 vpos;
out vec3 wpos;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uvs = p3d_MultiTexCoord0 * texture_scale + texture_offset;
    vcol = p3d_Color;
    vpos = (p3d_ModelViewMatrix * p3d_Vertex).xyz;
    wpos = (p3d_ModelMatrix * p3d_Vertex).xyz;
}
''', fragment='''
#version 130
#define MAX_LIGHTS 8
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
uniform vec4 fog_color;
uniform vec2 fog_range;
uniform vec3 ambient;               // light level everywhere (1 = full daylight)
uniform vec3 cam_pos;
uniform float glow;                 // 1 = ignores lighting (fire, sparks, tracers)
uniform vec4 light_pos[MAX_LIGHTS]; // xyz = position, w = radius (0 = off)
uniform vec4 light_col[MAX_LIGHTS]; // rgb = colour * strength
in vec2 uvs;
in vec4 vcol;
in vec3 vpos;
in vec3 wpos;
out vec4 color;
void main() {
    vec4 base = texture(p3d_Texture0, uvs) * p3d_ColorScale * vcol;
    // flat face normal from screen-space derivatives, turned towards the camera
    vec3 c = cross(dFdx(wpos), dFdy(wpos));
    float cl = length(c);
    vec3 n = cl > 1e-10 ? c / cl : vec3(0.0, 1.0, 0.0);
    if (dot(n, cam_pos - wpos) < 0.0) n = -n;
    vec3 light = ambient;
    for (int i = 0; i < MAX_LIGHTS; i++) {
        float r = light_pos[i].w;
        if (r <= 0.0) continue;
        vec3 L = light_pos[i].xyz - wpos;
        float d = length(L);
        float att = clamp(1.0 - d / r, 0.0, 1.0);
        att *= att;
        float lambert = max(dot(n, L / max(d, 0.001)), 0.0) * 0.7 + 0.3;
        light += light_col[i].rgb * (att * lambert);
    }
    color = vec4(mix(base.rgb * light, base.rgb, glow), base.a);
    float t = clamp((length(vpos) - fog_range.x) / max(0.001, fog_range.y - fog_range.x), 0.0, 1.0);
    color.rgb = mix(color.rgb, fog_color.rgb, t);
}
''', default_input={'texture_scale': Vec2(1, 1), 'texture_offset': Vec2(0, 0)})


def init_light_inputs(np, ambient=(1.0, 1.0, 1.0)):
    """Give a scene root every lighting input the world shader needs. Returns the light arrays
    (edit them in place to move lights; no need to set the inputs again)."""
    from panda3d.core import PTA_LVecBase4f, LVecBase3f
    pos, colour = PTA_LVecBase4f.emptyArray(MAX_LIGHTS), PTA_LVecBase4f.emptyArray(MAX_LIGHTS)
    np.setShaderInput('light_pos', pos)
    np.setShaderInput('light_col', colour)
    np.setShaderInput('ambient', LVecBase3f(*ambient))
    np.setShaderInput('cam_pos', LVecBase3f(0, 0, 0))
    np.setShaderInput('glow', 0.0)
    return pos, colour


def set_glow(np, amount=1.0):
    """Make a node (and everything under it) ignore the lighting: fire, sparks, glowing crystals."""
    np.setShaderInput('glow', float(amount))


def set_fog(node, rgb, near, far):
    """Fog is a shader input on a parent node, so every child (even ones made later) gets it."""
    node.setShaderInput('fog_color', float(rgb[0]), float(rgb[1]), float(rgb[2]), 1.0)
    node.setShaderInput('fog_range', float(near), float(far))


def hex_rgb(h):
    """'#aabbcc' -> (r, g, b) floats 0..1"""
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def col(h, a=1.0):
    r, g, b = hex_rgb(h)
    return ucolor.Color(r, g, b, a)


# Brightness per face, like classic block games: top bright, bottom dark.
SHADE = {'top': 1.0, 'bottom': 0.5, 'east': 0.8, 'west': 0.8, 'north': 0.65, 'south': 0.65}

# name, normal, viewer "right", viewer "up" (corners go CCW as seen from outside)
FACES = [
    ('top', (0, 1, 0), (1, 0, 0), (0, 0, 1)),
    ('bottom', (0, -1, 0), (-1, 0, 0), (0, 0, 1)),
    ('east', (1, 0, 0), (0, 0, 1), (0, 1, 0)),
    ('west', (-1, 0, 0), (0, 0, -1), (0, 1, 0)),
    ('north', (0, 0, 1), (-1, 0, 0), (0, 1, 0)),
    ('south', (0, 0, -1), (1, 0, 0), (0, 1, 0)),
]
CORNERS = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
CORNER_UV = [(0, 0), (1, 0), (1, 1), (0, 1)]


def add_box(verts, tris, uvs, cols, center, size, uv_rects=None, tint=(1, 1, 1), skip=()):
    """Append a box to mesh arrays. uv_rects: dict face -> (u0, v0, u1, v1)."""
    cx, cy, cz = center
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    for name, n, r, u in FACES:
        if name in skip:
            continue
        s = SHADE[name]
        c = ucolor.Color(tint[0] * s, tint[1] * s, tint[2] * s, 1)
        rect = (uv_rects or {}).get(name, (0, 0, 1, 1))
        base = len(verts)
        for (a, b), (cu, cv) in zip(CORNERS, CORNER_UV):
            verts.append(Vec3(
                cx + (n[0] + r[0] * a + u[0] * b) * hx,
                cy + (n[1] + r[1] * a + u[1] * b) * hy,
                cz + (n[2] + r[2] * a + u[2] * b) * hz,
            ))
            uvs.append(Vec2(rect[0] + (rect[2] - rect[0]) * cu, rect[1] + (rect[3] - rect[1]) * cv))
            cols.append(c)
        tris.extend((base, base + 1, base + 2, base, base + 2, base + 3))


def box_mesh(size=(1, 1, 1), center=(0, 0, 0), uv_rects=None, tint=(1, 1, 1)):
    verts, tris, uvs, cols = [], [], [], []
    add_box(verts, tris, uvs, cols, center, size, uv_rects, tint)
    return Mesh(vertices=verts, triangles=tris, uvs=uvs, colors=cols)


def node(parent=None, **kw):
    """An empty 3D container. Uses the world shader so it doesn't override the fog for its children."""
    if parent is None:
        from ursina import scene
        parent = scene
    return Entity(parent=parent, shader=WORLD_SHADER, **kw)


def block(parent=None, size=(1, 1, 1), center=(0, 0, 0), color='#ffffff', texture=None, uv_rects=None, **kw):
    """A shaded box entity. `center` is the box centre relative to the entity origin."""
    if parent is None:
        from ursina import scene
        parent = scene
    e = Entity(parent=parent, model=box_mesh(size, center, uv_rects), shader=WORLD_SHADER,
               color=col(color) if isinstance(color, str) else color, texture=texture, **kw)
    return e
