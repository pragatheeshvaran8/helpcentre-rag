# Generation: 3 cited answers, 3 forced refusals

- Strategy searched: `structured`
- Model: `google/gemini-2.5-flash` via OpenRouter, temperature 0.0
- Relevance gate: 0.3 (ON for the cited answers, OFF for the refusals)

## The grounding prompt, verbatim

The refusal is an instruction with a fixed output string. The prompt
never says "use your best judgement" and never says "do your best".

```
You are a support-desk answering assistant for a help-centre corpus.

You answer ONLY from the CONTEXT BLOCKS given to you in the user message.
Each block is labelled with a chunk_id in square brackets, like [HC-4002-structured-007].

RULES. These are absolute. There is no situation in which you may break them.

1. Every single sentence of your answer MUST end with a citation naming the block
   it came from, written exactly as [chunk_id]. A sentence with no citation is a
   rule violation.
2. You may cite ONLY chunk_ids that appear in the CONTEXT BLOCKS below. Never
   invent, guess, abbreviate or reformat a chunk_id.
3. You may state ONLY facts that are written in the CONTEXT BLOCKS. You may not
   use outside knowledge. You may not infer. You may not generalise. You may not
   fill a gap with something that sounds reasonable.
4. If the CONTEXT BLOCKS do not contain the information needed to answer the
   question, you MUST reply with exactly this, and nothing else:

REFUSED: The help-centre corpus does not contain this information.
Missing: <one short line naming what was asked for and not found>

5. A partial answer is a refusal. If you can answer only part of the question,
   you must still refuse using the format in rule 4, and name the missing part.
6. Never apologise, never offer a workaround, never suggest what the answer
   might be, and never tell the user to check elsewhere.

You are measured on refusing correctly, not on being helpful.
```

---

# Part A - 3 answerable questions, cited

## Q1

**Question:** What does ERR-4032 mean on an invoice, and what is the fix?

**Known-correct location:** `HC-4002` -> Invoice error codes -> table row ERR-4032

**Answer, verbatim:**

```
The error code ERR-4032 on an invoice means that the invoice line item references a legacy tax code that no longer exists in BL2, and the migration could not map it automatically [HC-4002-structured-004]. To fix this, you should re-map the line item to a current tax code under Billing then Tax Codes, and then reissue the invoice [HC-4002-structured-004].
```

**Citation check: all citations resolve** (1 distinct chunk_id(s) cited)

| chunk_id | resolves in store | was in context | article | source_file |
|---|---|---|---|---|
| [`HC-4002-structured-004`](chunks_structured.md#hc-4002-structured-004) | yes | yes | HC-4002 | HC-4002-invoice-errors.md |

Full text of every cited chunk, read back from the vector store:

<a id="hc-4002-structured-004"></a>
**`HC-4002-structured-004`**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. |
| ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that had overlapping legacy subscriptions. | Void the invoice, then run Rebuild Usage for the period. Never delete the usage record directly. |
| ERR-4032 | The invoice line item references a legacy tax code that no longer exists in BL2. The migration could not map it automatically. | Re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. |
```

**What retrieval returned:**

| rank | score | chunk_id | article | product_area |
|---|---|---|---|---|
| 1 | 0.8002 | `HC-4005-structured-004` | HC-4005 | tax |
| 2 | 0.8001 | `HC-4002-structured-005` | HC-4002 | invoicing |
| 3 | 0.7929 | `HC-4002-structured-004` | HC-4002 | invoicing |
| 4 | 0.7845 | `HC-4002-structured-006` | HC-4002 | invoicing |
| 5 | 0.7381 | `HC-4002-structured-007` | HC-4002 | invoicing |

---

## Q3

**Question:** A German business customer is getting ERR-7203 on their VAT number. What causes it and how do we clear it?

**Known-correct location:** `HC-4005` -> Tax validation error codes -> table row ERR-7203

**Answer, verbatim:**

```
The ERR-7203 error indicates that the VAT ID failed real-time validation against VIES, meaning the number is well-formed but is not registered or is not valid for cross-border trade [HC-4005-structured-003]. To clear this error, you should ask the customer to confirm the VAT ID with their tax authority, and then click Revalidate on the Tax tab [HC-4005-structured-003].
```

**Citation check: all citations resolve** (1 distinct chunk_id(s) cited)

| chunk_id | resolves in store | was in context | article | source_file |
|---|---|---|---|---|
| [`HC-4005-structured-003`](chunks_structured.md#hc-4005-structured-003) | yes | yes | HC-4005 | HC-4005-tax-and-vat.md |

Full text of every cited chunk, read back from the vector store:

<a id="hc-4005-structured-003"></a>
**`HC-4005-structured-003`**

```
## Tax validation error codes

| Error code | Cause | Fix |
|---|---|---|
| ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. |
| ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid for cross-border trade. | Ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab. |
| ERR-7208 | VIES was unreachable when validation ran. This is a temporary outage on the tax authority side, not a customer problem. | Retry after one hour. Do not remove the customer's VAT ID. Invoices finalise with the last known good status. |
| ERR-7215 | The customer name on the account does not match the name registered against the VAT ID. | Update the legal entity name on the account to match the registration exactly, then revalidate. |
```

**What retrieval returned:**

| rank | score | chunk_id | article | product_area |
|---|---|---|---|---|
| 1 | 0.7845 | `HC-4005-structured-003` | HC-4005 | tax |
| 2 | 0.7477 | `HC-4002-structured-004` | HC-4002 | invoicing |
| 3 | 0.7436 | `HC-4002-structured-005` | HC-4002 | invoicing |
| 4 | 0.7428 | `HC-4005-structured-004` | HC-4005 | tax |
| 5 | 0.7311 | `HC-4005-structured-001` | HC-4005 | tax |

---

## Q4

**Question:** Our webhook listener for invoice.payment_succeeded went silent after the migration. Which v2 event replaced it?

**Known-correct location:** `HC-4006` -> Webhook event renames -> table row invoice.payment_succeeded

**Answer, verbatim:**

```
The `invoice.payment_succeeded` event was replaced by `billing.invoice.paid` in v2. [HC-4006-structured-004] This new event fires once after ledger settlement, not upon processor approval. [HC-4006-structured-004]
```

**Citation check: all citations resolve** (1 distinct chunk_id(s) cited)

| chunk_id | resolves in store | was in context | article | source_file |
|---|---|---|---|---|
| [`HC-4006-structured-004`](chunks_structured.md#hc-4006-structured-004) | yes | yes | HC-4006 | HC-4006-billing-api-and-webhooks.md |

Full text of every cited chunk, read back from the vector store:

<a id="hc-4006-structured-004"></a>
**`HC-4006-structured-004`**

```
## Webhook event renames

Every event moved to a `billing.` namespace. Old event names are no longer sent at
all, so an endpoint listening for the old name goes quiet rather than erroring.
This is the single most common reason a customer reports "webhooks stopped
working" after migration.

| v1 event name | v2 event name | Note |
|---|---|---|
| `invoice.created` | `billing.invoice.created` | Payload unchanged except for the `number` field. |
| `invoice.payment_succeeded` | `billing.invoice.paid` | Renamed and reworded. Fires once, after ledger settlement, not on processor approval. |
| `invoice.payment_failed` | `billing.invoice.payment_failed` | Now includes the dunning `attempt` number. |
| `subscription.updated` | `billing.subscription.updated` | Fires for seat changes too, which v1 did not. |
| `customer.balance_changed` | removed | No replacement. Derive from `billing.ledger.entry_created`. |
```

**What retrieval returned:**

| rank | score | chunk_id | article | product_area |
|---|---|---|---|---|
| 1 | 0.8716 | `HC-4006-structured-004` | HC-4006 | api |
| 2 | 0.7858 | `HC-4006-structured-001` | HC-4006 | api |
| 3 | 0.7476 | `HC-4006-structured-005` | HC-4006 | api |
| 4 | 0.7329 | `HC-4001-structured-002` | HC-4001 | billing_core |
| 5 | 0.7323 | `HC-4006-structured-002` | HC-4006 | api |

---

# Part B - 3 out-of-corpus questions, refused

The gate is disabled for these three. Each model call was given the
retrieved context shown below and still had to refuse. The retrieval
scores prove the corpus had something topically close to offer.

## R1

**Question:** What is the refund SLA? How many business days does a refund take to reach the customer's bank?

**Why the corpus cannot answer it:** HC-4003 explains how refunds are routed (original token, else account credit) but never states any timeline or SLA anywhere in the corpus.

**Verdict: REFUSED** (gate fired: False)

**Model output, verbatim:**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: refund SLA and number of business days for a refund to reach the customer's bank
```

**Context the model was given before refusing:**

| rank | score | chunk_id | article | product_area |
|---|---|---|---|---|
| 1 | 0.6868 | `HC-4003-structured-006` | HC-4003 | payments |
| 2 | 0.6738 | `HC-4004-structured-004` | HC-4004 | subscriptions |
| 3 | 0.6612 | `HC-4003-structured-003` | HC-4003 | payments |
| 4 | 0.6528 | `HC-4001-structured-002` | HC-4001 | billing_core |
| 5 | 0.6494 | `HC-4006-structured-005` | HC-4006 | api |

<details><summary>Full context blocks sent to the model</summary>

```
[HC-4003-structured-006] (article HC-4003, file HC-4003-payment-methods.md, area payments, updated 2026-06-18, score 0.6868)
## Refunds

Refunds are issued back to the original payment method whenever the original token
still resolves. If the token was dropped during migration, the refund cannot be
returned to the card and must be issued as account credit instead. Agents can
issue account credit up to 250 in account currency without approval.

---

[HC-4004-structured-004] (article HC-4004, file HC-4004-subscription-plan-mapping.md, area subscriptions, updated 2026-05-29, score 0.6738)
## Renewal failures

A renewal that cannot be charged does not cancel the subscription. It moves the
subscription through the dunning schedule described in the payments article, then
suspends it. A suspended subscription keeps customer data for 60 days. After 60
days the data is deleted and cannot be restored, even if the customer pays.

Renewal retries and payment retries are the same schedule. Agents sometimes assume
subscriptions have their own retry timer. They do not.

---

[HC-4003-structured-003] (article HC-4003, file HC-4003-payment-methods.md, area payments, updated 2026-06-18, score 0.6612)
## Dunning and retry schedule

When a renewal payment fails, BL2 retries on a fixed schedule and then suspends
the subscription. The schedule replaced the legacy "3 attempts over 10 days" rule
and is not configurable per account.

| Attempt | When | Notification sent | Subscription state |
|---|---|---|---|
| 1 | Immediately on renewal | None | Active |
| 2 | 24 hours after attempt 1 | Email to billing contact | Active |
| 3 | 72 hours after attempt 1 | Email to billing contact and account owner | Active, banner shown in app |
| 4 | 7 days after attempt 1 | Email plus in-app blocking modal | Past due |
| Final | 14 days after attempt 1 | Suspension email | Suspended, data retained 60 days |

---

[HC-4001-structured-002] (article HC-4001, file HC-4001-billing-migration-overview.md, area billing_core, updated 2026-06-02, score 0.6528)
Agents should know three things before taking migration tickets. First, every
account was migrated, including cancelled accounts that still carry an open
balance. Second, invoice history was copied and not moved, so the legacy read-only
archive stays available for 18 months after cutover. Third, during the Phase 3
cutover the billing ledger is read-only for four hours. Inside that window a
customer can view invoices but cannot pay, change a plan, or update a card. If a
customer reports that "the pay button does nothing" and the timestamp falls inside
the freeze, that is expected behaviour and not a fault. Do not raise a payments
incident for it.

The migration did not change prices. It did change invoice numbering, tax
handling, the payment token format, and the billing API surface. Each of those has
its own article. Always confirm which of the four the customer is actually hitting
before you troubleshoot, because the error codes overlap in wording but not in
cause.

---

[HC-4006-structured-005] (article HC-4006, file HC-4006-billing-api-and-webhooks.md, area api, updated 2026-06-20, score 0.6494)
## Webhook delivery and retries

A webhook delivery that does not return a 2xx within 10 seconds is treated as
failed. Failed deliveries are retried with exponential backoff over 24 hours, at
roughly 1 minute, 5 minutes, 30 minutes, 2 hours, 6 hours and 24 hours. After the
final attempt the event is dropped and is not recoverable from the API.

Retries are per endpoint, not per event. If an endpoint is failing, every event
queued for it backs off together. A customer who fixes their endpoint mid-backoff
will receive the queued events on the next scheduled attempt, not immediately.

Signature verification did not change, but the signed payload now includes the
event name. Customers who verify signatures against a stored template must update
that template or every delivery will fail verification.
```

</details>

---

## R2

**Question:** What is the chargeback fee we pass on to the customer?

**Why the corpus cannot answer it:** Chargebacks are not covered by any of the 6 articles. HC-4003 mentions fraud blocks and manual review, which is close enough to tempt a model into inventing a fee.

**Verdict: REFUSED** (gate fired: False)

**Model output, verbatim:**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: chargeback fee
```

**Context the model was given before refusing:**

| rank | score | chunk_id | article | product_area |
|---|---|---|---|---|
| 1 | 0.6823 | `HC-4002-structured-005` | HC-4002 | invoicing |
| 2 | 0.6757 | `HC-4003-structured-006` | HC-4003 | payments |
| 3 | 0.6724 | `HC-4001-structured-002` | HC-4001 | billing_core |
| 4 | 0.6509 | `HC-4005-structured-001` | HC-4005 | tax |
| 5 | 0.6404 | `HC-4004-structured-004` | HC-4004 | subscriptions |

<details><summary>Full context blocks sent to the model</summary>

```
[HC-4002-structured-005] (article HC-4002, file HC-4002-invoice-errors.md, area invoicing, updated 2026-06-11, score 0.6823)
| Error code | Cause | Fix |
|---|---|---|
| ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. |
| ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Confirm the customer has not been charged twice before closing the ticket. |
| ERR-4061 | The invoice currency does not match the account currency. Caused by a mid-cycle currency change in the legacy system. | Escalate to Billing Ops. Agents cannot change invoice currency, and editing the account currency will not fix the existing invoice. |

---

[HC-4003-structured-006] (article HC-4003, file HC-4003-payment-methods.md, area payments, updated 2026-06-18, score 0.6757)
## Refunds

Refunds are issued back to the original payment method whenever the original token
still resolves. If the token was dropped during migration, the refund cannot be
returned to the card and must be issued as account credit instead. Agents can
issue account credit up to 250 in account currency without approval.

---

[HC-4001-structured-002] (article HC-4001, file HC-4001-billing-migration-overview.md, area billing_core, updated 2026-06-02, score 0.6724)
Agents should know three things before taking migration tickets. First, every
account was migrated, including cancelled accounts that still carry an open
balance. Second, invoice history was copied and not moved, so the legacy read-only
archive stays available for 18 months after cutover. Third, during the Phase 3
cutover the billing ledger is read-only for four hours. Inside that window a
customer can view invoices but cannot pay, change a plan, or update a card. If a
customer reports that "the pay button does nothing" and the timestamp falls inside
the freeze, that is expected behaviour and not a fault. Do not raise a payments
incident for it.

The migration did not change prices. It did change invoice numbering, tax
handling, the payment token format, and the billing API surface. Each of those has
its own article. Always confirm which of the four the customer is actually hitting
before you troubleshoot, because the error codes overlap in wording but not in
cause.

---

[HC-4005-structured-001] (article HC-4005, file HC-4005-tax-and-vat.md, area tax, updated 2026-06-05, score 0.6509)
# Tax IDs, VAT Numbers and Tax Validation Errors

## What changed in tax handling

Tax is now calculated per line item instead of once per invoice. An invoice that
mixes a taxable subscription with a zero-rated service fee therefore shows two tax
lines. The grand total is unchanged, but the breakdown looks different and
customers do ask about it.

Tax IDs are now validated in real time when they are saved, and again at every
invoice finalisation. The legacy system validated once at signup and never again.
This is why a customer whose VAT number was deregistered years ago suddenly sees a
validation failure after migration. The number really is invalid. The old system
simply never rechecked it.

Reverse charge is applied automatically for EU business customers with a valid VAT
ID outside our country of establishment. If the VAT ID fails validation, reverse
charge is not applied and local VAT is charged instead. Correcting the VAT ID does
not automatically re-issue past invoices.

---

[HC-4004-structured-004] (article HC-4004, file HC-4004-subscription-plan-mapping.md, area subscriptions, updated 2026-05-29, score 0.6404)
## Renewal failures

A renewal that cannot be charged does not cancel the subscription. It moves the
subscription through the dunning schedule described in the payments article, then
suspends it. A suspended subscription keeps customer data for 60 days. After 60
days the data is deleted and cannot be restored, even if the customer pays.

Renewal retries and payment retries are the same schedule. Agents sometimes assume
subscriptions have their own retry timer. They do not.
```

</details>

---

## R3

**Question:** Which SSO providers does the new billing portal support, and can we enforce SAML for the billing role?

**Why the corpus cannot answer it:** HC-4006 covers API keys and says authentication did not change, but no article mentions SSO, SAML or portal login at all.

**Verdict: REFUSED** (gate fired: False)

**Model output, verbatim:**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: Supported SSO providers and SAML enforcement for the billing role
```

**Context the model was given before refusing:**

| rank | score | chunk_id | article | product_area |
|---|---|---|---|---|
| 1 | 0.6726 | `HC-4001-structured-001` | HC-4001 | billing_core |
| 2 | 0.6629 | `HC-4006-structured-001` | HC-4006 | api |
| 3 | 0.6593 | `HC-4006-structured-002` | HC-4006 | api |
| 4 | 0.6517 | `HC-4004-structured-005` | HC-4004 | subscriptions |
| 5 | 0.6461 | `HC-4001-structured-002` | HC-4001 | billing_core |

<details><summary>Full context blocks sent to the model</summary>

```
[HC-4001-structured-001] (article HC-4001, file HC-4001-billing-migration-overview.md, area billing_core, updated 2026-06-02, score 0.6726)
# Billing Migration Overview and Cutover Timeline

## What changed

On 1 June 2026 we moved every customer account from the legacy billing ledger
(internally "BL1") to the new metered billing ledger ("BL2"). BL2 stores invoices,
credit notes, tax lines and subscription state in one double-entry ledger. The
legacy system kept invoices and subscriptions in two separate databases that were
reconciled once a night. That nightly reconciliation is the reason customers
sometimes saw an invoice before the matching plan change appeared.

---

[HC-4006-structured-001] (article HC-4006, file HC-4006-billing-api-and-webhooks.md, area api, updated 2026-06-20, score 0.6629)
# Billing API and Webhook Changes

## Versioning and sunset

The billing API moved from v1 to v2 at cutover. Both versions answer today. The v1
endpoints stop responding on 30 September 2026. After that date a v1 request
returns HTTP 410 with no body. There is no extension process, and customers who
ask for one should be routed to their account manager rather than told no by an
agent.

The v2 API is not a superset of v1. Three v1 endpoints have no v2 equivalent at
all, because the underlying concept no longer exists. Those are listed below as
"removed". Customers relying on them need a code change, not a URL change.

Authentication did not change. The same API keys work against both versions. Keys
issued before migration were not rotated.

---

[HC-4006-structured-002] (article HC-4006, file HC-4006-billing-api-and-webhooks.md, area api, updated 2026-06-20, score 0.6593)
## Endpoint mapping

| v1 endpoint | v2 endpoint | Breaking change |
|---|---|---|
| `GET /v1/invoices` | `GET /v2/billing/invoices` | Pagination is cursor-based. The `page` parameter is ignored and returns the first page silently. |
| `GET /v1/invoices/{id}` | `GET /v2/billing/invoices/{id}` | The `number` field now includes a revision suffix on reissued invoices. |
| `POST /v1/invoices/{id}/pay` | `POST /v2/billing/invoices/{id}/payments` | Returns 202 and settles asynchronously. Callers that assumed a synchronous 200 will misreport failures. |
| `GET /v1/subscriptions` | `GET /v2/billing/subscriptions` | The `plan` field returns the new capability-tier name, not the legacy seat-count name. |
| `POST /v1/subscriptions/{id}/cancel` | `POST /v2/billing/subscriptions/{id}/cancellations` | Cancellation is now scheduled at period end by default. Pass `immediate=true` for the old behaviour. |

---

[HC-4004-structured-005] (article HC-4004, file HC-4004-subscription-plan-mapping.md, area subscriptions, updated 2026-05-29, score 0.6517)
## Plan change errors

| Error code | Cause | Fix |
|---|---|---|
| ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued. |
| ERR-6210 | The account is on a contract-term plan and cannot self-serve a change. | Route to the account manager. Agents cannot override a contract term. |
| ERR-6244 | A plan change was attempted while an invoice for the current period is still in draft. | Wait for the hourly finalisation run, then retry the change. |
| ERR-6250 | The account is suspended for non-payment. | Collect payment first. Plan changes are blocked while suspended. |

---

[HC-4001-structured-002] (article HC-4001, file HC-4001-billing-migration-overview.md, area billing_core, updated 2026-06-02, score 0.6461)
Agents should know three things before taking migration tickets. First, every
account was migrated, including cancelled accounts that still carry an open
balance. Second, invoice history was copied and not moved, so the legacy read-only
archive stays available for 18 months after cutover. Third, during the Phase 3
cutover the billing ledger is read-only for four hours. Inside that window a
customer can view invoices but cannot pay, change a plan, or update a card. If a
customer reports that "the pay button does nothing" and the timestamp falls inside
the freeze, that is expected behaviour and not a fault. Do not raise a payments
incident for it.

The migration did not change prices. It did change invoice numbering, tax
handling, the payment token format, and the billing API surface. Each of those has
its own article. Always confirm which of the four the customer is actually hitting
before you troubleshoot, because the error codes overlap in wording but not in
cause.
```

</details>

---
