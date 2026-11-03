"""Build entries.json from the spherical-codes.org snapshot (index.html + plain.txt).
Each entry: dim, n, cosine (string as printed), optimal (asterisk), needs_opt flag,
poly (minimal polynomial string or None), refs (plain text of the references cell).
"""
import re, json, html, sys

src = open('./data/index.html', encoding='utf-8').read()
rows = re.findall(r'<tr>\s*<td>(\d+)</td>\s*<td><a href="/data/(\d+)/(\d+)">(\d+)</a>(&ast;)?</td>\s*<td>([0-9.]+)</td>\s*<td>(.*?)</td>\s*</tr>', src, re.S)
entries = {}
for dim, d2, n2, n, star, cos, refcell in rows:
    assert dim == d2 and n == n2
    needs = 'needs more optimization' in refcell
    has_math = '<math>' in refcell
    reftext = html.unescape(re.sub(r'<math>.*?</math>', '', refcell, flags=re.S))
    reftext = re.sub(r'<[^>]+>', '', reftext).strip()
    entries[(int(dim), int(n))] = dict(dim=int(dim), n=int(n), cosine=cos, optimal=bool(star), needs_opt=needs,
                                       has_poly_html=has_math, refs=reftext, poly=None)
plain_n = 0
for line in open('./data/plain.txt'):
    parts = line.strip().split(',')
    if len(parts) < 3: continue
    key = (int(parts[0]), int(parts[1])); plain_n += 1
    if key not in entries:
        print("in plain but not html:", key); continue
    if entries[key]['cosine'] != parts[2]:
        print("cosine differs html/plain", key, entries[key]['cosine'], parts[2])
    if len(parts) >= 4 and parts[3]:
        entries[key]['poly'] = parts[3]
print("html rows:", len(rows), "plain rows:", plain_n)
print("optimal:", sum(e['optimal'] for e in entries.values()), "needs_opt:", sum(e['needs_opt'] for e in entries.values()),
      "with poly:", sum(e['poly'] is not None for e in entries.values()))
json.dump([entries[k] for k in sorted(entries)], open('./data/entries.json', 'w'), indent=0)
