"""Voice-over (piper), lofi music bed, SFX, final mix. Writes timeline.json + mix.wav"""
import numpy as np, subprocess, json, os, math, wave, sys

SR = 44100
VD = '/tmp/claude-0/-home-user-multik/cd20a8da-bfc1-5897-be63-cde9ffe11883/scratchpad/voices'
OUT = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(OUT, 'work'); os.makedirs(WORK, exist_ok=True)

VOICE = {'steve': ('dmitri', 1.00, 1.0), 'hacker': ('denis', 0.84, 1.0), 'chill': ('ruslan', 1.07, 1.0)}

LINES = [
    ('L1', 'steve', 'Слушай, а что у вас вообще есть в клиенте?', 0.45),
    ('L2', 'hacker', 'Ну... аура есть.', 0.40),
    ('L3', 'steve', 'И всё?', 0.30),
    ('L4', 'hacker', 'А что вам ещё-то нужно?', 1.70),
    ('L5', 'chill', 'Секундочку. А у нас в Чилл — красивая атмосфера,', 0.25),
    ('L6', 'chill', 'лучшие боевые функции,', 0.25),
    ('L7', 'chill', 'и кастомные мечи.', 0.55),
    ('L8', 'hacker', 'А у меня... только аура.', 0.45),
    ('L9', 'steve', 'А сколько стоит?', 0.35),
    ('L10', 'chill', 'Двести рублей в месяц.', 0.35),
    ('L11', 'steve', 'Беру.', 1.30),
    ('L12', 'chill', 'Чилл клиент. Не просто аура.', 1.9),
]

def read_wav(p):
    with wave.open(p, 'rb') as w:
        n, sr, ch = w.getnframes(), w.getframerate(), w.getnchannels()
        a = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(1)
    return a, sr

def resample(a, sr, target=SR):
    if sr == target:
        return a
    n = int(len(a) * target / sr)
    return np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)

def pitch(a, r):
    """Resample without changing sample rate -> pitch * r, duration / r."""
    if abs(r - 1.0) < 1e-3:
        return a
    n = int(len(a) / r)
    return np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)

def tts():
    out = {}
    for lid, who, text, _gap in LINES:
        model, r, _ = VOICE[who]
        p = os.path.join(WORK, f'{lid}.wav')
        cmd = ['python3', '-m', 'piper', '--model', os.path.join(VD, model + '.onnx'),
               '--length-scale', f'{r*1.02:.3f}', '--sentence-silence', '0.12', '--output-file', p]
        subprocess.run(cmd, input=text.encode(), check=True, capture_output=True)
        a, sr = read_wav(p)
        a = resample(a, sr)
        a = pitch(a, r)
        # trim silence
        e = np.abs(a)
        k = np.convolve(e, np.ones(400) / 400, 'same')
        idx = np.where(k > 0.004)[0]
        if len(idx):
            a = a[max(0, idx[0] - 1200):min(len(a), idx[-1] + 2600)]
        a = a / max(1e-6, np.abs(a).max()) * 0.82
        if who == 'hacker':   # slight "cold" edge
            a = np.clip(a * 1.15, -0.95, 0.95)
        out[lid] = a
    return out

# ------------------------------------------------------------------- music
def adsr(n, a, d, s, r, sus=0.7):
    env = np.ones(n, np.float32)
    ai, di, ri = int(a * SR), int(d * SR), int(r * SR)
    ai = min(ai, n); di = min(di, max(0, n - ai)); ri = min(ri, n)
    if ai: env[:ai] = np.linspace(0, 1, ai)
    if di: env[ai:ai + di] = np.linspace(1, sus, di)
    env[ai + di:] = sus
    if ri: env[-ri:] *= np.linspace(1, 0, ri)
    return env

def note(freq, dur, kind='pad', amp=0.2, detune=0.004):
    n = int(dur * SR); t = np.arange(n) / SR
    if kind == 'pad':
        x = np.zeros(n, np.float32)
        for m, w in ((1, 1.0), (2, 0.34), (3, 0.16), (4, 0.09), (5, 0.05)):
            x += w * np.sin(2 * np.pi * freq * m * t + m)
            x += w * 0.6 * np.sin(2 * np.pi * freq * m * (1 + detune) * t)
        x *= adsr(n, 0.35, 0.5, 0.0, 0.8, 0.75)
    elif kind == 'bass':
        x = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
        x *= adsr(n, 0.01, 0.18, 0, 0.15, 0.5)
    elif kind == 'bell':
        x = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2.01 * t) + 0.25 * np.sin(2 * np.pi * freq * 3.02 * t)
        x *= np.exp(-t * 3.2)
    elif kind == 'pluck':
        x = np.sin(2 * np.pi * freq * t) * np.exp(-t * 5.0) + 0.3 * np.sin(4 * np.pi * freq * t) * np.exp(-t * 7)
    return (x / max(1e-9, np.abs(x).max()) * amp).astype(np.float32)

def kick(dur=0.32, f0=120, f1=42):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    x += np.random.RandomState(1).normal(0, 1, n) * np.exp(-t * 90) * 0.25
    return (x * 0.85).astype(np.float32)

def snare(dur=0.28, seed=2):
    n = int(dur * SR); t = np.arange(n) / SR
    rs = np.random.RandomState(seed)
    x = rs.normal(0, 1, n) * np.exp(-t * 16) * 0.5 + np.sin(2 * np.pi * 185 * t) * np.exp(-t * 22) * 0.35
    b, a = x.copy(), np.zeros_like(x)
    return (x * 0.55).astype(np.float32)

def hat(dur=0.08, seed=3, amp=0.22):
    n = int(dur * SR); t = np.arange(n) / SR
    rs = np.random.RandomState(seed)
    x = rs.normal(0, 1, n)
    x = x - np.convolve(x, np.ones(6) / 6, 'same')     # crude high-pass
    return (x * np.exp(-t * 55) * amp).astype(np.float32)

def put(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i < 0:
        x = x[-i:]; i = 0
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += x[:j - i] * gain

NOTE = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
def hz(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + (octave - 4) * 12 - 9) / 12.0)

def music(total, hype_at=None):
    buf = np.zeros(int(total * SR) + SR, np.float32)
    bpm = 78.0; beat = 60.0 / bpm; bar = beat * 4
    prog = [('A', ['A3', 'C4', 'E4', 'G4']), ('F', ['F3', 'A3', 'C4', 'E4']),
            ('C', ['C4', 'E4', 'G4', 'B4']), ('G', ['G3', 'B3', 'D4', 'F4'])]
    t = 0.0; i = 0
    while t < total:
        root, ch = prog[i % 4]
        for nm in ch:
            n, o = nm[:-1], int(nm[-1])
            put(buf, note(hz(n, o), bar * 1.05, 'pad', 0.10), t)
        bn, bo = ch[0][:-1], int(ch[0][-1]) - 1
        for k in (0, 1.5, 2.5):
            put(buf, note(hz(bn, bo), beat * 0.9, 'bass', 0.30), t + k * beat)
        for k in (0, 2):
            put(buf, kick(), t + k * beat, 0.55)
        put(buf, snare(), t + 1 * beat, 0.30)
        put(buf, snare(), t + 3 * beat, 0.30)
        for k in np.arange(0, 4, 0.5):
            put(buf, hat(seed=3 + int(k * 2)), t + k * beat, 0.5 if k % 1 else 0.75)
        if i % 2 == 0:
            for k, nm in ((0.5, ch[2]), (1.5, ch[3]), (3.0, ch[1])):
                n, o = nm[:-1], int(nm[-1])
                put(buf, note(hz(n, o + 1), beat, 'pluck', 0.10), t + k * beat)
        t += bar; i += 1
    rs = np.random.RandomState(11)
    buf += rs.normal(0, 1, len(buf)).astype(np.float32) * 0.0025      # vinyl hiss
    return buf

def riser(dur=2.2, f0=180, f1=1500):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    rs = np.random.RandomState(12)
    nz = rs.normal(0, 1, n) * (t / dur) ** 2 * 0.25
    return ((x + nz) * np.linspace(0.2, 1, n)).astype(np.float32)

def impact(dur=2.6):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 54 * t) * np.exp(-t * 2.2) * 0.8
    x += np.sin(2 * np.pi * 81 * t) * np.exp(-t * 3.0) * 0.3
    rs = np.random.RandomState(13)
    x += rs.normal(0, 1, n) * np.exp(-t * 9) * 0.25
    return x.astype(np.float32)

def whoosh(dur=0.55, seed=14):
    n = int(dur * SR); t = np.arange(n) / SR
    rs = np.random.RandomState(seed)
    x = rs.normal(0, 1, n)
    env = np.exp(-((t - dur * 0.55) / (dur * 0.22)) ** 2)
    x = x * env
    k = np.hanning(80) / np.hanning(80).sum()
    return (np.convolve(x, k, 'same') * 0.5).astype(np.float32)

def step(seed=15, amp=0.22):
    n = int(0.12 * SR); t = np.arange(n) / SR
    rs = np.random.RandomState(seed)
    x = rs.normal(0, 1, n) * np.exp(-t * 42)
    x += np.sin(2 * np.pi * 95 * t) * np.exp(-t * 30) * 0.5
    return (x * amp).astype(np.float32)

def blip(f=880, dur=0.12, amp=0.25):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 18) + 0.4 * np.sin(4 * np.pi * f * t) * np.exp(-t * 26)
    return (x * amp).astype(np.float32)

def build():
    V = tts()
    tl = []
    t = 1.15
    for lid, who, text, gap in LINES:
        if lid == 'L5':
            t += 1.25                       # chill guy walks in
        if lid == 'L12':
            t += 0.25
        d = len(V[lid]) / SR
        tl.append(dict(id=lid, who=who, text=text, start=round(t, 3), dur=round(d, 3)))
        t += d + gap
    total = t + 2.6
    mus = music(total)
    buf = np.zeros(int(total * SR) + SR, np.float32)
    put(buf, mus[:len(buf)], 0.0, 0.52)
    # voices + ducking
    duck = np.ones(len(buf), np.float32)
    for item in tl:
        a = V[item['id']]
        put(buf, a, item['start'], 1.0)
        i0 = max(0, int((item['start'] - 0.25) * SR)); i1 = min(len(buf), int((item['start'] + item['dur'] + 0.3) * SR))
        duck[i0:i1] = 0.52
    k = np.hanning(int(0.25 * SR)); k /= k.sum()
    duck = np.convolve(duck, k, 'same').astype(np.float32)
    mus_only = np.zeros_like(buf); put(mus_only, mus[:len(buf)], 0.0, 0.52)
    buf = buf - mus_only + mus_only * duck
    T = {x['id']: x for x in tl}
    # sfx
    for i in range(7):                                   # footsteps of the newcomer
        put(buf, step(seed=20 + i), T['L5']['start'] - 1.35 + i * 0.26, 0.5)
    put(buf, whoosh(), T['L6']['start'] + 0.55, 0.55)     # combat swing
    put(buf, whoosh(0.4, 21), T['L7']['start'] + 0.35, 0.45)
    put(buf, blip(1320, 0.18), T['L7']['start'] + 0.5, 0.5)
    put(buf, blip(660, 0.2), T['L10']['start'] + 0.1, 0.6)
    put(buf, blip(990, 0.25), T['L11']['start'] + 0.05, 0.5)
    logo_t = T['L12']['start'] - 0.85
    put(buf, riser(2.0), logo_t - 2.0, 0.55)
    put(buf, impact(), logo_t, 0.75)
    put(buf, note(hz('A', 4), 3.0, 'bell', 0.22), logo_t + 0.06)
    put(buf, note(hz('E', 5), 3.0, 'bell', 0.16), logo_t + 0.10)
    buf = buf[:int(total * SR)]
    # soft limiter + fade
    buf = np.tanh(buf * 1.25) * 0.92
    f = int(0.9 * SR)
    buf[-f:] *= np.linspace(1, 0, f)
    buf[:int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
    buf = buf / max(1e-6, np.abs(buf).max()) * 0.95
    st = np.stack([buf, buf], 1)
    with wave.open(os.path.join(OUT, 'mix.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    meta = dict(total=total, logo_at=logo_t, lines=tl)
    json.dump(meta, open(os.path.join(OUT, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    build()
