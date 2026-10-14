import os, sys, time, json
os.chdir(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '.')
import numpy as np
from PIL import Image
from multiprocessing import Pool

W, H, SS, FPS = 1280, 720, 2, 24
OUTD = 'work/frames'
os.makedirs(OUTD, exist_ok=True)
_M = None

def init():
    global _M
    import story
    _M = story.Movie(W, H, SS)

def job(i):
    t = i / FPS
    a = _M.frame(t)
    Image.fromarray(a).save('%s/%05d.png' % (OUTD, i), compress_level=1)
    return i

if __name__ == '__main__':
    import story
    N = int(story.TOTAL * FPS)
    todo = [i for i in range(N) if not os.path.exists('%s/%05d.png' % (OUTD, i))]
    print('frames', N, 'todo', len(todo), flush=True)
    t0 = time.time()
    with Pool(4, initializer=init) as p:
        for k, i in enumerate(p.imap_unordered(job, todo, chunksize=3)):
            if k % 24 == 0:
                el = time.time() - t0
                print('%d/%d  %.0fs elapsed, eta %.0fs' % (k, len(todo), el, el / max(1, k) * (len(todo) - k)), flush=True)
    print('done in %.0fs' % (time.time() - t0), flush=True)
