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

def oracle(path, cstr, ideal=False):
    """ideal: True when a minimal polynomial is listed for the entry (same convention as certify.py)."""
    P = load(path); n = len(P); c = Fraction(cstr)
    tol = c + Fraction(1, 10 ** 14); low = c - Fraction(1, 10 ** 12)
    pairs = 0; over_tol = 0; over_exact = 0; all_below_low = True
    best = None
    for i in range(n):
        for j in range(i + 1, n):
            pairs += 1
            if not cos_leq(P[i], P[j], tol): over_tol += 1
            elif not cos_leq(P[i], P[j], c): over_exact += 1
            if not cos_leq(P[i], P[j], low): all_below_low = False
            # exact maximum tracking (compare cos_ij with best)
            ip = sum(a * b for a, b in zip(P[i], P[j])); nx = sum(a * a for a in P[i]); ny = sum(b * b for b in P[j])
            if best is None: best = (ip, nx, ny)
            else:
                bip, bnx, bny = best
                if (ip > 0 and bip > 0 and ip * ip * bnx * bny > bip * bip * nx * ny) or (ip > 0 >= bip) or (ip <= 0 and bip <= 0 and ip * ip * bnx * bny < bip * bip * nx * ny):
                    best = (ip, nx, ny)
    if over_tol: v = 'FAIL'
    elif over_exact:
        frac = cstr.strip().lstrip('-').split('.')[1] if '.' in cstr else ''
        v = 'PASS_ROUNDING' if (ideal or len(frac.rstrip('0')) <= 6) else 'CEILING_LOW'
    elif all_below_low: v = 'BETTER'
    else: v = 'PASS'
    ip, nx, ny = best
    # exact rational ip/sqrt(nx ny): ip and nx, ny are Fractions; format at 15 decimals via mpmath-free Decimal arithmetic
    from decimal import Decimal, localcontext, ROUND_HALF_EVEN
    with localcontext() as ctx:
        ctx.prec = 60
        num = Decimal(ip.numerator) / Decimal(ip.denominator)
        den = (Decimal(nx.numerator) / Decimal(nx.denominator) * Decimal(ny.numerator) / Decimal(ny.denominator)).sqrt()
        s = str((num / den).quantize(Decimal('1e-15'), rounding=ROUND_HALF_EVEN))
    return dict(verdict=v, pairs=pairs, exact_max_cos=s, max_parts=(ip, nx, ny))

if __name__ == "__main__":
    r = oracle(sys.argv[1], sys.argv[2], ideal=len(sys.argv) > 3)
    r.pop('max_parts')
    print(json.dumps(r))
