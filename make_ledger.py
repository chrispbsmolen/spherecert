"""Build results/ledger.csv from data/results.jsonl and data/entries.json.
One row per table entry.  Coordinate files are identified by SHA-256 of the bytes as
served by spherical-codes.org on the snapshot date; they are not redistributed."""
import json, csv, hashlib, os, platform, datetime, collections, subprocess

W = '.'
E = {(e['dim'], e['n']): e for e in json.load(open(W + '/data/entries.json'))}
R = {}
for line in open(W + '/data/results.jsonl'):
    r = json.loads(line); R[(r['dim'], r['n'])] = r
snapshot = open(W + '/data/SNAPSHOT_DATE').read().strip() if os.path.exists(W + '/data/SNAPSHOT_DATE') else '2026-11-02'
commit = subprocess.run(['git', '-C', W, 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip() or 'uncommitted'
stamp = 'spherecert %s %s %s' % (commit, datetime.date.today().isoformat(), platform.system() + '-' + platform.machine())
os.makedirs(W + '/results', exist_ok=True)
fields = ['dim', 'n', 'stated_cosine', 'optimal_mark', 'needs_opt_mark', 'has_poly', 'verdict', 'method', 'exact_max_cosine',
          'stated_minus_exact_e12', 'pairs_over_by_rounding', 'violating_pairs', 'contact_pairs', 'rattlers_1e-9', 'poly_check',
          'coord_decimals', 'coord_sha256', 'verify_stamp', 'note']
rows = []
for key in sorted(E):
    e = E[key]; r = R.get(key, {})
    path = W + '/data/coords/%d_%d.txt' % key
    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest() if os.path.exists(path) else ''
    rows.append(dict(dim=key[0], n=key[1], stated_cosine=e['cosine'], optimal_mark=int(e['optimal']), needs_opt_mark=int(e['needs_opt']),
                     has_poly=int(e['poly'] is not None), verdict=r.get('verdict', 'NOT_RUN'),
                     method=r.get('path') or ('decimal_exact' if r.get('verdict') else ''), exact_max_cosine=r.get('exact_max_cos', ''),
                     stated_minus_exact_e12=r.get('stated_minus_actual_e12', ''), pairs_over_by_rounding=r.get('pairs_over_by_rounding', ''),
                     violating_pairs=r.get('violating_pairs', ''), contact_pairs=r.get('contact_pairs', ''), **{'rattlers_1e-9': r.get('rattlers_1e-9', '')},
                     poly_check=r.get('poly_check', ''), coord_decimals=r.get('decimals', ''), coord_sha256=sha, verify_stamp=stamp,
                     note=(r.get('note') or '').replace('\n', ' ')[:200]))
with open(W + '/results/ledger.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
c = collections.Counter(row['verdict'] for row in rows)
print("ledger rows:", len(rows), dict(c))
print("stamp:", stamp)
