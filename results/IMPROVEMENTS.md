# Certified improvements, 3 November 2026

The table marks 4252 entries as needing more optimization (`flagged_entries.json`). `optimize.py` was run on all of them in two batches (run_1 and run_2), and every candidate file was certified with `certify_all.py`.

- Candidate files certified: 4304, accepted: 4304. A file is accepted only if its exact maximum cosine has a 12-decimal ceiling strictly below the table value, `certify()` passes at that new value, and, for n <= 150, the independent oracle passes too.
- Entries improved (best file per entry): **3650 of the 4252 flagged entries**. Improved entries with n <= 150: 234, all 234 with an oracle PASS.
- Best file from run_1: 298, from run_2: 3352.

Gain in cosine (table value minus certified value):

| gain | entries |
|---|---|
| at least 1e-4 | 228 |
| 1e-6 to 1e-4 | 680 |
| 1e-9 to 1e-6 | 2296 |
| below 1e-9 | 446 |

Largest gains:

| dim | n | table | certified | gain |
|---|---|---|---|---|
| 27 | 612 | 0.231211909343 | 0.225897677118 | 5.314e-03 |
| 27 | 611 | 0.229572621730 | 0.225370282803 | 4.202e-03 |
| 15 | 1001 | 0.451682623395 | 0.448481045347 | 3.202e-03 |
| 16 | 866 | 0.421034905337 | 0.417940417421 | 3.094e-03 |
| 26 | 601 | 0.231771701824 | 0.228686176161 | 3.086e-03 |
| 15 | 1000 | 0.450504842608 | 0.447460075819 | 3.045e-03 |
| 16 | 865 | 0.420393389027 | 0.417734448486 | 2.659e-03 |
| 19 | 369 | 0.271284401119 | 0.268967136192 | 2.317e-03 |
| 25 | 1000 | 0.271945279113 | 0.269799272883 | 2.146e-03 |
| 15 | 995 | 0.446737400181 | 0.444611048685 | 2.126e-03 |
| 25 | 999 | 0.271453749655 | 0.269455638111 | 1.998e-03 |
| 15 | 994 | 0.446043457030 | 0.444100309628 | 1.943e-03 |
| 16 | 827 | 0.412742563973 | 0.410859385456 | 1.883e-03 |
| 15 | 993 | 0.445282649619 | 0.443447507203 | 1.835e-03 |
| 20 | 1007 | 0.316636191938 | 0.314815157770 | 1.821e-03 |
| 11 | 1005 | 0.562055142255 | 0.560286808042 | 1.768e-03 |
| 26 | 600 | 0.229513033411 | 0.227841382691 | 1.672e-03 |
| 9 | 777 | 0.640768942497 | 0.639145489949 | 1.623e-03 |
| 19 | 364 | 0.265108452326 | 0.263503987314 | 1.604e-03 |
| 19 | 365 | 0.266421291327 | 0.265042994416 | 1.378e-03 |
| 20 | 1006 | 0.316177394261 | 0.314815360701 | 1.362e-03 |
| 20 | 1020 | 0.322731268422 | 0.321394267531 | 1.337e-03 |
| 19 | 366 | 0.267497861944 | 0.266204868097 | 1.293e-03 |
| 19 | 368 | 0.269906771338 | 0.268620140081 | 1.287e-03 |
| 13 | 570 | 0.451277019046 | 0.450099813054 | 1.177e-03 |

Improved entries by dimension: 5: 7, 6: 78, 7: 86, 8: 299, 9: 67, 10: 124, 11: 217, 12: 321, 13: 264, 14: 261, 15: 187, 16: 169, 17: 191, 18: 264, 19: 206, 20: 47, 21: 105, 22: 22, 23: 29, 24: 65, 25: 62, 26: 64, 27: 81, 28: 103, 29: 100, 30: 82, 31: 68, 32: 81.

## Files

- `results/improvements_ledger.csv`: one row per improved entry, with the table value, the certified value, the gain, the run, and the SHA-256 of the coordinate file. sha256 of the ledger: `253026583b08eb5b5140ace1ab5505d41b2c831921a26e897df1ad418942357e`.
- `results/certify_all.jsonl`: the record of every candidate file, accepted or not.
- The coordinate files are in the release archive `improved_codes_2026-11-03.tar.gz` (one file `improved/<dim>_<n>.txt` per entry, in the same format as spherical-codes.org, plus `SHA256SUMS`).

## Independent checks

Besides the oracle for n <= 150, the 40 entries with the largest gains were rechecked with separate code: point count and dimension, distinctness of the normalized points, and the maximum cosine recomputed at 40 significant digits with mpmath over the twelve largest floating point pairs. All 40 agree with the certified values to 1e-12 and lie below the table values.

## Not claimed

Nothing here says the new values are optimal. The optimizer is a local method started from the table's own configurations, and many of the new codes are probably improvable further.
