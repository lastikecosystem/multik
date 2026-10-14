"""2D layer: subtitles, nametags, price badge, logo card, grade."""
import numpy as np, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FD = '/usr/share/fonts/opentype/inter/'
_F = {}
def font(name, size):
    k = (name, size)
    if k not in _F:
        _F[k] = ImageFont.truetype(FD + name + '.otf', size)
    return _F[k]

COL = {'steve': (120, 232, 240), 'hacker': (130, 255, 180), 'chill': (170, 170, 255)}
NAME = {'steve': 'Стив', 'hacker': 'Хакер', 'chill': 'Chill'}

def outlined(d, xy, text, f, fill, ow=3, oc=(0, 0, 0, 235), anchor='mm'):
    x, y = xy
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            if dx * dx + dy * dy <= ow * ow and (dx or dy):
                d.text((x + dx, y + dy), text, font=f, fill=oc, anchor=anchor)
    d.text((x, y), text, font=f, fill=fill, anchor=anchor)

def wrap(text, f, maxw, d):
    words = text.split(); lines = []; cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) > maxw and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines

def subtitle(img, text, who, a=1.0):
    if a <= 0.01:
        return img
    W, H = img.size
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    fs = int(H * 0.052)
    f = font('Inter-Bold', fs)
    fn = font('Inter-Black', int(fs * 0.86))
    lines = wrap(text, f, W * 0.76, d)
    lh = int(fs * 1.26)
    y = int(H * 0.845) - (len(lines) - 1) * lh
    nm = NAME[who] + ':'
    outlined(d, (W // 2, y - lh - int(fs * 0.12)), nm, fn, COL[who] + (255,), ow=3)
    for i, ln in enumerate(lines):
        outlined(d, (W // 2, y + i * lh), ln, f, (255, 255, 255, 255), ow=3)
    if a < 1:
        ov.putalpha(ov.getchannel('A').point(lambda v: int(v * a)))
    return Image.alpha_composite(img.convert('RGBA'), ov)

def nametag(img, pos, who, a=1.0, scale=1.0):
    if a <= 0.02 or pos is None:
        return img
    W, H = img.size
    x, y, z = pos
    s = max(0.45, min(1.6, 7.0 / max(1.0, z))) * scale
    fs = max(10, int(H * 0.034 * s))
    f = font('Inter-SemiBold', fs)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    txt = NAME[who]
    tw = d.textlength(txt, font=f)
    pad = int(fs * 0.42)
    box = (x - tw / 2 - pad, y - fs * 0.78 - pad * 0.5, x + tw / 2 + pad, y + fs * 0.52 + pad * 0.5)
    d.rounded_rectangle(box, radius=int(fs * 0.3), fill=(8, 10, 16, int(150 * a)))
    d.text((x, y - fs * 0.12), txt, font=f, fill=COL[who] + (int(248 * a),), anchor='mm')
    return Image.alpha_composite(img.convert('RGBA'), ov)

def _gradient_text(size, text, f, c0, c1, anchor_xy, glow=(120, 220, 255), glow_r=18, glow_a=0.85):
    W, H = size
    mask = Image.new('L', size, 0)
    ImageDraw.Draw(mask).text(anchor_xy, text, font=f, fill=255, anchor='mm')
    bb = mask.getbbox()
    grad = Image.new('RGB', size, c0)
    if bb:
        g = np.zeros((H, W, 3), np.uint8)
        y0, y1 = bb[1], max(bb[3], bb[1] + 1)
        tt = np.clip((np.arange(H) - y0) / max(1, (y1 - y0)), 0, 1)[:, None]
        g[:] = (np.array(c0) * (1 - tt) + np.array(c1) * tt)[:, None, :].astype(np.uint8)
        grad = Image.fromarray(g)
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    if glow:
        gl = mask.filter(ImageFilter.GaussianBlur(glow_r))
        gi = Image.new('RGBA', size, glow + (0,))
        gi.putalpha(gl.point(lambda v: int(v * glow_a)))
        out = Image.alpha_composite(out, gi)
    tx = Image.new('RGBA', size, (0, 0, 0, 0))
    tx.paste(grad, (0, 0), mask)
    tx.putalpha(mask)
    return Image.alpha_composite(out, tx)

def price_badge(img, u):
    """u: 0..1 animation progress."""
    if u <= 0:
        return img
    W, H = img.size
    e = 1 - (1 - min(1.0, u * 1.9)) ** 3
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    bw, bh = int(W * 0.30), int(H * 0.125)
    x0 = int(W * 0.64 - bw / 2 + (1 - e) * W * 0.22)
    y0 = int(H * 0.18)
    al = int(235 * e)
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=int(bh * 0.28), fill=(14, 16, 28, al))
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=int(bh * 0.28), outline=(120, 220, 255, al), width=3)
    f1 = font('Inter-Black', int(bh * 0.46))
    f2 = font('Inter-SemiBold', int(bh * 0.24))
    d.text((x0 + bw / 2, y0 + bh * 0.42), "200 ₽", font=f1, fill=(255, 255, 255, al), anchor='mm')
    d.text((x0 + bw / 2, y0 + bh * 0.76), "В МЕСЯЦ", font=f2, fill=(150, 225, 255, al), anchor='mm')
    return Image.alpha_composite(img.convert('RGBA'), ov)

def logo_card(img, u, price_u=0.0):
    """u: seconds since logo hit."""
    W, H = img.size
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    k = min(1.0, max(0.0, u / 0.55))
    e = 1 - (1 - k) ** 3
    sc = 1.28 - 0.28 * e
    fs = int(H * 0.26 * sc)
    f = font('Inter-Black', fs)
    cy = int(H * 0.40)
    lg = _gradient_text((W, H), "CHILL", f, (150, 245, 255), (150, 120, 255), (W / 2, cy),
                        glow=(110, 200, 255), glow_r=int(H * 0.035), glow_a=0.9 * e)
    lg.putalpha(lg.getchannel('A').point(lambda v: int(v * e)))
    ov = Image.alpha_composite(ov, lg)
    d = ImageDraw.Draw(ov)
    if u > 0.28:
        a = min(1.0, (u - 0.28) / 0.45)
        f2 = font('Inter-SemiBold', int(H * 0.058))
        txt = "C  L  I  E  N  T"
        d.text((W / 2, cy + fs * 0.44), txt, font=f2, fill=(205, 230, 255, int(235 * a)), anchor='mm')
        d.line((W * 0.5 - W * 0.17 * a, cy + fs * 0.60, W * 0.5 + W * 0.17 * a, cy + fs * 0.60),
               fill=(120, 210, 255, int(200 * a)), width=2)
    if u > 0.75:
        a = min(1.0, (u - 0.75) / 0.5)
        f3 = font('Inter-Black', int(H * 0.072))
        outlined(d, (W / 2, H * 0.70), "НЕ ПРОСТО АУРА.", f3, (255, 255, 255, int(252 * a)), ow=3,
                 oc=(6, 8, 18, int(220 * a)))
    if u > 1.35:
        a = min(1.0, (u - 1.35) / 0.5)
        f4 = font('Inter-SemiBold', int(H * 0.042))
        d.text((W / 2, H * 0.785), "играй спокойно — побеждай красиво", font=f4,
               fill=(190, 215, 240, int(225 * a)), anchor='mm')
    if u > 1.9:
        a = min(1.0, (u - 1.9) / 0.45)
        bw, bh = int(W * 0.30), int(H * 0.105)
        x0, y0 = int(W / 2 - bw / 2), int(H * 0.845)
        d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=int(bh * 0.5),
                            fill=(255, 255, 255, int(236 * a)))
        f5 = font('Inter-Black', int(bh * 0.52))
        d.text((W / 2, y0 + bh * 0.52), "200 ₽ / МЕСЯЦ", font=f5, fill=(16, 18, 32, int(255 * a)), anchor='mm')
    return Image.alpha_composite(img.convert('RGBA'), ov)

_VIG = {}
def grade(arr, vignette=0.32, warm=(1.0, 1.0, 1.0), contrast=1.04, lift=0.0):
    h, w = arr.shape[:2]
    k = (h, w)
    if k not in _VIG:
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.sqrt(((yy - h / 2) / (h / 2)) ** 2 + ((xx - w / 2) / (w / 2)) ** 2)
        _VIG[k] = np.clip(1.0 - 0.55 * np.clip(d - 0.55, 0, None) ** 1.6, 0, 1).astype(np.float32)[:, :, None]
    a = arr.astype(np.float32)
    a *= (1 - vignette) + vignette * _VIG[k]
    a = (a - 128) * contrast + 128 + lift * 255
    a *= np.array(warm, np.float32)
    return np.clip(a, 0, 255).astype(np.uint8)

def flash(img, a, color=(255, 255, 255)):
    if a <= 0.004:
        return img
    ov = Image.new('RGBA', img.size, color + (int(min(1.0, a) * 255),))
    return Image.alpha_composite(img.convert('RGBA'), ov)

def fade_black(img, a):
    return flash(img, a, (0, 0, 0))
