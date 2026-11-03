# Run of record, spherical-codes.org certification

- Snapshot: table page and plain-text table fetched 2 November 2026 (14,894 HTML rows, 14,801 plain rows;
  the 93 rows absent from the plain table are the entries beyond 32 dimensions or 1024 points).
- Coordinate files: all 14,894 fetched from https://spherical-codes.org/data/DIM/N on 2 November 2026,
  1,998 MB, 0 failures. SHA-256 of each file as served is in ledger.csv.
- Certifier: spherecert, git commit recorded in the ledger's verify_stamp, Python 3 with numpy,
  Linux x86_64, 2 cores. Total certification time about 25 minutes, of which 17.6 minutes were
  the Leech entry (24,196560).

## Counts

| | entries |
|---|---|
| PASS | 14,826 |
| PASS_ROUNDING | 68 |
| BETTER | 0 |
| FAIL | 0 |
| BADFILE | 0 |
| entries marked optimal (asterisk) | 32, all PASS or PASS_ROUNDING |
| entries marked "needs more optimization" | 4,252, all PASS |
| entries with a minimal polynomial | 707: all irreducible over Q and primitive, and each changes sign on [c - 1e-12, c] (exact rational evaluation), so each has a root within 1e-12 of the stated cosine |
| method | 14,834 decimal_exact, 60 integer_exact |
| coordinate precision | 0 to 171 decimal digits per entry |

Stated minus exact maximum, over all entries, lies in [0, 1e-12) for PASS entries, confirming that
every stated value is the ceiling of the file's exact maximum at 12 decimals. 110 entries have the
file maximum exactly equal to the stated value.

## The 68 PASS_ROUNDING entries

Listed in exact_value_entries.csv. 49 carry a minimal polynomial; the other 19 state simple exact
values (0.25, 0.3, 0.5, 0.7, 0.786777304640) without one. The file's exact cosine exceeds the stated
value by between 3e-17 and 1.95e-16, consistent with coordinates rounded to 16 or 17 significant digits.

## Checks on the checker

- Differential: 60 random entries with n <= 120, certify.py vs oracle.py (pure Fraction arithmetic,
  all pairs, no shared code): identical verdicts and exact maxima.
- Negative: on three entries, moving one point 0.1 percent toward its nearest neighbour gives FAIL;
  claiming a cosine 1e-9 below the exact maximum gives FAIL; claiming 2e-12 above gives BETTER.
- Structural: (24,196560) 452,088,000 contact pairs = 196560*4600/2; (23,4600) 2,049,300 = 4600*891/2;
  (64,4224) 4,325,376 = 4224*2048/2.
- Two defects found and fixed in the certifier during development, both by the data: an open-path
  pruning that was unsound (removed) and a float overflow in the reporting line for files with
  more than 150 decimals (replaced by exact rational conversion). Neither affected a verdict that was
  reported.

## Not checked

- Whether any entry could be improved by further optimization (the table's own "needs more
  optimization" flags are taken as given; 911 of those 4,252 entries have every point in contact
  within 1e-9, which says nothing about optimality).
- The kissing number table. Its values for dimensions 18 and 25 to 46 were compared with the
  current table in github.com/alexlegeartis/KissingNumbers (29 October 2026 release) and agree;
  no configuration was re-verified.
- Rattler counts are informal (1e-9 tolerance) and were not used in any verdict.
