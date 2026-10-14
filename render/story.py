"""Director: shots, camera moves, character blocking, per-frame render."""
import numpy as np, math, json, os
from PIL import Image
from mc3d import Renderer, Cam, rot_y, rot_z, rot_x, nrm
import scene, rig, tex, overlay

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, 'timeline.json')))
L = {x['id']: x for x in TL['lines']}
LOGO_T = TL['logo_at']
TOTAL = TL['total']

def s(i):  return L[i]['start']
def e(i):  return L[i]['start'] + L[i]['dur']

SUN_DIR = nrm([0.50, 0.21, -0.84])
PAL_DAY = ((78, 136, 216), (156, 198, 240), (250, 214, 162))
PAL_DUSK = ((40, 54, 120), (118, 108, 176), (248, 166, 120))
PAL_NIGHT = ((6, 8, 26), (18, 22, 58), (62, 44, 92))

def smooth(u):  return u * u * (3 - 2 * u)
def ease_out(u): return 1 - (1 - u) ** 3
def clamp01(u): return max(0.0, min(1.0, u))

def lerp(a, b, u):
    return np.array(a, np.float64) * (1 - u) + np.array(b, np.float64) * u

# --------------------------------------------------------------------- blocking
STEVE_P = np.array([-1.75, 0.0, 0.95]);  STEVE_Y = 0.45
HACK_P = np.array([1.45, 0.0, 0.30]);    HACK_Y = -0.55
CHILL_A = np.array([9.2, 0.0, 3.6]);     CHILL_B = np.array([3.55, 0.0, 1.70])
WALK_T0, WALK_T1 = 8.55, 11.05
HACK_LEAVE0, HACK_LEAVE1 = 22.75, TOTAL

def chill_state(t):
    if t <= WALK_T0:
        return CHILL_A, -1.86, False
    if t >= WALK_T1:
        u = clamp01((t - WALK_T1) / 0.8)
        return CHILL_B, -1.86 + (-0.55 + 1.86) * smooth(u), False
    u = (t - WALK_T0) / (WALK_T1 - WALK_T0)
    p = lerp(CHILL_A, CHILL_B, smooth(u))
    return p, -1.86, True

def hacker_state(t):
    if t < HACK_LEAVE0:
        return HACK_P, HACK_Y, False
    u = clamp01((t - HACK_LEAVE0) / 2.4)
    p = lerp(HACK_P, HACK_P + np.array([-1.2, 0, -5.4]), smooth(u))
    yaw = HACK_Y + (math.pi - 0.25 - HACK_Y) * smooth(min(1.0, u * 2.4))
    return p, yaw, u < 1.0

def speaker(t):
    for k, v in L.items():
        if v['start'] - 0.06 <= t <= v['start'] + v['dur'] + 0.08:
            return k, v
    return None, None

# ------------------------------------------------------------------------ shots
def S(t0, t1, A, B, fov=(44, 44), **kw):
    d = dict(t0=t0, t1=t1, A=A, B=B, fov=fov, shake=0.0, kind='normal', tags=(), pal='day', tint=None)
    d.update(kw)
    return d

SHOTS = [
    S(0.00, 1.12, ((4.3, 2.95, 8.7), (0.2, 1.5, 0.4)), ((3.2, 2.62, 7.3), (0.1, 1.45, 0.4)), (50, 48)),
    S(1.12, 3.46, ((0.35, 2.20, 6.45), (-0.25, 1.46, 0.45)), ((0.05, 2.14, 5.95), (-0.20, 1.44, 0.45)),
      (43, 42), tags=('steve', 'hacker')),
    S(3.46, 5.06, ((-2.95, 2.38, 3.25), (1.48, 1.58, 0.35)), ((-2.60, 2.30, 3.05), (1.48, 1.56, 0.35)), (41, 40)),
    S(5.06, 5.95, ((2.05, 2.26, 4.55), (-1.72, 1.54, 0.95)), ((1.85, 2.22, 4.35), (-1.74, 1.52, 0.95)), (40, 39)),
    S(5.95, 8.42, ((0.95, 1.12, 3.45), (1.52, 1.72, 0.30)), ((1.25, 1.02, 2.95), (1.52, 1.70, 0.30)), (44, 41)),
    S(8.42, 11.62, ((2.0, 2.72, 9.4), (2.75, 1.40, 1.25)), ((1.6, 2.58, 8.4), (2.30, 1.40, 1.10)), (54, 50),
      tags=('steve', 'hacker', 'chill')),
    S(11.62, 13.52, ((-7.0, 0.70, 5.6), (-5.4, 2.2, -7.0)), ((-3.4, 2.55, 3.8), (-4.2, 2.6, -9.5)),
      (54, 47), kind='atmo', pal='dusk'),
    S(13.52, 15.16, ((5.35, 1.30, 4.45), (3.55, 1.42, 1.70)), ((4.95, 1.44, 3.75), (3.58, 1.40, 1.70)),
      (50, 46), shake=0.9, kind='combat', pal='dusk'),
    S(15.16, 16.62, None, None, (39, 37), kind='sword', pal='dusk'),
    S(16.62, 18.56, ((-0.15, 2.10, 4.45), (1.46, 1.50, 0.33)), ((0.10, 2.02, 3.95), (1.46, 1.46, 0.33)), (41, 39)),
    S(18.56, 19.86, ((2.95, 2.18, 4.10), (-1.72, 1.54, 0.95)), ((2.70, 2.14, 3.85), (-1.72, 1.52, 0.95)), (41, 40)),
    S(19.86, 22.46, ((3.00, 2.20, 6.20), (5.40, 1.45, 1.40)), ((3.20, 2.12, 5.75), (5.45, 1.43, 1.40)),
      (46, 44), kind='price'),
    S(22.46, LOGO_T, ((1.1, 2.80, 9.0), (1.0, 1.42, 0.9)), ((0.7, 2.70, 8.2), (0.9, 1.40, 0.7)), (53, 51),
      tags=('steve', 'chill')),
    S(LOGO_T, TOTAL + 0.1, None, None, (46, 42), kind='logo', pal='night'),
]

def shot_at(t):
    for sh in SHOTS:
        if sh['t0'] <= t < sh['t1']:
            return sh
    return SHOTS[-1]

SWORD_P = np.array([-0.60, 1.95, 4.25])
LOGO_SWORD = np.array([0.0, 2.95, 0.0])

def camera(sh, t):
    u = clamp01((t - sh['t0']) / max(1e-6, sh['t1'] - sh['t0']))
    k = sh['kind']
    if k == 'sword':
        a = 0.9 + u * 1.15
        eye = SWORD_P + np.array([math.sin(a) * 2.05, 0.16 - 0.08 * u, math.cos(a) * 2.05])
        tgt = SWORD_P + np.array([0, 0.33, 0])
        fov = sh['fov'][0] + (sh['fov'][1] - sh['fov'][0]) * u
        return Cam(eye, tgt, fov)
    if k == 'logo':
        a = -0.35 + u * 0.55
        eye = LOGO_SWORD + np.array([math.sin(a) * 8.2, -0.35 - 0.2 * u, math.cos(a) * 8.2])
        tgt = LOGO_SWORD + np.array([0, -0.62, 0])
        fov = sh['fov'][0] + (sh['fov'][1] - sh['fov'][0]) * smooth(u)
        return Cam(eye, tgt, fov)
    uu = smooth(u) if k != 'combat' else ease_out(u)
    eye = lerp(sh['A'][0], sh['B'][0], uu)
    tgt = lerp(sh['A'][1], sh['B'][1], uu)
    fov = sh['fov'][0] + (sh['fov'][1] - sh['fov'][0]) * uu
    # handheld
    ph = sh['t0'] * 3.7
    amp = 0.016 + 0.05 * sh['shake']
    eye = eye + np.array([math.sin(t * 2.3 + ph), math.sin(t * 1.7 + ph * 2), math.sin(t * 2.9 + ph * 3)]) * amp
    if sh['shake'] > 0:
        hit = max(0.0, 1.0 - abs(t - (s('L6') + 0.55)) * 4.0) + max(0.0, 1.0 - abs(t - (s('L6') + 1.25)) * 4.0)
        eye = eye + np.array([math.sin(t * 61), math.sin(t * 47), 0]) * 0.05 * hit * sh['shake']
    roll = 0.0
    if k == 'combat':
        roll = -0.045 + 0.03 * math.sin(t * 2.0)
    return Cam(eye, tgt, fov, roll=roll)

class Movie:
    def __init__(self, W=1280, H=720, SS=2):
        self.r = Renderer(W, H, SS)
        self.world = scene.build_world()
        self.W, self.H = W, H
        self._sky = {}

    def sky(self, cam, pal, shot):
        key = pal
        base = self._sky.get(key)
        if base is None:
            P = {'day': PAL_DAY, 'dusk': PAL_DUSK, 'night': PAL_NIGHT}[pal]
            base = self.r.sky_buffer(*P)
            self._sky[key] = base
        if pal == 'night':
            return base
        sp = None
        tmp = Cam(cam.eye, cam.eye + cam.M[2], 1)
        self.r.cam = cam
        pt = self.r.project_point(tuple(np.array(cam.eye) + SUN_DIR * 400))
        if pt is not None:
            fx, fy = pt[0] / self.W, pt[1] / self.H
            if -0.5 < fx < 1.5 and -0.6 < fy < 1.4:
                S_ = self.r
                rad = 0.075 * S_.W
                cx, cy = fx * S_.W, fy * S_.H
                x0 = max(0, int(cx - rad * 3.2)); x1 = min(S_.W, int(cx + rad * 3.2))
                y0 = max(0, int(cy - rad * 3.2)); y1 = min(S_.H, int(cy + rad * 3.2))
                if x1 <= x0 or y1 <= y0:
                    return base
                sky = base.copy()
                X = np.arange(x0, x1, dtype=np.float32)[None, :]
                Y = np.arange(y0, y1, dtype=np.float32)[:, None]
                d = np.sqrt((X - np.float32(cx)) ** 2 + (Y - np.float32(cy)) ** 2) / np.float32(rad)
                glow = np.exp(-d * d * 0.85)[:, :, None]
                core = np.clip(1.6 - d * 1.6, 0, 1)[:, :, None]
                c = np.array([255, 246, 214], np.float32)
                w = sky[y0:y1, x0:x1]
                w = w * (1 - 0.8 * glow) + c * 0.8 * glow
                sky[y0:y1, x0:x1] = np.clip(w * (1 - core) + c * core, 0, 255)
                return sky
        return base

    # ----------------------------------------------------------------- render
    def frame(self, t):
        r = self.r
        sh = shot_at(t)
        cam = camera(sh, t)
        pal = sh['pal']
        night = pal == 'night'
        sky = self.sky(cam, pal, sh)
        if night:
            tint = (0.56, 0.60, 0.86)
        elif pal == 'dusk':
            tint = (1.14, 0.99, 0.86)
        else:
            tint = (1.03, 1.0, 0.95)
        tint = sh['tint'] or tint
        fog = (18, 62) if night else ((16, 78) if pal == 'dusk' else (26, 100))
        r.begin(cam, sky, fog=fog, tint=tint)
        scene.ground(r)
        scene.patch(r, -9.5, -4.2, 9.5, 3.0, 'path')
        self.world.draw(r)
        scene.props(r, t)
        spk, line = speaker(t)
        who = line['who'] if line else None

        if not night:
            # ------------- characters
            cp, cy, cwalk = chill_state(t)
            hp, hy, hwalk = hacker_state(t)
            st = rig.Char('steve', STEVE_P, STEVE_Y)
            hk = rig.Char('hacker', hp, hy)
            ch = rig.Char('chill', cp, cy)
            st.idle(t, talk=(who == 'steve'))
            if hwalk:
                hk.walk(t, 0.85, talk=(who == 'hacker'))
            else:
                hk.idle(t, talk=(who == 'hacker'))
            if cwalk:
                ch.walk(t, 1.0, talk=(who == 'chill'))
            else:
                ch.idle(t + 0.7, talk=(who == 'chill'), energy=1.25)
            ch.p['item'] = 'sword'
            # looks
            focus = {'steve': STEVE_P, 'hacker': hp, 'chill': cp}
            tgt = focus.get(who, HACK_P)
            if t < WALK_T0:
                st.look_at(HACK_P + np.array([0, 1.6, 0]))
                hk.look_at(STEVE_P + np.array([0, 1.6, 0]))
            else:
                st.look_at(tgt + np.array([0, 1.6, 0]))
                if not hwalk:
                    hk.look_at(tgt + np.array([0, 1.6, 0]))
                if not cwalk:
                    ch.look_at((STEVE_P if who == 'chill' else tgt) + np.array([0, 1.6, 0]))
            if s('L8') - 0.35 < t < s('L9'):          # hacker deflates
                k = clamp01((t - (s('L8') - 0.35)) / 0.8)
                hk.p['head'] = (hk.p['head'][0] * (1 - 0.5 * k), hk.p['head'][1] + 0.42 * k, hk.p['head'][2])
                hk.p['armA'] = hk.p['armA'] * (1 - k) + 0.12 * k
                hk.p['armB'] = hk.p['armB'] * (1 - k) + 0.10 * k
            if t > s('L11') - 0.1 and t < s('L11') + 1.2:   # Steve nods / thumbs up
                k = clamp01((t - s('L11') + 0.1) / 0.45)
                st.p['armA'] = -1.95 * k
                st.p['armA_z'] = 0.18 + 0.25 * k
            if sh['kind'] == 'price':
                dcam = np.array(cam.eye) - cp
                ch.yaw = math.atan2(dcam[0], dcam[2]) - 0.30
                ch.look_at(np.array(cam.eye) + np.array([0, -0.25, 0]), 0.75)
            if sh['kind'] == 'combat':
                dcam = np.array(cam.eye) - cp
                ch.yaw = math.atan2(dcam[0], dcam[2]) - 0.22
                ch.look_at(np.array(cam.eye) + np.array([0, -0.3, 0]), 0.7)
                for k0 in (s('L6') + 0.18, s('L6') + 0.92):
                    if k0 <= t < k0 + 0.55:
                        ch.swing(t, (t - k0) / 0.55)
            for c in (st, hk, ch):
                scene.blob_shadow(r, c.pos, 0.56)
            st.draw(r); hk.draw(r); ch.draw(r)
            if sh['kind'] == 'sword':
                M = rot_y(t * 1.35) @ rot_z(0.16) @ rot_x(0.08)
                scene.glow(r, SWORD_P + np.array([0, 0.33, 0]), 1.05, (150, 112, 226), 0.55)
                rig.draw_sword(r, M, SWORD_P, 0.95, glow=0.55)
                scene.particles(r, t, n=46, box=(7, 4, 5), color=(214, 186, 255), speed=0.5)
            scene.particles(r, t, n=38 if pal != 'dusk' else 88,
                            box=(20, 5, 16), color=(255, 232, 186), emissive=0.92, speed=0.3)
        else:
            scene.stars(r, t)
            M = rot_y(0.55 + (t - LOGO_T) * 0.55) @ rot_z(0.22)
            scene.glow(r, LOGO_SWORD + np.array([0, 0.35, 0]), 1.95, (132, 104, 214), 0.60)
            rig.draw_sword(r, M, LOGO_SWORD, 1.95, glow=0.75)
            scene.particles(r, t, n=85, box=(16, 6, 12), color=(180, 210, 255), emissive=1.0, speed=0.45)

        arr = r.finish()
        # ------------------------------------------------------------ 2D layer
        if night:
            arr = overlay.grade(arr, vignette=0.52, warm=(0.95, 0.97, 1.08), contrast=1.08)
        elif pal == 'dusk':
            arr = overlay.grade(arr, vignette=0.42, warm=(1.08, 1.01, 0.92), contrast=1.06)
        else:
            arr = overlay.grade(arr, vignette=0.33, warm=(1.035, 1.005, 0.965), contrast=1.045)
        img = Image.fromarray(arr).convert('RGBA')

        for who_t in sh['tags']:
            p = {'steve': STEVE_P, 'hacker': hacker_state(t)[0], 'chill': chill_state(t)[0]}[who_t]
            if who_t == 'chill' and t < WALK_T0 + 0.3:
                continue
            pt = r.project_point(tuple(np.array(p) + np.array([0, 2.22, 0])))
            a = clamp01((t - sh['t0']) / 0.4) * clamp01((sh['t1'] - t) / 0.3)
            img = overlay.nametag(img, pt, who_t, a=a * 0.95)

        if line and not night:
            st_, en_ = line['start'], line['start'] + line['dur']
            a = clamp01((t - st_ + 0.1) / 0.18) * clamp01((en_ + 0.32 - t) / 0.3)
            img = overlay.subtitle(img, line['text'], line['who'], a)

        if sh['kind'] == 'price' or (19.9 < t < 23.0):
            u = (t - (s('L10') + 0.05)) / 0.8
            if u > 0:
                img = overlay.price_badge(img, u)
        if night:
            img = overlay.logo_card(img, t - LOGO_T)
            img = overlay.flash(img, max(0.0, 0.85 - (t - LOGO_T) * 2.6))
        if t < 0.7:
            img = overlay.fade_black(img, 1.0 - clamp01(t / 0.7))
        if t > TOTAL - 0.9:
            img = overlay.fade_black(img, clamp01((t - (TOTAL - 0.9)) / 0.85))
        return np.asarray(img.convert('RGB'))
