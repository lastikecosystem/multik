"""The Minecraft-ish world: blocks, ground, trees, props, particles."""
import numpy as np, math, random
import tex
from tex import BLOCKS, simple, logblock, grassblock
from rig import xbox
from mc3d import nrm, rot_y, face_shade

NAMED = {'grass': grassblock, 'log': logblock}

def block_tex(name):
    if name in NAMED:
        return NAMED[name]()
    return simple(name)

class World:
    def __init__(self):
        self.b = {}
        self.cache = {}

    def set(self, x, y, z, name):
        self.b[(int(x), int(y), int(z))] = name

    def fill(self, x0, x1, y0, y1, z0, z1, name):
        for x in range(int(x0), int(x1) + 1):
            for y in range(int(y0), int(y1) + 1):
                for z in range(int(z0), int(z1) + 1):
                    self.set(x, y, z, name)

    def tx(self, name):
        if name not in self.cache:
            self.cache[name] = block_tex(name)
        return self.cache[name]

    def draw(self, r, maxdist=70.0):
        eye = r.cam.eye
        fwd = r.cam.M[2]
        for (x, y, z), name in self.b.items():
            c = np.array([x + 0.5, y + 0.5, z + 0.5])
            d = c - eye
            dist = np.linalg.norm(d)
            if dist > maxdist or np.dot(d, fwd) < -1.5:
                continue
            t = self.tx(name)
            em = 0.75 if name in ('glowstone', 'sealantern', 'portal') else 0.0
            td = dict(t)
            for key, off in (('top', (0, 1, 0)), ('bottom', (0, -1, 0)), ('south', (0, 0, 1)),
                             ('north', (0, 0, -1)), ('east', (1, 0, 0)), ('west', (-1, 0, 0))):
                if (x + off[0], y + off[1], z + off[2]) in self.b:
                    td[key] = None
            xbox(r, (x, y, z), (x + 1, y + 1, z + 1), td, emissive=em)

def ground(r, size=90, y=0.0, t=None, tile=1.0):
    t = BLOCKS['grass_top'] if t is None else t
    s = size * 0.5
    pts = [(-s, y, -s), (s, y, -s), (s, y, s), (-s, y, s)]
    uv = [(-s * tile, -s * tile), (s * tile, -s * tile), (s * tile, s * tile), (-s * tile, s * tile)]
    r.quad(pts, t, uv=uv, normal=(0, 1, 0), cull=False)

def patch(r, x0, z0, x1, z1, name, y=0.02, tile=1.0):
    t = BLOCKS[name]
    pts = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]
    uv = [(x0 * tile, z0 * tile), (x1 * tile, z0 * tile), (x1 * tile, z1 * tile), (x0 * tile, z1 * tile)]
    r.quad(pts, t, uv=uv, normal=(0, 1, 0), cull=False)

def sprite(r, pos, size, color, emissive=0.9):
    right, up = r.cam.M[0], r.cam.M[1]
    p = np.asarray(pos, np.float64)
    q = [p - right * size - up * size, p + right * size - up * size,
         p + right * size + up * size, p - right * size + up * size]
    t = np.tile(np.array(color, np.uint8), (2, 2, 1))
    r.quad(q, t, shade=1.0, normal=r.cam.M[2] * -1, cull=False, emissive=emissive)

def tree(w, x, z, h=5, kind='oak', big=False):
    for y in range(h):
        w.set(x, y, z, 'log')
    lv = 'leaves' if kind == 'oak' else 'leaves_dark'
    top = h
    for dy, rad in ((0, 2), (1, 2), (2, 1)):
        y = top - 2 + dy
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                if abs(dx) == rad and abs(dz) == rad:
                    continue
                if dx == 0 and dz == 0 and dy < 2:
                    continue
                w.set(x + dx, y, z + dz, lv)
    w.set(x, top, z, lv)
    if big:
        w.set(x, top + 1, z, lv)

def fencepost(r, x, z, h=1.25, lantern=True):
    xbox(r, (x - 0.09, 0, z - 0.09), (x + 0.09, h, z + 0.09), simple('darkwood'))
    if lantern:
        xbox(r, (x - 0.14, h, z - 0.14), (x + 0.14, h + 0.28, z + 0.14), simple('glowstone'), emissive=0.85)
        xbox(r, (x - 0.16, h + 0.28, z - 0.16), (x + 0.16, h + 0.34, z + 0.16), simple('iron'))

def rail(r, x0, x1, z, y):
    xbox(r, (x0, y, z - 0.05), (x1, y + 0.08, z + 0.05), simple('darkwood'))

def build_world():
    w = World()
    random.seed(5)
    # forest ring behind the characters
    for (x, z, h, k) in [(-9, -14, 6, 'oak'), (-4, -19, 7, 'spruce'), (3, -16, 6, 'oak'),
                         (9, -13, 5, 'spruce'), (14, -20, 7, 'oak'), (-15, -21, 6, 'oak'),
                         (-20, -16, 5, 'spruce'), (19, -17, 6, 'spruce'), (7, -24, 7, 'oak'),
                         (-11, -27, 6, 'spruce'), (24, -24, 6, 'oak'), (-25, -26, 7, 'spruce')]:
        tree(w, x, z, h, k, big=(h >= 7))
    # little hill right
    for (x, z, hh) in [(12, -6, 1), (13, -6, 1), (13, -7, 2), (14, -7, 2), (14, -6, 1),
                       (15, -8, 2), (14, -9, 3), (15, -9, 3), (16, -9, 3), (16, -10, 4)]:
        for y in range(hh):
            w.set(x, y, z, 'dirt' if y < hh - 1 else 'grass')
    # stone outcrop left
    for (x, z, hh) in [(-12, -5, 1), (-13, -5, 2), (-13, -6, 2), (-14, -6, 3), (-14, -7, 3), (-15, -7, 4)]:
        for y in range(hh):
            w.set(x, y, z, 'cobble' if y else 'stone')
    # cozy cabin far back
    bx, bz = -6, -11
    w.fill(bx, bx + 5, 0, 2, bz, bz, 'planks')
    w.fill(bx, bx, 0, 2, bz, bz + 3, 'planks')
    w.fill(bx, bx + 5, 3, 3, bz, bz + 3, 'darkwood')
    for yy in (0, 3):
        w.fill(bx, bx + 5, yy, yy, bz, bz, 'log')
    w.set(bx + 2, 1, bz, 'glowstone')
    w.set(bx + 3, 1, bz, 'glowstone')
    # distant mountains
    for (x, z, hh, s) in [(-34, -46, 11, 7), (-18, -52, 14, 9), (6, -56, 17, 11), (30, -48, 12, 8), (46, -40, 9, 6)]:
        for lvl in range(hh):
            rad = max(0, int(s * (1 - lvl / hh)))
            for dx in range(-rad, rad + 1):
                for dz in range(-rad, rad + 1):
                    if dx * dx + dz * dz > rad * rad:
                        continue
                    n = 'snow' if lvl > hh - 3 else ('stone' if lvl > hh * 0.45 else 'grass')
                    if lvl == hh - 1 or abs(dx) >= rad - 1 or abs(dz) >= rad - 1 or lvl % 2 == 0:
                        w.set(x + dx, lvl, z + dz, n)
    return w

def props(r, t, night=False):
    """Fence line + lanterns + rails, drawn each frame (not block-aligned)."""
    for x in (-7.5, -3.5, 0.5, 4.5, 8.5):
        fencepost(r, x, -4.0, 1.25, lantern=True)
    for i in range(4):
        x0 = -7.5 + i * 4.0
        rail(r, x0, x0 + 4.0, -4.0, 0.95)
        rail(r, x0, x0 + 4.0, -4.0, 0.55)

PARTS = None
def particles(r, t, n=70, box=(16, 5, 14), color=(255, 236, 190), emissive=0.95, speed=0.35, seed=4):
    global PARTS
    if PARTS is None or PARTS[0] != (n, seed):
        rs = np.random.RandomState(seed)
        P = np.stack([rs.uniform(-box[0] / 2, box[0] / 2, n), rs.uniform(0.2, box[1], n),
                      rs.uniform(-box[2], 2.0, n)], 1)
        PH = rs.uniform(0, 6.28, n)
        PARTS = ((n, seed), P, PH)
    _, P, PH = PARTS
    for i in range(n):
        y = P[i, 1] + math.sin(t * speed * 1.7 + PH[i]) * 0.45 + ((t * speed * 0.4 + PH[i]) % 2.0)
        x = P[i, 0] + math.sin(t * 0.6 + PH[i] * 2) * 0.35
        d = np.linalg.norm(np.array([x, y, P[i, 2]]) - r.cam.eye)
        s = 0.035 + 0.02 * math.sin(t * 3 + PH[i])
        sprite(r, (x, y, P[i, 2]), s * max(0.5, min(2.0, d / 8)), color, emissive)

def stars(r, t, n=120, seed=9):
    rs = np.random.RandomState(seed)
    for i in range(n):
        a = rs.uniform(0, 6.28); e = rs.uniform(0.1, 1.2)
        d = 60
        p = (math.cos(a) * d * math.cos(e), 12 + math.sin(e) * 46, math.sin(a) * d * math.cos(e) - 20)
        if p[1] < 6:
            continue
        tw = 0.55 + 0.45 * math.sin(t * 2.2 + i)
        sprite(r, p, 0.105 * tw, (255, 252, 240), 1.0)


def blob_shadow(r, pos, size=0.62, y=0.03):
    x, _, z = pos
    pts = [(x - size, y, z - size), (x + size, y, z - size), (x + size, y, z + size), (x - size, y, z + size)]
    r.quad(pts, tex.shadow_tex(), shade=1.0, normal=(0, 1, 0), cull=False)


def glow(r, pos, size, color=(150, 110, 220), peak=0.72):
    right, up = r.cam.M[0], r.cam.M[1]
    p = np.asarray(pos, np.float64)
    q = [p - right * size - up * size, p + right * size - up * size,
         p + right * size + up * size, p - right * size + up * size]
    r.quad(q, tex.glow_tex(color, peak=peak), shade=1.0, normal=r.cam.M[2] * -1, cull=False, emissive=1.0)
