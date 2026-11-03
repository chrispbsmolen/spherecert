"""For every entry with a listed minimal polynomial: irreducibility over Q and the content of the
polynomial (sympy factor_list, with a per-polynomial time limit).  The root check, that the stated
cosine lies within 1e-12 of a root, is done exactly by certify.py (check_poly).
Writes results/poly_checks.csv."""
import json, csv, multiprocessing as mp, sys, time
sys.path.insert(0, '.')
from certify import parse_poly
import sympy as sp

E = [e for e in json.load(open('./data/entries.json')) if e['poly']]
x = sp.symbols('x')

def work(e):
    t0 = time.time()
    try:
        P = parse_poly(e['poly'])
        poly = sp.Poly(sum(c * x ** p for p, c in P.items()), x)
        deg = poly.degree()
        _, fl = sp.factor_list(poly.as_expr())
        nfac = sum(m for _, m in fl)
        irreducible = (nfac == 1)
        content = sp.Poly(poly, x).content() if hasattr(poly, 'content') else 1
        return dict(dim=e['dim'], n=e['n'], degree=deg, factors=nfac, irreducible=int(irreducible), content=int(content),
                    seconds=round(time.time() - t0, 1), note='')
    except Exception as ex:
        return dict(dim=e['dim'], n=e['n'], degree='', factors='', irreducible='', content='', seconds=round(time.time() - t0, 1), note=repr(ex)[:120])

if __name__ == "__main__":
    E.sort(key=lambda e: len(e['poly']))
    out = []
    with mp.Pool(2) as pool:
        it = pool.imap_unordered(work, E, chunksize=1)
        for k in range(len(E)):
            try:
                r = it.next(timeout=900)
            except mp.TimeoutError:
                print("timeout, stopping at", k, flush=True); break
            out.append(r)
            if k % 100 == 0: print("done", k, flush=True)
    with open('./results/poly_checks.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['dim', 'n', 'degree', 'factors', 'irreducible', 'content', 'seconds', 'note']); w.writeheader(); w.writerows(sorted(out, key=lambda r: (r['dim'], r['n'])))
    red = [r for r in out if r['irreducible'] == 0]
    print("checked", len(out), "polynomials; reducible:", len(red), [(r['dim'], r['n'], r['degree'], r['factors']) for r in red][:20])
    print("content != 1:", [(r['dim'], r['n'], r['content']) for r in out if r['content'] not in (1, '')][:20])
