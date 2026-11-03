# Run of record, spherical-codes.org certification

- Snapshot: table page fetched 2026-11-02, 14,894 entries (4 of them beyond 32 dimensions or 1024 points: (23,4600), (24,196560), (52,325), (64,4224)).
- Coordinate files: 14,894 of 14,894 present in data/coords/, 1,998 MB in total, fetched from https://spherical-codes.org/data/DIM/N. The SHA-256 of each file as served is in ledger.csv.
- Certifier: `spherecert 71755be certify.py-sha256:cff412c9673f 2026-11-03 Linux-x86_64` (git commit, SHA-256 prefix of certify.py, date, platform). Total certification time 43 minutes, of which 16.6 minutes were the Leech entry (24,196560).

## Counts

| | entries |
|---|---|
| PASS | 14,826 |
| PASS_ROUNDING | 66 |
| CEILING_LOW | 2 |
| entries marked optimal (asterisk) | 32: PASS 27, PASS_ROUNDING 5 |
| entries marked "needs more optimization" | 4,252: CEILING_LOW 1, PASS 4,251 |
| entries with a minimal polynomial | 707. Root check (certify.py, exact rational sign change on [c - 1e-12, c]): root_in_interval 707. Irreducible over Q (check_polys.py): 707 of 707; content 1: 707 of 707 |
| method | decimal_exact 14,834, integer_exact 60 |
| coordinate precision | 0 to 171 decimal digits per entry |

For PASS entries the exact maximum lies in (c - 1e-12, c], so c is the 12-decimal ceiling of the file's maximum.

## PASS_ROUNDING entries (66)

The stated value is an ideal value (a listed polynomial root, or a short exact decimal) and the file is a floating point approximation whose exact maximum exceeds it by at most 1e-14. 49 have a minimal polynomial; the others state 0.2 (4), 0.25 (8), 0.375 (1), 0.4 (3), 0.5 (1). The excess of the file over the stated value ranges from 4.60e-18 to 1.95e-16.

All are listed in exact_value_entries.csv; the CEILING_LOW entries are in ceiling_low_entries.csv.

## CEILING_LOW entries (2)

The stated value is a 12-decimal number, not an ideal value, and the file's exact maximum exceeds it by less than 1e-14, so the correct 12-decimal ceiling is one unit higher.

| dim | n | stated | exact excess of the file |
|---|---|---|---|
| 6 | 531 | 0.786777304640 | 3.178e-17 |
| 12 | 712 | 0.495761907422 | 6.779e-17 |

## Structural checks

- (24,196560): 452,088,000 contact pairs, expected 196560*4600/2 = 452,088,000: agrees
- (23,4600): 2,049,300 contact pairs, expected 4600*891/2 = 2,049,300: agrees
- (64,4224): 4,325,376 contact pairs, expected 4224*2048/2 = 4,325,376: agrees

## Checks on the checker

`selftest.py` output for this run (constructed adversarial cases compared with the independent oracle, then a differential test on 60 table entries and perturbation tests):

```
Part A: constructed cases
simplex_exact                      certify PASS          oracle PASS          expected PASS ok
simplex_claim_too_low              certify FAIL          oracle FAIL          expected FAIL ok
simplex_claim_high                 certify BETTER        oracle BETTER        expected BETTER ok
negative_claim                     certify FAIL          oracle FAIL          expected FAIL ok
negative_claim_ok                  certify PASS          oracle PASS          expected PASS ok
cross_polytope                     certify PASS          oracle PASS          expected PASS ok
cross_claim_negative               certify FAIL          oracle FAIL          expected FAIL ok
long_decimals_exact                certify PASS          oracle PASS          expected PASS ok
exceed_nonideal_5e-15              certify CEILING_LOW   oracle CEILING_LOW   expected CEILING_LOW ok
exceed_nonideal_5e-15_listed       certify PASS          oracle PASS          expected PASS ok
exceed_ideal_0.25_by_5e-15         certify PASS_ROUNDING oracle PASS_ROUNDING expected PASS_ROUNDING ok
exceed_0.25_by_2e-14               certify FAIL          oracle FAIL          expected FAIL ok
exceed_0.25_by_1e-13               certify FAIL          oracle FAIL          expected FAIL ok
duplicate                          certify FAIL          oracle FAIL          expected FAIL ok
scaled_duplicate                   certify FAIL          oracle FAIL          expected FAIL ok
exponent_notation                  certify PASS_ROUNDING oracle PASS_ROUNDING expected PASS_ROUNDING ok
exponent_notation_exact            certify PASS          oracle PASS          expected PASS ok
large_1e200                        certify FAIL          oracle FAIL          expected FAIL ok
tiny_1e-160                        certify FAIL          oracle FAIL          expected FAIL ok
tiny_entries_ok                    certify PASS          oracle PASS          expected PASS ok
overflow_1e400                     certify BADFILE       expected BADFILE ok
row_underflow_1e-300               certify BADFILE       expected BADFILE ok
zero_vector                        certify BADFILE       expected BADFILE ok
one_point                          certify BADFILE       expected BADFILE ok
wrong_shape                        certify BADFILE       expected BADFILE ok

Part B: table files
differential: 60 entries compared, 0 disagreements
perturbation tests on 5,56: moved point -> FAIL, underclaim -> FAIL, overclaim -> BETTER  ok
perturbation tests on 24,57: moved point -> FAIL, underclaim -> FAIL, overclaim -> BETTER  ok
perturbation tests on 9,66: moved point -> FAIL, underclaim -> FAIL, overclaim -> BETTER  ok

ALL TESTS PASS
```

## Defects found and fixed in the certifier

- During development, both found by the data: coordinates in exponent notation were not parsed exactly (now parsed through Decimal and Fraction), and a float overflow in the reporting line for files with more than 150 decimals (replaced by exact rational conversion).
- In an independent review before publication: (1) coordinates near 1e200 overflowed the floating point screen, so a false file could pass (now any coordinate outside 1e-100..1e100 is BADFILE, rows are scaled before squaring, and a non-finite screen is BADFILE); (2) negative stated cosines were compared with the wrong sign (all comparisons are now sign-correct and tested against a square-root-free reference); (3) the 1e-14 rounding tolerance applied to every stated value (it now applies only to ideal values, and other excesses get CEILING_LOW). The table contains no coordinate outside that range and no negative stated cosine, so (1) and (2) could not have affected a verdict here; (3) reclassified the CEILING_LOW entries above, which were previously reported as PASS_ROUNDING.

## Not checked

- Whether any entry is optimal, or could be improved further (see IMPROVEMENTS.md for the optimizer results).
- The kissing number table.
- Rattler counts are informal (1e-9 tolerance in floating point) and play no part in any verdict.
