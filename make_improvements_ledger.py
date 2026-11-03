"""Build results/improvements_ledger.csv (best accepted file per entry) and its stamp from
results/certify_all.jsonl.  The run label is the name of the candidate folder."""
import json, csv, hashlib, os
W = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(W, 'results', 'certify_all.jsonl'))]
best = {}
for r in rows:
    k = (r['dim'], r['n'])
    if r['accepted'] and (k not in best or r['units_1e12'] > best[k]['units_1e12']): best[k] = r
def tier(g):
    return '>=1e-4' if g >= 10 ** 8 else '>=1e-6' if g >= 10 ** 6 else '>=1e-9' if g >= 10 ** 3 else '<1e-9'
out = os.path.join(W, 'results', 'improvements_ledger.csv')
with open(out, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['dim', 'n', 'table_cosine', 'new_cosine', 'gain', 'gain_units_1e12', 'tier', 'oracle', 'run', 'file', 'sha256'])
    for k in sorted(best):
        r = best[k]; g = r['units_1e12']
        w.writerow([r['dim'], r['n'], r['table_cosine'], r['new_cosine'], '%.3e' % (g / 1e12), g, tier(g), r.get('oracle') or '',
                    r['source'], 'improved/%d_%d.txt' % k, r['sha256']])
h = hashlib.sha256(open(out, 'rb').read()).hexdigest()
open(os.path.join(W, 'results', 'improvements_ledger_stamp.txt'), 'w').write('sha256(improvements_ledger.csv) = %s\nentries %d\n' % (h, len(best)))
print('entries', len(best), 'sha256', h)
