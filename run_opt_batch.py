"""Optimizer batch.  Run from this folder:

    python3 run_opt_batch.py [workers]      (default 8 workers)

Reads flagged_entries.json (the entries the table marks as needing more optimization),
downloads their coordinate files from spherical-codes.org into coords/ (skipping ones
already present), and runs optimize.hybrid on each, largest entries first.  Resumable:
entries already in opt_results.jsonl are skipped.  A candidate whose floating point
maximum cosine beats the table is written to improved/; nothing written there counts
until certify_all.py has certified it exactly.  Stop any time with Ctrl-C."""
import json, os, sys, time, urllib.request, multiprocessing as mp
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1'); os.environ.setdefault('MKL_NUM_THREADS', '1')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from optimize import hybrid, load

E = json.load(open(os.path.join(HERE, 'flagged_entries.json')))
COORDS = os.path.join(HERE, 'coords'); IMP = os.path.join(HERE, 'improved'); RES = os.path.join(HERE, 'opt_results.jsonl')
os.makedirs(COORDS, exist_ok=True); os.makedirs(IMP, exist_ok=True)

def fetch(e):
    p = os.path.join(COORDS, '%d_%d.txt' % (e['dim'], e['n']))
    if os.path.exists(p): return True
    for attempt in range(4):
        try:
            with urllib.request.urlopen('https://spherical-codes.org/data/%d/%d' % (e['dim'], e['n']), timeout=120) as r: data = r.read()
            if data.strip():
                open(p + '.part', 'wb').write(data); os.replace(p + '.part', p); return True
        except Exception:
            time.sleep(2 * (attempt + 1))
    return False

def work(e):
    key = (e['dim'], e['n']); t0 = time.time()
    try:
        X0 = load(os.path.join(COORDS, '%d_%d.txt' % key))
        B, v, s, method, rounds = hybrid(X0)
        stated = float(e['cosine']); gain_vs_table = stated - v
        rec = dict(dim=e['dim'], n=e['n'], stated=e['cosine'], start=repr(s), best=repr(v), gain=repr(s - v),
                   gain_vs_table=repr(gain_vs_table), method=method, rounds=rounds, seconds=round(time.time() - t0, 1), host='batch')
        if gain_vs_table > 2e-12:
            with open(os.path.join(IMP, '%d_%d.txt' % key), 'w') as f:
                for row in B: f.write(','.join(repr(float(x)) for x in row) + '\n')
            rec['improved_file'] = True
        return rec
    except Exception as ex:
        return dict(dim=e['dim'], n=e['n'], stated=e['cosine'], error=repr(ex)[:200], seconds=round(time.time() - t0, 1), host='batch')

if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    done = set()
    if os.path.exists(RES):
        for l in open(RES):
            try: r = json.loads(l); done.add((r['dim'], r['n']))
            except Exception: pass
    todo = sorted([e for e in E if (e['dim'], e['n']) not in done], key=lambda e: (-e['n'], -e['dim']))
    print("entries to do: %d (already done %d)" % (len(todo), len(done)), flush=True)
    print("downloading coordinate files (skipping existing)...", flush=True)
    with mp.Pool(4) as pool:
        ok = pool.map(fetch, todo, chunksize=8)
    todo = [e for e, o in zip(todo, ok) if o]
    print("downloaded; optimizing %d entries with %d workers, largest first" % (len(todo), workers), flush=True)
    k = 0; t0 = time.time()
    with mp.Pool(workers) as pool, open(RES, 'a') as out:
        for r in pool.imap_unordered(work, todo, chunksize=1):
            out.write(json.dumps(r) + '\n'); out.flush(); k += 1
            if k % 10 == 0:
                imp = len(os.listdir(IMP)); print("optimized %d/%d in %.0f min, candidate improvements so far %d" % (k, len(todo), (time.time() - t0) / 60, imp), flush=True)
    print("finished %d in %.0f min" % (k, (time.time() - t0) / 60), flush=True)
