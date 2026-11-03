"""Download every coordinate file from spherical-codes.org/data/<dim>/<n> into data/coords/<dim>_<n>.txt.
Four workers, retries, skips files already present. Records failures in data/download_failures.txt."""
import json, os, sys, time, concurrent.futures, urllib.request, urllib.error

E = json.load(open('./data/entries.json'))
out = './data/coords'; os.makedirs(out, exist_ok=True)
todo = [(e['dim'], e['n']) for e in E if not os.path.exists('%s/%d_%d.txt' % (out, e['dim'], e['n']))]
print("to download:", len(todo), flush=True)
fails = []
def fetch(k):
    dim, n = k; url = 'https://spherical-codes.org/data/%d/%d' % (dim, n)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                data = r.read()
            if not data.strip(): raise ValueError("empty")
            tmp = '%s/%d_%d.txt.part' % (out, dim, n)
            open(tmp, 'wb').write(data); os.replace(tmp, '%s/%d_%d.txt' % (out, dim, n))
            return (k, len(data), None)
        except Exception as ex:
            err = repr(ex); time.sleep(2 * (attempt + 1))
    return (k, 0, err)
done = 0; total_bytes = 0; t0 = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    for k, nb, err in ex.map(fetch, todo):
        done += 1; total_bytes += nb
        if err: fails.append((k, err))
        if done % 500 == 0:
            print("done %d/%d, %.1f MB, %.0f s, failures %d" % (done, len(todo), total_bytes / 1e6, time.time() - t0, len(fails)), flush=True)
open('./data/download_failures.txt', 'w').write(''.join("%d %d %s\n" % (k[0], k[1], e) for k, e in fails))
print("finished: %d files, %.1f MB, failures %d" % (done, total_bytes / 1e6, len(fails)), flush=True)
