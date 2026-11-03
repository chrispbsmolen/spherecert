# spherecert

An exact certifier for the entries of Henry Cohn's table of spherical codes at
https://spherical-codes.org/ (dataset archived at https://hdl.handle.net/1721.1/153543).

Each table entry states a dimension d, a number of points n, and the cosine c of the
minimal angle, printed with 12 decimals, together with a coordinate file. `certify.py`
reads the coordinate file and proves, in exact integer arithmetic on the printed
decimals, that every pair of (normalized) points has cosine at most c. Floating point is
used only as a screen, with a rigorous forward error bound, to decide which pairs need
the exact test. Files whose coordinates are small integers (lattice-type configurations
such as the 196,560 minimal vectors of the Leech lattice) take an exact double-precision
path, where no rounding occurs at all.

## Conventions learned from the data

- The table rounds cosines up to 12 decimals (3,9 is listed as 0.333333333334), so the
  stated value is a ceiling and the test is "cosine at most c".
- Where the stated value is the exact value of an ideal configuration (0.25, 0.5, or a
  root of a listed minimal polynomial), the file is a double precision approximation and
  its exact cosine can exceed c by a few parts in 10^17. The certifier reports this as
  PASS_ROUNDING, with the tolerance set at 1e-14, far above anything 17-digit coordinates
  can produce in 32 dimensions (the largest excess found was 1.95e-16) and far below the
  12-decimal precision of the table.

## Verdicts

| Verdict | Meaning |
|---|---|
| PASS | every pair has cosine at most c, and c is the correct 12-decimal ceiling of the file's maximum |
| PASS_ROUNDING | some pair exceeds c by at most 1e-14 (ideal value stated, approximate file) |
| BETTER | every pair is at most c - 1e-12: the table could state a smaller value |
| FAIL | some pair exceeds c + 1e-14; the exact maximum is reported |
| BADFILE | wrong shape, unreadable number, or zero vector |

Also reported per entry: the exact maximum cosine, the pair attaining it, the number of
pairs within 1e-9 of the maximum ("contacts") and the number of points with no such
contact (an informal rattler count whose meaning depends on how converged the code is),
and, where a minimal polynomial is listed, an exact proof that it changes sign on
[c - 1e-12, c].

## Results, snapshot of 2 November 2026

All 14,894 entries: 14,826 PASS, 68 PASS_ROUNDING, no BETTER, no FAIL, no BADFILE.
All 707 listed minimal polynomials are irreducible over Q, primitive, and have a root
within 1e-12 of the stated cosine. See `results/VERIFICATION.md` for the run of record,
`results/ledger.csv` for one row per entry (with the SHA-256 of each coordinate file as
served), `results/exact_value_entries.csv` for the 68 ideal-value entries, and
`results/poly_checks.csv`.

Coordinate files are not redistributed here; they are identified by hash and remain at
spherical-codes.org.

## Checks on the checker

- `oracle.py` is a slow pure-rational implementation sharing no logic with `certify.py`
  (every pair, no screening). `selftest.py` compares the two on a random sample of entries
  and runs negative tests: a perturbed coordinate, an underclaimed cosine and an
  overclaimed one must produce FAIL, FAIL and BETTER. All pass.
- The three largest entries (24,196560), (23,4600) and (64,4224) give contact counts of
  196560*4600/2, 4600*891/2 and 4224*2048/2, as the known structures require.

## Usage

```
python3 certify.py DIM N STATED_COSINE coords.txt [MINIMAL_POLYNOMIAL]
```
prints one JSON line with the verdict and the fields above. `run_all.py` certifies a
whole snapshot (`parse_table.py` builds the entry index from the table page,
`download_coords.py` fetches the files), `make_ledger.py` writes the ledger.

Christopher Smolen, November 2026. Every result above
was reproduced and checked by the author.
