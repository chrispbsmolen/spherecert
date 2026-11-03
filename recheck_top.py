"""Independent recheck of the largest gains, sharing no code with certify.py: for each of the K
entries with the largest gain in results/improvements_ledger.csv, read release/improved/<dim>_<n>.txt,
check the shape and that the normalized points are distinct, find the 12 largest pairs in floating
point, and recompute those pairs at 40 significant digits with mpmath.  The recomputed maximum must
agree with the ledger's new value to 1e-12, be at most it, and be below the table value.
Writes results/recheck_top.txt.  Usage: python3 recheck_top.py [K]   (default 40)"""
import csv, os, sys
import numpy as np, mpmath
mpmath.mp.dps = 40
W = os.path.dirname(os.path.abspath(__file__))
K = int(sys.argv[1]) if len(sys.argv) > 1 else 40
L = sorted(csv.DictReader(open(os.path.join(W, 'results', 'improvements_ledger.csv'))), key=lambda r: -int(r['gain_units_1e12']))[:K]
out = []; bad = 0
for r in L:
    d, n = int(r['dim']), int(r['n'])
    lines = [l for l in open(os.path.join(W, 'release', r['file'])) if l.strip()]
    X = np.array([[float(t) for t in l.split(',')] for l in lines])
    shape = X.shape == (n, d)
    Xn = X / np.linalg.norm(X, axis=1)[:, None]
    distinct = len({tuple(np.round(v, 12)) for v in Xn}) == n
    G = Xn @ Xn.T; np.fill_diagonal(G, -2)
    top = np.argsort(G, axis=None)[::-1][:24]
    def mpcos(a, b):
        ta = [mpmath.mpf(t) for t in lines[a].split(',')]; tb = [mpmath.mpf(t) for t in lines[b].split(',')]
        return mpmath.fsum(x * y for x, y in zip(ta, tb)) / mpmath.sqrt(mpmath.fsum(x * x for x in ta) * mpmath.fsum(y * y for y in tb))
    mx = max(mpcos(*np.unravel_index(o, G.shape)) for o in top)
    ok = shape and distinct and abs(mx - mpmath.mpf(r['new_cosine'])) < mpmath.mpf('1e-12') and mx <= mpmath.mpf(r['new_cosine']) and mx < mpmath.mpf(r['table_cosine'])
    bad += not ok
    out.append('%3d %5d  shape %s  distinct %s  max %s  certified %s  table %s  %s' % (d, n, shape, distinct, mpmath.nstr(mx, 15), r['new_cosine'], r['table_cosine'], 'ok' if ok else 'PROBLEM'))
out.append('problems: %d of %d' % (bad, len(L)))
open(os.path.join(W, 'results', 'recheck_top.txt'), 'w').write('\n'.join(out) + '\n'); print('\n'.join(out[-3:]))
sys.exit(1 if bad else 0)
