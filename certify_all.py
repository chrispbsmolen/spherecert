"""Certify candidate improvements.  Usage, from the repository root:

    python3 certify_all.py [--workers N] candidate_dir [candidate_dir ...]

Each candidate_dir holds files named <dim>_<n>.txt.  Per file: the exact maximum cosine of
the written coordinates (integer arithmetic on the decimals), its exact 12-decimal ceiling,
a strict comparison with the table value, a full certify() run at the new value (must be
PASS), and for n <= 150 the independent oracle.  A file is accepted only if all of these
hold.  Resumable: results/certify_all.jsonl, one JSON record per file."""
import json, os, sys, glob, hashlib, time
from fractions import Fraction
from decimal import Decimal, getcontext
from multiprocessing import Pool
sys.path.insert(0, '.')
from certify import certify, parse_coords, to_int_matrix, exact_cos
from oracle import oracle
getcontext().prec = 60
W = '.'
E = {(e['dim'], e['n']): e for e in json.load(open(W + '/data/entries.json'))}
OUT = W + '/results/certify_all.jsonl'

def cos_leq(ip, nx, ny, kk):
    """exact test: ip / sqrt(nx*ny) <= kk / 10^12"""
    if kk >= 0:
        return ip <= 0 or ip * ip * 10 ** 24 <= kk * kk * nx * ny
    return ip < 0 and ip * ip * 10 ** 24 >= kk * kk * nx * ny

def exact_ceiling(ip, nx, ny):
    est = Decimal(ip) / (Decimal(nx) * Decimal(ny)).sqrt()
    k = int((est * Decimal(10) ** 12).to_integral_value(rounding='ROUND_CEILING'))
    while not cos_leq(ip, nx, ny, k): k += 1
    while cos_leq(ip, nx, ny, k - 1): k -= 1
    return k

def fmt(k):
    s = '-' if k < 0 else ''; k = abs(k)
    return '%s%d.%012d' % (s, k // 10 ** 12, k % 10 ** 12)

def work(path):
    t0 = time.time()
    dim, n = map(int, os.path.basename(path)[:-4].split('_'))
    e = E[(dim, n)]; src = os.path.basename(os.path.dirname(path))
    rec = dict(dim=dim, n=n, source=src, file=path, table_cosine=e['cosine'])
    try:
        r0 = certify(dim, n, '1.0', path)
        i, j = r0['max_pair']
        M, K = to_int_matrix(parse_coords(path))
        ip, nx, ny = exact_cos(M[i], M[j])
        k = exact_ceiling(ip, nx, ny); old_k = int(Fraction(e['cosine']) * 10 ** 12)
        new = fmt(k); r = certify(dim, n, new, path)
        rec.update(new_cosine=new, units_1e12=old_k - k, verdict=r['verdict'], exact_new_max=r.get('exact_max_cos'))
        acc = k < old_k and r['verdict'] == 'PASS'
        if acc and n <= 150:
            o = oracle(path, new); rec['oracle'] = o['verdict']; acc = o['verdict'] == 'PASS'
        rec['accepted'] = int(acc)
        rec['sha256'] = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    except Exception as ex:
        rec.update(verdict='ERROR', note=repr(ex)[:300], accepted=0)
    rec['seconds'] = round(time.time() - t0, 1)
    return rec

if __name__ == '__main__':
    done = set()
    if os.path.exists(OUT):
        for l in open(OUT): done.add(json.loads(l)['file'])
    args = sys.argv[1:]; nw = 1
    if args[:1] == ['--workers']: nw = int(args[1]); args = args[2:]
    files = [os.path.abspath(f) for d in args for f in sorted(glob.glob(os.path.join(d, '*.txt')))]
    todo = [f for f in files if f not in done]
    todo.sort(key=lambda f: os.path.getsize(f))
    print('files', len(files), 'todo', len(todo), flush=True)
    with Pool(nw) as pool, open(OUT, 'a') as out:
        for k, rec in enumerate(pool.imap_unordered(work, todo, chunksize=4)):
            out.write(json.dumps(rec) + '\n'); out.flush()
            if (k + 1) % 200 == 0: print('certified', k + 1, flush=True)
    print('finished', flush=True)
