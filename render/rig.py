"""Blocky characters: parts, poses, animation, held items."""
import numpy as np, math
from mc3d import box_faces, face_shade, rot_x, rot_y, rot_z
import tex

def xbox(r, lo, hi, t, M=None, T=(0, 0, 0), emissive=0.0, tint=1.0):
    """Draw a box transformed by p' = M @ p + T."""
    M = np.eye(3) if M is None else np.asarray(M, np.float64)
    T = np.asarray(T, np.float64)
    for pts, n, key in box_faces(lo, hi):
        wp = pts @ M.T + T
        nn = M @ n
        tt = t[key] if isinstance(t, dict) else t
        if tt is None:
            continue
        r.quad(wp, tt, shade=face_shade(nn) * tint, normal=nn, emissive=emissive)

HEAD = ((-0.25, 0.0, -0.25), (0.25, 0.5, 0.25))
BODY = ((-0.25, -0.75, -0.125), (0.25, 0.0, 0.125))
ARM = ((-0.125, -0.70, -0.125), (0.125, 0.05, 0.125))
LEG = ((-0.125, -0.75, -0.125), (0.125, 0.0, 0.125))
NECK = 1.5

class Char:
    def __init__(self, kind, pos=(0, 0, 0), yaw=0.0, scale=1.0):
        self.kind = kind
        self.pos = np.array(pos, np.float64)
        self.yaw = yaw
        self.scale = scale
        self.head_fn = {'steve': tex.steve_head, 'hacker': tex.hacker_head, 'chill': tex.chill_head}[kind]
        if kind == 'steve':
            self.body = tex.body_tex((0, 158, 158), (0, 124, 128), (58, 74, 140))
            self.arm = tex.limb_tex((0, 158, 158), (198, 146, 108), 4)
            self.leg = tex.limb_tex((58, 74, 140), (74, 66, 62), 6)
        elif kind == 'hacker':
            self.body = tex.body_tex((26, 26, 32), (16, 16, 20), (16, 16, 20), logo=(120, 255, 170))
            self.arm = tex.limb_tex((26, 26, 32), (22, 22, 28), 6)
            self.leg = tex.limb_tex((34, 34, 40), (20, 20, 24), 6)
        else:
            self.body = tex.body_tex((66, 86, 180), (46, 60, 140), (34, 40, 90), logo=(120, 230, 255))
            self.arm = tex.limb_tex((66, 86, 180), (212, 164, 126), 5)
            self.leg = tex.limb_tex((46, 50, 74), (236, 240, 248), 6)
        # animation state (filled by pose())
        self.p = dict(head=(0, 0, 0), armA=0.0, armB=0.0, armA_z=0.0, armB_z=0.0,
                      legA=0.0, legB=0.0, bob=0.0, lean=0.0, mouth='closed', item=None, item_rot=0.0)

    # ------------------------------------------------------------------ poses
    def idle(self, t, talk=False, energy=1.0):
        p = self.p
        p['bob'] = 0.012 * math.sin(t * 1.7)
        p['armA'] = 0.05 * math.sin(t * 1.3)
        p['armB'] = -0.05 * math.sin(t * 1.3 + 0.7)
        p['armA_z'] = 0.07 + 0.02 * math.sin(t * 1.1)
        p['armB_z'] = -0.07 - 0.02 * math.sin(t * 1.1)
        p['legA'] = p['legB'] = 0.0
        p['head'] = (0.04 * math.sin(t * 0.8), 0.07 * math.sin(t * 0.53), 0)
        p['mouth'] = 'closed'
        if talk:
            k = int(t * 8.5) % 3
            p['mouth'] = ['open', 'closed', 'wide'][k]
            p['head'] = (0.05 * math.sin(t * 0.8) + 0.05 * math.sin(t * 8.0),
                         0.09 * math.sin(t * 1.9), 0.02 * math.sin(t * 6.0))
            g = energy
            p['armA'] = -0.30 * g - 0.26 * g * (0.5 + 0.5 * math.sin(t * 5.2))
            p['armB'] = -0.10 * g - 0.12 * g * (0.5 + 0.5 * math.sin(t * 4.1 + 1.4))
            p['armA_z'] = 0.22 + 0.16 * g * math.sin(t * 5.2)
            p['armB_z'] = -0.18 - 0.10 * g * math.sin(t * 4.1)
            p['bob'] += 0.008 * math.sin(t * 5.0)
        return self

    def walk(self, t, speed=1.0, talk=False):
        self.idle(t, talk=talk)
        ph = t * 7.0 * speed
        a = 0.85 * speed
        self.p['legA'] = a * math.sin(ph)
        self.p['legB'] = -a * math.sin(ph)
        if not talk:
            self.p['armA'] = -0.7 * a * math.sin(ph)
            self.p['armB'] = 0.7 * a * math.sin(ph)
        self.p['bob'] = 0.035 * abs(math.sin(ph)) - 0.01
        return self

    def swing(self, t, k):
        """k in 0..1 across one swing."""
        self.p['armA'] = -2.3 + 3.0 * min(1.0, k * 1.6)
        self.p['armA_z'] = 0.35 - 0.5 * k
        self.p['lean'] = 0.12 * math.sin(k * math.pi)
        self.p['item_rot'] = -0.9 + 1.9 * k
        return self

    def look_at(self, p, w=1.0):
        d = np.asarray(p, np.float64) - (self.pos + np.array([0, NECK + 0.25, 0]))
        ty = math.atan2(d[0], d[2])
        dy = (ty - self.yaw + math.pi) % (2 * math.pi) - math.pi
        hy = max(-0.85, min(0.85, dy)) * w
        pit = max(-0.45, min(0.45, -math.atan2(d[1], max(0.2, math.hypot(d[0], d[2]))))) * w
        c = self.p['head']
        self.p['head'] = (c[0] * 0.3 + hy, c[1] * 0.3 + pit, c[2])
        return self

    # ------------------------------------------------------------------- draw
    def draw(self, r):
        p = self.p
        s = self.scale
        Ry = rot_y(self.yaw) @ rot_x(p['lean'])
        root = self.pos + np.array([0, p['bob'], 0]) * s

        def part(lo, hi, t, rot, off, **kw):
            lo = tuple(np.array(lo) * s); hi = tuple(np.array(hi) * s)
            M = Ry @ rot * s if False else Ry @ rot
            off = np.array(off, np.float64) * s
            xbox(r, lo, hi, t, M=M * 1.0, T=Ry @ off + root, **kw)

        hy, hp, hr = p['head']
        part(BODY[0], BODY[1], self.body, np.eye(3), (0, NECK, 0))
        part(HEAD[0], HEAD[1], self.head_fn(p['mouth']), rot_y(hy) @ rot_x(hp) @ rot_z(hr), (0, NECK, 0),
             emissive=(0.34 if self.kind == 'hacker' else 0.0))
        part(ARM[0], ARM[1], self.arm, rot_x(p['armA']) @ rot_z(p['armA_z']), (0.375, NECK - 0.05, 0))
        part(ARM[0], ARM[1], self.arm, rot_x(p['armB']) @ rot_z(p['armB_z']), (-0.375, NECK - 0.05, 0))
        part(LEG[0], LEG[1], self.leg, rot_x(p['legA']), (0.125, NECK - 0.75, 0))
        part(LEG[0], LEG[1], self.leg, rot_x(p['legB']), (-0.125, NECK - 0.75, 0))
        if self.kind == 'chill':
            self.headphones(r, Ry, root, hy, hp, s)
        if p['item'] is not None:
            self.hand_item(r, Ry, root, s, p['item'])

    def headphones(self, r, Ry, root, hy, hp, s):
        Rh = Ry @ (rot_y(hy) @ rot_x(hp))
        T = Ry @ (np.array([0, NECK, 0]) * s) + root
        w = tex.simple('white'); b = tex.simple('black')
        pad = tex.simple('amethyst')
        xbox(r, (-0.31 * s, 0.30 * s, -0.09 * s), (-0.25 * s, 0.46 * s, 0.09 * s), pad, M=Rh, T=T, emissive=0.25)
        xbox(r, (0.25 * s, 0.30 * s, -0.09 * s), (0.31 * s, 0.46 * s, 0.09 * s), pad, M=Rh, T=T, emissive=0.25)
        xbox(r, (-0.29 * s, 0.46 * s, -0.045 * s), (0.29 * s, 0.53 * s, 0.045 * s), b, M=Rh, T=T)

    def hand_item(self, r, Ry, root, s, item):
        p = self.p
        Rarm = rot_x(p['armA']) @ rot_z(p['armA_z'])
        hand = np.array([0.375, NECK - 0.05, 0]) * s + Rarm @ (np.array([0, -0.68, 0.02]) * s)
        M = Ry @ Rarm @ rot_x(p['item_rot'] - 0.35) @ rot_z(0.12)
        T = Ry @ hand + root
        if item == 'sword':
            draw_sword(r, M, T, s)

def draw_sword(r, M, T, s=1.0, glow=0.35):
    """Custom 'Chill' sword: amethyst blade with a glowing diamond fuller."""
    bl = tex.simple('amethyst'); ed = tex.simple('diamond')
    gd = tex.simple('gold'); hd = tex.simple('darkwood')
    def b(lo, hi, t, e=0.0):
        xbox(r, tuple(np.array(lo) * s), tuple(np.array(hi) * s), t, M=M, T=T, emissive=e)
    b((-0.042, -0.26, -0.032), (0.042, 0.06, 0.032), hd)
    b((-0.062, -0.34, -0.046), (0.062, -0.26, 0.046), gd, 0.12)
    b((-0.195, 0.06, -0.046), (0.195, 0.135, 0.046), gd, 0.14)
    b((-0.145, 0.085, -0.040), (-0.105, 0.125, 0.040), ed, glow + 0.25)
    b((0.105, 0.085, -0.040), (0.145, 0.125, 0.040), ed, glow + 0.25)
    b((-0.058, 0.135, -0.026), (0.058, 0.745, 0.026), bl, glow)
    b((-0.022, 0.165, 0.024), (0.022, 0.715, 0.033), ed, glow + 0.35)
    b((-0.022, 0.165, -0.033), (0.022, 0.715, -0.024), ed, glow + 0.35)
    b((-0.040, 0.745, -0.022), (0.040, 0.860, 0.022), bl, glow + 0.1)
    b((-0.020, 0.860, -0.016), (0.020, 0.945, 0.016), ed, glow + 0.4)
