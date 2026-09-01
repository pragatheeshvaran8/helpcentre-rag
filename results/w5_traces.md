# Week 5 — the 20 traces, as collected

Raw material for the error analysis. Nothing here is grouped or named.
Grading is pass/fail only, by the rule in [`evals/w5_trace.py`](../evals/w5_trace.py).

> **The corpus and the question pool are both invented.** See the README.

## How this sample was drawn

Seed `5`, drawn with `random.Random(seed).sample(ids, 20)` over the pool in file order.

| Traffic kind | In pool | Drawn | Expected at 1/3 |
|---|---|---|---|
| `code_lookup` | 18 | 6 | 6.0 |
| `symptom` | 8 | 2 | 2.7 |
| `policy` | 7 | 2 | 2.3 |
| `procedure` | 6 | 1 | 2.0 |
| `multi_part` | 6 | 3 | 2.0 |
| `noisy` | 5 | 1 | 1.7 |
| `vague` | 4 | 4 | 1.3 |
| `cross_article` | 3 | 0 | 1.0 |
| `out_of_corpus` | 3 | 1 | 1.0 |
| **total** | **60** | **20** | |

Drawn ids, in draw order: `P40`, `P17`, `P48`, `P23`, `P51`, `P45`, `P54`, `P58`, `P42`, `P34`, `P02`, `P30`, `P16`, `P52`, `P04`, `P11`, `P08`, `P24`, `P31`, `P53`

## The machinery, identical for all 20

| Setting | Value |
|---|---|
| `strategy` | `structured` |
| `collection` | `hc_structured` |
| `retrieval_mode` | `hybrid` |
| `k` | `3` |
| `score_threshold` | `0.3` |
| `embedding_model` | `BAAI/bge-small-en-v1.5` |
| `chunk_count` | `34` |
| `rrf_k` | `60` |
| `bm25_k1` | `1.5` |
| `bm25_b` | `0.75` |
| `llm_model` | `poolside/laguna-s-2.1:free` |
| `llm_temperature` | `0.0` |
| `llm_max_tokens` | `320` |
| `prompt_sha` | `9a61e3569211b597` |
| `corpus_sha` | `b5eed06a26dba4e3` |

Every trace carries its own copy of this table, so a trace stays true to the run that produced it even after `config.py` changes.

## Outcome counts

| Outcome | Traces |
|---|---|
| pass | 14 |
| fail | 6 |
| error | 0 |
| **total** | **20** |

---

### T01 — P40 · `multi_part`

**Question:** Two things. What causes ERR-4021, and can I just delete the duplicate usage record?

**Expected:** answer · **Outcome:** PASS · retrieval_ok True · answer_ok True

**What a correct answer must contain**

1. HC-4002: "ERR-4021" + "Never delete the usage record directly"
   - retrieved by: `HC-4002-structured-004`
   - cited by: `HC-4002-structured-004`

**Retrieved (top 3)**

1. `HC-4002-structured-004` (HC-4002 / invoicing) score 0.0328 [dense #1  bm25 #1] **<- meets requirement 1**

   > | Error code | Cause | Fix | |---|---|---| | ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. | | ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that ...

2. `HC-4003-structured-004` (HC-4003 / payments) score 0.0315 [dense #5  bm25 #2]

   > ## Decline and token error codes | Error code | Cause | Fix | |---|---|---| | ERR-5101 | Generic decline returned by the issuing bank with no reason given. | Ask the customer to contact their bank. Do not retry more than once, because repeated attempts can trigger a fraud block. | | ERR-5108 | The saved card token was not re-tokenised during cutover. The token reference points at a BL1 record that no longer resolves. ...

3. `HC-4002-structured-006` (HC-4002 / invoicing) score 0.0306 [dense #7  bm25 #4]

   > | Error code | Cause | Fix | |---|---|---| | ERR-4077 | PDF rendering failed because a line item description contains an unsupported control character. | Edit the line item description to remove the character, then click Regenerate PDF. The invoice itself is valid and payable meanwhile. | | ERR-4090 | The invoice was finalised while the ledger was read-only during Phase 3 cutover. It has no ledger entry. | Do not voi ...

**Answer**

```
ERR-4021 is caused by two line items on the same invoice resolving to the same metered usage record, which happens on accounts that had overlapping legacy subscriptions [HC-4002-structured-004]. You should not delete the usage record directly; instead, void the invoice and run Rebuild Usage for the period [HC-4002-structured-004].
```

**Flags:** none

**Citations:** `HC-4002-structured-004`

**Replay:** `python -m evals.w5_collect --only P40 --force`

---
### T02 — P17 · `code_lookup`

**Question:** ERR-7215 on VAT validation. What has to change?

**Expected:** answer · **Outcome:** FAIL · retrieval_ok True · answer_ok False

**What a correct answer must contain**

1. HC-4005: "ERR-7215" + "legal entity name"
   - retrieved by: `HC-4005-structured-003`
   - cited by: `HC-4005-structured-003`

**Retrieved (top 3)**

1. `HC-4005-structured-003` (HC-4005 / tax) score 0.0328 [dense #1  bm25 #1] **<- meets requirement 1**

   > ## Tax validation error codes | Error code | Cause | Fix | |---|---|---| | ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. | | ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid  ...

2. `HC-4005-structured-004` (HC-4005 / tax) score 0.032 [dense #2  bm25 #3]

   > | Error code | Cause | Fix | |---|---|---| | ERR-7302 | An invoice line item has no tax code and no default could be inferred from the product. | Set a tax code on the product, then rebuild the invoice. Escalate to Tax Ops if the product has no correct code. | | ERR-7310 | A United States exemption certificate has expired. | Ask the customer to upload a current certificate. Tax is charged in the meantime and is not r ...

3. `HC-4005-structured-001` (HC-4005 / tax) score 0.0318 [dense #4  bm25 #2]

   > # Tax IDs, VAT Numbers and Tax Validation Errors ## What changed in tax handling Tax is now calculated per line item instead of once per invoice. An invoice that mixes a taxable subscription with a zero-rated service fee therefore shows two tax lines. The grand total is unchanged, but the breakdown looks different and customers do ask about it. Tax IDs are now validated in real time when they are saved, and again at  ...

**Answer**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: The specific change required to resolve ERR-7215.

Wait, let me re-read the context blocks to verify.

Actually, looking at the context blocks again, I can see that [HC-4005-structured-003] contains information about ERR-7215. Let me provide the correct answer.

For ERR-7215, the customer name on the account does not match the name registered against the VAT ID. The fix is to update the legal entity name on the account to match the registration exactly, then revalidate. [HC-4005-structured-003]
```

**Flags:** refused

**Citations:** `HC-4005-structured-003`

**Replay:** `python -m evals.w5_collect --only P17 --force`

---
### T03 — P48 · `noisy`

**Question:** 5114 insufficent funds? do we retry

**Expected:** answer · **Outcome:** PASS · retrieval_ok True · answer_ok True

**What a correct answer must contain**

1. HC-4003: "ERR-5114" + "dunning schedule will retry"
   - retrieved by: `HC-4003-structured-004`
   - cited by: `HC-4003-structured-004`

**Retrieved (top 3)**

1. `HC-4003-structured-004` (HC-4003 / payments) score 0.0328 [dense #1  bm25 #1] **<- meets requirement 1**

   > ## Decline and token error codes | Error code | Cause | Fix | |---|---|---| | ERR-5101 | Generic decline returned by the issuing bank with no reason given. | Ask the customer to contact their bank. Do not retry more than once, because repeated attempts can trigger a fraud block. | | ERR-5108 | The saved card token was not re-tokenised during cutover. The token reference points at a BL1 record that no longer resolves. ...

2. `HC-4003-structured-005` (HC-4003 / payments) score 0.031 [dense #4  bm25 #5]

   > | Error code | Cause | Fix | |---|---|---| | ERR-5133 | The card is valid but the billing country on the card does not match the account tax country. | Correct the account tax country, or ask the customer to use a card issued in the account country. | | ERR-5140 | The payment method is a wallet token bound to a device that is no longer registered. | Ask the customer to pay once from the original device, or to add a n ...

3. `HC-4004-structured-005` (HC-4004 / subscriptions) score 0.0306 [dense #3  bm25 #8]

   > ## Plan change errors | Error code | Cause | Fix | |---|---|---| | ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued. | | ERR-6210 | The account is on a contract-term plan and cannot self-serve a change. | Route to the account manager. Agents cannot override a contract term ...

**Answer**

```
ERR-5114 means insufficient funds, returned verbatim by the issuing bank, and the fix is to advise the customer to retry after funding the account, with the dunning schedule retrying on its own. [HC-4003-structured-004]
```

**Flags:** none

**Citations:** `HC-4003-structured-004`

**Replay:** `python -m evals.w5_collect --only P48 --force`

---
### T04 — P23 · `symptom`

**Question:** Customer sent a screenshot where the invoice number field is empty. Is payment due?

**Expected:** answer · **Outcome:** FAIL · retrieval_ok True · answer_ok False

**What a correct answer must contain**

1. HC-4002: "still a draft and no payment is due yet"
   - retrieved by: `HC-4002-structured-002`
   - cited by: **nothing**

**Retrieved (top 3)**

1. `HC-4002-structured-002` (HC-4002 / invoicing) score 0.0328 [dense #1  bm25 #1] **<- meets requirement 1**

   > Draft invoices behave differently from the legacy system. A draft has no number at all until it is finalised. If a customer sends a screenshot with an empty invoice number field, the invoice is still a draft and no payment is due yet.

2. `HC-4005-structured-003` (HC-4005 / tax) score 0.0303 [dense #8  bm25 #4]

   > ## Tax validation error codes | Error code | Cause | Fix | |---|---|---| | ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. | | ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid  ...

3. `HC-4006-structured-004` (HC-4006 / api) score 0.0302 [dense #11  bm25 #2]

   > ## Webhook event renames Every event moved to a `billing.` namespace. Old event names are no longer sent at all, so an endpoint listening for the old name goes quiet rather than erroring. This is the single most common reason a customer reports "webhooks stopped working" after migration. | v1 event name | v2 event name | Note | |---|---|---| | `invoice.created` | `billing.invoice.created` | Payload unchanged except f ...

**Answer**

```
No, payment is not due yet. The invoice is still a draft because a draft has no number at all until it is finalised. If a customer sends a screenshot with an empty invoice number field, the invoice is still a draft and no payment is due yet.
```

**Flags:** none

**Citations:** none

**Replay:** `python -m evals.w5_collect --only P23 --force`

---
### T05 — P51 · `vague`

**Question:** invoice error, what do I do?

**Expected:** refuse · **Outcome:** PASS · retrieval_ok None · answer_ok True

**Retrieved (top 3)**

1. `HC-4002-structured-005` (HC-4002 / invoicing) score 0.0315 [dense #1  bm25 #6]

   > | Error code | Cause | Fix | |---|---|---| | ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. | | ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Co ...

2. `HC-4002-structured-006` (HC-4002 / invoicing) score 0.0313 [dense #3  bm25 #5]

   > | Error code | Cause | Fix | |---|---|---| | ERR-4077 | PDF rendering failed because a line item description contains an unsupported control character. | Edit the line item description to remove the character, then click Regenerate PDF. The invoice itself is valid and payable meanwhile. | | ERR-4090 | The invoice was finalised while the ledger was read-only during Phase 3 cutover. It has no ledger entry. | Do not voi ...

3. `HC-4002-structured-007` (HC-4002 / invoicing) score 0.0311 [dense #7  bm25 #2]

   > ## What agents must not do Never void an invoice that a customer has already paid, even if it shows an error code. Voiding a paid invoice creates an orphaned payment that has to be repaired by hand in the ledger. If the invoice is paid and shows an error, the correct route is always a Billing Ops ticket. Never edit tax codes on a historical invoice to "make the total match". The tax code drives the ledger entry, and  ...

**Answer**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: The specific invoice error code or error message you are encountering.
```

**Flags:** refused

**Citations:** none

**Replay:** `python -m evals.w5_collect --only P51 --force`

---
### T06 — P45 · `multi_part`

**Question:** Their integration broke on two things: the pay call and the plan field. What changed in v2 for each?

**Expected:** answer · **Outcome:** PASS · retrieval_ok True · answer_ok True

**What a correct answer must contain**

1. HC-4006: "POST /v2/billing/invoices/{id}/payments" + "settles asynchronously"
   - retrieved by: `HC-4006-structured-002`
   - cited by: `HC-4006-structured-002`
2. HC-4006: "capability-tier name"
   - retrieved by: `HC-4006-structured-002`
   - cited by: `HC-4006-structured-002`

**Retrieved (top 3)**

1. `HC-4006-structured-002` (HC-4006 / api) score 0.0328 [dense #1  bm25 #1] **<- meets requirement 1, 2**

   > ## Endpoint mapping | v1 endpoint | v2 endpoint | Breaking change | |---|---|---| | `GET /v1/invoices` | `GET /v2/billing/invoices` | Pagination is cursor-based. The `page` parameter is ignored and returns the first page silently. | | `GET /v1/invoices/{id}` | `GET /v2/billing/invoices/{id}` | The `number` field now includes a revision suffix on reissued invoices. | | `POST /v1/invoices/{id}/pay` | `POST /v2/billing/ ...

2. `HC-4001-structured-002` (HC-4001 / billing_core) score 0.0315 [dense #5  bm25 #2]

   > Agents should know three things before taking migration tickets. First, every account was migrated, including cancelled accounts that still carry an open balance. Second, invoice history was copied and not moved, so the legacy read-only archive stays available for 18 months after cutover. Third, during the Phase 3 cutover the billing ledger is read-only for four hours. Inside that window a customer can view invoices  ...

3. `HC-4006-structured-004` (HC-4006 / api) score 0.0308 [dense #6  bm25 #4]

   > ## Webhook event renames Every event moved to a `billing.` namespace. Old event names are no longer sent at all, so an endpoint listening for the old name goes quiet rather than erroring. This is the single most common reason a customer reports "webhooks stopped working" after migration. | v1 event name | v2 event name | Note | |---|---|---| | `invoice.created` | `billing.invoice.created` | Payload unchanged except f ...

**Answer**

```
The pay call changed from `POST /v1/invoices/{id}/pay` to `POST /v2/billing/invoices/{id}/payments`, now returning a 202 and settling asynchronously instead of a synchronous 200, which can cause callers to misreport failures [HC-4006-structured-002]. The plan field changed in the `GET /v1/subscriptions` to `GET /v2/billing/subscriptions` mapping, where the `plan` field now returns the new capability-tier name instead of the legacy seat-count name [HC-4006-structured-002].
```

**Flags:** none

**Citations:** `HC-4006-structured-002`

**Replay:** `python -m evals.w5_collect --only P45 --force`

---
### T07 — P54 · `vague`

**Question:** what's the code for this?

**Expected:** refuse · **Outcome:** PASS · retrieval_ok None · answer_ok True

**Retrieved (top 3)**

1. `HC-4002-structured-004` (HC-4002 / invoicing) score 0.031 [dense #6  bm25 #3]

   > | Error code | Cause | Fix | |---|---|---| | ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. | | ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that ...

2. `HC-4004-structured-005` (HC-4004 / subscriptions) score 0.0306 [dense #9  bm25 #2]

   > ## Plan change errors | Error code | Cause | Fix | |---|---|---| | ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued. | | ERR-6210 | The account is on a contract-term plan and cannot self-serve a change. | Route to the account manager. Agents cannot override a contract term ...

3. `HC-4005-structured-003` (HC-4005 / tax) score 0.0305 [dense #11  bm25 #1]

   > ## Tax validation error codes | Error code | Cause | Fix | |---|---|---| | ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. | | ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid  ...

**Answer**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: The specific error scenario or issue the user is asking about.
```

**Flags:** refused

**Citations:** none

**Replay:** `python -m evals.w5_collect --only P54 --force`

---
### T08 — P58 · `out_of_corpus`

**Question:** What is our SLA for a P1 billing incident?

**Expected:** refuse · **Outcome:** PASS · retrieval_ok None · answer_ok True

**Retrieved (top 3)**

1. `HC-4001-structured-002` (HC-4001 / billing_core) score 0.0313 [dense #7  bm25 #1]

   > Agents should know three things before taking migration tickets. First, every account was migrated, including cancelled accounts that still carry an open balance. Second, invoice history was copied and not moved, so the legacy read-only archive stays available for 18 months after cutover. Third, during the Phase 3 cutover the billing ledger is read-only for four hours. Inside that window a customer can view invoices  ...

2. `HC-4006-structured-002` (HC-4006 / api) score 0.0313 [dense #1  bm25 #7]

   > ## Endpoint mapping | v1 endpoint | v2 endpoint | Breaking change | |---|---|---| | `GET /v1/invoices` | `GET /v2/billing/invoices` | Pagination is cursor-based. The `page` parameter is ignored and returns the first page silently. | | `GET /v1/invoices/{id}` | `GET /v2/billing/invoices/{id}` | The `number` field now includes a revision suffix on reissued invoices. | | `POST /v1/invoices/{id}/pay` | `POST /v2/billing/ ...

3. `HC-4002-structured-007` (HC-4002 / invoicing) score 0.0303 [dense #6  bm25 #6]

   > ## What agents must not do Never void an invoice that a customer has already paid, even if it shows an error code. Voiding a paid invoice creates an orphaned payment that has to be repaired by hand in the ledger. If the invoice is paid and shows an error, the correct route is always a Billing Ops ticket. Never edit tax codes on a historical invoice to "make the total match". The tax code drives the ledger entry, and  ...

**Answer**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: SLA for a P1 billing incident
```

**Flags:** refused

**Citations:** none

**Replay:** `python -m evals.w5_collect --only P58 --force`

---
### T09 — P42 · `multi_part`

**Question:** Account badge says MIG-220. What does that mean and what is my action?

**Expected:** answer · **Outcome:** FAIL · retrieval_ok True · answer_ok False

**What a correct answer must contain**

1. HC-4001: "MIG-220" + "Do not reissue invoices yourself"
   - retrieved by: `HC-4001-structured-005`
   - cited by: **nothing**

**Retrieved (top 3)**

1. `HC-4001-structured-005` (HC-4001 / billing_core) score 0.0328 [dense #1  bm25 #1] **<- meets requirement 1**

   > | Code | Badge text | Meaning | Agent action | |---|---|---|---| | MIG-100 | Migrated | The account moved cleanly. Balances match to the cent. | None. Treat the account as normal. | | MIG-140 | Migrated with rounding | Balance differs from BL1 by less than 0.05 in account currency. The difference was written off automatically. | None. Explain the write-off if the customer asks. | | MIG-220 | Partial | Invoices moved  ...

2. `HC-4001-structured-004` (HC-4001 / billing_core) score 0.032 [dense #3  bm25 #2]

   > ## Migration status codes on the account page Every account carries a migration status badge on the Billing tab. The badge is set once by the migration job and is never recalculated, so a stale badge is possible on accounts that were repaired by hand.

3. `HC-4003-structured-005` (HC-4003 / payments) score 0.0301 [dense #4  bm25 #9]

   > | Error code | Cause | Fix | |---|---|---| | ERR-5133 | The card is valid but the billing country on the card does not match the account tax country. | Correct the account tax country, or ask the customer to use a card issued in the account country. | | ERR-5140 | The payment method is a wallet token bound to a device that is no longer registered. | Ask the customer to pay once from the original device, or to add a n ...

**Answer**

```
MIG-220 means the account is marked as Partial, which indicates that invoices were moved successfully but at least one credit note failed to import. Your action is to open a Billing Ops ticket with the account ID and not to reissue invoices yourself. This information comes from the migration status codes table.
```

**Flags:** none

**Citations:** none

**Replay:** `python -m evals.w5_collect --only P42 --force`

---
### T10 — P34 · `procedure`

**Question:** A VAT ID failed VIES validation. Walk me through correcting it.

**Expected:** answer · **Outcome:** FAIL · retrieval_ok True · answer_ok False

**What a correct answer must contain**

1. HC-4005: "ERR-7203" + "Revalidate on the Tax tab"
   - retrieved by: `HC-4005-structured-003`
   - cited by: **nothing**

**Retrieved (top 3)**

1. `HC-4005-structured-003` (HC-4005 / tax) score 0.0328 [dense #1  bm25 #1] **<- meets requirement 1**

   > ## Tax validation error codes | Error code | Cause | Fix | |---|---|---| | ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. | | ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid  ...

2. `HC-4005-structured-001` (HC-4005 / tax) score 0.0323 [dense #2  bm25 #2]

   > # Tax IDs, VAT Numbers and Tax Validation Errors ## What changed in tax handling Tax is now calculated per line item instead of once per invoice. An invoice that mixes a taxable subscription with a zero-rated service fee therefore shows two tax lines. The grand total is unchanged, but the breakdown looks different and customers do ask about it. Tax IDs are now validated in real time when they are saved, and again at  ...

3. `HC-4005-structured-002` (HC-4005 / tax) score 0.0313 [dense #5  bm25 #3]

   > ## Accepted tax ID formats | Region | Field name | Format | Validated against | |---|---|---|---| | European Union | VAT ID | Two-letter country code followed by 8 to 12 characters, no spaces | VIES, in real time | | United Kingdom | VAT registration number | GB followed by 9 or 12 digits | HMRC service | | India | GSTIN | 15 characters, state code first | GSTN portal | | Australia | ABN | 11 digits | ABR lookup | |  ...

**Answer**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: Step-by-step walkthrough for correcting a VAT ID that failed VIES validation.
```

**Flags:** refused

**Citations:** none

**Replay:** `python -m evals.w5_collect --only P34 --force`

---
### T11 — P02 · `code_lookup`

**Question:** Getting ERR-4032 on an invoice line. What is the fix?

**Expected:** answer · **Outcome:** FAIL · retrieval_ok True · answer_ok False

**What a correct answer must contain**

1. HC-4002: "ERR-4032" + "Tax Codes"
   - retrieved by: `HC-4002-structured-004`
   - cited by: **nothing**

**Retrieved (top 3)**

1. `HC-4005-structured-004` (HC-4005 / tax) score 0.0325 [dense #1  bm25 #2]

   > | Error code | Cause | Fix | |---|---|---| | ERR-7302 | An invoice line item has no tax code and no default could be inferred from the product. | Set a tax code on the product, then rebuild the invoice. Escalate to Tax Ops if the product has no correct code. | | ERR-7310 | A United States exemption certificate has expired. | Ask the customer to upload a current certificate. Tax is charged in the meantime and is not r ...

2. `HC-4002-structured-004` (HC-4002 / invoicing) score 0.032 [dense #4  bm25 #1] **<- meets requirement 1**

   > | Error code | Cause | Fix | |---|---|---| | ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. | | ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that ...

3. `HC-4002-structured-005` (HC-4002 / invoicing) score 0.0318 [dense #2  bm25 #4]

   > | Error code | Cause | Fix | |---|---|---| | ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. | | ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Co ...

**Answer**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: The fix for ERR-4032 is not found in the provided context blocks.
```

**Flags:** refused

**Citations:** none

**Replay:** `python -m evals.w5_collect --only P02 --force`

---
### T12 — P30 · `policy`

**Question:** How much account credit can I issue without asking for approval?

**Expected:** answer · **Outcome:** PASS · retrieval_ok True · answer_ok True

**What a correct answer must contain**

1. HC-4003: "250 in account currency"
   - retrieved by: `HC-4003-structured-006`
   - cited by: `HC-4003-structured-006`

**Retrieved (top 3)**

1. `HC-4003-structured-006` (HC-4003 / payments) score 0.0328 [dense #1  bm25 #1] **<- meets requirement 1**

   > ## Refunds Refunds are issued back to the original payment method whenever the original token still resolves. If the token was dropped during migration, the refund cannot be returned to the card and must be issued as account credit instead. Agents can issue account credit up to 250 in account currency without approval.

2. `HC-4002-structured-005` (HC-4002 / invoicing) score 0.0318 [dense #4  bm25 #2]

   > | Error code | Cause | Fix | |---|---|---| | ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. | | ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Co ...

3. `HC-4001-structured-002` (HC-4001 / billing_core) score 0.0313 [dense #2  bm25 #6]

   > Agents should know three things before taking migration tickets. First, every account was migrated, including cancelled accounts that still carry an open balance. Second, invoice history was copied and not moved, so the legacy read-only archive stays available for 18 months after cutover. Third, during the Phase 3 cutover the billing ledger is read-only for four hours. Inside that window a customer can view invoices  ...

**Answer**

```
Agents can issue account credit up to 250 in account currency without approval. [HC-4003-structured-006]
```

**Flags:** none

**Citations:** `HC-4003-structured-006`

**Replay:** `python -m evals.w5_collect --only P30 --force`

---
### T13 — P16 · `code_lookup`

**Question:** Tax ID rejected with ERR-7101. Is any invoice affected?

**Expected:** answer · **Outcome:** PASS · retrieval_ok True · answer_ok True

**What a correct answer must contain**

1. HC-4005: "ERR-7101" + "Tax tab"
   - retrieved by: `HC-4005-structured-003`
   - cited by: `HC-4005-structured-003`

**Retrieved (top 3)**

1. `HC-4005-structured-003` (HC-4005 / tax) score 0.0325 [dense #2  bm25 #1] **<- meets requirement 1**

   > ## Tax validation error codes | Error code | Cause | Fix | |---|---|---| | ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. | | ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid  ...

2. `HC-4005-structured-004` (HC-4005 / tax) score 0.0318 [dense #1  bm25 #5]

   > | Error code | Cause | Fix | |---|---|---| | ERR-7302 | An invoice line item has no tax code and no default could be inferred from the product. | Set a tax code on the product, then rebuild the invoice. Escalate to Tax Ops if the product has no correct code. | | ERR-7310 | A United States exemption certificate has expired. | Ask the customer to upload a current certificate. Tax is charged in the meantime and is not r ...

3. `HC-4005-structured-001` (HC-4005 / tax) score 0.0315 [dense #4  bm25 #3]

   > # Tax IDs, VAT Numbers and Tax Validation Errors ## What changed in tax handling Tax is now calculated per line item instead of once per invoice. An invoice that mixes a taxable subscription with a zero-rated service fee therefore shows two tax lines. The grand total is unchanged, but the breakdown looks different and customers do ask about it. Tax IDs are now validated in real time when they are saved, and again at  ...

**Answer**

```
No invoice is affected yet, because the field rejects the value on save. [HC-4005-structured-003]
```

**Flags:** none

**Citations:** `HC-4005-structured-003`

**Replay:** `python -m evals.w5_collect --only P16 --force`

---
### T14 — P52 · `vague`

**Question:** Customer is angry about their bill. What should I say?

**Expected:** refuse · **Outcome:** PASS · retrieval_ok None · answer_ok True

**Retrieved (top 3)**

1. `HC-4001-structured-006` (HC-4001 / billing_core) score 0.032 [dense #4  bm25 #1]

   > ## What to tell a customer who asks why their invoice looks different Say that the invoice layout changed because tax is now calculated per line item instead of once per invoice. Totals are unchanged. Point them at the invoice PDF, which shows the same grand total as before. Do not promise a re-issue of old invoices in the new layout, because historical invoices are served from the archive and keep their original lay ...

2. `HC-4001-structured-002` (HC-4001 / billing_core) score 0.0301 [dense #7  bm25 #6]

   > Agents should know three things before taking migration tickets. First, every account was migrated, including cancelled accounts that still carry an open balance. Second, invoice history was copied and not moved, so the legacy read-only archive stays available for 18 months after cutover. Third, during the Phase 3 cutover the billing ledger is read-only for four hours. Inside that window a customer can view invoices  ...

3. `HC-4002-structured-007` (HC-4002 / invoicing) score 0.0299 [dense #5  bm25 #9]

   > ## What agents must not do Never void an invoice that a customer has already paid, even if it shows an error code. Voiding a paid invoice creates an orphaned payment that has to be repaired by hand in the ledger. If the invoice is paid and shows an error, the correct route is always a Billing Ops ticket. Never edit tax codes on a historical invoice to "make the total match". The tax code drives the ledger entry, and  ...

**Answer**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: Specific guidance on how to respond to an angry customer about their bill beyond the invoice layout explanation.
```

**Flags:** refused

**Citations:** none

**Replay:** `python -m evals.w5_collect --only P52 --force`

---
### T15 — P04 · `code_lookup`

**Question:** What does ERR-4055 mean and which invoice do I keep?

**Expected:** answer · **Outcome:** PASS · retrieval_ok True · answer_ok True

**What a correct answer must contain**

1. HC-4002: "ERR-4055" + "Void the newer invoice"
   - retrieved by: `HC-4002-structured-005`
   - cited by: `HC-4002-structured-005`

**Retrieved (top 3)**

1. `HC-4002-structured-005` (HC-4002 / invoicing) score 0.0323 [dense #3  bm25 #1] **<- meets requirement 1**

   > | Error code | Cause | Fix | |---|---|---| | ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. | | ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Co ...

2. `HC-4002-structured-006` (HC-4002 / invoicing) score 0.031 [dense #4  bm25 #5]

   > | Error code | Cause | Fix | |---|---|---| | ERR-4077 | PDF rendering failed because a line item description contains an unsupported control character. | Edit the line item description to remove the character, then click Regenerate PDF. The invoice itself is valid and payable meanwhile. | | ERR-4090 | The invoice was finalised while the ledger was read-only during Phase 3 cutover. It has no ledger entry. | Do not voi ...

3. `HC-4005-structured-004` (HC-4005 / tax) score 0.0301 [dense #1  bm25 #13]

   > | Error code | Cause | Fix | |---|---|---| | ERR-7302 | An invoice line item has no tax code and no default could be inferred from the product. | Set a tax code on the product, then rebuild the invoice. Escalate to Tax Ops if the product has no correct code. | | ERR-7310 | A United States exemption certificate has expired. | Ask the customer to upload a current certificate. Tax is charged in the meantime and is not r ...

**Answer**

```
ERR-4055 means the billing period on the invoice overlaps a period that is already invoiced and paid. You should void the newer invoice and keep the paid invoice, which is the correct one. Before closing the ticket, confirm the customer has not been charged twice. [HC-4002-structured-005]
```

**Flags:** none

**Citations:** `HC-4002-structured-005`

**Replay:** `python -m evals.w5_collect --only P04 --force`

---
### T16 — P11 · `code_lookup`

**Question:** Wallet payment failing with ERR-5140. How does the customer pay?

**Expected:** answer · **Outcome:** PASS · retrieval_ok True · answer_ok True

**What a correct answer must contain**

1. HC-4003: "ERR-5140" + "original device"
   - retrieved by: `HC-4003-structured-005`
   - cited by: `HC-4003-structured-005`

**Retrieved (top 3)**

1. `HC-4003-structured-005` (HC-4003 / payments) score 0.0328 [dense #1  bm25 #1] **<- meets requirement 1**

   > | Error code | Cause | Fix | |---|---|---| | ERR-5133 | The card is valid but the billing country on the card does not match the account tax country. | Correct the account tax country, or ask the customer to use a card issued in the account country. | | ERR-5140 | The payment method is a wallet token bound to a device that is no longer registered. | Ask the customer to pay once from the original device, or to add a n ...

2. `HC-4004-structured-005` (HC-4004 / subscriptions) score 0.031 [dense #6  bm25 #3]

   > ## Plan change errors | Error code | Cause | Fix | |---|---|---| | ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued. | | ERR-6210 | The account is on a contract-term plan and cannot self-serve a change. | Route to the account manager. Agents cannot override a contract term ...

3. `HC-4003-structured-004` (HC-4003 / payments) score 0.0308 [dense #4  bm25 #6]

   > ## Decline and token error codes | Error code | Cause | Fix | |---|---|---| | ERR-5101 | Generic decline returned by the issuing bank with no reason given. | Ask the customer to contact their bank. Do not retry more than once, because repeated attempts can trigger a fraud block. | | ERR-5108 | The saved card token was not re-tokenised during cutover. The token reference points at a BL1 record that no longer resolves. ...

**Answer**

```
The customer should pay once from the original device, or add a normal card. [HC-4003-structured-005]
```

**Flags:** none

**Citations:** `HC-4003-structured-005`

**Replay:** `python -m evals.w5_collect --only P11 --force`

---
### T17 — P08 · `code_lookup`

**Question:** Card declined with ERR-5101 and no reason given. What do I tell the customer?

**Expected:** answer · **Outcome:** PASS · retrieval_ok True · answer_ok True

**What a correct answer must contain**

1. HC-4003: "ERR-5101" + "contact their bank"
   - retrieved by: `HC-4003-structured-004`
   - cited by: `HC-4003-structured-004`

**Retrieved (top 3)**

1. `HC-4003-structured-004` (HC-4003 / payments) score 0.0325 [dense #2  bm25 #1] **<- meets requirement 1**

   > ## Decline and token error codes | Error code | Cause | Fix | |---|---|---| | ERR-5101 | Generic decline returned by the issuing bank with no reason given. | Ask the customer to contact their bank. Do not retry more than once, because repeated attempts can trigger a fraud block. | | ERR-5108 | The saved card token was not re-tokenised during cutover. The token reference points at a BL1 record that no longer resolves. ...

2. `HC-4003-structured-005` (HC-4003 / payments) score 0.0323 [dense #1  bm25 #3]

   > | Error code | Cause | Fix | |---|---|---| | ERR-5133 | The card is valid but the billing country on the card does not match the account tax country. | Correct the account tax country, or ask the customer to use a card issued in the account country. | | ERR-5140 | The payment method is a wallet token bound to a device that is no longer registered. | Ask the customer to pay once from the original device, or to add a n ...

3. `HC-4005-structured-004` (HC-4005 / tax) score 0.0306 [dense #4  bm25 #7]

   > | Error code | Cause | Fix | |---|---|---| | ERR-7302 | An invoice line item has no tax code and no default could be inferred from the product. | Set a tax code on the product, then rebuild the invoice. Escalate to Tax Ops if the product has no correct code. | | ERR-7310 | A United States exemption certificate has expired. | Ask the customer to upload a current certificate. Tax is charged in the meantime and is not r ...

**Answer**

```
Tell the customer to contact their bank, and do not retry the payment more than once because repeated attempts can trigger a fraud block. [HC-4003-structured-004]
```

**Flags:** none

**Citations:** `HC-4003-structured-004`

**Replay:** `python -m evals.w5_collect --only P08 --force`

---
### T18 — P24 · `symptom`

**Question:** Customer is upset that their VAT number is suddenly invalid after years of working.

**Expected:** answer · **Outcome:** PASS · retrieval_ok True · answer_ok True

**What a correct answer must contain**

1. HC-4005: "The number really is invalid"
   - retrieved by: `HC-4005-structured-001`
   - cited by: `HC-4005-structured-001`

**Retrieved (top 3)**

1. `HC-4005-structured-001` (HC-4005 / tax) score 0.0328 [dense #1  bm25 #1] **<- meets requirement 1**

   > # Tax IDs, VAT Numbers and Tax Validation Errors ## What changed in tax handling Tax is now calculated per line item instead of once per invoice. An invoice that mixes a taxable subscription with a zero-rated service fee therefore shows two tax lines. The grand total is unchanged, but the breakdown looks different and customers do ask about it. Tax IDs are now validated in real time when they are saved, and again at  ...

2. `HC-4005-structured-003` (HC-4005 / tax) score 0.0323 [dense #2  bm25 #2]

   > ## Tax validation error codes | Error code | Cause | Fix | |---|---|---| | ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. | | ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid  ...

3. `HC-4001-structured-006` (HC-4001 / billing_core) score 0.0305 [dense #6  bm25 #5]

   > ## What to tell a customer who asks why their invoice looks different Say that the invoice layout changed because tax is now calculated per line item instead of once per invoice. Totals are unchanged. Point them at the invoice PDF, which shows the same grand total as before. Do not promise a re-issue of old invoices in the new layout, because historical invoices are served from the archive and keep their original lay ...

**Answer**

```
The customer's VAT number is now being validated in real time when saved and at every invoice finalisation, whereas the legacy system only validated once at signup and never again, so a number that was deregistered years ago now correctly shows as invalid [HC-4005-structured-001]. The number really is invalid, and the old system simply never rechecked it [HC-4005-structured-001]. You should ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab [HC-4005-structured-003].
```

**Flags:** none

**Citations:** `HC-4005-structured-001`, `HC-4005-structured-003`

**Replay:** `python -m evals.w5_collect --only P24 --force`

---
### T19 — P31 · `policy`

**Question:** Customer wants an extension on the v1 API sunset. Can I give them one?

**Expected:** answer · **Outcome:** FAIL · retrieval_ok True · answer_ok False

**What a correct answer must contain**

1. HC-4006: "There is no extension process" + "routed to their account manager"
   - retrieved by: `HC-4006-structured-001`
   - cited by: **nothing**

**Retrieved (top 3)**

1. `HC-4006-structured-001` (HC-4006 / api) score 0.0328 [dense #1  bm25 #1] **<- meets requirement 1**

   > # Billing API and Webhook Changes ## Versioning and sunset The billing API moved from v1 to v2 at cutover. Both versions answer today. The v1 endpoints stop responding on 30 September 2026. After that date a v1 request returns HTTP 410 with no body. There is no extension process, and customers who ask for one should be routed to their account manager rather than told no by an agent. The v2 API is not a superset of v1 ...

2. `HC-4006-structured-004` (HC-4006 / api) score 0.0315 [dense #5  bm25 #2]

   > ## Webhook event renames Every event moved to a `billing.` namespace. Old event names are no longer sent at all, so an endpoint listening for the old name goes quiet rather than erroring. This is the single most common reason a customer reports "webhooks stopped working" after migration. | v1 event name | v2 event name | Note | |---|---|---| | `invoice.created` | `billing.invoice.created` | Payload unchanged except f ...

3. `HC-4001-structured-002` (HC-4001 / billing_core) score 0.0315 [dense #4  bm25 #3]

   > Agents should know three things before taking migration tickets. First, every account was migrated, including cancelled accounts that still carry an open balance. Second, invoice history was copied and not moved, so the legacy read-only archive stays available for 18 months after cutover. Third, during the Phase 3 cutover the billing ledger is read-only for four hours. Inside that window a customer can view invoices  ...

**Answer**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: Whether an extension can be given for the v1 API sunset.
```

**Flags:** refused

**Citations:** none

**Replay:** `python -m evals.w5_collect --only P31 --force`

---
### T20 — P53 · `vague`

**Question:** it's broken since the migration

**Expected:** refuse · **Outcome:** PASS · retrieval_ok None · answer_ok True

**Retrieved (top 3)**

1. `HC-4001-structured-002` (HC-4001 / billing_core) score 0.0323 [dense #1  bm25 #3]

   > Agents should know three things before taking migration tickets. First, every account was migrated, including cancelled accounts that still carry an open balance. Second, invoice history was copied and not moved, so the legacy read-only archive stays available for 18 months after cutover. Third, during the Phase 3 cutover the billing ledger is read-only for four hours. Inside that window a customer can view invoices  ...

2. `HC-4004-structured-005` (HC-4004 / subscriptions) score 0.0318 [dense #2  bm25 #4]

   > ## Plan change errors | Error code | Cause | Fix | |---|---|---| | ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued. | | ERR-6210 | The account is on a contract-term plan and cannot self-serve a change. | Route to the account manager. Agents cannot override a contract term ...

3. `HC-4001-structured-004` (HC-4001 / billing_core) score 0.0308 [dense #4  bm25 #6]

   > ## Migration status codes on the account page Every account carries a migration status badge on the Billing tab. The badge is set once by the migration job and is never recalculated, so a stale badge is possible on accounts that were repaired by hand.

**Answer**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: Specific details about what is broken since the migration and how to fix it.
```

**Flags:** refused

**Citations:** none

**Replay:** `python -m evals.w5_collect --only P53 --force`

---
