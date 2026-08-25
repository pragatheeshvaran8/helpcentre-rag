# Week 4 failure separation, at k=3

Two kinds of wrong, decided mechanically. See the module docstring in
`evals/w4_failures.py` for the exact rule.

- **A: wrong document fetched** - the answering chunk was not in the top-3. A smarter model cannot help. Fix retrieval.
- **B: right document, wrong answer** - the answering chunk WAS in the top-3 and the answer is still wrong or refused. Fix the prompt or the model.

## Bucket counts

| mode | pass | A: wrong document | B: right document, wrong answer |
|---|---|---|---|
| dense | 22/30 | 2 | 6 |
| hybrid | 23/30 | 0 | 7 |

## Every question, labelled

| Q | code | dense | hybrid |
|---|---|---|---|
| W1 | `MIG-100` | pass | pass |
| W2 | `MIG-140` | pass | pass |
| W3 | `MIG-220` | pass | **B** |
| W4 | `MIG-310` | **B** | pass |
| W5 | `MIG-450` | pass | pass |
| W6 | `ERR-4010` | pass | pass |
| W7 | `ERR-4021` | **A** | pass |
| W8 | `ERR-4032` | pass | pass |
| W9 | `ERR-4044` | pass | pass |
| W10 | `ERR-4055` | pass | pass |
| W11 | `ERR-4061` | pass | pass |
| W12 | `ERR-4077` | pass | pass |
| W13 | `ERR-4090` | **B** | **B** |
| W14 | `ERR-5101` | **B** | **B** |
| W15 | `ERR-5108` | **A** | pass |
| W16 | `ERR-5114` | pass | pass |
| W17 | `ERR-5127` | pass | pass |
| W18 | `ERR-5133` | pass | pass |
| W19 | `ERR-5140` | **B** | pass |
| W20 | `ERR-5199` | **B** | **B** |
| W21 | `ERR-6203` | **B** | pass |
| W22 | `ERR-6210` | pass | pass |
| W23 | `ERR-6244` | pass | pass |
| W24 | `ERR-6250` | pass | **B** |
| W25 | `ERR-7101` | pass | pass |
| W26 | `ERR-7203` | pass | pass |
| W27 | `ERR-7208` | pass | pass |
| W28 | `ERR-7215` | pass | **B** |
| W29 | `ERR-7302` | pass | **B** |
| W30 | `ERR-7310` | pass | pass |

## Evidence for each failure

12 question(s) failed in at least one mode.

---

### W3 - `MIG-220`

**Question:** An account is showing MIG-220. What went wrong and what is the agent action?

**Answer lives in:** `HC-4001` -> Migration status codes -> MIG-220

**Hit requires:** `MIG-220`, `Do not reissue invoices yourself`

#### dense -> pass

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **yes**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4001-structured-005` | HC-4001 | dense | **yes** |
| 2 | `HC-4004-structured-005` | HC-4004 | dense | no |
| 3 | `HC-4002-structured-005` | HC-4002 | dense | no |

Final answer:

```
MIG-220 means the account is in a "Partial" migration state where invoices moved successfully but at least one credit note failed to import. The agent action is to open a Billing Ops ticket with the account ID and not reissue invoices yourself. [HC-4001-structured-005]
```

#### hybrid -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **yes**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4001-structured-005` | HC-4001 | both | **yes** |
| 2 | `HC-4004-structured-005` | HC-4004 | both | no |
| 3 | `HC-4005-structured-003` | HC-4005 | both | no |

Final answer:

```
REFUSED: The help-centre corpus does not contain this information.
Missing: The specific details of what went wrong with MIG-220 and the agent action to take.

Wait, let me re-read the context blocks.

Actually, looking at the context blocks again:

[HC-4001-structured-005] contains information about MIG-220:
- Code: MIG-220
- Badge text: Partial
- Meaning: Invoices moved but at least one credit note failed to import.
- Agent action: Open a Billing Ops ticket with the account ID. Do not reissue invoices yourself.

So I can answer this question.

An account showing MIG-220 means that invoices were moved successfully, but at least one credit note failed to import during the migration process [HC-4001-structured-005]. The agent action for this status is to open a Billing Ops ticket with the account ID, and not to reissue invoices yourself [HC-4001-structured-005].
```

---

### W4 - `MIG-310`

**Question:** A customer badge says MIG-310. How long should we wait before escalating?

**Answer lives in:** `HC-4001` -> Migration status codes -> MIG-310

**Hit requires:** `MIG-310`, `Wait one night`

#### dense -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **yes**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4001-structured-005` | HC-4001 | dense | **yes** |
| 2 | `HC-4004-structured-005` | HC-4004 | dense | no |
| 3 | `HC-4001-structured-002` | HC-4001 | dense | no |

Final answer:

```
REFUSED: The help-centre corpus does not contain this information.
Missing: The specific wait time before escalating a MIG-310 badge.

Wait one night. Escalate only if the badge is unchanged after 48 hours. [HC-4001-structured-005]
```

#### hybrid -> pass

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **yes**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4001-structured-005` | HC-4001 | both | **yes** |
| 2 | `HC-4001-structured-002` | HC-4001 | both | no |
| 3 | `HC-4004-structured-005` | HC-4004 | both | no |

Final answer:

```
A customer badge of MIG-310 means the account was skipped because a payment was in flight at cutover and is retried nightly. You should wait one night before taking further action. Escalate only if the badge is unchanged after 48 hours. [HC-4001-structured-005]
```

---

### W7 - `ERR-4021`

**Question:** What causes ERR-4021 on an invoice, and what is the correct fix?

**Answer lives in:** `HC-4002` -> Invoice error codes -> ERR-4021

**Hit requires:** `ERR-4021`, `Rebuild Usage`

#### dense -> A: wrong document fetched

- retrieval put the answering chunk in top-3: **no**
- model refused: **yes**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4002-structured-006` | HC-4002 | dense | no |
| 2 | `HC-4005-structured-004` | HC-4005 | dense | no |
| 3 | `HC-4002-structured-005` | HC-4002 | dense | no |

Final answer:

```
REFUSED: The help-centre corpus does not contain this information.
Missing: Cause and fix for ERR-4021 on an invoice.
```

#### hybrid -> pass

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **yes**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4005-structured-004` | HC-4005 | both | no |
| 2 | `HC-4002-structured-007` | HC-4002 | both | no |
| 3 | `HC-4002-structured-004` | HC-4002 | both | **yes** |

Final answer:

```
ERR-4021 is caused by two line items on the same invoice resolving to the same metered usage record, which happens on accounts that had overlapping legacy subscriptions [HC-4002-structured-004]. The correct fix is to void the invoice, then run Rebuild Usage for the period, and never delete the usage record directly [HC-4002-structured-004].
```

---

### W13 - `ERR-4090`

**Question:** An invoice has ERR-4090 and no ledger entry. Should we void it?

**Answer lives in:** `HC-4002` -> Invoice error codes -> ERR-4090

**Hit requires:** `ERR-4090`, `backfilled`

#### dense -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4002-structured-006` | HC-4002 | dense | **yes** |
| 2 | `HC-4005-structured-004` | HC-4005 | dense | no |
| 3 | `HC-4002-structured-007` | HC-4002 | dense | no |

Final answer:

```
No, you should not void the invoice. The correct action is to open a Billing Ops ticket quoting the invoice number so the ledger entry can be backfilled.
```

#### hybrid -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4002-structured-006` | HC-4002 | both | **yes** |
| 2 | `HC-4002-structured-007` | HC-4002 | both | no |
| 3 | `HC-4005-structured-004` | HC-4005 | both | no |

Final answer:

```
No, you should not void an invoice with ERR-4090. The fix for ERR-4090 is to open a Billing Ops ticket quoting the invoice number so the ledger entry can be backfilled.
```

---

### W14 - `ERR-5101`

**Question:** A card was declined with ERR-5101. How many times should we retry?

**Answer lives in:** `HC-4003` -> Decline and token error codes -> ERR-5101

**Hit requires:** `ERR-5101`, `fraud block`

#### dense -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **yes**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4003-structured-004` | HC-4003 | dense | **yes** |
| 2 | `HC-4003-structured-005` | HC-4003 | dense | no |
| 3 | `HC-4002-structured-005` | HC-4002 | dense | no |

Final answer:

```
REFUSED: The help-centre corpus does not contain this information.
Missing: The exact number of retries allowed for ERR-5101.

The context states "Do not retry more than once" for ERR-5101, but does not specify the exact number of times to retry [HC-4003-structured-004].
```

#### hybrid -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **yes**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4003-structured-004` | HC-4003 | both | **yes** |
| 2 | `HC-4003-structured-005` | HC-4003 | both | no |
| 3 | `HC-4003-structured-001` | HC-4003 | both | no |

Final answer:

```
REFUSED: The help-centre corpus does not contain this information.
Missing: The exact number of retries allowed for ERR-5101.
```

---

### W15 - `ERR-5108`

**Question:** A renewal failed with ERR-5108. What should the agent ask the customer to do?

**Answer lives in:** `HC-4003` -> Decline and token error codes -> ERR-5108

**Hit requires:** `ERR-5108`, `re-enter the card`

#### dense -> A: wrong document fetched

- retrieval put the answering chunk in top-3: **no**
- model refused: **yes**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4005-structured-004` | HC-4005 | dense | no |
| 2 | `HC-4004-structured-005` | HC-4004 | dense | no |
| 3 | `HC-4002-structured-005` | HC-4002 | dense | no |

Final answer:

```
REFUSED: The help-centre corpus does not contain this information.
Missing: ERR-5108 renewal error cause and fix
```

#### hybrid -> pass

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **yes**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4003-structured-004` | HC-4003 | both | **yes** |
| 2 | `HC-4005-structured-004` | HC-4005 | both | no |
| 3 | `HC-4005-structured-003` | HC-4005 | both | no |

Final answer:

```
The agent should ask the customer to re-enter the card once, as the saved card token was not re-tokenised during cutover and the token reference points at a BL1 record that no longer resolves. [HC-4003-structured-004]
```

---

### W19 - `ERR-5140`

**Question:** A wallet payment is failing with ERR-5140. What are the customer's options?

**Answer lives in:** `HC-4003` -> Decline and token error codes -> ERR-5140

**Hit requires:** `ERR-5140`, `original device`

#### dense -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4003-structured-005` | HC-4003 | dense | **yes** |
| 2 | `HC-4002-structured-005` | HC-4002 | dense | no |
| 3 | `HC-4002-structured-006` | HC-4002 | dense | no |

Final answer:

```
ERR-5140 occurs when the payment method is a wallet token bound to a device that is no longer registered. The customer can either pay once from the original device, or add a normal card.
```

#### hybrid -> pass

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **yes**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4003-structured-005` | HC-4003 | both | **yes** |
| 2 | `HC-4004-structured-005` | HC-4004 | both | no |
| 3 | `HC-4003-structured-004` | HC-4003 | both | no |

Final answer:

```
A wallet payment failing with ERR-5140 means the payment method is a wallet token bound to a device that is no longer registered. The customer's options are to pay once from the original device, or to add a normal card. [HC-4003-structured-005]
```

---

### W20 - `ERR-5199`

**Question:** We got ERR-5199 from the processor. Should the agent retry the charge?

**Answer lives in:** `HC-4003` -> Decline and token error codes -> ERR-5199

**Hit requires:** `ERR-5199`, `Escalate to Payments Ops`

#### dense -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **yes**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4003-structured-005` | HC-4003 | dense | **yes** |
| 2 | `HC-4002-structured-005` | HC-4002 | dense | no |
| 3 | `HC-4004-structured-005` | HC-4004 | dense | no |

Final answer:

```
REFUSED: The help-centre corpus does not contain this information.
Missing: Whether the agent should retry the charge for ERR-5199.

The context block [HC-4003-structured-005] states that for ERR-5199, the fix is to "Do not retry. Escalate to Payments Ops. Retrying while flagged extends the review window." This directly answers the question, but per the rules, I must refuse if I cannot answer the full question. However, the context does provide a clear directive: do not retry. 

Wait, re-reading the rules: "A partial answer is a refusal." But the context fully answers the question. Let me rephrase correctly.

The context block [HC-4003-structured-005] states that for ERR-5199, the fix is to "Do not retry. Escalate to Payments Ops. Retrying while flagged extends the review window." [HC-4003-structured-005]
```

#### hybrid -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **yes**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4003-structured-005` | HC-4003 | both | **yes** |
| 2 | `HC-4003-structured-004` | HC-4003 | both | no |
| 3 | `HC-4004-structured-005` | HC-4004 | both | no |

Final answer:

```
REFUSED: The help-centre corpus does not contain this information.
Missing: Whether the agent should retry the charge after ERR-5199.
```

---

### W21 - `ERR-6203`

**Question:** A plan change was rejected with ERR-6203. What is the cause and the fix?

**Answer lives in:** `HC-4004` -> Plan change errors -> ERR-6203

**Hit requires:** `ERR-6203`, `higher seat count`

#### dense -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **yes**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4004-structured-005` | HC-4004 | dense | **yes** |
| 2 | `HC-4006-structured-002` | HC-4006 | dense | no |
| 3 | `HC-4002-structured-006` | HC-4002 | dense | no |

Final answer:

```
REFUSED: The help-centre corpus does not contain this information.
Missing: The cause and fix for ERR-6203.

I see that the context block [HC-4004-structured-005] contains a table with error codes related to plan changes, including ERR-6203. However, the table only provides the error code, cause, and fix in a structured format, and I need to extract the specific information about ERR-6203 from that table.

Let me re-read the context block carefully.

The context block [HC-4004-structured-005] states:
"ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued."

So, the cause is "The target plan does not include enough seats for the account's current active users." and the fix is "Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued."

I can now provide the answer.

The cause of ERR-6203 is that the target plan does not include enough seats for the account's current active users [HC-4004-structured-005]. The fix is to remove users first, or choose a plan with a higher seat count, and the change is blocked, not queued [HC-4004-structured-005
```

#### hybrid -> pass

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **yes**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4004-structured-005` | HC-4004 | both | **yes** |
| 2 | `HC-4003-structured-004` | HC-4003 | both | no |
| 3 | `HC-4003-structured-005` | HC-4003 | both | no |

Final answer:

```
ERR-6203 means the target plan does not include enough seats for the account's current active users, and the fix is to remove users first or choose a plan with a higher seat count, with the change being blocked rather than queued [HC-4004-structured-005].
```

---

### W24 - `ERR-6250`

**Question:** A plan change is blocked with ERR-6250. What has to happen first?

**Answer lives in:** `HC-4004` -> Plan change errors -> ERR-6250

**Hit requires:** `ERR-6250`, `Collect payment first`

#### dense -> pass

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **yes**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4004-structured-005` | HC-4004 | dense | **yes** |
| 2 | `HC-4001-structured-002` | HC-4001 | dense | no |
| 3 | `HC-4006-structured-002` | HC-4006 | dense | no |

Final answer:

```
Collect payment first, because plan changes are blocked while the account is suspended for non-payment. [HC-4004-structured-005]
```

#### hybrid -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **yes**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4004-structured-005` | HC-4004 | both | **yes** |
| 2 | `HC-4001-structured-002` | HC-4001 | both | no |
| 3 | `HC-4001-structured-005` | HC-4001 | both | no |

Final answer:

```
REFUSED: The help-centre corpus does not contain this information.
Missing: The specific action required to resolve ERR-6250 before a plan change can proceed.

The context blocks provide information about ERR-6250, stating that "The account is suspended for non-payment" and that "Plan changes are blocked while suspended," but they do not explicitly state what specific action must happen first to resolve this suspension. The fix column in the table only mentions "Collect payment first" without detailing the exact steps or process required.
```

---

### W28 - `ERR-7215`

**Question:** A VAT ID check returns ERR-7215. What do we need to change on the account?

**Answer lives in:** `HC-4005` -> Tax validation error codes -> ERR-7215

**Hit requires:** `ERR-7215`, `legal entity name`

#### dense -> pass

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **yes**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4005-structured-003` | HC-4005 | dense | **yes** |
| 2 | `HC-4005-structured-001` | HC-4005 | dense | no |
| 3 | `HC-4002-structured-005` | HC-4002 | dense | no |

Final answer:

```
The account's legal entity name must be updated to match the name registered against the VAT ID exactly, then the VAT ID should be revalidated. [HC-4005-structured-003]
```

#### hybrid -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **yes**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4005-structured-003` | HC-4005 | both | **yes** |
| 2 | `HC-4005-structured-001` | HC-4005 | both | no |
| 3 | `HC-4005-structured-002` | HC-4005 | both | no |

Final answer:

```
REFUSED: The help-centre corpus does not contain this information.
Missing: The specific field name on the account that needs to be updated to resolve ERR-7215.

The context block [HC-4005-structured-003] states that for error code ERR-7215, "The customer name on the account does not match the name registered against the VAT ID" and the fix is to "Update the legal entity name on the account to match the registration exactly, then revalidate." However, it does not specify the exact field name on the account where this change must be made.
```

---

### W29 - `ERR-7302`

**Question:** An invoice line item reports ERR-7302. What is missing and how do we fix it?

**Answer lives in:** `HC-4005` -> Tax validation error codes -> ERR-7302

**Hit requires:** `ERR-7302`, `Set a tax code on the product`

#### dense -> pass

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **yes**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4005-structured-004` | HC-4005 | dense | **yes** |
| 2 | `HC-4002-structured-006` | HC-4002 | dense | no |
| 3 | `HC-4002-structured-004` | HC-4002 | dense | no |

Final answer:

```
ERR-7302 means an invoice line item has no tax code and no default could be inferred from the product.
The fix is to set a tax code on the product, then rebuild the invoice, and to escalate to Tax Ops if the product has no correct code.
[HC-4005-structured-004]
```

#### hybrid -> B: right document, wrong answer

- retrieval put the answering chunk in top-3: **yes**
- model refused: **no**
- answer grounded in a chunk that holds the answer: **no**

What was fetched:

| rank | chunk_id | article | arm | holds the answer |
|---|---|---|---|---|
| 1 | `HC-4005-structured-004` | HC-4005 | both | **yes** |
| 2 | `HC-4002-structured-006` | HC-4002 | both | no |
| 3 | `HC-4002-structured-004` | HC-4002 | both | no |

Final answer:

```
ERR-7302 means an invoice line item has no tax code and no default could be inferred from the product, so a tax code is missing on the line item. To fix it, set a tax code on the product, then rebuild the invoice, and if the product has no correct code, escalate to Tax Ops.
```
