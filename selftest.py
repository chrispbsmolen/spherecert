"""Differential and negative tests for certify.py.
1. Differential: certify() vs oracle() on a random sample of entries with n <= 120 (every verdict and
   exact maximum must agree).
2. Negative: perturb one coordinate of a passing entry so that one pair gets closer, and check FAIL;
   claim a cosine 1e-9 below the exact maximum and check FAIL; claim a cosine 2e-12 above and check BETTER.
Exit 0 only if everything passes."""
import json, random, sys, os, tempfile
sys.path.insert(0, '.')
from certify import certify
from oracle import oracle
from fractions import Fraction
from decimal import Decimal

E = json.load(open('./data/entries.json'))
small = [e for e in E if e['n'] <= 120 and os.path.exists('./data/coords/%d_%d.txt' % (e['dim'], e['n']))]
random.seed(20261102)
sample = random.sample(small, 60)
bad = 0
for e in sample:
    path = './data/coords/%d_%d.txt' % (e['dim'], e['n'])
    a = certify(e['dim'], e['n'], e['cosine'], path); b = oracle(path, e['cosine'])
    if a['verdict'] != b['verdict'] or a['exact_max_cos'] != b['exact_max_cos']:
        bad += 1; print("DIFF", e['dim'], e['n'], a['verdict'], b['verdict'], a['exact_max_cos'], b['exact_max_cos'])
print("differential: %d entries compared, %d disagreements" % (len(sample), bad))

# negative tests on three entries
neg_bad = 0
for e in sample[:3]:
    path = './data/coords/%d_%d.txt' % (e['dim'], e['n'])
    base = certify(e['dim'], e['n'], e['cosine'], path)
    i, j = base['max_pair']
    rows = [l.strip().split(',') for l in open(path) if l.strip()]
    # (a) move point i a little toward point j: cosine of pair (i,j) rises
    xi = [Fraction(Decimal(s)) for s in rows[i]]; xj = [Fraction(Decimal(s)) for s in rows[j]]
    moved = [a + (b - a) / 1000 for a, b in zip(xi, xj)]
    rows2 = [r[:] for r in rows]; rows2[i] = ['%.17f' % float(v) for v in moved]
    tmp = tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False); tmp.write('\n'.join(','.join(r) for r in rows2) + '\n'); tmp.close()
    r1 = certify(e['dim'], e['n'], e['cosine'], tmp.name)
    # (b) claim a cosine 1e-9 below the exact maximum
    claim_low = '%.12f' % (float(base['exact_max_cos']) - 1e-9)
    r2 = certify(e['dim'], e['n'], claim_low, path)
    # (c) claim a cosine 2e-12 above the ceiling: should be BETTER
    claim_high = '%.12f' % (float(Fraction(e['cosine']) + Fraction(2, 10 ** 12)))
    r3 = certify(e['dim'], e['n'], claim_high, path)
    ok = r1['verdict'] == 'FAIL' and r2['verdict'] == 'FAIL' and r3['verdict'] == 'BETTER'
    print("negative tests on %d,%d: perturbed -> %s, underclaim -> %s, overclaim -> %s  %s" % (e['dim'], e['n'], r1['verdict'], r2['verdict'], r3['verdict'], 'ok' if ok else 'PROBLEM'))
    if not ok: neg_bad += 1
    os.unlink(tmp.name)
sys.exit(1 if (bad or neg_bad) else 0)
