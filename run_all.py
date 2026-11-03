"""Run certify() over every entry with a coordinate file present; append results to
data/results.jsonl (resumable: entries already in the file are skipped).  Two workers."""
import json, os, sys, time, traceback, multiprocessing as mp
sys.path.insert(0, '.')
from certify import certify

E = json.load(open('./data/entries.json'))
RES = './data/results.jsonl'
done = set()
if os.path.exists(RES):
    for line in open(RES):
        try:
            r = json.loads(line); done.add((r['dim'], r['n']))
        except Exception: pass

def work(e):
    path = './data/coords/%d_%d.txt' % (e['dim'], e['n'])
    t0 = time.time()
    try:
        r = certify(e['dim'], e['n'], e['cosine'], path, e['poly'])
    except Exception as ex:
        r = dict(dim=e['dim'], n=e['n'], stated=e['cosine'], verdict='ERROR', note=traceback.format_exc()[-500:])
    r['seconds'] = round(time.time() - t0, 2)
    r['optimal'] = e['optimal']; r['needs_opt'] = e['needs_opt']; r['has_poly'] = e['poly'] is not None
    return r

if __name__ == "__main__":
    big = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9  # skip entries with n above this (run separately)
    todo = [e for e in E if (e['dim'], e['n']) not in done and e['n'] <= big
            and os.path.exists('./data/coords/%d_%d.txt' % (e['dim'], e['n']))]
    todo.sort(key=lambda e: e['n'])
    print("to certify:", len(todo), "already done:", len(done), flush=True)
    t0 = time.time(); k = 0
    with mp.Pool(2) as pool, open(RES, 'a') as out:
        for r in pool.imap_unordered(work, todo, chunksize=4):
            out.write(json.dumps(r) + "\n"); out.flush(); k += 1
            if k % 500 == 0: print("certified %d/%d in %.0f s" % (k, len(todo), time.time() - t0), flush=True)
    print("finished %d in %.0f s" % (k, time.time() - t0), flush=True)
