"""Procedural 16x16 block textures + pixel-art character skins."""
import numpy as np

R = np.random.RandomState(1337)

def _n(base, amp, size=16, seed=None):
    rs = np.random.RandomState(seed) if seed is not None else R
    t = np.array(base, np.float32)[None, None, :] + rs.uniform(-amp, amp, (size, size, 1))
    return np.clip(t, 0, 255).astype(np.uint8)

def grid(rows, cmap):
    """rows: list of equal-length strings; cmap: char -> (r,g,b)."""
    h = len(rows); w = len(rows[0])
    out = np.zeros((h, w, 3), np.uint8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            out[y, x] = cmap[ch]
    return out

def flat(c, size=8):
    return np.tile(np.array(c, np.uint8), (size, size, 1))

def speckle(t, color, n, seed=3, amp=0):
    rs = np.random.RandomState(seed)
    t = t.copy()
    h, w = t.shape[:2]
    for _ in range(n):
        y, x = rs.randint(h), rs.randint(w)
        t[y, x] = np.clip(np.array(color, np.int32) + rs.randint(-amp, amp + 1) if amp else color, 0, 255)
    return t

# --------------------------------------------------------------- world blocks
def make_blocks():
    B = {}
    g = _n((104, 168, 68), 16, seed=1)
    g = speckle(g, (122, 186, 76), 40, 11)
    g = speckle(g, (88, 148, 58), 40, 12)
    B['grass_top'] = g
    d = _n((134, 96, 67), 14, seed=2)
    d = speckle(d, (112, 78, 53), 50, 13)
    B['dirt'] = d
    gs = d.copy()
    rs = np.random.RandomState(7)
    for x in range(16):
        k = 3 + rs.randint(0, 3)
        gs[:k, x] = g[rs.randint(16), x]
    B['grass_side'] = gs
    ls = _n((104, 83, 50), 10, seed=4)
    for x in range(0, 16, 3):
        ls[:, x] = np.clip(ls[:, x].astype(int) - 22, 0, 255)
    for x in range(2, 16, 5):
        ls[:, x] = np.clip(ls[:, x].astype(int) + 16, 0, 255)
    B['log_side'] = ls
    lt = _n((150, 120, 72), 8, seed=5)
    yy, xx = np.mgrid[0:16, 0:16]
    rr = np.sqrt((yy - 7.5) ** 2 + (xx - 7.5) ** 2)
    ring = (np.sin(rr * 1.9) * 16).astype(np.int32)[:, :, None]
    B['log_top'] = np.clip(lt.astype(np.int32) + ring, 0, 255).astype(np.uint8)
    lv = _n((56, 124, 42), 18, seed=6)
    lv = speckle(lv, (40, 96, 32), 60, 14)
    lv = speckle(lv, (74, 150, 54), 50, 15)
    B['leaves'] = lv
    lv2 = np.clip(lv.astype(np.int32) + np.array([10, -6, -14]), 0, 255).astype(np.uint8)
    B['leaves_dark'] = np.clip(lv.astype(np.int32) - 16, 0, 255).astype(np.uint8)
    B['leaves_autumn'] = lv2
    pl = _n((162, 130, 78), 9, seed=8)
    for y in range(0, 16, 4):
        pl[y] = np.clip(pl[y].astype(int) - 26, 0, 255)
    B['planks'] = pl
    st = _n((126, 126, 126), 12, seed=9)
    B['stone'] = st
    cb = _n((122, 122, 122), 20, seed=10)
    cb = speckle(cb, (92, 92, 92), 70, 16)
    cb = speckle(cb, (150, 150, 150), 40, 17)
    B['cobble'] = cb
    B['stonebrick'] = (lambda t: t)(_n((124, 124, 124), 8, seed=18))
    sb = B['stonebrick'].copy()
    for y in range(0, 16, 8):
        sb[y] = np.clip(sb[y].astype(int) - 34, 0, 255)
    for y in range(0, 16, 8):
        for x in range((0 if y == 0 else 8), 16, 16):
            sb[y:y + 8, x % 16] = np.clip(sb[y:y + 8, x % 16].astype(int) - 34, 0, 255)
    sb[:, 7] = np.clip(sb[:, 7].astype(int) - 30, 0, 255)
    B['stonebrick'] = sb
    gl = _n((246, 214, 140), 12, seed=19)
    gl = speckle(gl, (255, 246, 206), 45, 20)
    B['glowstone'] = gl
    sl = _n((190, 228, 214), 10, seed=21)
    sl = speckle(sl, (235, 255, 248), 40, 22)
    B['sealantern'] = sl
    B['obsidian'] = speckle(_n((22, 16, 36), 8, seed=23), (58, 40, 92), 40, 24)
    B['portal'] = speckle(_n((122, 48, 186), 22, seed=25), (186, 120, 236), 60, 26)
    B['gravel'] = speckle(_n((124, 120, 118), 18, seed=27), (92, 88, 86), 70, 28)
    B['path'] = speckle(_n((146, 120, 82), 12, seed=29), (120, 98, 66), 60, 30)
    B['amethyst'] = speckle(_n((150, 110, 212), 16, seed=31), (196, 160, 240), 50, 32)
    B['darkwood'] = _n((72, 52, 34), 9, seed=33)
    B['snow'] = _n((238, 244, 252), 7, seed=34)
    B['netherbrick'] = (lambda t: t)(_n((62, 30, 34), 10, seed=35))
    B['white'] = flat((236, 240, 248), 8)
    B['black'] = flat((16, 16, 20), 8)
    B['iron'] = _n((206, 206, 210), 10, seed=36)
    B['diamond'] = speckle(_n((96, 220, 222), 14, seed=37), (180, 248, 250), 40, 38)
    B['gold'] = speckle(_n((236, 196, 70), 12, seed=39), (255, 232, 140), 35, 40)
    B['purpur'] = _n((168, 118, 180), 10, seed=41)
    return B

BLOCKS = make_blocks()

def logblock():
    return {'top': BLOCKS['log_top'], 'bottom': BLOCKS['log_top'], 'north': BLOCKS['log_side'],
            'south': BLOCKS['log_side'], 'east': BLOCKS['log_side'], 'west': BLOCKS['log_side']}

def grassblock():
    s = BLOCKS['grass_side']
    return {'top': BLOCKS['grass_top'], 'bottom': BLOCKS['dirt'], 'north': s, 'south': s, 'east': s, 'west': s}

def simple(name):
    t = BLOCKS[name]
    return {'top': t, 'bottom': t, 'north': t, 'south': t, 'east': t, 'west': t}

# ------------------------------------------------------------------- skins
def _skin(cmap, front, back, left, right, top, bottom):
    return {'south': grid(front, cmap), 'north': grid(back, cmap), 'east': grid(right, cmap),
            'west': grid(left, cmap), 'top': grid(top, cmap), 'bottom': grid(bottom, cmap)}

STEVE_C = {'s': (198, 146, 108), 'd': (168, 118, 84), 'H': (62, 42, 24), 'h': (78, 54, 30),
           'W': (236, 236, 240), 'E': (60, 96, 168), 'B': (46, 30, 18), 'M': (110, 62, 50),
           'c': (0, 158, 158), 'C': (0, 178, 178), 'j': (58, 74, 140), 'J': (68, 86, 158),
           'b': (62, 62, 68), 'k': (28, 28, 32), 'x': (142, 98, 70)}

_SH = None
def shadow_tex(size=24, power=2.2):
    global _SH
    if _SH is None:
        yy, xx = np.mgrid[0:size, 0:size]
        d = np.sqrt(((yy - (size - 1) / 2) / (size / 2)) ** 2 + ((xx - (size - 1) / 2) / (size / 2)) ** 2)
        a = np.clip(1.0 - d, 0, 1) ** power * 0.55
        _SH = (np.zeros((size, size, 3), np.uint8) + np.array([18, 26, 14], np.uint8), a.astype(np.float32))
    return _SH

def steve_head(mouth='closed'):
    mouthrow = {'closed': "ssMMMMss", 'open': "ssMMMMss", 'wide': "sMMMMMMs"}[mouth]
    front = ["HHHHHHHH",
             "HHHHHHHH",
             "HHHHHHHH",
             "sWEssEWs",
             "sssxxsss",
             "ssssssss",
             mouthrow,
             "ssssssss"]
    if mouth == 'open':
        front[6] = "sskkkkss"
        front[7] = "ssMMMMss"
    elif mouth == 'wide':
        front[5] = "ssssssss"
        front[6] = "skkkkkks"
        front[7] = "sMkkkkMs"
    back = ["HHHHHHHH"] * 4 + ["hhhhhhhh"] * 2 + ["ssssssss"] * 2
    side = ["HHHHHHHH", "HHHHHHHH", "HHHHHHHH", "HHsssssh",
            "ssssssss", "ssssssss", "ssdsssss", "ssssssss"]
    top = ["HHHHHHHH"] * 8
    bot = ["dddddddd"] * 8
    return _skin(STEVE_C, front, back, side, side, top, bot)

def body_tex(c_shirt, c_shirt2, c_belt=None, logo=None):
    cm = dict(STEVE_C); cm['1'] = c_shirt; cm['2'] = c_shirt2; cm['3'] = c_belt or c_shirt2
    cm['L'] = logo or c_shirt2
    front = ["11111111", "11211211", "11111111", "11111111",
             "1111L111" if logo else "11111111", "11111111", "33333333", "33333333"]
    back = ["11111111", "11111111", "11111111", "11111111",
            "11111111", "11111111", "33333333", "33333333"]
    side = ["21111112", "21111112", "21111112", "21111112",
            "21111112", "21111112", "23333332", "23333332"]
    top = ["11111111"] * 8
    bot = ["33333333"] * 8
    return _skin(cm, front, back, side, side, top, bot)

def limb_tex(c_top, c_bot, n_top=4, cm_extra=None):
    cm = dict(STEVE_C); cm['1'] = c_top; cm['2'] = c_bot
    rows = ["11111111"] * n_top + ["22222222"] * (8 - n_top)
    return _skin(cm, rows, rows, rows, rows, ["11111111"] * 8, ["22222222"] * 8)

def hacker_head(mouth='closed'):
    cm = {'k': (26, 26, 32), 'K': (16, 16, 20), 'g': (40, 42, 50), 'G': (120, 255, 170),
          'w': (210, 255, 230), 's': (150, 132, 120), 'd': (108, 92, 84), 'm': (60, 40, 40)}
    front = ["KKKKKKKK",
             "KKKKKKKK",
             "KggggggK",
             "KGGssGGK",
             "KssssssK",
             "KssssssK",
             "KsmmmmsK",
             "KssssssK"]
    if mouth == 'open':
        front[6] = "KsKKKKsK"
    elif mouth == 'wide':
        front[5] = "KssssssK"; front[6] = "KKKKKKKK"; front[7] = "KsKKKKsK"
    back = ["KKKKKKKK"] * 8
    side = ["KKKKKKKK", "KKKKKKKK", "KKKKKKKK", "KKKKKKKK",
            "KKKKssss", "KKKssssd", "KKKssdss", "KKKsssss"]
    return _skin(cm, front, back, side, side, ["KKKKKKKK"] * 8, ["dddddddd"] * 8)

def chill_head(mouth='closed'):
    cm = {'s': (212, 164, 126), 'd': (182, 132, 98), 'H': (36, 32, 44), 'W': (240, 244, 252),
          'E': (54, 168, 220), 'B': (34, 30, 40), 'M': (142, 78, 64), 'k': (30, 26, 34),
          'h': (46, 40, 56)}
    front = ["HHHHHHHH",
             "HHHHHHHH",
             "HBBssBBH",
             "sWEssEWs",
             "ssssssss",
             "sMssssMs",
             "ssMMMMss",
             "ssssssss"]
    if mouth == 'open':
        front[6] = "sWkkkkWs"; front[7] = "ssMMMMss"
    elif mouth == 'wide':
        front[5] = "ssssssss"; front[6] = "sWWWWWWs"; front[7] = "skkkkkks"
    back = ["HHHHHHHH"] * 5 + ["hhhhhhhh"] + ["ssssssss"] * 2
    side = ["HHHHHHHH", "HHHHHHHH", "HHHHHHHH", "HHHsssss",
            "ssssssss", "ssssssss", "ssdsssss", "ssssssss"]
    return _skin(cm, front, back, side, side, ["HHHHHHHH"] * 8, ["dddddddd"] * 8)


_GL = {}
def glow_tex(color, size=40, power=2.0, peak=0.72):
    k = (tuple(color), size, power, peak)
    if k not in _GL:
        yy, xx = np.mgrid[0:size, 0:size]
        d = np.sqrt(((yy - (size - 1) / 2) / (size / 2)) ** 2 + ((xx - (size - 1) / 2) / (size / 2)) ** 2)
        a = (np.clip(1.0 - d, 0, 1) ** power * peak).astype(np.float32)
        _GL[k] = (np.zeros((size, size, 3), np.uint8) + np.array(color, np.uint8), a)
    return _GL[k]
