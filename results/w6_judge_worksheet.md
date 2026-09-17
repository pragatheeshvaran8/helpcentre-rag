# Judge validation worksheet, run `before`

20 cases to grade by hand. Fill `faithful_human` and
`relevant_human` in [w6_judge_worksheet.csv](w6_judge_worksheet.csv) with **y** or **n**.

Grade from the answer and the source text below, nothing else. Do not
look at the judge's verdict first. It is deliberately not shown here.

- **faithful** — does the answer say ONLY what the sources say?
- **relevant** — does it answer the question that was actually asked?

---

## P02  (code_lookup)

**Question:** Getting ERR-4032 on an invoice line. What is the fix?

**Answer:**

```
ERR-4032 occurs when an invoice line item references a legacy tax code that no longer exists in BL2 and could not be mapped automatically during migration. The fix is to re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice.
```

**Sources it cited:**

```
NO RESOLVABLE SOURCES WERE CITED.
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P04  (code_lookup)

**Question:** What does ERR-4055 mean and which invoice do I keep?

**Answer:**

```
ERR-4055 means the billing period on the invoice overlaps a period that is already invoiced and paid. You keep the paid invoice, which is the correct one, and you should void the newer invoice. Confirm the customer has not been charged twice before closing the ticket. [HC-4002-structured-005]
```

**Sources it cited:**

```
[HC-4002-structured-005]
| Error code | Cause | Fix |
|---|---|---|
| ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. |
| ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Confirm the customer has not been charged twice before closing the ticket. |
| ERR-4061 | The invoice currency does not match the account currency. Caused by a mid-cycle currency change in the legacy system. | Escalate to Billing Ops. Agents cannot change invoice currency, and editing the account currency will not fix the existing invoice. |
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P06  (code_lookup)

**Question:** Invoice PDF will not render, code is ERR-4077. Is the invoice still payable?

**Answer:**

```
Yes, the invoice is still payable. The ERR-4077 error occurs because a line item description contains an unsupported control character, which prevents PDF rendering, but the invoice itself remains valid and payable meanwhile. To resolve the rendering issue, edit the line item description to remove the character, then click Regenerate PDF.
```

**Sources it cited:**

```
NO RESOLVABLE SOURCES WERE CITED.
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P09  (code_lookup)

**Question:** ERR-5127 on a payment. What is the next step?

**Answer:**

```
Send the customer a fresh payment link from the invoice, because links expire after 30 minutes. [HC-4003-structured-004]
```

**Sources it cited:**

```
[HC-4003-structured-004]
## Decline and token error codes

| Error code | Cause | Fix |
|---|---|---|
| ERR-5101 | Generic decline returned by the issuing bank with no reason given. | Ask the customer to contact their bank. Do not retry more than once, because repeated attempts can trigger a fraud block. |
| ERR-5108 | The saved card token was not re-tokenised during cutover. The token reference points at a BL1 record that no longer resolves. | Ask the customer to re-enter the card once. The new token is created automatically and the failed renewal retries within the hour. |
| ERR-5114 | Insufficient funds. Returned verbatim by the issuer. | Advise the customer to retry after funding the account. The dunning schedule will retry on its own. |
| ERR-5127 | 3-D Secure authentication was required but the session expired before the customer completed it. | Send the customer a fresh payment link from the invoice. Links expire after 30 minutes. |
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P11  (code_lookup)

**Question:** Wallet payment failing with ERR-5140. How does the customer pay?

**Answer:**

```
ERR-5140 means the payment method is a wallet token bound to a device that is no longer registered. The customer should pay once from the original device, or add a normal card. [HC-4003-structured-005]
```

**Sources it cited:**

```
[HC-4003-structured-005]
| Error code | Cause | Fix |
|---|---|---|
| ERR-5133 | The card is valid but the billing country on the card does not match the account tax country. | Correct the account tax country, or ask the customer to use a card issued in the account country. |
| ERR-5140 | The payment method is a wallet token bound to a device that is no longer registered. | Ask the customer to pay once from the original device, or to add a normal card. |
| ERR-5199 | The processor rejected the request because the account is flagged for manual review. | Do not retry. Escalate to Payments Ops. Retrying while flagged extends the review window. |
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P15  (code_lookup)

**Question:** ERR-6244 on a plan change. How long do I wait?

**Answer:**

```
ERR-6244 occurs when a plan change is attempted while an invoice for the current period is still in draft. The fix is to wait for the hourly finalisation run, then retry the change. [HC-4004-structured-005]
```

**Sources it cited:**

```
[HC-4004-structured-005]
## Plan change errors

| Error code | Cause | Fix |
|---|---|---|
| ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued. |
| ERR-6210 | The account is on a contract-term plan and cannot self-serve a change. | Route to the account manager. Agents cannot override a contract term. |
| ERR-6244 | A plan change was attempted while an invoice for the current period is still in draft. | Wait for the hourly finalisation run, then retry the change. |
| ERR-6250 | The account is suspended for non-payment. | Collect payment first. Plan changes are blocked while suspended. |
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P16  (code_lookup)

**Question:** Tax ID rejected with ERR-7101. Is any invoice affected?

**Answer:**

```
No invoice is affected yet. The ERR-7101 error means the tax ID format is wrong for the selected country, and the field rejects the value on save before any invoice is impacted. Correct the format on the Tax tab to resolve it. [HC-4005-structured-003]
```

**Sources it cited:**

```
[HC-4005-structured-003]
## Tax validation error codes

| Error code | Cause | Fix |
|---|---|---|
| ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. |
| ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid for cross-border trade. | Ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab. |
| ERR-7208 | VIES was unreachable when validation ran. This is a temporary outage on the tax authority side, not a customer problem. | Retry after one hour. Do not remove the customer's VAT ID. Invoices finalise with the last known good status. |
| ERR-7215 | The customer name on the account does not match the name registered against the VAT ID. | Update the legal entity name on the account to match the registration exactly, then revalidate. |
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P18  (code_lookup)

**Question:** US customer getting ERR-7310. What do I ask them for?

**Answer:**

```
Ask the customer to upload a current United States exemption certificate. [HC-4005-structured-004]
```

**Sources it cited:**

```
[HC-4005-structured-004]
| Error code | Cause | Fix |
|---|---|---|
| ERR-7302 | An invoice line item has no tax code and no default could be inferred from the product. | Set a tax code on the product, then rebuild the invoice. Escalate to Tax Ops if the product has no correct code. |
| ERR-7310 | A United States exemption certificate has expired. | Ask the customer to upload a current certificate. Tax is charged in the meantime and is not refundable once remitted. |
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P22  (symptom)

**Question:** Customer says invoice numbers have gaps and thinks an invoice is missing.

**Answer:**

```
The invoice numbering system changed after the billing migration, and gaps in the sequence are expected behavior rather than a sign of a missing invoice.

Invoice numbers are no longer sequential per account. BL2 issues numbers from a single global sequence with a regional prefix, for example `EU-2026-0004417`. Customers who reconcile by number will see gaps in their own sequence, and that is expected and is not a sign of a missing invoice.

When an invoice is corrected, BL2 does not allocate a new number. A reissued invoice keeps the original invoice number and gains a revision suffix, such as `EU-2026-0004417-R2`, so reissues do not fill gaps in the numbering sequence either.

If the customer is concerned about a specific invoice, they should check whether the invoice they are looking for has been reissued with a revision suffix, since the highest revision is the valid document and lower revisions should be ignored.

REFUSED: The help-centre corpus does not contain this information.
Missing: Confirmation of a specific missing invoice number or additional troubleshooting steps beyond explaining the numbering change.
```

**Sources it cited:**

```
NO RESOLVABLE SOURCES WERE CITED.
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P25  (symptom)

**Question:** Customer says a tiny proration charge on their upgrade looks wrong.

**Answer:**

```
Proration is now calculated by the second rather than by the day, so an upgrade made at 14:30 is charged from 14:30, not from midnight, which makes small proration amounts look unfamiliar [HC-4004-structured-003]. These small amounts are not errors, even though customers occasionally report them as such [HC-4004-structured-003].
```

**Sources it cited:**

```
[HC-4004-structured-003]
## Proration

Proration is now calculated by the second rather than by the day. An upgrade made
at 14:30 is charged from 14:30, not from midnight. This makes small proration
amounts look unfamiliar, and customers occasionally report them as errors. They
are not errors.

Downgrades never prorate. A downgrade takes effect at the next renewal and the
customer keeps the higher tier until then. The legacy system issued a partial
credit note on downgrade. BL2 does not, and no credit is due.

Seat reductions follow the downgrade rule. Removing a seat mid-term frees the
licence immediately but does not reduce the current invoice.
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P26  (symptom)

**Question:** Customer got an extra authentication prompt paying with Apple Pay after migration. Is something wrong?

**Answer:**

```
No, something is not wrong. Wallet payment methods behave differently, and Apple Pay tokens are device-bound and were re-issued automatically on first use. A customer using a wallet may see one extra authentication prompt after migration, and that prompt is expected and appears once per device. [HC-4003-structured-002]
```

**Sources it cited:**

```
[HC-4003-structured-002]
Wallet payment methods behave differently. Apple Pay and Google Pay tokens are
device-bound and were re-issued automatically on first use. A customer using a
wallet may see one extra authentication prompt after migration. That prompt is
expected and appears once per device.
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P30  (policy)

**Question:** How much account credit can I issue without asking for approval?

**Answer:**

```
Agents can issue account credit up to 250 in account currency without approval. [HC-4003-structured-006]
```

**Sources it cited:**

```
[HC-4003-structured-006]
## Refunds

Refunds are issued back to the original payment method whenever the original token
still resolves. If the token was dropped during migration, the refund cannot be
returned to the card and must be issued as account credit instead. Agents can
issue account credit up to 250 in account currency without approval.
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P32  (policy)

**Question:** Customer removed a seat mid-term. Does the current invoice go down?

**Answer:**

```
No, the current invoice does not go down when a seat is removed mid-term. Seat reductions follow the downgrade rule, which means removing a seat frees the licence immediately but does not reduce the current invoice. [HC-4004-structured-003]
```

**Sources it cited:**

```
[HC-4004-structured-003]
## Proration

Proration is now calculated by the second rather than by the day. An upgrade made
at 14:30 is charged from 14:30, not from midnight. This makes small proration
amounts look unfamiliar, and customers occasionally report them as errors. They
are not errors.

Downgrades never prorate. A downgrade takes effect at the next renewal and the
customer keeps the higher tier until then. The legacy system issued a partial
credit note on downgrade. BL2 does not, and no credit is due.

Seat reductions follow the downgrade rule. Removing a seat mid-term frees the
licence immediately but does not reduce the current invoice.
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P35  (procedure)

**Question:** I need to reissue a corrected invoice. Does it get a new invoice number?

**Answer:**

```
No, a corrected invoice does not get a new invoice number. When an invoice is corrected, BL2 keeps the original invoice number and adds a revision suffix, such as `EU-2026-0004417-R2`, with the suffix incrementing on every reissue. Accounting teams should treat the highest revision as the valid document and ignore lower revisions.
```

**Sources it cited:**

```
NO RESOLVABLE SOURCES WERE CITED.
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P45  (multi_part)

**Question:** Their integration broke on two things: the pay call and the plan field. What changed in v2 for each?

**Answer:**

```
The pay call changed from `POST /v1/invoices/{id}/pay` to `POST /v2/billing/invoices/{id}/payments`, and it now returns a 202 response and settles asynchronously instead of synchronously returning a 200, which means callers that assumed a synchronous 200 will misreport failures [HC-4006-structured-002].

The plan field changed in the `GET /v2/billing/subscriptions` endpoint, where the `plan` field now returns the new capability-tier name instead of the legacy seat-count name [HC-4006-structured-002].
```

**Sources it cited:**

```
[HC-4006-structured-002]
## Endpoint mapping

| v1 endpoint | v2 endpoint | Breaking change |
|---|---|---|
| `GET /v1/invoices` | `GET /v2/billing/invoices` | Pagination is cursor-based. The `page` parameter is ignored and returns the first page silently. |
| `GET /v1/invoices/{id}` | `GET /v2/billing/invoices/{id}` | The `number` field now includes a revision suffix on reissued invoices. |
| `POST /v1/invoices/{id}/pay` | `POST /v2/billing/invoices/{id}/payments` | Returns 202 and settles asynchronously. Callers that assumed a synchronous 200 will misreport failures. |
| `GET /v1/subscriptions` | `GET /v2/billing/subscriptions` | The `plan` field returns the new capability-tier name, not the legacy seat-count name. |
| `POST /v1/subscriptions/{id}/cancel` | `POST /v2/billing/subscriptions/{id}/cancellations` | Cancellation is now scheduled at period end by default. Pass `immediate=true` for the old behaviour. |
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P46  (noisy)

**Question:** err 4032 pls

**Answer:**

```
ERR-4032 occurs when an invoice line item references a legacy tax code that no longer exists in BL2 and the migration could not map it automatically. The fix is to re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. [HC-4002-structured-005]
```

**Sources it cited:**

```
[HC-4002-structured-005]
| Error code | Cause | Fix |
|---|---|---|
| ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. |
| ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Confirm the customer has not been charged twice before closing the ticket. |
| ERR-4061 | The invoice currency does not match the account currency. Caused by a mid-cycle currency change in the legacy system. | Escalate to Billing Ops. Agents cannot change invoice currency, and editing the account currency will not fix the existing invoice. |
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P48  (noisy)

**Question:** 5114 insufficent funds? do we retry

**Answer:**

```
ERR-5114 indicates insufficient funds, and the dunning schedule will retry on its own, so no manual retry is required. [HC-4003-structured-004]
```

**Sources it cited:**

```
[HC-4003-structured-004]
## Decline and token error codes

| Error code | Cause | Fix |
|---|---|---|
| ERR-5101 | Generic decline returned by the issuing bank with no reason given. | Ask the customer to contact their bank. Do not retry more than once, because repeated attempts can trigger a fraud block. |
| ERR-5108 | The saved card token was not re-tokenised during cutover. The token reference points at a BL1 record that no longer resolves. | Ask the customer to re-enter the card once. The new token is created automatically and the failed renewal retries within the hour. |
| ERR-5114 | Insufficient funds. Returned verbatim by the issuer. | Advise the customer to retry after funding the account. The dunning schedule will retry on its own. |
| ERR-5127 | 3-D Secure authentication was required but the session expired before the customer completed it. | Send the customer a fresh payment link from the invoice. Links expire after 30 minutes. |
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P49  (noisy)

**Question:** invocie error 4010 addres missing

**Answer:**

```
ERR-4010 occurs when the invoice references a customer address that failed validation during import, most often due to a missing postal code. To fix it, open Billing then Customer Details, complete the address, then click Revalidate, and the invoice will finalise on the next hourly run. [HC-4002-structured-004]
```

**Sources it cited:**

```
[HC-4002-structured-004]
| Error code | Cause | Fix |
|---|---|---|
| ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. |
| ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that had overlapping legacy subscriptions. | Void the invoice, then run Rebuild Usage for the period. Never delete the usage record directly. |
| ERR-4032 | The invoice line item references a legacy tax code that no longer exists in BL2. The migration could not map it automatically. | Re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. |
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P50  (noisy)

**Question:** gstin format india?

**Answer:**

```
GSTIN for India is 15 characters with the state code first, and it is validated against the GSTN portal. [HC-4005-structured-002]
```

**Sources it cited:**

```
[HC-4005-structured-002]
## Accepted tax ID formats

| Region | Field name | Format | Validated against |
|---|---|---|---|
| European Union | VAT ID | Two-letter country code followed by 8 to 12 characters, no spaces | VIES, in real time |
| United Kingdom | VAT registration number | GB followed by 9 or 12 digits | HMRC service |
| India | GSTIN | 15 characters, state code first | GSTN portal |
| Australia | ABN | 11 digits | ABR lookup |
| United States | Tax exemption certificate | Uploaded document, no automatic format check | Manual review by Tax Ops |
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |

## P57  (cross_article)

**Question:** An invoice failed with ERR-4032 and the customer also has ERR-7203 on their VAT ID. Are the two related?

**Answer:**

```
ERR-4032 occurs when an invoice line item references a legacy tax code that no longer exists in BL2 and could not be mapped automatically, and the fix is to re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice [HC-4002-structured-004].

ERR-7203 occurs when the VAT ID failed real-time validation against VIES because the number is well-formed but is not registered or is not valid for cross-border trade, and the fix is to ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab [HC-4005-structured-003].

The help-centre corpus does not state that ERR-4032 and ERR-7203 are related to each other.

REFUSED: The help-centre corpus does not contain this information.
Missing: Whether ERR-4032 and ERR-7203 are related.
```

**Sources it cited:**

```
[HC-4002-structured-004]
| Error code | Cause | Fix |
|---|---|---|
| ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. |
| ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that had overlapping legacy subscriptions. | Void the invoice, then run Rebuild Usage for the period. Never delete the usage record directly. |
| ERR-4032 | The invoice line item references a legacy tax code that no longer exists in BL2. The migration could not map it automatically. | Re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. |

---

[HC-4005-structured-003]
## Tax validation error codes

| Error code | Cause | Fix |
|---|---|---|
| ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. |
| ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid for cross-border trade. | Ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab. |
| ERR-7208 | VIES was unreachable when validation ran. This is a temporary outage on the tax authority side, not a customer problem. | Retry after one hour. Do not remove the customer's VAT ID. Invoices finalise with the last known good status. |
| ERR-7215 | The customer name on the account does not match the name registered against the VAT ID. | Update the legal entity name on the account to match the registration exactly, then revalidate. |
```

| faithful (y/n) | relevant (y/n) | note |
|---|---|---|
|  |  |  |
