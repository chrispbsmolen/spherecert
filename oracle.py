"""Slow oracle sharing no logic with certify.py: every pair, pure Fraction arithmetic,
no numpy, no screening.  Returns the exact maximum cosine as a Fraction of a square root
comparison, the verdict under the same conventions, and the number of pairs checked.
Intended for small entries (n up to a few hundred) as a differential test."""
import sys, json
from fractions import Fraction
from decimal import Decimal

def load(path):
    return [[Fraction(Decimal(s.strip())) for s in line.strip().split(',')] for line in open(path) if line.strip()]

def cos_leq(x, y, c):
    """exact test  <x,y>/(|x||y|) <= c  for rationals x, y, c"""
    ip = sum(a * b for a, b in zip(x, y))
    if ip <= 0:
        return c >= 0 or ip * ip >= c * c * sum(a * a for a in x) * sum(b * b for b in y)
    if c < 0:
        return False
    return ip * ip <= c * c * sum(a * a for a in x) * sum(b * b for b in y)

def oracle(path, cstr):
    P = load(path); n = len(P); c = Fraction(cstr)
    tol = c + Fraction(1, 10 ** 14); low = c - Fraction(1, 10 ** 12)
    pairs = 0; over_tol = 0; over_exact = 0; all_below_low = True
    best = None
    for i in range(n):
        for j in range(i + 1, n):
            pairs += 1
            if not cos_leq(P[i], P[j], tol): over_tol += 1
            elif not cos_leq(P[i], P[j], c): over_exact += 1
            if low > 0 and not cos_leq(P[i], P[j], low): all_below_low = False
            # exact maximum tracking (compare cos_ij with best)
            ip = sum(a * b for a, b in zip(P[i], P[j])); nx = sum(a * a for a in P[i]); ny = sum(b * b for b in P[j])
            if best is None: best = (ip, nx, ny)
            else:
                bip, bnx, bny = best
                if (ip > 0 and bip > 0 and ip * ip * bnx * bny > bip * bip * nx * ny) or (ip > 0 >= bip) or (ip <= 0 and bip <= 0 and ip * ip * bnx * bny < bip * bip * nx * ny):
                    best = (ip, nx, ny)
    if over_tol: v = 'FAIL'
    elif over_exact: v = 'PASS_ROUNDING'
    elif all_below_low and low > 0: v = 'BETTER'
    else: v = 'PASS'
    ip, nx, ny = best
    return dict(verdict=v, pairs=pairs, exact_max_cos='%.15f' % (float(ip) / (float(nx) * float(ny)) ** 0.5))

if __name__ == "__main__":
    print(json.dumps(oracle(sys.argv[1], sys.argv[2])))
