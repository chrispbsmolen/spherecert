"""Delsarte linear programming bound for spherical codes: the maximum number of points on
S^{d-1} with pairwise cosine at most s.  Standard LP: find f(t) = sum_k f_k G_k(t) (Gegenbauer
polynomials for S^{d-1}, normalized G_k(1) = 1) with f_0 > 0, f_k >= 0, and f(t) <= 0 on
[-1, s]; then N <= f(1)/f_0.  Discretize t on a fine grid plus the endpoints; the result is a
valid bound up to the discretization (we add a small safety margin by checking f on a finer grid)."""
import numpy as np
from scipy.optimize import linprog
from scipy.special import gegenbauer, eval_gegenbauer

def lp_bound(d, s, K=40, grid=4000):
    alpha = (d - 2) / 2.0
    ts = np.concatenate([np.linspace(-1, s, grid), [s]])
    # G_k(t) normalized so G_k(1) = 1
    def G(k, t): return eval_gegenbauer(k, alpha, t) / eval_gegenbauer(k, alpha, 1.0)
    A = np.array([[G(k, t) for k in range(K + 1)] for t in ts])   # f(t) <= 0  ->  A f <= 0
    # normalize f_0 = 1, minimize f(1) = sum f_k
    c = np.ones(K + 1)
    bounds = [(1, 1)] + [(0, None)] * K
    res = linprog(c, A_ub=A, b_ub=np.zeros(len(ts)), bounds=bounds, method='highs')
    if not res.success: return None
    f = res.x
    # verify on a finer grid
    tf = np.linspace(-1, s, 20 * grid)
    vals = np.array([sum(f[k] * G(k, t) for k in range(K + 1)) for t in tf[::7]])
    return res.fun, vals.max()

if __name__ == "__main__":
    import sys
    for d, s in [(24, 0.25), (23, 0.25), (16, 1/3), (16, 0.25), (8, 1/3), (22, 3/11), (7, 3/7), (16, 3/7)]:
        b = lp_bound(d, s)
        print("d=%2d s=%.6f  LP bound N <= %.2f   (max f on [-1,s] = %.1e, should be <= ~0)" % (d, s, b[0], b[1]))
