"""Local optimizer for spherical codes: reduce the maximal pairwise cosine of n unit
vectors in R^d, starting from a given configuration.  Target-descent method.

Given a target t below the current maximum m, minimize the penalty
    P_t(X) = sum_{i<j} max(0, <x_i,x_j> - t)^2,   x_i = y_i/|y_i|,
by L-BFGS.  If P_t reaches (numerically) zero the configuration has maximum at most t and
becomes the new incumbent, and the step m - t is doubled; otherwise the step is halved.
Stop when the step falls below `min_step` or the time budget is used up.  Only true
reductions of the maximum are ever accepted, so the output is never worse than the input.

Exact certification of the result is done separately by certify.py.
"""
import numpy as np, time
from scipy.optimize import minimize

def unit(X):
    return X / np.linalg.norm(X, axis=1, keepdims=True)

def maxcos(X):
    G = unit(X) @ unit(X).T
    np.fill_diagonal(G, -2.0)
    return G.max()

def penalty_and_grad(y, n, d, t):
    Y = y.reshape(n, d); nrm = np.linalg.norm(Y, axis=1, keepdims=True); X = Y / nrm
    G = X @ X.T
    np.fill_diagonal(G, -2.0)
    V = G - t
    V[V < 0] = 0.0
    P = 0.5 * (V * V).sum()          # each pair counted twice (symmetric), hence 0.5
    dX = 2.0 * (V @ X)               # d/dx_i of sum_{j} V_ij^2 = 2 sum_j V_ij x_j  (both orderings)
    dY = (dX - X * (dX * X).sum(axis=1, keepdims=True)) / nrm
    return P, dY.ravel()

def optimize(X0, time_budget=60.0, min_step=1e-13, maxiter=300, first_step=None):
    t0 = time.time()
    n, d = X0.shape
    X = unit(X0); best = X.copy(); m = maxcos(X); start = m
    step = first_step if first_step else max(1e-6, (1.0 - m) * 1e-3)
    y = X.ravel().copy()
    rounds = 0
    while step >= min_step and time.time() - t0 < time_budget:
        t = m - step
        res = minimize(penalty_and_grad, y, args=(n, d, t), jac=True, method='L-BFGS-B',
                       options=dict(maxiter=maxiter, maxcor=20, ftol=0.0, gtol=1e-16))
        Xc = unit(res.x.reshape(n, d)); v = maxcos(Xc); rounds += 1
        if v < m:                    # accepted: a true reduction of the maximum
            m, best, y = v, Xc.copy(), Xc.ravel().copy()
            step *= 2.0
        else:
            step *= 0.5
    return best, m, start, rounds, time.time() - t0

def load(path):
    return np.array([[float(s) for s in line.strip().split(',')] for line in open(path) if line.strip()])

if __name__ == "__main__":
    import sys
    X0 = load(sys.argv[1])
    B, v, s, r, secs = optimize(X0, time_budget=float(sys.argv[2]) if len(sys.argv) > 2 else 60.0)
    print("start %.15f  best %.15f  gain %.3e  rounds %d  %.1fs" % (s, v, s - v, r, secs))


# ---- loose smooth pass (log-sum-exp), useful for escaping a basin before target descent ----
def lse_energy_and_grad(y, n, d, p, iu):
    Y = y.reshape(n, d); nrm = np.linalg.norm(Y, axis=1, keepdims=True); X = Y / nrm
    G = X @ X.T; g = G[iu]; m = g.max()
    w = np.exp(p * (g - m)); S = w.sum(); E = m + np.log(S) / p; w /= S
    dX = np.zeros_like(X)
    np.add.at(dX, iu[0], w[:, None] * X[iu[1]]); np.add.at(dX, iu[1], w[:, None] * X[iu[0]])
    dY = (dX - X * (dX * X).sum(axis=1, keepdims=True)) / nrm
    return E, dY.ravel()

def lse_pass(X0, schedule=(100, 300, 1000, 3000, 10000, 30000), maxiter=200, time_budget=20.0):
    t0 = time.time(); n, d = X0.shape; iu = np.triu_indices(n, 1)
    X = unit(X0); best = X.copy(); best_val = maxcos(X); y = X.ravel().copy()
    for p in schedule:
        if time.time() - t0 > time_budget: break
        res = minimize(lse_energy_and_grad, y, args=(n, d, p, iu), jac=True, method='L-BFGS-B',
                       options=dict(maxiter=maxiter, maxcor=20, ftol=1e-15, gtol=1e-12))
        y = res.x; Xc = unit(y.reshape(n, d)); v = maxcos(Xc)
        if v < best_val: best_val, best = v, Xc.copy()
    return best, best_val

def hybrid(X0, budget_td=30.0, budget_lse=15.0, budget_td2=15.0):
    """target descent from X0; separately an LSE pass then target descent; return the better."""
    B1, v1, s, r1, t1 = optimize(X0, time_budget=budget_td)
    L, vl = lse_pass(X0, time_budget=budget_lse)
    B2, v2, _, r2, t2 = optimize(L, time_budget=budget_td2)
    if v2 < v1: return B2, v2, s, 'lse+td', r1 + r2
    return B1, v1, s, 'td', r1 + r2
