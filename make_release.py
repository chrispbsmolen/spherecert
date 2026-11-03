"""Build the release archive from the ledger: release/improved/<dim>_<n>.txt (copied from the
candidate folder named in the ledger's run column), release/SHA256SUMS with paths relative to
release/ (check with: cd release && sha256sum -c SHA256SUMS), and
release/improved_codes_<date>.tar.gz.  Every hash is checked against the ledger."""
import csv, hashlib, os, shutil, sys, tarfile
W = os.path.dirname(os.path.abspath(__file__))
date = sys.argv[1] if len(sys.argv) > 1 else '2026-11-03'
R = os.path.join(W, 'release'); os.makedirs(os.path.join(R, 'improved'), exist_ok=True)
lines = []
for row in csv.DictReader(open(os.path.join(W, 'results', 'improvements_ledger.csv'))):
    name = os.path.basename(row['file'])
    src = os.path.join(W, 'candidates', row['run'], name); dst = os.path.join(R, 'improved', name)
    shutil.copyfile(src, dst)
    h = hashlib.sha256(open(dst, 'rb').read()).hexdigest()
    if h != row['sha256']: raise SystemExit('hash mismatch for %s' % name)
    lines.append('%s  improved/%s\n' % (h, name))
open(os.path.join(R, 'SHA256SUMS'), 'w').write(''.join(lines))
tar = os.path.join(R, 'improved_codes_%s.tar.gz' % date)
with tarfile.open(tar, 'w:gz') as t:
    t.add(os.path.join(R, 'improved'), arcname='improved'); t.add(os.path.join(R, 'SHA256SUMS'), arcname='SHA256SUMS')
print(len(lines), 'files; archive', tar, hashlib.sha256(open(tar, 'rb').read()).hexdigest())
