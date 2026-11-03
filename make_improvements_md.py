"""Write results/IMPROVEMENTS.md from results/improvements_ledger.csv and results/certify_all.jsonl."""
import csv, json, collections
L = list(csv.DictReader(open('results/improvements_ledger.csv')))
C = [json.loads(l) for l in open('results/certify_all.jsonl')]
F = json.load(open('flagged_entries.json'))
tiers = collections.Counter(r['tier'] for r in L)
runs = collections.Counter(r['run'] for r in L)
orc = sum(1 for r in L if r['oracle'] == 'PASS'); small = sum(1 for r in L if int(r['n']) <= 150)
acc = sum(r['accepted'] for r in C)
stamp = open('results/improvements_ledger_stamp.txt').read().split()[2]
top = sorted(L, key=lambda r: -int(r['gain_units_1e12']))[:25]
bydim = collections.Counter(int(r['dim']) for r in L)
out = []
out.append('# Certified improvements, 3 November 2026\n')
out.append('The table marks %d entries as needing more optimization (`flagged_entries.json`). `optimize.py` was run on all of them in two batches (run_1 and run_2), and every candidate file was certified with `certify_all.py`.\n' % len(F))
out.append('- Candidate files certified: %d, accepted: %d. A file is accepted only if its exact maximum cosine has a 12-decimal ceiling strictly below the table value, `certify()` passes at that new value, and, for n <= 150, the independent oracle passes too.' % (len(C), acc))
out.append('- Entries improved (best file per entry): **%d of the %d flagged entries**. Improved entries with n <= 150: %d, all %d with an oracle PASS.' % (len(L), len(F), small, orc))
out.append('- Best file from run_1: %d, from run_2: %d.\n' % (runs['run_1'], runs['run_2']))
out.append('Gain in cosine (table value minus certified value):\n')
out.append('| gain | entries |\n|---|---|')
for t in ['>=1e-4', '>=1e-6', '>=1e-9', '<1e-9']:
    lab = {'>=1e-4': 'at least 1e-4', '>=1e-6': '1e-6 to 1e-4', '>=1e-9': '1e-9 to 1e-6', '<1e-9': 'below 1e-9'}[t]
    out.append('| %s | %d |' % (lab, tiers[t]))
out.append('\nLargest gains:\n')
out.append('| dim | n | table | certified | gain |\n|---|---|---|---|---|')
for r in top: out.append('| %s | %s | %s | %s | %s |' % (r['dim'], r['n'], r['table_cosine'], r['new_cosine'], r['gain']))
out.append('\nImproved entries by dimension: ' + ', '.join('%d: %d' % (d, bydim[d]) for d in sorted(bydim)) + '.\n')
out.append('## Files\n')
out.append('- `results/improvements_ledger.csv`: one row per improved entry, with the table value, the certified value, the gain, the run, and the SHA-256 of the coordinate file. sha256 of the ledger: `%s`.' % stamp)
out.append('- `results/certify_all.jsonl`: the record of every candidate file, accepted or not.')
out.append('- The coordinate files are in the release archive `improved_codes_2026-11-03.tar.gz` (one file `improved/<dim>_<n>.txt` per entry, in the same format as spherical-codes.org, plus `SHA256SUMS`, checked with `sha256sum -c SHA256SUMS` in the unpacked folder).\n')
out.append('## Independent checks\n')
rc = open('results/recheck_top.txt').read().strip().splitlines()
out.append('Besides the oracle for n <= 150, the %d entries with the largest gains were rechecked by `recheck_top.py`, which shares no code with certify.py: point count and dimension, distinctness of the normalized points, and the maximum cosine recomputed at 40 significant digits with mpmath over the 24 largest floating point pairs. Result (from results/recheck_top.txt): %s.\n' % (len(rc) - 1, rc[-1]))
out.append('## Not claimed\n')
out.append('Nothing here says the new values are optimal. The optimizer is a local method started from the table\'s own configurations, and many of the new codes are probably improvable further.')
open('results/IMPROVEMENTS.md', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out[:12]))
