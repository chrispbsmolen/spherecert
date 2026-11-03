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
  PASS_ROUNDING  some pair exceeds c, but by at most 1e-14: the table states the exact value of an
                 ideal configuration and the file is its double precision approximation (coordinates
                 printed to 16 or 17 significant digits perturb a cosine by at most about 1e-15 in 32 dimensions)
  BETTER         all pairs satisfy it and the exact maximum is at most c - 1e-12 (table could state a smaller value)
  FAIL           some pair exceeds c + 1e-14; the exact maximum is reported
  BADFILE   wrong number of points or coordinates, non-numeric data, or a zero vector

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
    M = [[int(d.scaleb(K)) for d in row] for row in D]
    for row, drow in zip(M, D):
        for v, d in zip(row, drow):
            assert Decimal(v).scaleb(-K) == d
    return M, K

def exact_cos_sq_cmp(xi, xj, num, den):
    """Return sign of  <xi,xj>/(|xi||xj|) - num/den  exactly (num/den >= 0 assumed). """
    ip = sum(a * b for a, b in zip(xi, xj))
    if ip <= 0:
        return -1 if num > 0 else (0 if ip == 0 else -1)
    lhs = ip * ip * den * den
    rhs = num * num * sum(a * a for a in xi) * sum(b * b for b in xj)
    return (lhs > rhs) - (lhs < rhs)

def exact_cos(xi, xj):
    ip = sum(a * b for a, b in zip(xi, xj))
    nx = sum(a * a for a in xi); ny = sum(b * b for b in xj)
    return ip, nx, ny  # cosine = ip / sqrt(nx*ny)

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
    try:
        M, K = to_int_matrix(pts)
    except Exception as ex:
        res['verdict'] = 'BADFILE'; res['note'] = repr(ex); return res
    res['decimals'] = K
    # floating screen
    X = np.array([[float(s) for s in r] for r in pts], dtype=np.float64)
    norms = np.sqrt((X * X).sum(axis=1))
    if np.any(norms == 0):
        res['verdict'] = 'BADFILE'; res['note'] = 'zero vector'; return res
    Xn = X / norms[:, None]
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
        if best is None:
            best = (ip, nx, ny, i, j)
        else:
            bip, bnx, bny, _, _ = best
            # compare ip/sqrt(nx ny) vs bip/sqrt(bnx bny)
            if ip > 0 and bip > 0:
                if ip * ip * bnx * bny > bip * bip * nx * ny: best = (ip, nx, ny, i, j)
            elif ip > bip:  # sign-based cases
                best = (ip, nx, ny, i, j)
    ip, nx, ny, bi, bj = best
    exact_max = cos_from_parts(ip, nx, ny)
    res['exact_max_cos'] = '%.15f' % exact_max
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
        res['verdict'] = 'PASS_ROUNDING'; res['pairs_over_by_rounding'] = over_exact
    else:
        lower = cstated - Fraction(1, 10 ** 12)
        # exact: is max < lower ?  i.e. all near_max pairs below lower
        below = all(exact_cos_sq_cmp(M[i], M[j], lower.numerator, lower.denominator) <= 0 for i, j in near_max) if lower > 0 else False
        res['verdict'] = 'BETTER' if below else 'PASS'
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
    viol = 0; best = None; exact_ok = (q * q * (dim * (X.max() ** 2)) ** 2 < 2 ** 52) and (p * p * nx.max() ** 2 < 2 ** 52)
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
            v = np.nonzero((G > 0) & (lhs > rhs)); viol += len(v[0])
        else:
            rows2, cols2 = np.nonzero(C > float(cstated) - 1e-9)
            for a, j in zip(rows2.tolist(), cols2.tolist()):
                if exact_cos_sq_cmp(M[i0 + a], M[j], p, q) > 0: viol += 1
        # exact max among this block's maximal pairs
        rr, cc = np.nonzero(C >= bm - 1e-12)
        for a, j in zip(rr[:50].tolist(), cc[:50].tolist()):
            ip, nxi, nyj = exact_cos(M[i0 + a], M[j])
            if best is None or (ip > 0 and best[0] > 0 and ip * ip * best[1] * best[2] > best[0] * best[0] * nxi * nyj) or (ip > best[0] and not (ip > 0 and best[0] > 0)):
                best = (ip, nxi, nyj, i0 + a, j)
    ip, nxi, nyj, bi, bj = best
    exact_max = cos_from_parts(ip, nxi, nyj)
    res['exact_max_cos'] = '%.15f' % exact_max; res['max_pair'] = [bi, bj]
    res['stated_minus_actual_e12'] = round((float(cstated) - exact_max) * 1e12, 3)
    res['contact_pairs'] = maxcount; res['rattlers_1e-9'] = int((~row_has_contact).sum()); res['path'] = 'integer_exact'
    if viol:
        res['verdict'] = 'FAIL'; res['violating_pairs'] = int(viol)
    else:
        lower = cstated - Fraction(1, 10 ** 12)
        res['verdict'] = 'BETTER' if (lower > 0 and exact_cos_sq_cmp(M[bi], M[bj], lower.numerator, lower.denominator) <= 0) else 'PASS'
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
