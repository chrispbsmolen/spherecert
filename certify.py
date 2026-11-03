"""Exact certifier for spherical-codes.org entries.

For an entry (dim d, n points, stated cosine c printed with 12 decimals), the
coordinate file gives n vectors with decimal entries.  The claim certified is

    max over pairs i<j of  <x_i, x_j> / (|x_i| |x_j|)  <=  c,

i.e. the normalized points have minimal angle whose cosine is at most the stated
value.  The table rounds cosines UP to 12 decimals (3,9 is listed as
0.333333333334), so the stated value is a ceiling and this is the right test.
Everything is done in integer arithmetic on the printed decimals, so a PASS is a
proof about the published file.  A floating point screen with a rigorous forward
error bound is used only to decide which pairs need the exact check.

Verdicts
  PASS           all pairs satisfy the inequality and the maximum exceeds c - 1e-12 (c is the correct ceiling)
  PASS_ROUNDING  some pair exceeds c, but by at most 1e-14, and c is an ideal value: a short exact
                 decimal (at most 6 decimals, such as 0.25 or 0.375) or a root of the listed minimal
                 polynomial.  The file is then a double precision approximation of the ideal configuration
                 (coordinates printed to 16 or 17 significant digits perturb a cosine by at most about
                 1e-15 in 32 dimensions)
  CEILING_LOW    some pair exceeds c by at most 1e-14 and c is not an ideal value: the stated value is
                 one unit too low in the 12th decimal (the correct ceiling of the file's maximum is c + 1e-12)
  BETTER         all pairs satisfy it and the exact maximum is at most c - 1e-12 (table could state a smaller value)
  FAIL           some pair exceeds c + 1e-14; the exact maximum is reported
  BADFILE        wrong number of points or coordinates, fewer than 2 points, non-numeric data, a zero
                 vector, a coordinate of size 1e300 or more, or a row whose largest coordinate is below
                 1e-290 (where the floating point screen could not be trusted)

Also reported: exact maximum cosine (as a 15-digit decimal with the exact
rational available), number of pairs at the maximum (within 1e-9 of it in
floating point) and number of points with no such contact ("rattlers", informal).
Minimal polynomial check: if a polynomial p is listed, verify that p changes sign
on [c - 1e-12, c] (exact rational evaluation), which proves a root there.
"""
import sys, os, json, math
from fractions import Fraction
import numpy as np

U = 2.0 ** -53  # unit roundoff, double precision

def parse_coords(path):
    pts = []
    for line in open(path):
        line = line.strip()
        if not line: continue
        pts.append(line.split(','))
    return pts

def to_int_matrix(pts):
    """Scale all decimal strings (plain or exponent notation) to integers with a common
    power of ten, exactly.  Returns (ints as list of lists, K)."""
    from decimal import Decimal
    D = [[Decimal(s.strip()) for s in row] for row in pts]
    K = 0
    for row in D:
        for d in row:
            e = d.as_tuple().exponent
            if e < 0: K = max(K, -e)
    S = 10 ** K
    M = []
    for row in D:
        out = []
        for d in row:
            f = Fraction(d) * S            # exact: Fraction(Decimal) is exact, and d * 10^K is an integer
            if f.denominator != 1: raise ValueError('coordinate %s not exactly representable at 10^-%d' % (d, K))
            out.append(f.numerator)
        M.append(out)
    return M, K

def cos_cmp(ip, nx, ny, num, den):
    """Exact sign of  ip / sqrt(nx*ny) - num/den  for integers, nx, ny > 0, den > 0, any signs."""
    if ip == 0:
        return (0 > num) - (0 < num)          # cosine 0 against num/den
    if ip > 0 and num <= 0:
        return 1
    if ip < 0 and num >= 0:
        return -1
    lhs = ip * ip * den * den
    rhs = num * num * nx * ny
    d = (lhs > rhs) - (lhs < rhs)
    return d if ip > 0 else -d        # both negative: the larger magnitude is the smaller cosine

def cos_pair_cmp(a, b):
    """Exact sign of cos_a - cos_b, each given as (ip, nx, ny)."""
    ia, xa, ya = a[:3]; ib, xb, yb = b[:3]
    if ia >= 0 and ib <= 0: return 0 if (ia == 0 and ib == 0) else 1
    if ia <= 0 and ib >= 0: return -1
    lhs = ia * ia * xb * yb; rhs = ib * ib * xa * ya
    d = (lhs > rhs) - (lhs < rhs)
    return d if ia > 0 else -d

def exact_cos_sq_cmp(xi, xj, num, den):
    """Exact sign of  <xi,xj>/(|xi||xj|) - num/den  for integer vectors, any signs."""
    ip = sum(a * b for a, b in zip(xi, xj))
    return cos_cmp(ip, sum(a * a for a in xi), sum(b * b for b in xj), num, den)

def is_ideal_value(cstr, poly):
    """An ideal value is a listed polynomial root or a short exact decimal (at most 6 decimals)."""
    if poly: return True
    frac = cstr.strip().lstrip('-').split('.')[1] if '.' in cstr else ''
    return len(frac.rstrip('0')) <= 6

def exact_cos(xi, xj):
    ip = sum(a * b for a, b in zip(xi, xj))
    nx = sum(a * a for a in xi); ny = sum(b * b for b in xj)
    return ip, nx, ny  # cosine = ip / sqrt(nx*ny)

def cos_str(ip, nx, ny):
    """The cosine ip / sqrt(nx*ny) to 15 decimals, from exact arithmetic (50 digit Decimal)."""
    from decimal import Decimal, localcontext, ROUND_HALF_EVEN
    with localcontext() as ctx:
        ctx.prec = 50
        v = Decimal(ip) / (Decimal(nx) * Decimal(ny)).sqrt()
        return str(v.quantize(Decimal('1e-15'), rounding=ROUND_HALF_EVEN))

def cos_from_parts(ip, nx, ny):
    # exact rational square, converted to float only at the end (big integers safe)
    if not (nx and ny): return float('nan')
    v = math.sqrt(float(Fraction(ip * ip, nx * ny)))
    return v if ip >= 0 else -v

def certify(dim, n, cstr, path, poly=None):
    res = dict(dim=dim, n=n, stated=cstr)
    try:
        pts = parse_coords(path)
    except Exception as ex:
        res['verdict'] = 'BADFILE'; res['note'] = 'unreadable: ' + repr(ex); return res
    if len(pts) != n or any(len(r) != dim for r in pts):
        res['verdict'] = 'BADFILE'; res['note'] = 'shape %dx%s, expected %dx%d' % (len(pts), {len(r) for r in pts}, n, dim); return res
    if n < 2:
        res['verdict'] = 'BADFILE'; res['note'] = 'fewer than 2 points'; return res
    try:
        M, K = to_int_matrix(pts)
    except Exception as ex:
        res['verdict'] = 'BADFILE'; res['note'] = repr(ex); return res
    res['decimals'] = K
    # range guard for the floating point screen: every coordinate must convert to a finite double
    # (|x| < 1e300), and every row's largest coordinate must be at least 1e-290 so that scaling the
    # row by it is exact enough.  Tiny entries next to normal ones are harmless after scaling.
    hi = 10 ** (300 + K); lo = Fraction(10 ** K, 10 ** 290)
    for row in M:
        m = max(abs(v) for v in row)
        if m >= hi or (m != 0 and m < lo):
            res['verdict'] = 'BADFILE'; res['note'] = 'coordinate magnitude outside the floating point range of the screen'; return res
    # floating screen
    X = np.array([[float(s) for s in r] for r in pts], dtype=np.float64)
    if any(all(v == 0 for v in row) for row in M):
        res['verdict'] = 'BADFILE'; res['note'] = 'zero vector'; return res
    # scale each row by its largest entry before squaring so the norm cannot overflow or underflow
    Xs = X / np.max(np.abs(X), axis=1)[:, None]
    norms = np.sqrt((Xs * Xs).sum(axis=1))
    Xn = Xs / norms[:, None]
    if not np.isfinite(Xn).all():
        res['verdict'] = 'BADFILE'; res['note'] = 'non-finite value in the floating point screen'; return res
    # rigorous bound on |computed cosine - true cosine| for normalized float computation:
    # inner product of d terms: relative error <= gamma_d, normalization adds a few ulps; use a safe 20*d*U + 1e-15.
    bound = 20 * dim * U + 1e-15
    cstated = Fraction(cstr)  # exact decimal
    thr = cstated
    thr_f = float(thr)
    # Exact-float path: integer coordinates small enough that every inner product and
    # norm is computed exactly in double precision (no rounding at all).
    maxabs = max(abs(v) for r in M for v in r)
    if K == 0 and dim * maxabs * maxabs < 2 ** 52:
        return certify_integer_exact(res, M, X, dim, n, cstated, poly)
    # blocked max search to limit memory
    B = 512 if n > 4096 else n
    gmax = -2.0; cand = []
    for i0 in range(0, n, B):
        G = Xn[i0:i0 + B] @ Xn.T
        for a in range(G.shape[0]):
            G[a, i0 + a] = -2.0  # exclude diagonal
            if i0 + a + 1 < n: G[a, :i0 + a + 1] = -2.0  # keep i<j only
        bm = G.max()
        if bm > gmax: gmax = bm
        # candidates: within 2*bound of the screening threshold or of the current max are collected later; first pass collects near-threshold
        rows, cols = np.nonzero(G > thr_f - 2 * bound)
        cand.extend(zip((rows + i0).tolist(), cols.tolist()))
    # pairs possibly at the maximum (for exact max and contact counts)
    near_max = []
    for i0 in range(0, n, B):
        G = Xn[i0:i0 + B] @ Xn.T
        for a in range(G.shape[0]):
            G[a, :i0 + a + 1] = -2.0
        rows, cols = np.nonzero(G > gmax - 2 * bound - 1e-9)
        near_max.extend(zip((rows + i0).tolist(), cols.tolist()))
    # exact check of threshold candidates: a pair "violates" only beyond the file-precision tolerance
    FILE_TOL = Fraction(1, 10 ** 14)
    thr_tol = thr + FILE_TOL
    viol = 0; over_exact = 0
    for i, j in cand:
        if exact_cos_sq_cmp(M[i], M[j], thr_tol.numerator, thr_tol.denominator) > 0:
            viol += 1
        elif exact_cos_sq_cmp(M[i], M[j], thr.numerator, thr.denominator) > 0:
            over_exact += 1
    # exact maximum over near_max pairs (compare exactly by cross multiplication)
    best = None
    for i, j in near_max:
        ip, nx, ny = exact_cos(M[i], M[j])
        if best is None or cos_pair_cmp((ip, nx, ny), best) > 0:
            best = (ip, nx, ny, i, j)
    ip, nx, ny, bi, bj = best
    exact_max = cos_from_parts(ip, nx, ny)
    res['exact_max_cos'] = cos_str(ip, nx, ny)
    res['max_pair'] = [bi, bj]
    res['stated_minus_actual_e12'] = round((float(cstated) - exact_max) * 1e12, 3)
    # contacts: pairs within 1e-9 of the max (floating)
    contacts = [(i, j) for i, j in near_max if Xn[i] @ Xn[j] > exact_max - 1e-9]
    res['contact_pairs'] = len(contacts)
    touched = set(); [touched.update(p) for p in contacts]
    res['rattlers_1e-9'] = n - len(touched)
    if viol:
        res['verdict'] = 'FAIL'; res['violating_pairs'] = viol
    elif over_exact:
        res['verdict'] = 'PASS_ROUNDING' if is_ideal_value(cstr, poly) else 'CEILING_LOW'
        res['pairs_over_by_rounding'] = over_exact
    else:
        lower = cstated - Fraction(1, 10 ** 12)
        # BETTER: the exact maximum (attained by the best pair) is at most c - 1e-12
        res['verdict'] = 'BETTER' if cos_cmp(ip, nx, ny, lower.numerator, lower.denominator) <= 0 else 'PASS'
    if poly:
        res['poly_check'] = check_poly(poly, cstated)
    return res

def certify_integer_exact(res, M, X, dim, n, cstated, poly):
    """All coordinates are small integers: G = X X^T and the squared norms are exact in float64.
    cos_ij <= c  <=>  ip_ij <= 0 or ip_ij^2 <= c^2 nx ny.  With c = p/q this is q^2 ip^2 <= p^2 nx ny,
    evaluated here in float64 only when the products stay below 2^53, otherwise in Python ints on the
    (few) pairs at the float maximum."""
    nx = (X * X).sum(axis=1)  # exact
    p, q = cstated.numerator, cstated.denominator
    B = 256 if n > 4096 else n
    gmax = -2.0; maxcount = 0; row_has_contact = np.zeros(n, dtype=bool)
    viol = 0; best = None; exact_ok = (q * q * (dim * (np.abs(X).max() ** 2)) ** 2 < 2 ** 52) and (p * p * nx.max() ** 2 < 2 ** 52)
    for i0 in range(0, n, B):
        G = X[i0:i0 + B] @ X.T  # exact integers in float64
        for a in range(G.shape[0]):
            G[a, :i0 + a + 1] = -np.inf
        C = G / np.sqrt(np.outer(nx[i0:i0 + B], nx))
        bm = C.max()
        if bm > gmax + 1e-9: gmax = bm; maxcount = 0; row_has_contact[:] = False
        hit = C > gmax - 1e-9
        maxcount += int(hit.sum())
        rows, cols = np.nonzero(hit); row_has_contact[rows + i0] = True; row_has_contact[cols] = True
        # exact threshold test on this block
        if exact_ok:
            lhs = (q * q) * G * G; rhs = (p * p) * np.outer(nx[i0:i0 + B], nx)
            valid = np.isfinite(G)
            if p >= 0:   # cos > c  <=>  ip > 0 and q^2 ip^2 > p^2 nx ny
                v = np.nonzero(valid & (G > 0) & (lhs > rhs))
            else:        # c < 0:  cos > c  <=>  ip >= 0, or ip < 0 and q^2 ip^2 < p^2 nx ny
                v = np.nonzero(valid & ((G >= 0) | (lhs < rhs)))
            viol += len(v[0])
        else:
            rows2, cols2 = np.nonzero(C > float(cstated) - 1e-9)
            for a, j in zip(rows2.tolist(), cols2.tolist()):
                if exact_cos_sq_cmp(M[i0 + a], M[j], p, q) > 0: viol += 1
        # exact max among this block's near-maximal pairs: every distinct (ip, nx_i, nx_j) value
        # within 1e-12 of the block maximum is compared exactly (lattice files have very many ties
        # but few distinct values, so this stays cheap)
        rr, cc = np.nonzero(C >= bm - 1e-12)
        seen = {}
        for a, j in zip(rr.tolist(), cc.tolist()):
            key = (int(G[a, j]), int(nx[i0 + a]), int(nx[j]))
            if key not in seen: seen[key] = (i0 + a, j)
        for (ipf, nxf, nyf), (i, j) in seen.items():
            ip, nxi, nyj = exact_cos(M[i], M[j])
            if best is None or cos_pair_cmp((ip, nxi, nyj), best) > 0:
                best = (ip, nxi, nyj, i, j)
    ip, nxi, nyj, bi, bj = best
    exact_max = cos_from_parts(ip, nxi, nyj)
    res['exact_max_cos'] = cos_str(ip, nxi, nyj); res['max_pair'] = [bi, bj]
    res['stated_minus_actual_e12'] = round((float(cstated) - exact_max) * 1e12, 3)
    res['contact_pairs'] = maxcount; res['rattlers_1e-9'] = int((~row_has_contact).sum()); res['path'] = 'integer_exact'
    if viol:
        res['verdict'] = 'FAIL'; res['violating_pairs'] = int(viol)
    else:
        lower = cstated - Fraction(1, 10 ** 12)
        res['verdict'] = 'BETTER' if cos_cmp(ip, nxi, nyj, lower.numerator, lower.denominator) <= 0 else 'PASS'
    if poly: res['poly_check'] = check_poly(poly, cstated)
    return res

def parse_poly(s):
    """'3*x^3-9*x^2-3*x+1' -> dict degree->int coefficient"""
    s = s.replace(' ', '').replace('-', '+-')
    coeffs = {}
    for term in s.split('+'):
        if not term: continue
        if 'x' in term:
            c, _, p = term.partition('x')
            c = c.rstrip('*'); c = -1 if c == '-' else (1 if c in ('', '+') else int(c))
            p = int(p[1:]) if p.startswith('^') else 1
        else:
            c, p = int(term), 0
        coeffs[p] = coeffs.get(p, 0) + c
    return coeffs

def peval(coeffs, x):
    return sum(c * x ** p for p, c in coeffs.items())

def check_poly(poly, c):
    try:
        P = parse_poly(poly)
    except Exception as ex:
        return 'unparsed: ' + repr(ex)
    lo, hi = c - Fraction(1, 10 ** 12), c
    a, b = peval(P, lo), peval(P, hi)
    if a == 0 or b == 0 or (a < 0) != (b < 0):
        return 'root_in_interval'
    # no sign change: maybe a double root or wider rounding; test relative smallness
    d = {p - 1: c0 * p for p, c0 in P.items() if p > 0}
    pc, dpc = peval(P, c), peval(d, c)
    if dpc != 0 and abs(pc) <= abs(dpc) * Fraction(1, 10 ** 11):
        return 'near_root_no_sign_change'
    return 'NO_ROOT_NEAR_STATED'

if __name__ == "__main__":
    dim, n, cstr, path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
    poly = sys.argv[5] if len(sys.argv) > 5 else None
    print(json.dumps(certify(dim, n, cstr, path, poly)))
