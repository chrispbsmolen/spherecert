"""Tests for certify.py.  Run from the repository root:  python3 selftest.py

Part A needs nothing but this repository.  It builds small configurations in a temporary
folder and checks that certify() and the independent slow oracle (oracle.py, pure rational
arithmetic, every pair, no shared code) give the expected verdict and the same exact maximum.
The cases include the ways a checker like this can be fooled: excesses just above the stated
value, ideal versus non-ideal stated values, negative cosines, duplicate points, exponent
notation, very long decimals, coordinates near the edges of the floating point range, and
integer (lattice type) files.

Part B runs only if the table's coordinate files have been downloaded to data/coords/
(python3 parse_table.py, then python3 download_coords.py, about 2 GB).  It compares certify()
with the oracle on a fixed random sample of 60 entries with n <= 120, and runs three
perturbation tests.

Exit status 0 only if every test passes."""
import json, os, sys, random, tempfile
from fractions import Fraction
from decimal import Decimal
sys.path.insert(0, '.')
from certify import certify
from oracle import oracle

TMP = tempfile.mkdtemp(prefix='spherecert_selftest_')
failures = 0

def write(name, rows):
    p = os.path.join(TMP, name)
    open(p, 'w').write('\n'.join(','.join(str(v) for v in r) for r in rows) + '\n')
    return p

def check(label, dim, n, c, rows, expect, poly=None, oracle_too=True):
    global failures
    p = write(label + '.txt', rows)
    a = certify(dim, n, c, p, poly)
    msg = '%-34s certify %-13s' % (label, a['verdict'])
    ok = a['verdict'] == expect
    if oracle_too and a['verdict'] != 'BADFILE':
        b = oracle(p, c, ideal=poly is not None)
        msg += ' oracle %-13s' % b['verdict']
        ok = ok and b['verdict'] == expect and b['exact_max_cos'] == a['exact_max_cos']
        if b['exact_max_cos'] != a.get('exact_max_cos'): msg += ' max %s vs %s' % (a.get('exact_max_cos'), b['exact_max_cos'])
    print(msg, 'expected', expect, 'ok' if ok else 'PROBLEM')
    if not ok: failures += 1

print('Part A: constructed cases')
# regular simplex in 3 dimensions written in 4 coordinates: cosine exactly -1/3
simplex = [[3, -1, -1, -1], [-1, 3, -1, -1], [-1, -1, 3, -1], [-1, -1, -1, 3]]
check('simplex_exact', 4, 4, '-0.333333333333', simplex, 'PASS')          # ceiling of -1/3 at 12 decimals
check('simplex_claim_too_low', 4, 4, '-0.333333333334', simplex, 'FAIL')  # -1/3 > -0.333333333334
check('simplex_claim_high', 4, 4, '-0.333333333331', simplex, 'BETTER')
# negative stated cosine, the reviewer's case: true maximum -0.707..., claim -0.9 must fail
check('negative_claim', 2, 2, '-0.9', [[1, 0], [-1, 1]], 'FAIL')
check('negative_claim_ok', 2, 2, '-0.707106781186', [[1, 0], [-1, 1]], 'PASS')
# cross polytope in 3 dimensions: cosine 0 (integer path)
cross = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]]
check('cross_polytope', 3, 6, '0.0', cross, 'PASS')
check('cross_claim_negative', 3, 6, '-0.000000000001', cross, 'FAIL')
# decimal file: two points at cosine c0, then claims around it
c0 = Fraction(123456789012, 10 ** 12)
s0 = (1 - c0 * c0)                       # second point (c0, sqrt(1 - c0^2)) written to 40 digits
from decimal import getcontext
getcontext().prec = 60
y = (Decimal(s0.numerator) / Decimal(s0.denominator)).sqrt()
pair = [['1', '0'], [str(Decimal(c0.numerator) / Decimal(c0.denominator)), '%.40f' % y]]
check('long_decimals_exact', 2, 2, '0.123456789013', pair, 'PASS')  # 40-digit y makes the cosine just above c0 or just below; ceiling is ...013 or ...012
# exceed a non-ideal 12-decimal value by about 5e-15: CEILING_LOW, never PASS_ROUNDING
cc = Fraction(123456789012, 10 ** 12) + Fraction(5, 10 ** 15)
s1 = 1 - cc * cc
y1 = (Decimal(s1.numerator) / Decimal(s1.denominator)).sqrt()
pair1 = [['1', '0'], [str(Decimal(cc.numerator) / Decimal(cc.denominator)), '%.45f' % y1]]
check('exceed_nonideal_5e-15', 2, 2, '0.123456789012', pair1, 'CEILING_LOW')
check('exceed_nonideal_5e-15_listed', 2, 2, '0.123456789013', pair1, 'PASS')
# exceed an ideal value 0.25 by about 5e-15: PASS_ROUNDING
cq = Fraction(1, 4) + Fraction(5, 10 ** 15)
s2 = 1 - cq * cq
y2 = (Decimal(s2.numerator) / Decimal(s2.denominator)).sqrt()
pair2 = [['1', '0'], [str(Decimal(cq.numerator) / Decimal(cq.denominator)), '%.45f' % y2]]
check('exceed_ideal_0.25_by_5e-15', 2, 2, '0.25', pair2, 'PASS_ROUNDING')
# exceed by 2e-14 and 1e-13: FAIL
for k, lab in ((20, '2e-14'), (100, '1e-13')):
    ce = Fraction(1, 4) + Fraction(k, 10 ** 15)
    se = 1 - ce * ce
    ye = (Decimal(se.numerator) / Decimal(se.denominator)).sqrt()
    check('exceed_0.25_by_' + lab, 2, 2, '0.25', [['1', '0'], [str(Decimal(ce.numerator) / Decimal(ce.denominator)), '%.45f' % ye]], 'FAIL')
# duplicate point and scaled duplicate: cosine 1
check('duplicate', 3, 3, '0.5', [[1, 0, 0], [0, 1, 0], [1, 0, 0]], 'FAIL')
check('scaled_duplicate', 3, 3, '0.5', [['0.5', '0', '0'], [0, 1, 0], ['2e0', '0', '0']], 'FAIL')
# exponent notation: a 16-digit approximation of the hexagon, exact cosine just above the ideal -0.5
check('exponent_notation', 2, 3, '-0.5', [['1e0', '0'], ['-5e-1', '0.8660254037844386'], ['-0.5', '-8.660254037844386e-1']], 'PASS_ROUNDING')
# exponent notation with exact values
check('exponent_notation_exact', 3, 3, '0.0', [['1e0', '0', '0'], ['0', '2.5e1', '0'], ['0', '0', '-3E-2']], 'PASS')
# range guard: the reviewer's overflow case and an underflow case must not pass
# the reviewer's overflow case: rows are scaled before squaring, so it is computed correctly (cosine about 1)
check('large_1e200', 3, 3, '0.1', [['1e200', '0', '0'], ['1e200', '1e190', '0'], ['0', '0', '1']], 'FAIL')
check('tiny_1e-160', 3, 3, '0.1', [['1e-160', '0', '0'], ['1e-160', '1e-170', '0'], ['0', '0', '1']], 'FAIL')
check('tiny_entries_ok', 2, 2, '0.000000000001', [['1', '1e-155'], ['-1e-160', '1']], 'PASS')
check('overflow_1e400', 2, 2, '0.5', [['1e400', '0'], ['0', '1']], 'BADFILE', oracle_too=False)
check('row_underflow_1e-300', 2, 2, '0.5', [['1e-300', '0'], ['0', '1']], 'BADFILE', oracle_too=False)
check('zero_vector', 2, 2, '0.5', [[0, 0], [1, 0]], 'BADFILE', oracle_too=False)
check('one_point', 2, 1, '0.5', [[1, 0]], 'BADFILE', oracle_too=False)
check('wrong_shape', 3, 2, '0.5', [[1, 0], [0, 1]], 'BADFILE', oracle_too=False)

print('\nPart B: table files')
if not os.path.isdir('./data/coords') or not os.listdir('./data/coords'):
    print('skipped: data/coords/ is empty (run parse_table.py and download_coords.py first)')
else:
    E = json.load(open('./data/entries.json'))
    small = [e for e in E if e['n'] <= 120 and os.path.exists('./data/coords/%d_%d.txt' % (e['dim'], e['n']))]
    random.seed(20261102)
    sample = random.sample(small, min(60, len(small)))
    bad = 0
    for e in sample:
        path = './data/coords/%d_%d.txt' % (e['dim'], e['n'])
        a = certify(e['dim'], e['n'], e['cosine'], path, e.get('poly')); b = oracle(path, e['cosine'], ideal=bool(e.get('poly')))
        if a['verdict'] != b['verdict'] or a['exact_max_cos'] != b['exact_max_cos']:
            bad += 1; print('DIFF', e['dim'], e['n'], a['verdict'], b['verdict'], a['exact_max_cos'], b['exact_max_cos'])
    print('differential: %d entries compared, %d disagreements' % (len(sample), bad))
    failures += bad
    for e in sample[:3]:
        path = './data/coords/%d_%d.txt' % (e['dim'], e['n'])
        base = certify(e['dim'], e['n'], e['cosine'], path, e.get('poly'))
        i, j = base['max_pair']
        rows = [l.strip().split(',') for l in open(path) if l.strip()]
        xi = [Fraction(Decimal(s)) for s in rows[i]]; xj = [Fraction(Decimal(s)) for s in rows[j]]
        moved = [a + (b - a) / 1000 for a, b in zip(xi, xj)]
        rows2 = [r[:] for r in rows]; rows2[i] = ['%.17f' % float(v) for v in moved]
        p2 = write('perturbed_%d_%d.txt' % (e['dim'], e['n']), rows2)
        r1 = certify(e['dim'], e['n'], e['cosine'], p2)
        r2 = certify(e['dim'], e['n'], '%.12f' % (float(base['exact_max_cos']) - 1e-9), path)
        r3 = certify(e['dim'], e['n'], '%.12f' % (float(Fraction(e['cosine']) + Fraction(2, 10 ** 12))), path)
        ok = r1['verdict'] == 'FAIL' and r2['verdict'] == 'FAIL' and r3['verdict'] == 'BETTER'
        print('perturbation tests on %d,%d: moved point -> %s, underclaim -> %s, overclaim -> %s  %s' % (e['dim'], e['n'], r1['verdict'], r2['verdict'], r3['verdict'], 'ok' if ok else 'PROBLEM'))
        if not ok: failures += 1

print('\n%s' % ('ALL TESTS PASS' if failures == 0 else '%d PROBLEMS' % failures))
sys.exit(1 if failures else 0)
