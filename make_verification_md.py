"""Write results/VERIFICATION.md from data/entries.json, data/results.jsonl, results/ledger.csv,
results/poly_checks.csv and results/selftest_output.txt.  Every number in the document is computed
here from those files; nothing is typed by hand."""
import json, csv, os, collections
from decimal import Decimal, localcontext
from fractions import Fraction
W = os.path.dirname(os.path.abspath(__file__))
import sys; sys.path.insert(0, W)
from certify import parse_coords, to_int_matrix

E = {(e['dim'], e['n']): e for e in json.load(open(W + '/data/entries.json'))}
R = {}
for l in open(W + '/data/results.jsonl'):
    r = json.loads(l); R[(r['dim'], r['n'])] = r
L = {(int(r['dim']), int(r['n'])): r for r in csv.DictReader(open(W + '/results/ledger.csv'))}
P = list(csv.DictReader(open(W + '/results/poly_checks.csv')))
snapshot = open(W + '/data/SNAPSHOT_DATE').read().strip()
stamp = next(iter(L.values()))['verify_stamp']
fmt = lambda x: '{:,}'.format(x)

def excess(key):
    """exact (max cosine of the file) - (stated cosine), as a Decimal, from the maximizing pair"""
    r = R[key]; i, j = r['max_pair']
    M, K = to_int_matrix(parse_coords(W + '/data/coords/%d_%d.txt' % key))
    ip = sum(a * b for a, b in zip(M[i], M[j])); nx = sum(a * a for a in M[i]); ny = sum(b * b for b in M[j])
    c = Fraction(E[key]['cosine'])
    with localcontext() as ctx:
        ctx.prec = 60
        return Decimal(ip) / (Decimal(nx) * Decimal(ny)).sqrt() - Decimal(c.numerator) / Decimal(c.denominator)

V = collections.Counter(r['verdict'] for r in L.values())
order = ['PASS', 'PASS_ROUNDING', 'CEILING_LOW', 'BETTER', 'FAIL', 'BADFILE', 'NOT_RUN']
opt = [k for k in E if E[k]['optimal']]; need = [k for k in E if E[k]['needs_opt']]
poly = [k for k in E if E[k]['poly']]
meth = collections.Counter(r['method'] for r in L.values())
decs = [int(r['coord_decimals']) for r in L.values() if r['coord_decimals'] != '']
big = [k for k in E if k[0] > 32 or k[1] > 1024]
sizes = sum(os.path.getsize(W + '/data/coords/%d_%d.txt' % k) for k in E if os.path.exists(W + '/data/coords/%d_%d.txt' % k))
secs = sum(R[k].get('seconds', 0) for k in R); leech = R.get((24, 196560), {}).get('seconds', 0)
pc = collections.Counter(R[k].get('poly_check') for k in poly)
irr = collections.Counter(r['irreducible'] for r in P); cont = collections.Counter(r['content'] for r in P)
rounding = sorted(k for k in L if L[k]['verdict'] == 'PASS_ROUNDING')
ceiling = sorted(k for k in L if L[k]['verdict'] == 'CEILING_LOW')
ex_r = {k: excess(k) for k in rounding}; ex_c = {k: excess(k) for k in ceiling}
for name, keys, ex in (('exact_value_entries.csv', rounding, ex_r), ('ceiling_low_entries.csv', ceiling, ex_c)):
    with open(W + '/results/' + name, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['dim', 'n', 'stated_cosine', 'file_max_cosine_20dp', 'file_exceeds_stated_by', 'has_minimal_polynomial'])
        for k in keys:
            c = Fraction(E[k]['cosine'])
            with localcontext() as ctx:
                ctx.prec = 60
                m = ex[k] + Decimal(c.numerator) / Decimal(c.denominator)
            w.writerow([k[0], k[1], E[k]['cosine'], str(m.quantize(Decimal('1e-20'))), '%.3e' % ex[k], int(bool(E[k]['poly']))])
ideal_vals = collections.Counter(E[k]['cosine'] for k in rounding if not E[k]['poly'])

o = []
o.append('# Run of record, spherical-codes.org certification\n')
o.append('- Snapshot: table page fetched %s, %s entries (%d of them beyond 32 dimensions or 1024 points: %s).' % (snapshot, fmt(len(E)), len(big), ', '.join('(%d,%d)' % k for k in sorted(big))))
o.append('- Coordinate files: %s of %s present in data/coords/, %s MB in total, fetched from https://spherical-codes.org/data/DIM/N. The SHA-256 of each file as served is in ledger.csv.' % (fmt(sum(1 for k in E if os.path.exists(W + '/data/coords/%d_%d.txt' % k))), fmt(len(E)), fmt(round(sizes / 1e6))))
o.append('- Certifier: `%s` (git commit, SHA-256 prefix of certify.py, date, platform). Total certification time %s minutes, of which %.1f minutes were the Leech entry (24,196560).\n' % (stamp, fmt(round(secs / 60)), leech / 60))
o.append('## Counts\n')
o.append('| | entries |\n|---|---|')
for v in order:
    if V.get(v): o.append('| %s | %s |' % (v, fmt(V[v])))
o.append('| entries marked optimal (asterisk) | %d: %s |' % (len(opt), ', '.join('%s %d' % (v, c) for v, c in sorted(collections.Counter(L[k]['verdict'] for k in opt).items()))))
o.append('| entries marked "needs more optimization" | %s: %s |' % (fmt(len(need)), ', '.join('%s %s' % (v, fmt(c)) for v, c in sorted(collections.Counter(L[k]['verdict'] for k in need).items()))))
o.append('| entries with a minimal polynomial | %d. Root check (certify.py, exact rational sign change on [c - 1e-12, c]): %s. Irreducible over Q (check_polys.py): %d of %d; content 1: %d of %d |' % (
    len(poly), ', '.join('%s %d' % (v, c) for v, c in sorted(pc.items(), key=lambda t: str(t[0]))), irr.get('1', 0), len(P), cont.get('1', 0), len(P)))
o.append('| method | %s |' % ', '.join('%s %s' % (m, fmt(c)) for m, c in sorted(meth.items())))
o.append('| coordinate precision | %d to %d decimal digits per entry |\n' % (min(decs), max(decs)))
o.append('For PASS entries the exact maximum lies in (c - 1e-12, c], so c is the 12-decimal ceiling of the file\'s maximum.\n')
o.append('## PASS_ROUNDING entries (%d)\n' % len(rounding))
o.append('The stated value is an ideal value (a listed polynomial root, or a short exact decimal) and the file is a floating point approximation whose exact maximum exceeds it by at most 1e-14. %d have a minimal polynomial; the others state %s. The excess of the file over the stated value ranges from %.2e to %.2e.\n' % (
    sum(1 for k in rounding if E[k]['poly']), ', '.join('%s (%d)' % (v, c) for v, c in sorted(ideal_vals.items())), min(ex_r.values()), max(ex_r.values())))
o.append('All are listed in exact_value_entries.csv; the CEILING_LOW entries are in ceiling_low_entries.csv.\n')
o.append('## CEILING_LOW entries (%d)\n' % len(ceiling))
if ceiling:
    o.append('The stated value is a 12-decimal number, not an ideal value, and the file\'s exact maximum exceeds it by less than 1e-14, so the correct 12-decimal ceiling is one unit higher.\n')
    o.append('| dim | n | stated | exact excess of the file |\n|---|---|---|---|')
    for k in ceiling: o.append('| %d | %d | %s | %.3e |' % (k[0], k[1], E[k]['cosine'], ex_c[k]))
    o.append('')
o.append('## Structural checks\n')
for k, expect in (((24, 196560), (196560 * 4600 // 2, '196560*4600/2')), ((23, 4600), (4600 * 891 // 2, '4600*891/2')), ((64, 4224), (4224 * 2048 // 2, '4224*2048/2'))):
    got = int(L[k]['contact_pairs']) if L[k]['contact_pairs'] else None
    o.append('- (%d,%d): %s contact pairs, expected %s = %s: %s' % (k[0], k[1], fmt(got) if got is not None else 'n/a', expect[1], fmt(expect[0]), 'agrees' if got == expect[0] else 'DIFFERS'))
o.append('')
o.append('## Checks on the checker\n')
st = open(W + '/results/selftest_output.txt').read().strip().splitlines() if os.path.exists(W + '/results/selftest_output.txt') else []
o.append('`selftest.py` output for this run (constructed adversarial cases compared with the independent oracle, then a differential test on 60 table entries and perturbation tests):\n')
o.append('```\n' + '\n'.join(st) + '\n```\n')
o.append('## Defects found and fixed in the certifier\n')
o.append('- During development, both found by the data: coordinates in exponent notation were not parsed exactly (now parsed through Decimal and Fraction), and a float overflow in the reporting line for files with more than 150 decimals (replaced by exact rational conversion).')
o.append('- In an independent review before publication: (1) coordinates near 1e200 overflowed the floating point screen, so a false file could pass (now any coordinate outside 1e-100..1e100 is BADFILE, rows are scaled before squaring, and a non-finite screen is BADFILE); (2) negative stated cosines were compared with the wrong sign (all comparisons are now sign-correct and tested against a square-root-free reference); (3) the 1e-14 rounding tolerance applied to every stated value (it now applies only to ideal values, and other excesses get CEILING_LOW). The table contains no coordinate outside that range and no negative stated cosine, so (1) and (2) could not have affected a verdict here; (3) reclassified the CEILING_LOW entries above, which were previously reported as PASS_ROUNDING.')
o.append('')
o.append('## Not checked\n')
o.append('- Whether any entry is optimal, or could be improved further (see IMPROVEMENTS.md for the optimizer results).')
o.append('- The kissing number table.')
o.append('- Rattler counts are informal (1e-9 tolerance in floating point) and play no part in any verdict.')
open(W + '/results/VERIFICATION.md', 'w').write('\n'.join(o) + '\n')
print('\n'.join(o[:40]))
