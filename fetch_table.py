"""Fetch the table page and the plain text table from spherical-codes.org into data/index.html and
data/plain.txt (the inputs of parse_table.py), and record today's date in data/SNAPSHOT_DATE."""
import urllib.request, datetime, os
W = os.path.dirname(os.path.abspath(__file__)); os.makedirs(W + '/data', exist_ok=True)
for url, name in (('https://spherical-codes.org/', 'index.html'), ('https://spherical-codes.org/plain', 'plain.txt')):
    with urllib.request.urlopen(url, timeout=120) as r: open(W + '/data/' + name, 'wb').write(r.read())
open(W + '/data/SNAPSHOT_DATE', 'w').write(datetime.date.today().isoformat() + '\n')
print('fetched index.html and plain.txt')
