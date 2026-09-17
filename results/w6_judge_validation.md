# Judge validation against hand grading, run `before`

- Cases graded by hand: **20**
- Bar: agreement >= 80% AND Cohen's kappa >= 0.6
- Verdict: **DO NOT TRUST**

## Agreement per dimension

| Dimension | Agreed | Agreement | Kappa | Human yes | Judge yes | Trustworthy |
|---|---|---|---|---|---|---|
| faithful | 20/20 | 100% | 1.0 | 15 | 15 | yes |
| relevant | 19/20 | 95% | **n/a, no variance** | 20 | 19 | **no** |

Kappa matters more than raw agreement here. If most answers are
faithful, a judge that always says yes still scores high agreement.
Kappa subtracts that free credit.

## Where we disagreed

| Case | Dimension | Human | Judge | Judge's reason |
|---|---|---|---|---|
| P46 | relevant | yes | no | Answer describes ERR-4032, but source chunks do not contain that error code. |

## What this licenses

**The judge is not validated.** Its numbers must not be quoted as findings. The assertion checks are unaffected: they are deterministic and need no judge.
