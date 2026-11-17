"""Write README.md.  The results paragraphs are filled from results/ledger.csv,
results/poly_checks.csv, results/improvements_ledger.csv and results/certify_all.jsonl, so the
README cannot drift from the data."""
import csv, json, os, collections
W = os.path.dirname(os.path.abspath(__file__))
fmt = lambda x: '{:,}'.format(x)
L = list(csv.DictReader(open(W + '/results/ledger.csv')))
V = collections.Counter(r['verdict'] for r in L)
P = list(csv.DictReader(open(W + '/results/poly_checks.csv')))
polyok = sum(1 for r in L if r['has_poly'] == '1' and r['poly_check'] == 'root_in_interval')
npoly = sum(1 for r in L if r['has_poly'] == '1')
irr = sum(1 for r in P if r['irreducible'] == '1')
I = list(csv.DictReader(open(W + '/results/improvements_ledger.csv')))
C = [json.loads(l) for l in open(W + '/results/certify_all.jsonl')]
F = json.load(open(W + '/flagged_entries.json'))
tiers = collections.Counter(r['tier'] for r in I)
top = max(I, key=lambda r: int(r['gain_units_1e12']))
ceil = [r for r in L if r['verdict'] == 'CEILING_LOW']
date = open(W + '/data/SNAPSHOT_DATE').read().strip()
maxex = max(float(r['file_exceeds_stated_by']) for r in csv.DictReader(open(W + '/results/exact_value_entries.csv')))
counts = ', '.join('%s %s' % (fmt(V[v]), v) for v in ['PASS', 'PASS_ROUNDING', 'CEILING_LOW', 'BETTER', 'FAIL', 'BADFILE'] if V.get(v))
absent = ', '.join('no %s' % v for v in ['BETTER', 'FAIL', 'BADFILE'] if not V.get(v))

text = f'''# spherecert

An exact certifier for the entries of Henry Cohn's table of spherical codes at
https://spherical-codes.org/ (data set: H. Cohn, Table of spherical codes, https://hdl.handle.net/1721.1/153543),
and certified improvements for entries the table marks as needing more optimization.

Each table entry states a dimension d, a number of points n, and the cosine c of the
minimal angle, printed with 12 decimals, together with a coordinate file. `certify.py`
reads the coordinate file and proves, in exact integer arithmetic on the printed
decimals, that every pair of (normalized) points has cosine at most c. Floating point is
used only as a screen, with a rigorous forward error bound, to decide which pairs need
the exact test. Files whose coordinates are small integers (lattice type configurations
such as the 196,560 minimal vectors of the Leech lattice) take an exact double precision
path, where no rounding occurs at all.

## Conventions learned from the data

- The table rounds cosines up to 12 decimals (3,9 is listed as 0.333333333334), so the
  stated value is a ceiling and the test is "cosine at most c".
- Where the stated value is an ideal value (a short exact decimal such as 0.25, 0.375 or
  0.5, or a root of a listed minimal polynomial), the file is a floating point
  approximation and its exact cosine can exceed c by a tiny amount (at most {maxex:.2e}
  in this table). The certifier reports this as PASS_ROUNDING, with a tolerance of 1e-14.
  The same excess over a stated value that is not ideal is reported as CEILING_LOW: the
  printed 12-decimal value is one unit too low.

## Verdicts

| Verdict | Meaning |
|---|---|
| PASS | every pair has cosine at most c, and c is the correct 12-decimal ceiling of the file's maximum |
| PASS_ROUNDING | some pair exceeds c by at most 1e-14, and c is an ideal value (approximate file) |
| CEILING_LOW | some pair exceeds c by at most 1e-14, and c is not an ideal value (c should be one unit higher) |
| BETTER | every pair is at most c - 1e-12: the table could state a smaller value |
| FAIL | some pair exceeds c + 1e-14 (or exceeds c, for integer files); the exact maximum is reported |
| BADFILE | wrong shape, fewer than 2 points, unreadable number, zero vector, or a coordinate outside the floating point range of the screen |

Also reported per entry: the exact maximum cosine, the pair attaining it, the number of
pairs within 1e-9 of the maximum ("contacts") and the number of points with no such
contact (an informal rattler count), and, where a minimal polynomial is listed, an exact
proof that it changes sign on [c - 1e-12, c].

## Results, snapshot of {date}

All {fmt(len(L))} entries: {counts}; {absent}.
{polyok} of the {npoly} listed minimal polynomials change sign on [c - 1e-12, c], and {irr} of
the {len(P)} are irreducible over Q. The CEILING_LOW entries are {', '.join('({},{})'.format(r['dim'], r['n']) for r in ceil) or 'none'}.
See `results/VERIFICATION.md` for the run of record, `results/ledger.csv` for one row per
entry (with the SHA-256 of each coordinate file as served), `results/exact_value_entries.csv`,
`results/ceiling_low_entries.csv` and `results/poly_checks.csv`.

The site's coordinate files are not redistributed here; they are identified by hash and
remain at spherical-codes.org.

## Certified improvements

`optimize.py` (penalty descent toward a target cosine, followed by a log-sum-exp pass)
was run on all {fmt(len(F))} entries the table marks as needing more optimization, with
`run_opt_batch.py`. Every candidate was then certified by `certify_all.py`, which accepts a
file only if its exact maximum cosine has a 12-decimal ceiling strictly below the table
value, `certify()` gives PASS at the new value, and, for n <= 150, the independent oracle
agrees.

Result: {fmt(len(I))} of the {fmt(len(F))} flagged entries improve ({fmt(len(C))} candidate files certified).
For {fmt(tiers['>=1e-4'])} of them the cosine drops by at least 1e-4; the largest gain is
{top['dim']} dimensions with {top['n']} points, from {top['table_cosine']} to {top['new_cosine']}.
See `results/IMPROVEMENTS.md`, `results/improvements_ledger.csv` (one row per improved entry
with the SHA-256 of the coordinate file), `results/certify_all.jsonl` (every candidate) and
`results/recheck_top.txt` (independent recheck of the largest gains). The coordinate files
are in the release archive, in the same format as the site, with `SHA256SUMS`
(check with `cd release && sha256sum -c SHA256SUMS` after unpacking). Nothing here claims
that any new value is optimal.

## Usage

Requirements: Python 3 and the packages in `requirements.txt`. Run every script from the
repository root.

```
python3 selftest.py                    # constructed tests; also table tests if data/coords is filled
python3 certify.py DIM N STATED_COSINE coords.txt [MINIMAL_POLYNOMIAL]

python3 fetch_table.py                 # data/index.html, data/plain.txt, data/SNAPSHOT_DATE
python3 parse_table.py                 # data/entries.json
python3 download_coords.py             # data/coords/ (about 2 GB)
python3 run_all.py                     # data/results.jsonl
python3 check_polys.py                 # results/poly_checks.csv
python3 make_ledger.py                 # results/ledger.csv
python3 make_verification_md.py        # results/VERIFICATION.md and the exact value lists

python3 run_opt_batch.py [workers]     # candidates/new/
python3 certify_all.py --workers N candidates/run_1 candidates/run_2
python3 make_improvements_ledger.py    # results/improvements_ledger.csv and stamp
python3 make_release.py                # release/ archive and SHA256SUMS
python3 recheck_top.py                 # results/recheck_top.txt
python3 make_improvements_md.py        # results/IMPROVEMENTS.md
python3 make_readme.py                 # this file
```

`lp_bound.py` computes the Delsarte linear programming bound, used only to gauge how much
room an entry has; it plays no part in any verdict.

## Citing

Please cite this repository as: Christopher Smolen, spherecert: an exact certifier for the table of
spherical codes, with certified improvements, Zenodo, doi:10.5281/zenodo.24299107 (all versions;
version v2026.11.16 is doi:10.5281/zenodo.24299108). For the table itself, cite H. Cohn, Table of
spherical codes, https://hdl.handle.net/1721.1/153543.

## Licence

The code is under the MIT licence (`LICENSE`). The improved coordinate files in the release
are derived from the coordinate files of the table cited above; please cite that data set
together with this repository when using them.

Christopher Smolen, November 2026. Every result above
was reproduced and checked by the author.
'''
open(W + '/README.md', 'w').write(text)
print(text[text.index('## Results'):text.index('## Usage')])
