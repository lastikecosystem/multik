"""Minimal software 3D rasterizer: textured boxes, z-buffer, fog. Minecraft look."""
import numpy as np, math

def nrm(v):
    v = np.asarray(v, np.float64)
    n = np.linalg.norm(v)
    return v / (n if n else 1.0)

SUN  = nrm([0.42, 0.88, 0.22])
SUNH = nrm([0.62, 0.0, 0.78])

def face_shade(n):
    ny = max(0.0, n[1])
    s = 0.50 + 0.50 * (ny ** 0.85) + 0.22 * max(0.0, float(np.dot(n, SUNH)))
    if n[1] < -0.5:
        s = 0.42
    return min(s, 1.12)

class Cam:
    def __init__(self, eye, target, fov=58.0, up=(0, 1, 0), roll=0.0):
        self.eye = np.asarray(eye, np.float64)
        f = nrm(np.asarray(target, np.float64) - self.eye)
        r = nrm(np.cross(f, np.asarray(up, np.float64)))
        u = np.cross(r, f)
        if roll:
            c, s = math.cos(roll), math.sin(roll)
            r, u = c * r + s * u, -s * r + c * u
        self.M = np.stack([r, u, f])
        self.tan = math.tan(math.radians(fov) * 0.5)

    def view(self, P):
        return (np.asarray(P, np.float64) - self.eye) @ self.M.T

# ---------------------------------------------------------------- box geometry
# faces: (indices into corner list, normal)
_F = [((4, 5, 7, 6), (0, 0, 1)),    # +z
      ((1, 0, 2, 3), (0, 0, -1)),   # -z
      ((5, 1, 3, 7), (1, 0, 0)),    # +x
      ((0, 4, 6, 2), (-1, 0, 0)),   # -x
      ((2, 3, 7, 6), (0, 1, 0)),    # +y  (top)  -- fixed below
      ((0, 1, 5, 4), (0, -1, 0))]

def box_faces(lo, hi):
    """Yield (4x3 corner array, normal, face-key) for an axis-aligned box."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    c = [(x0, y0, z0), (x1, y0, z0), (x0, y1, z0), (x1, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x0, y1, z1), (x1, y1, z1)]
    out = [((4, 5, 7, 6), (0, 0, 1), 'south'),
           ((1, 0, 2, 3), (0, 0, -1), 'north'),
           ((5, 1, 3, 7), (1, 0, 0), 'east'),
           ((0, 4, 6, 2), (-1, 0, 0), 'west'),
           ((6, 7, 3, 2), (0, 1, 0), 'top'),
           ((0, 1, 5, 4), (0, -1, 0), 'bottom')]
    for idx, n, key in out:
        yield np.array([c[i] for i in idx], np.float64), np.array(n, np.float64), key

QUAD_UV = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], np.float64)

class Renderer:
    def __init__(self, w, h, ss=2):
        self.w, self.h, self.ss = w, h, ss
        self.W, self.H = w * ss, h * ss
        yy = np.arange(self.H, dtype=np.float32)
        self._rows = yy

    def sky_buffer(self, top, mid, bottom, sun=None):
        """Vertical gradient sky, optional sun disc (x_frac, y_frac, radius_frac, color)."""
        t = (self._rows / max(1, self.H - 1)).astype(np.float32)[:, None]
        top = np.array(top, np.float32); mid = np.array(mid, np.float32); bot = np.array(bottom, np.float32)
        a = np.clip(t / 0.55, 0, 1); b = np.clip((t - 0.55) / 0.45, 0, 1)
        col = top * (1 - a) + mid * a
        col = col * (1 - b) + bot * b
        sky = np.repeat(col[:, None, :], self.W, axis=1).copy()
        if sun:
            fx, fy, fr, sc = sun
            X, Y = np.meshgrid(np.arange(self.W, dtype=np.float32), self._rows)
            d = np.sqrt((X - fx * self.W) ** 2 + (Y - fy * self.H) ** 2) / (fr * self.W)
            glow = np.exp(-d * d * 1.5)[:, :, None]
            core = (d < 1.0).astype(np.float32)[:, :, None]
            sc = np.array(sc, np.float32)
            sky = sky * (1 - 0.75 * glow) + sc * 0.75 * glow
            sky = sky * (1 - core) + sc * core
        return np.clip(sky, 0, 255)

    def begin(self, cam, sky, fog=(26.0, 95.0), tint=(1.0, 1.0, 1.0), exposure=1.0):
        self.cam = cam
        self.sky = sky
        self.col = sky.copy()
        self.depth = np.zeros((self.H, self.W), np.float32)
        self.fog0, self.fog1 = fog
        self.tint = np.array(tint, np.float32) * exposure

    # ------------------------------------------------------------- projection
    def _project(self, V):
        z = np.maximum(V[:, 2], 1e-6)
        px = (V[:, 0] / (z * self.tan_a) * 0.5 + 0.5) * self.W
        py = (0.5 - V[:, 1] / (z * self.cam.tan) * 0.5) * self.H
        return np.stack([px, py, 1.0 / z], 1).astype(np.float32)

    @property
    def tan_a(self):
        return self.cam.tan * (self.W / self.H)

    def project_point(self, P):
        """World point -> (x, y) in OUTPUT pixels, and whether in front of camera."""
        V = self.cam.view(np.array([P], np.float64))[0]
        if V[2] <= 0.05:
            return None
        x = (V[0] / (V[2] * self.tan_a) * 0.5 + 0.5) * self.w
        y = (0.5 - V[1] / (V[2] * self.cam.tan) * 0.5) * self.h
        return (x, y, V[2])

    # ------------------------------------------------------------------ polys
    def quad(self, pts, tex, shade=None, uv=None, normal=None, cull=True, emissive=0.0):
        pts = np.asarray(pts, np.float64)
        if normal is None:
            normal = nrm(np.cross(pts[1] - pts[0], pts[2] - pts[0]))
        if cull and np.dot(normal, self.cam.eye - pts.mean(0)) <= 0:
            return
        if shade is None:
            shade = face_shade(normal)
        uv = QUAD_UV if uv is None else np.asarray(uv, np.float64)
        V = self.cam.view(pts)
        poly = [(V[i], uv[i]) for i in range(len(pts))]
        poly = self._clip_near(poly)
        if len(poly) < 3:
            return
        Vc = np.array([p[0] for p in poly]); UVc = np.array([p[1] for p in poly])
        S = self._project(Vc)
        for i in range(1, len(poly) - 1):
            self._tri(S[0], S[i], S[i + 1], UVc[0], UVc[i], UVc[i + 1], tex, shade, emissive)

    def _clip_near(self, poly, near=0.08):
        out = []
        n = len(poly)
        for i in range(n):
            a, ua = poly[i]; b, ub = poly[(i + 1) % n]
            ina, inb = a[2] >= near, b[2] >= near
            if ina:
                out.append((a, ua))
            if ina != inb:
                t = (near - a[2]) / (b[2] - a[2])
                out.append((a + (b - a) * t, ua + (ub - ua) * t))
        return out

    def _tri(self, p0, p1, p2, uv0, uv1, uv2, tex, shade, emissive):
        atex = None
        if isinstance(tex, tuple):
            tex, atex = tex
        W, H = self.W, self.H
        xs = (p0[0], p1[0], p2[0]); ys = (p0[1], p1[1], p2[1])
        x0i = max(int(math.floor(min(xs))), 0); x1i = min(int(math.ceil(max(xs))) + 1, W)
        y0i = max(int(math.floor(min(ys))), 0); y1i = min(int(math.ceil(max(ys))) + 1, H)
        if x1i <= x0i or y1i <= y0i:
            return
        ax0, ay0, aw0 = float(p0[0]), float(p0[1]), float(p0[2])
        ax1, ay1, aw1 = float(p1[0]), float(p1[1]), float(p1[2])
        ax2, ay2, aw2 = float(p2[0]), float(p2[1]), float(p2[2])
        area = (ax1 - ax0) * (ay2 - ay0) - (ax2 - ax0) * (ay1 - ay0)
        if abs(area) < 1e-9:
            return
        ia = np.float32(1.0 / area)
        X = np.arange(x0i, x1i, dtype=np.float32)[None, :] + np.float32(0.5)
        Y = np.arange(y0i, y1i, dtype=np.float32)[:, None] + np.float32(0.5)
        l0 = ((np.float32(ax2 - ax1) * (Y - np.float32(ay1)) - np.float32(ay2 - ay1) * (X - np.float32(ax1))) * ia)
        l1 = ((np.float32(ax0 - ax2) * (Y - np.float32(ay2)) - np.float32(ay0 - ay2) * (X - np.float32(ax2))) * ia)
        l2 = np.float32(1.0) - l0 - l1
        m = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        if not m.any():
            return
        iw = l0 * np.float32(aw0) + l1 * np.float32(aw1) + l2 * np.float32(aw2)
        dsl = self.depth[y0i:y1i, x0i:x1i]
        m &= iw > dsl
        if not m.any():
            return
        l0, l1, l2, iw = l0[m], l1[m], l2[m], iw[m]
        u = (l0 * np.float32(uv0[0] * aw0) + l1 * np.float32(uv1[0] * aw1) + l2 * np.float32(uv2[0] * aw2)) / iw
        v = (l0 * np.float32(uv0[1] * aw0) + l1 * np.float32(uv1[1] * aw1) + l2 * np.float32(uv2[1] * aw2)) / iw
        th, tw = tex.shape[0], tex.shape[1]
        ix = np.mod((u * tw).astype(np.int32), tw)
        iy = np.mod(((1.0 - v) * th).astype(np.int32), th)
        base = tex[iy, ix].astype(np.float32)
        c = base * (np.float32(shade) * self.tint)
        z = np.float32(1.0) / np.maximum(iw, np.float32(1e-6))
        f = np.clip((z - np.float32(self.fog0)) / np.float32(self.fog1 - self.fog0), 0, 1)[:, None] * np.float32(0.92)
        skys = self.sky[y0i:y1i, x0i:x1i][m]
        c = c * (1 - f) + skys * f
        if emissive:
            c = c * np.float32(1 - emissive) + base * np.float32(emissive * 1.25)
        cs = self.col[y0i:y1i, x0i:x1i]
        if atex is None:
            cs[m] = np.clip(c, 0, 255)
            dsl[m] = iw
        else:
            a = atex[iy, ix].astype(np.float32)[:, None]
            dst = cs[m]
            cs[m] = np.clip(c * a + dst * (1 - a), 0, 255)
            op = (a[:, 0] > 0.92)
            if op.any():
                idx = np.where(m)
                dsl[idx[0][op], idx[1][op]] = iw[op]

    def box(self, lo, hi, tex, rot=None, pivot=(0, 0, 0), pos=(0, 0, 0), emissive=0.0, tint=1.0):
        """tex: single array or dict with keys top/bottom/north/south/east/west."""
        R = None if rot is None else np.asarray(rot, np.float64)
        T = np.asarray(pos, np.float64); Pv = np.asarray(pivot, np.float64)
        for pts, n, key in box_faces(lo, hi):
            if R is not None:
                pts = (pts - Pv) @ R.T + Pv + T
                nn = R @ n
            else:
                pts = pts + T
                nn = n
            t = tex[key] if isinstance(tex, dict) else tex
            if t is None:
                continue
            sh = face_shade(nn) * tint
            self.quad(pts, t, shade=sh, normal=nn, emissive=emissive)

    def finish(self):
        s = self.ss
        if s == 1:
            return np.clip(self.col, 0, 255).astype(np.uint8)
        c = self.col.reshape(self.h, s, self.w, s, 3).mean(axis=(1, 3))
        return np.clip(c, 0, 255).astype(np.uint8)

def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float64)

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float64)

def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float64)
