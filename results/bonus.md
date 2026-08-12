# Bonus: precision against completeness

**Question:** What does ERR-4032 mean, what is the fix, and what happens to the invoice number after I reissue the invoice?

Three parts. Parts 1 and 2 live in one row of the invoice error table
in HC-4002. Part 3 lives in prose, in a different section of the same
article, several paragraphs from that table.

Run at two retrieval budgets. k=5 is the budget used everywhere else in
this write-up. k=1 is the tight budget, where precision and completeness
pull hardest against each other.

## Summary

| k | strategy | ERR-4032 row retrieved | numbering prose retrieved | parts answered | refused |
|---|---|---|---|---|---|
| 5 | baseline | yes | yes | 3/3 | False |
| 5 | structured | yes | yes | 3/3 | False |
| 1 | baseline | no | no | 0/3 | True |
| 1 | structured | yes | no | 1/3 | True |

## Retrieval budget k=5

### k=5 / baseline - 3/3 parts (meaning=yes, fix=yes, numbering=yes)

```
ERR-4032 means that the invoice line item references a legacy tax code that no longer exists in BL2, because the migration could not map it automatically [HC-4002-baseline-003]. To fix this, you need to re-map the line item to a current tax code under Billing then Tax Codes, and then reissue the invoice [HC-4002-baseline-003]. When an invoice is corrected and reissued, it keeps the original invoice number and gains a revision suffix, such as `EU-2026-0004417-R2` [HC-4002-baseline-001]. The revision suffix increments on every reissue [HC-4002-baseline-001].
```

`has_4032` = chunk holds the ERR-4032 row. `has_prose` = chunk holds the invoice-numbering sentence.

| rank | score | chunk_id | chars | has_4032 | has_prose |
|---|---|---|---|---|---|
| 1 | 0.8169 | `HC-4002-baseline-004` | 965 | no | no |
| 2 | 0.8106 | `HC-4002-baseline-003` | 802 | yes | no |
| 3 | 0.7837 | `HC-4005-baseline-004` | 403 | no | no |
| 4 | 0.7807 | `HC-4003-baseline-004` | 894 | no | no |
| 5 | 0.7758 | `HC-4002-baseline-001` | 806 | no | yes |

### k=5 / structured - 3/3 parts (meaning=yes, fix=yes, numbering=yes)

```
The error code ERR-4032 means that the invoice line item references a legacy tax code that no longer exists in BL2, and the migration could not map it automatically [HC-4002-structured-004]. To fix this, you need to re-map the line item to a current tax code under Billing then Tax Codes, and then reissue the invoice [HC-4002-structured-004]. When an invoice is reissued, it keeps the original invoice number and gains a revision suffix, such as `EU-2026-0004417-R2` [HC-4002-structured-001]. The revision suffix increments on every reissue [HC-4002-structured-001].
```

`has_4032` = chunk holds the ERR-4032 row. `has_prose` = chunk holds the invoice-numbering sentence.

| rank | score | chunk_id | chars | has_4032 | has_prose |
|---|---|---|---|---|---|
| 1 | 0.8106 | `HC-4002-structured-004` | 802 | yes | no |
| 2 | 0.8098 | `HC-4002-structured-005` | 761 | no | no |
| 3 | 0.8018 | `HC-4005-structured-004` | 446 | no | no |
| 4 | 0.7758 | `HC-4002-structured-001` | 806 | no | yes |
| 5 | 0.7726 | `HC-4002-structured-006` | 519 | no | no |


## Retrieval budget k=1

### k=1 / baseline - 0/3 parts (meaning=no, fix=no, numbering=no)

```
REFUSED: The help-centre corpus does not contain this information.
Missing: ERR-4032 meaning, fix, and impact on invoice number after reissuing
```

`has_4032` = chunk holds the ERR-4032 row. `has_prose` = chunk holds the invoice-numbering sentence.

| rank | score | chunk_id | chars | has_4032 | has_prose |
|---|---|---|---|---|---|
| 1 | 0.8169 | `HC-4002-baseline-004` | 965 | no | no |

### k=1 / structured - 1/3 parts (meaning=no, fix=yes, numbering=no)

```
REFUSED: The help-centre corpus does not contain this information.
Missing: what happens to the invoice number after I reissue the invoice
```

`has_4032` = chunk holds the ERR-4032 row. `has_prose` = chunk holds the invoice-numbering sentence.

| rank | score | chunk_id | chars | has_4032 | has_prose |
|---|---|---|---|---|---|
| 1 | 0.8106 | `HC-4002-structured-004` | 802 | yes | no |
