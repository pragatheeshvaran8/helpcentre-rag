# Search-only dump: all 8 questions, both strategies, top-5 each

No LLM was called to produce this file. Scores are cosine relevance
(1 - cosine distance); higher is better.

Legend: `HIT` = right article AND chunk contains the full answer.
`hdr` = chunk retains a markdown table header row.
`ORPHAN` = chunk carries table data rows but lost its header row.

---

## Q1 (table_row)

**Question:** What does ERR-4032 mean on an invoice, and what is the fix?

**Known-correct location:** `HC-4002` -> Invoice error codes -> table row ERR-4032

**Known answer:** The invoice line item references a legacy tax code that no longer exists in BL2, and the migration could not map it automatically. Fix: re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice.

**Hit requires the chunk to contain:** `ERR-4032`, `reissue the invoice`

### Q1 / baseline -> HIT at rank 2

**1. score 0.8047 - `HC-4002-baseline-004` - HC-4002 / invoicing - 965 chars [right-article-wrong-chunk, ORPHAN]**

```
| ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. |
| ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Confirm the customer has not been charged twice before closing the ticket. |
| ERR-4061 | The invoice currency does not match the account currency. Caused by a mid-cycle currency change in the legacy system. | Escalate to Billing Ops. Agents cannot change invoice currency, and editing the account currency will not fix the existing invoice. |
| ERR-4077 | PDF rendering failed because a line item description contains an unsupported control character. | Edit the line item description to remove the character, then click Regenerate PDF. The invoice itself is valid and payable meanwhile. |
```

**2. score 0.7929 - `HC-4002-baseline-003` - HC-4002 / invoicing - 802 chars [HIT, hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. |
| ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that had overlapping legacy subscriptions. | Void the invoice, then run Rebuild Usage for the period. Never delete the usage record directly. |
| ERR-4032 | The invoice line item references a legacy tax code that no longer exists in BL2. The migration could not map it automatically. | Re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. |
```

**3. score 0.7798 - `HC-4005-baseline-004` - HC-4005 / tax - 403 chars [ORPHAN]**

```
| ERR-7302 | An invoice line item has no tax code and no default could be inferred from the product. | Set a tax code on the product, then rebuild the invoice. Escalate to Tax Ops if the product has no correct code. |
| ERR-7310 | A United States exemption certificate has expired. | Ask the customer to upload a current certificate. Tax is charged in the meantime and is not refundable once remitted. |
```

**4. score 0.7436 - `HC-4005-baseline-003` - HC-4005 / tax - 968 chars [hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. |
| ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid for cross-border trade. | Ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab. |
| ERR-7208 | VIES was unreachable when validation ran. This is a temporary outage on the tax authority side, not a customer problem. | Retry after one hour. Do not remove the customer's VAT ID. Invoices finalise with the last known good status. |
| ERR-7215 | The customer name on the account does not match the name registered against the VAT ID. | Update the legal entity name on the account to match the registration exactly, then revalidate. |
```

**5. score 0.7409 - `HC-4002-baseline-005` - HC-4002 / invoicing - 229 chars [right-article-wrong-chunk, ORPHAN]**

```
| ERR-4090 | The invoice was finalised while the ledger was read-only during Phase 3 cutover. It has no ledger entry. | Do not void it. Open a Billing Ops ticket quoting the invoice number so the ledger entry can be backfilled. |
```

### Q1 / structured -> HIT at rank 3

**1. score 0.8002 - `HC-4005-structured-004` - HC-4005 / tax - 446 chars [hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-7302 | An invoice line item has no tax code and no default could be inferred from the product. | Set a tax code on the product, then rebuild the invoice. Escalate to Tax Ops if the product has no correct code. |
| ERR-7310 | A United States exemption certificate has expired. | Ask the customer to upload a current certificate. Tax is charged in the meantime and is not refundable once remitted. |
```

**2. score 0.8001 - `HC-4002-structured-005` - HC-4002 / invoicing - 761 chars [right-article-wrong-chunk, hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. |
| ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Confirm the customer has not been charged twice before closing the ticket. |
| ERR-4061 | The invoice currency does not match the account currency. Caused by a mid-cycle currency change in the legacy system. | Escalate to Billing Ops. Agents cannot change invoice currency, and editing the account currency will not fix the existing invoice. |
```

**3. score 0.7929 - `HC-4002-structured-004` - HC-4002 / invoicing - 802 chars [HIT, hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. |
| ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that had overlapping legacy subscriptions. | Void the invoice, then run Rebuild Usage for the period. Never delete the usage record directly. |
| ERR-4032 | The invoice line item references a legacy tax code that no longer exists in BL2. The migration could not map it automatically. | Re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. |
```

**4. score 0.7845 - `HC-4002-structured-006` - HC-4002 / invoicing - 519 chars [right-article-wrong-chunk, hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4077 | PDF rendering failed because a line item description contains an unsupported control character. | Edit the line item description to remove the character, then click Regenerate PDF. The invoice itself is valid and payable meanwhile. |
| ERR-4090 | The invoice was finalised while the ledger was read-only during Phase 3 cutover. It has no ledger entry. | Do not void it. Open a Billing Ops ticket quoting the invoice number so the ledger entry can be backfilled. |
```

**5. score 0.7381 - `HC-4002-structured-007` - HC-4002 / invoicing - 498 chars [right-article-wrong-chunk]**

```
## What agents must not do

Never void an invoice that a customer has already paid, even if it shows an error
code. Voiding a paid invoice creates an orphaned payment that has to be repaired
by hand in the ledger. If the invoice is paid and shows an error, the correct
route is always a Billing Ops ticket.

Never edit tax codes on a historical invoice to "make the total match". The tax
code drives the ledger entry, and changing it after payment causes the account to
drift out of reconciliation.
```

---

## Q2 (table_row)

**Question:** A renewal failed with a token error because the saved card was not re-tokenised at cutover. Which error code is that, and what should the agent ask the customer to do?

**Known-correct location:** `HC-4003` -> Decline and token error codes -> table row ERR-5108

**Known answer:** ERR-5108. The saved card token was not re-tokenised during cutover. Ask the customer to re-enter the card once; the new token is created automatically and the failed renewal retries within the hour.

**Hit requires the chunk to contain:** `ERR-5108`, `re-enter the card`

### Q2 / baseline -> HIT at rank 1

**1. score 0.8752 - `HC-4003-baseline-004` - HC-4003 / payments - 894 chars [HIT, hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-5101 | Generic decline returned by the issuing bank with no reason given. | Ask the customer to contact their bank. Do not retry more than once, because repeated attempts can trigger a fraud block. |
| ERR-5108 | The saved card token was not re-tokenised during cutover. The token reference points at a BL1 record that no longer resolves. | Ask the customer to re-enter the card once. The new token is created automatically and the failed renewal retries within the hour. |
| ERR-5114 | Insufficient funds. Returned verbatim by the issuer. | Advise the customer to retry after funding the account. The dunning schedule will retry on its own. |
| ERR-5127 | 3-D Secure authentication was required but the session expired before the customer completed it. | Send the customer a fresh payment link from the invoice. Links expire after 30 minutes. |
```

**2. score 0.8175 - `HC-4003-baseline-001` - HC-4003 / payments - 786 chars [right-article-wrong-chunk]**

```
# Payment Methods, Card Tokens and Decline Codes

## What happened to stored cards

Every stored card was re-tokenised during cutover. The card number itself never
moved, because we never held it. What moved was the token issued by the payment
processor. Customers do not need to do anything if their card was re-tokenised
successfully, and most were.

Two groups of cards were not migrated. Cards that had not been used for more than
24 months were dropped, because the processor will not re-tokenise a dormant card.
Those customers must add a payment method again before their next renewal.
Customers whose card had already expired were also dropped, for the same reason.
In both cases the account shows no default payment method, and renewal will fail
silently until a card is added.
```

**3. score 0.8029 - `HC-4003-baseline-003` - HC-4003 / payments - 32 chars [right-article-wrong-chunk]**

```
## Decline and token error codes
```

**4. score 0.7728 - `HC-4004-baseline-004` - HC-4004 / subscriptions - 852 chars [hdr]**

```
Renewal retries and payment retries are the same schedule. Agents sometimes assume
subscriptions have their own retry timer. They do not.

## Plan change errors

| Error code | Cause | Fix |
|---|---|---|
| ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued. |
| ERR-6210 | The account is on a contract-term plan and cannot self-serve a change. | Route to the account manager. Agents cannot override a contract term. |
| ERR-6244 | A plan change was attempted while an invoice for the current period is still in draft. | Wait for the hourly finalisation run, then retry the change. |
| ERR-6250 | The account is suspended for non-payment. | Collect payment first. Plan changes are blocked while suspended. |
```

**5. score 0.7645 - `HC-4005-baseline-003` - HC-4005 / tax - 968 chars [hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. |
| ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid for cross-border trade. | Ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab. |
| ERR-7208 | VIES was unreachable when validation ran. This is a temporary outage on the tax authority side, not a customer problem. | Retry after one hour. Do not remove the customer's VAT ID. Invoices finalise with the last known good status. |
| ERR-7215 | The customer name on the account does not match the name registered against the VAT ID. | Update the legal entity name on the account to match the registration exactly, then revalidate. |
```

### Q2 / structured -> HIT at rank 1

**1. score 0.8825 - `HC-4003-structured-004` - HC-4003 / payments - 928 chars [HIT, hdr]**

```
## Decline and token error codes

| Error code | Cause | Fix |
|---|---|---|
| ERR-5101 | Generic decline returned by the issuing bank with no reason given. | Ask the customer to contact their bank. Do not retry more than once, because repeated attempts can trigger a fraud block. |
| ERR-5108 | The saved card token was not re-tokenised during cutover. The token reference points at a BL1 record that no longer resolves. | Ask the customer to re-enter the card once. The new token is created automatically and the failed renewal retries within the hour. |
| ERR-5114 | Insufficient funds. Returned verbatim by the issuer. | Advise the customer to retry after funding the account. The dunning schedule will retry on its own. |
| ERR-5127 | 3-D Secure authentication was required but the session expired before the customer completed it. | Send the customer a fresh payment link from the invoice. Links expire after 30 minutes. |
```

**2. score 0.8175 - `HC-4003-structured-001` - HC-4003 / payments - 786 chars [right-article-wrong-chunk]**

```
# Payment Methods, Card Tokens and Decline Codes

## What happened to stored cards

Every stored card was re-tokenised during cutover. The card number itself never
moved, because we never held it. What moved was the token issued by the payment
processor. Customers do not need to do anything if their card was re-tokenised
successfully, and most were.

Two groups of cards were not migrated. Cards that had not been used for more than
24 months were dropped, because the processor will not re-tokenise a dormant card.
Those customers must add a payment method again before their next renewal.
Customers whose card had already expired were also dropped, for the same reason.
In both cases the account shows no default payment method, and renewal will fail
silently until a card is added.
```

**3. score 0.7815 - `HC-4002-structured-005` - HC-4002 / invoicing - 761 chars [hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. |
| ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Confirm the customer has not been charged twice before closing the ticket. |
| ERR-4061 | The invoice currency does not match the account currency. Caused by a mid-cycle currency change in the legacy system. | Escalate to Billing Ops. Agents cannot change invoice currency, and editing the account currency will not fix the existing invoice. |
```

**4. score 0.7704 - `HC-4003-structured-005` - HC-4003 / payments - 625 chars [right-article-wrong-chunk, hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-5133 | The card is valid but the billing country on the card does not match the account tax country. | Correct the account tax country, or ask the customer to use a card issued in the account country. |
| ERR-5140 | The payment method is a wallet token bound to a device that is no longer registered. | Ask the customer to pay once from the original device, or to add a normal card. |
| ERR-5199 | The processor rejected the request because the account is flagged for manual review. | Do not retry. Escalate to Payments Ops. Retrying while flagged extends the review window. |
```

**5. score 0.7623 - `HC-4002-structured-004` - HC-4002 / invoicing - 802 chars [hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. |
| ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that had overlapping legacy subscriptions. | Void the invoice, then run Rebuild Usage for the period. Never delete the usage record directly. |
| ERR-4032 | The invoice line item references a legacy tax code that no longer exists in BL2. The migration could not map it automatically. | Re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. |
```

---

## Q3 (table_row)

**Question:** A German business customer is getting ERR-7203 on their VAT number. What causes it and how do we clear it?

**Known-correct location:** `HC-4005` -> Tax validation error codes -> table row ERR-7203

**Known answer:** The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid for cross-border trade. Ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab.

**Hit requires the chunk to contain:** `ERR-7203`, `Revalidate on the Tax tab`

### Q3 / baseline -> HIT at rank 1

**1. score 0.8054 - `HC-4005-baseline-003` - HC-4005 / tax - 968 chars [HIT, hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. |
| ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid for cross-border trade. | Ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab. |
| ERR-7208 | VIES was unreachable when validation ran. This is a temporary outage on the tax authority side, not a customer problem. | Retry after one hour. Do not remove the customer's VAT ID. Invoices finalise with the last known good status. |
| ERR-7215 | The customer name on the account does not match the name registered against the VAT ID. | Update the legal entity name on the account to match the registration exactly, then revalidate. |
```

**2. score 0.7477 - `HC-4002-baseline-003` - HC-4002 / invoicing - 802 chars [hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. |
| ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that had overlapping legacy subscriptions. | Void the invoice, then run Rebuild Usage for the period. Never delete the usage record directly. |
| ERR-4032 | The invoice line item references a legacy tax code that no longer exists in BL2. The migration could not map it automatically. | Re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. |
```

**3. score 0.7394 - `HC-4005-baseline-004` - HC-4005 / tax - 403 chars [right-article-wrong-chunk, ORPHAN]**

```
| ERR-7302 | An invoice line item has no tax code and no default could be inferred from the product. | Set a tax code on the product, then rebuild the invoice. Escalate to Tax Ops if the product has no correct code. |
| ERR-7310 | A United States exemption certificate has expired. | Ask the customer to upload a current certificate. Tax is charged in the meantime and is not refundable once remitted. |
```

**4. score 0.7311 - `HC-4002-baseline-004` - HC-4002 / invoicing - 965 chars [ORPHAN]**

```
| ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. |
| ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Confirm the customer has not been charged twice before closing the ticket. |
| ERR-4061 | The invoice currency does not match the account currency. Caused by a mid-cycle currency change in the legacy system. | Escalate to Billing Ops. Agents cannot change invoice currency, and editing the account currency will not fix the existing invoice. |
| ERR-4077 | PDF rendering failed because a line item description contains an unsupported control character. | Edit the line item description to remove the character, then click Regenerate PDF. The invoice itself is valid and payable meanwhile. |
```

**5. score 0.7311 - `HC-4005-baseline-001` - HC-4005 / tax - 991 chars [right-article-wrong-chunk]**

```
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
```

### Q3 / structured -> HIT at rank 1

**1. score 0.7845 - `HC-4005-structured-003` - HC-4005 / tax - 999 chars [HIT, hdr]**

```
## Tax validation error codes

| Error code | Cause | Fix |
|---|---|---|
| ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. |
| ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid for cross-border trade. | Ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab. |
| ERR-7208 | VIES was unreachable when validation ran. This is a temporary outage on the tax authority side, not a customer problem. | Retry after one hour. Do not remove the customer's VAT ID. Invoices finalise with the last known good status. |
| ERR-7215 | The customer name on the account does not match the name registered against the VAT ID. | Update the legal entity name on the account to match the registration exactly, then revalidate. |
```

**2. score 0.7477 - `HC-4002-structured-004` - HC-4002 / invoicing - 802 chars [hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. |
| ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that had overlapping legacy subscriptions. | Void the invoice, then run Rebuild Usage for the period. Never delete the usage record directly. |
| ERR-4032 | The invoice line item references a legacy tax code that no longer exists in BL2. The migration could not map it automatically. | Re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. |
```

**3. score 0.7436 - `HC-4002-structured-005` - HC-4002 / invoicing - 761 chars [hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. |
| ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Confirm the customer has not been charged twice before closing the ticket. |
| ERR-4061 | The invoice currency does not match the account currency. Caused by a mid-cycle currency change in the legacy system. | Escalate to Billing Ops. Agents cannot change invoice currency, and editing the account currency will not fix the existing invoice. |
```

**4. score 0.7428 - `HC-4005-structured-004` - HC-4005 / tax - 446 chars [right-article-wrong-chunk, hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-7302 | An invoice line item has no tax code and no default could be inferred from the product. | Set a tax code on the product, then rebuild the invoice. Escalate to Tax Ops if the product has no correct code. |
| ERR-7310 | A United States exemption certificate has expired. | Ask the customer to upload a current certificate. Tax is charged in the meantime and is not refundable once remitted. |
```

**5. score 0.7311 - `HC-4005-structured-001` - HC-4005 / tax - 991 chars [right-article-wrong-chunk]**

```
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
```

---

## Q4 (table_row)

**Question:** Our webhook listener for invoice.payment_succeeded went silent after the migration. Which v2 event replaced it?

**Known-correct location:** `HC-4006` -> Webhook event renames -> table row invoice.payment_succeeded

**Known answer:** It was renamed to billing.invoice.paid. It fires once, after ledger settlement, not on processor approval.

**Hit requires the chunk to contain:** `invoice.payment_succeeded`, `billing.invoice.paid`

### Q4 / baseline -> HIT at rank 1

**1. score 0.8735 - `HC-4006-baseline-004` - HC-4006 / api - 944 chars [HIT, hdr]**

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

## Webhook delivery and retries
```

**2. score 0.7890 - `HC-4006-baseline-001` - HC-4006 / api - 769 chars [right-article-wrong-chunk]**

```
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

## Endpoint mapping
```

**3. score 0.7476 - `HC-4006-baseline-005` - HC-4006 / api - 805 chars [right-article-wrong-chunk]**

```
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

**4. score 0.7473 - `HC-4006-baseline-002` - HC-4006 / api - 880 chars [right-article-wrong-chunk, hdr]**

```
| v1 endpoint | v2 endpoint | Breaking change |
|---|---|---|
| `GET /v1/invoices` | `GET /v2/billing/invoices` | Pagination is cursor-based. The `page` parameter is ignored and returns the first page silently. |
| `GET /v1/invoices/{id}` | `GET /v2/billing/invoices/{id}` | The `number` field now includes a revision suffix on reissued invoices. |
| `POST /v1/invoices/{id}/pay` | `POST /v2/billing/invoices/{id}/payments` | Returns 202 and settles asynchronously. Callers that assumed a synchronous 200 will misreport failures. |
| `GET /v1/subscriptions` | `GET /v2/billing/subscriptions` | The `plan` field returns the new capability-tier name, not the legacy seat-count name. |
| `POST /v1/subscriptions/{id}/cancel` | `POST /v2/billing/subscriptions/{id}/cancellations` | Cancellation is now scheduled at period end by default. Pass `immediate=true` for the old behaviour. |
```

**5. score 0.7329 - `HC-4001-baseline-002` - HC-4001 / billing_core - 980 chars**

```
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

### Q4 / structured -> HIT at rank 1

**1. score 0.8716 - `HC-4006-structured-004` - HC-4006 / api - 911 chars [HIT, hdr]**

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

**2. score 0.7858 - `HC-4006-structured-001` - HC-4006 / api - 748 chars [right-article-wrong-chunk]**

```
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
```

**3. score 0.7476 - `HC-4006-structured-005` - HC-4006 / api - 805 chars [right-article-wrong-chunk]**

```
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

**4. score 0.7329 - `HC-4001-structured-002` - HC-4001 / billing_core - 980 chars**

```
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

**5. score 0.7323 - `HC-4006-structured-002` - HC-4006 / api - 901 chars [right-article-wrong-chunk, hdr]**

```
## Endpoint mapping

| v1 endpoint | v2 endpoint | Breaking change |
|---|---|---|
| `GET /v1/invoices` | `GET /v2/billing/invoices` | Pagination is cursor-based. The `page` parameter is ignored and returns the first page silently. |
| `GET /v1/invoices/{id}` | `GET /v2/billing/invoices/{id}` | The `number` field now includes a revision suffix on reissued invoices. |
| `POST /v1/invoices/{id}/pay` | `POST /v2/billing/invoices/{id}/payments` | Returns 202 and settles asynchronously. Callers that assumed a synchronous 200 will misreport failures. |
| `GET /v1/subscriptions` | `GET /v2/billing/subscriptions` | The `plan` field returns the new capability-tier name, not the legacy seat-count name. |
| `POST /v1/subscriptions/{id}/cancel` | `POST /v2/billing/subscriptions/{id}/cancellations` | Cancellation is now scheduled at period end by default. Pass `immediate=true` for the old behaviour. |
```

---

## Q5 (table_row)

**Question:** A customer was on the legacy Team 10 plan. Which new plan did they move to, and what is the seat rule on it?

**Known-correct location:** `HC-4004` -> Legacy to new plan map -> table row Team 10

**Known answer:** Team 10 maps to Growth. Seat rule: 10 included, overflow billed per seat at renewal.

**Hit requires the chunk to contain:** `Team 10`, `Growth`, `10 included, overflow billed per seat at renewal`

### Q5 / baseline -> HIT at rank 1

**1. score 0.8268 - `HC-4004-baseline-002` - HC-4004 / subscriptions - 824 chars [HIT, hdr]**

```
## Legacy to new plan map

| Legacy plan | New plan | Seat rule | Price held until |
|---|---|---|---|
| Solo | Starter | 1 seat. Additional seats not allowed. | First renewal after 1 June 2026 |
| Team 5 | Starter | 5 included. Overflow seats blocked at checkout. | First renewal after 1 June 2026 |
| Team 10 | Growth | 10 included, overflow billed per seat at renewal. | First renewal after 1 June 2026 |
| Team 25 | Growth | 25 included, overflow billed per seat at renewal. | First renewal after 1 June 2026 |
| Business 50 | Scale | 50 included, overflow billed monthly in arrears. | Contract end date |
| Business 100 | Scale | 100 included, overflow billed monthly in arrears. | Contract end date |
| Enterprise (custom) | Enterprise | Seats set by contract. No self-serve change. | Contract end date |

## Proration
```

**2. score 0.7385 - `HC-4004-baseline-001` - HC-4004 / subscriptions - 757 chars [right-article-wrong-chunk]**

```
# Subscription and Plan Mapping After Migration

## How legacy plans were mapped

Legacy plans were named by seat count. BL2 plans are named by capability tier, so
every account was mapped onto a new plan at migration. Price was preserved for the
remainder of the current term. The new list price applies from the first renewal
after 1 June 2026, and the account owner was emailed 30 days before that renewal.

Mapping was done once, from the plan recorded in BL1 at 00:00 UTC on 1 June 2026.
A plan change made after that timestamp but before the customer's own cutover was
applied afterwards as a normal plan change, not as part of the mapping. That is
why a small number of accounts show two plan-change events on the same day.

## Legacy to new plan map
```

**3. score 0.7081 - `HC-4004-baseline-004` - HC-4004 / subscriptions - 852 chars [right-article-wrong-chunk, hdr]**

```
Renewal retries and payment retries are the same schedule. Agents sometimes assume
subscriptions have their own retry timer. They do not.

## Plan change errors

| Error code | Cause | Fix |
|---|---|---|
| ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued. |
| ERR-6210 | The account is on a contract-term plan and cannot self-serve a change. | Route to the account manager. Agents cannot override a contract term. |
| ERR-6244 | A plan change was attempted while an invoice for the current period is still in draft. | Wait for the hourly finalisation run, then retry the change. |
| ERR-6250 | The account is suspended for non-payment. | Collect payment first. Plan changes are blocked while suspended. |
```

**4. score 0.7019 - `HC-4001-baseline-002` - HC-4001 / billing_core - 980 chars**

```
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

**5. score 0.6813 - `HC-4006-baseline-002` - HC-4006 / api - 880 chars [hdr]**

```
| v1 endpoint | v2 endpoint | Breaking change |
|---|---|---|
| `GET /v1/invoices` | `GET /v2/billing/invoices` | Pagination is cursor-based. The `page` parameter is ignored and returns the first page silently. |
| `GET /v1/invoices/{id}` | `GET /v2/billing/invoices/{id}` | The `number` field now includes a revision suffix on reissued invoices. |
| `POST /v1/invoices/{id}/pay` | `POST /v2/billing/invoices/{id}/payments` | Returns 202 and settles asynchronously. Callers that assumed a synchronous 200 will misreport failures. |
| `GET /v1/subscriptions` | `GET /v2/billing/subscriptions` | The `plan` field returns the new capability-tier name, not the legacy seat-count name. |
| `POST /v1/subscriptions/{id}/cancel` | `POST /v2/billing/subscriptions/{id}/cancellations` | Cancellation is now scheduled at period end by default. Pass `immediate=true` for the old behaviour. |
```

### Q5 / structured -> HIT at rank 1

**1. score 0.8302 - `HC-4004-structured-002` - HC-4004 / subscriptions - 810 chars [HIT, hdr]**

```
## Legacy to new plan map

| Legacy plan | New plan | Seat rule | Price held until |
|---|---|---|---|
| Solo | Starter | 1 seat. Additional seats not allowed. | First renewal after 1 June 2026 |
| Team 5 | Starter | 5 included. Overflow seats blocked at checkout. | First renewal after 1 June 2026 |
| Team 10 | Growth | 10 included, overflow billed per seat at renewal. | First renewal after 1 June 2026 |
| Team 25 | Growth | 25 included, overflow billed per seat at renewal. | First renewal after 1 June 2026 |
| Business 50 | Scale | 50 included, overflow billed monthly in arrears. | Contract end date |
| Business 100 | Scale | 100 included, overflow billed monthly in arrears. | Contract end date |
| Enterprise (custom) | Enterprise | Seats set by contract. No self-serve change. | Contract end date |
```

**2. score 0.7525 - `HC-4004-structured-005` - HC-4004 / subscriptions - 713 chars [right-article-wrong-chunk, hdr]**

```
## Plan change errors

| Error code | Cause | Fix |
|---|---|---|
| ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued. |
| ERR-6210 | The account is on a contract-term plan and cannot self-serve a change. | Route to the account manager. Agents cannot override a contract term. |
| ERR-6244 | A plan change was attempted while an invoice for the current period is still in draft. | Wait for the hourly finalisation run, then retry the change. |
| ERR-6250 | The account is suspended for non-payment. | Collect payment first. Plan changes are blocked while suspended. |
```

**3. score 0.7311 - `HC-4004-structured-001` - HC-4004 / subscriptions - 730 chars [right-article-wrong-chunk]**

```
# Subscription and Plan Mapping After Migration

## How legacy plans were mapped

Legacy plans were named by seat count. BL2 plans are named by capability tier, so
every account was mapped onto a new plan at migration. Price was preserved for the
remainder of the current term. The new list price applies from the first renewal
after 1 June 2026, and the account owner was emailed 30 days before that renewal.

Mapping was done once, from the plan recorded in BL1 at 00:00 UTC on 1 June 2026.
A plan change made after that timestamp but before the customer's own cutover was
applied afterwards as a normal plan change, not as part of the mapping. That is
why a small number of accounts show two plan-change events on the same day.
```

**4. score 0.7019 - `HC-4001-structured-002` - HC-4001 / billing_core - 980 chars**

```
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

**5. score 0.6790 - `HC-4006-structured-002` - HC-4006 / api - 901 chars [hdr]**

```
## Endpoint mapping

| v1 endpoint | v2 endpoint | Breaking change |
|---|---|---|
| `GET /v1/invoices` | `GET /v2/billing/invoices` | Pagination is cursor-based. The `page` parameter is ignored and returns the first page silently. |
| `GET /v1/invoices/{id}` | `GET /v2/billing/invoices/{id}` | The `number` field now includes a revision suffix on reissued invoices. |
| `POST /v1/invoices/{id}/pay` | `POST /v2/billing/invoices/{id}/payments` | Returns 202 and settles asynchronously. Callers that assumed a synchronous 200 will misreport failures. |
| `GET /v1/subscriptions` | `GET /v2/billing/subscriptions` | The `plan` field returns the new capability-tier name, not the legacy seat-count name. |
| `POST /v1/subscriptions/{id}/cancel` | `POST /v2/billing/subscriptions/{id}/cancellations` | Cancellation is now scheduled at period end by default. Pass `immediate=true` for the old behaviour. |
```

---

## Q6 (prose)

**Question:** How long is the billing ledger read-only during the cutover, and can customers pay during that time?

**Known-correct location:** `HC-4001` -> What changed (prose) / Cutover phases -> Phase 3 row

**Known answer:** Four hours. During the freeze a customer can view invoices but cannot pay, change a plan, or update a card.

**Hit requires the chunk to contain:** `read-only for four hours`

### Q6 / baseline -> HIT at rank 1

**1. score 0.8414 - `HC-4001-baseline-002` - HC-4001 / billing_core - 980 chars [HIT]**

```
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

**2. score 0.8216 - `HC-4002-baseline-005` - HC-4002 / invoicing - 229 chars [ORPHAN]**

```
| ERR-4090 | The invoice was finalised while the ledger was read-only during Phase 3 cutover. It has no ledger entry. | Do not void it. Open a Billing Ops ticket quoting the invoice number so the ledger entry can be backfilled. |
```

**3. score 0.7502 - `HC-4001-baseline-003` - HC-4001 / billing_core - 793 chars [HIT, hdr]**

```
## Cutover phases

| Phase | Window (UTC) | What changes | Rollback available |
|---|---|---|---|
| Phase 0 — Shadow write | 12 May, 02:00-06:00 | BL2 receives a copy of every BL1 write. Customers see no change at all. | Yes |
| Phase 1 — Balance import | 19 May, 02:00-05:00 | Open balances and credit notes are imported into BL2. Invoices are still served from BL1. | Yes |
| Phase 2 — Read mirror | 26 May, 02:00-04:00 | Invoice reads are served from BL2. Writes still land in BL1. | Yes |
| Phase 3 — Ledger cutover | 1 June, 01:00-05:00 | BL2 becomes the system of record. The ledger is read-only for four hours. | No |
| Phase 4 — Legacy freeze | 8 June, 02:00-03:00 | BL1 is set to read-only archive. No further writes are accepted. | No |

## Migration status codes on the account page
```

**4. score 0.7423 - `HC-4001-baseline-001` - HC-4001 / billing_core - 533 chars [right-article-wrong-chunk]**

```
# Billing Migration Overview and Cutover Timeline

## What changed

On 1 June 2026 we moved every customer account from the legacy billing ledger
(internally "BL1") to the new metered billing ledger ("BL2"). BL2 stores invoices,
credit notes, tax lines and subscription state in one double-entry ledger. The
legacy system kept invoices and subscriptions in two separate databases that were
reconciled once a night. That nightly reconciliation is the reason customers
sometimes saw an invoice before the matching plan change appeared.
```

**5. score 0.7399 - `HC-4002-baseline-006` - HC-4002 / invoicing - 498 chars**

```
## What agents must not do

Never void an invoice that a customer has already paid, even if it shows an error
code. Voiding a paid invoice creates an orphaned payment that has to be repaired
by hand in the ledger. If the invoice is paid and shows an error, the correct
route is always a Billing Ops ticket.

Never edit tax codes on a historical invoice to "make the total match". The tax
code drives the ledger entry, and changing it after payment causes the account to
drift out of reconciliation.
```

### Q6 / structured -> HIT at rank 1

**1. score 0.8414 - `HC-4001-structured-002` - HC-4001 / billing_core - 980 chars [HIT]**

```
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

**2. score 0.7643 - `HC-4001-structured-003` - HC-4001 / billing_core - 746 chars [HIT, hdr]**

```
## Cutover phases

| Phase | Window (UTC) | What changes | Rollback available |
|---|---|---|---|
| Phase 0 — Shadow write | 12 May, 02:00-06:00 | BL2 receives a copy of every BL1 write. Customers see no change at all. | Yes |
| Phase 1 — Balance import | 19 May, 02:00-05:00 | Open balances and credit notes are imported into BL2. Invoices are still served from BL1. | Yes |
| Phase 2 — Read mirror | 26 May, 02:00-04:00 | Invoice reads are served from BL2. Writes still land in BL1. | Yes |
| Phase 3 — Ledger cutover | 1 June, 01:00-05:00 | BL2 becomes the system of record. The ledger is read-only for four hours. | No |
| Phase 4 — Legacy freeze | 8 June, 02:00-03:00 | BL1 is set to read-only archive. No further writes are accepted. | No |
```

**3. score 0.7423 - `HC-4001-structured-001` - HC-4001 / billing_core - 533 chars [right-article-wrong-chunk]**

```
# Billing Migration Overview and Cutover Timeline

## What changed

On 1 June 2026 we moved every customer account from the legacy billing ledger
(internally "BL1") to the new metered billing ledger ("BL2"). BL2 stores invoices,
credit notes, tax lines and subscription state in one double-entry ledger. The
legacy system kept invoices and subscriptions in two separate databases that were
reconciled once a night. That nightly reconciliation is the reason customers
sometimes saw an invoice before the matching plan change appeared.
```

**4. score 0.7409 - `HC-4006-structured-003` - HC-4006 / api - 404 chars [hdr]**

```
| v1 endpoint | v2 endpoint | Breaking change |
|---|---|---|
| `GET /v1/customers/{id}/balance` | removed | Balance is derived from the ledger. Use `GET /v2/billing/ledger/entries` and sum the open entries. |
| `POST /v1/credits` | removed | Credit notes are created through the invoice, not directly. |
| `GET /v1/plans` | removed | Plans are now a catalogue object. Use `GET /v2/catalogue/products`. |
```

**5. score 0.7399 - `HC-4002-structured-007` - HC-4002 / invoicing - 498 chars**

```
## What agents must not do

Never void an invoice that a customer has already paid, even if it shows an error
code. Voiding a paid invoice creates an orphaned payment that has to be repaired
by hand in the ledger. If the invoice is paid and shows an error, the correct
route is always a Billing Ops ticket.

Never edit tax codes on a historical invoice to "make the total match". The tax
code drives the ledger entry, and changing it after payment causes the account to
drift out of reconciliation.
```

---

## Q7 (prose)

**Question:** What happened to stored cards that had not been used for a long time, and what do those customers need to do?

**Known-correct location:** `HC-4003` -> What happened to stored cards (prose)

**Known answer:** Cards unused for more than 24 months were dropped, because the processor will not re-tokenise a dormant card. Those customers must add a payment method again before their next renewal.

**Hit requires the chunk to contain:** `24 months`, `add a payment method again`

### Q7 / baseline -> HIT at rank 1

**1. score 0.8070 - `HC-4003-baseline-001` - HC-4003 / payments - 786 chars [HIT]**

```
# Payment Methods, Card Tokens and Decline Codes

## What happened to stored cards

Every stored card was re-tokenised during cutover. The card number itself never
moved, because we never held it. What moved was the token issued by the payment
processor. Customers do not need to do anything if their card was re-tokenised
successfully, and most were.

Two groups of cards were not migrated. Cards that had not been used for more than
24 months were dropped, because the processor will not re-tokenise a dormant card.
Those customers must add a payment method again before their next renewal.
Customers whose card had already expired were also dropped, for the same reason.
In both cases the account shows no default payment method, and renewal will fail
silently until a card is added.
```

**2. score 0.7416 - `HC-4001-baseline-002` - HC-4001 / billing_core - 980 chars**

```
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

**3. score 0.6965 - `HC-4001-baseline-001` - HC-4001 / billing_core - 533 chars**

```
# Billing Migration Overview and Cutover Timeline

## What changed

On 1 June 2026 we moved every customer account from the legacy billing ledger
(internally "BL1") to the new metered billing ledger ("BL2"). BL2 stores invoices,
credit notes, tax lines and subscription state in one double-entry ledger. The
legacy system kept invoices and subscriptions in two separate databases that were
reconciled once a night. That nightly reconciliation is the reason customers
sometimes saw an invoice before the matching plan change appeared.
```

**4. score 0.6960 - `HC-4003-baseline-005` - HC-4003 / payments - 582 chars [right-article-wrong-chunk, ORPHAN]**

```
| ERR-5133 | The card is valid but the billing country on the card does not match the account tax country. | Correct the account tax country, or ask the customer to use a card issued in the account country. |
| ERR-5140 | The payment method is a wallet token bound to a device that is no longer registered. | Ask the customer to pay once from the original device, or to add a normal card. |
| ERR-5199 | The processor rejected the request because the account is flagged for manual review. | Do not retry. Escalate to Payments Ops. Retrying while flagged extends the review window. |
```

**5. score 0.6859 - `HC-4003-baseline-004` - HC-4003 / payments - 894 chars [right-article-wrong-chunk, hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-5101 | Generic decline returned by the issuing bank with no reason given. | Ask the customer to contact their bank. Do not retry more than once, because repeated attempts can trigger a fraud block. |
| ERR-5108 | The saved card token was not re-tokenised during cutover. The token reference points at a BL1 record that no longer resolves. | Ask the customer to re-enter the card once. The new token is created automatically and the failed renewal retries within the hour. |
| ERR-5114 | Insufficient funds. Returned verbatim by the issuer. | Advise the customer to retry after funding the account. The dunning schedule will retry on its own. |
| ERR-5127 | 3-D Secure authentication was required but the session expired before the customer completed it. | Send the customer a fresh payment link from the invoice. Links expire after 30 minutes. |
```

### Q7 / structured -> HIT at rank 1

**1. score 0.8070 - `HC-4003-structured-001` - HC-4003 / payments - 786 chars [HIT]**

```
# Payment Methods, Card Tokens and Decline Codes

## What happened to stored cards

Every stored card was re-tokenised during cutover. The card number itself never
moved, because we never held it. What moved was the token issued by the payment
processor. Customers do not need to do anything if their card was re-tokenised
successfully, and most were.

Two groups of cards were not migrated. Cards that had not been used for more than
24 months were dropped, because the processor will not re-tokenise a dormant card.
Those customers must add a payment method again before their next renewal.
Customers whose card had already expired were also dropped, for the same reason.
In both cases the account shows no default payment method, and renewal will fail
silently until a card is added.
```

**2. score 0.7416 - `HC-4001-structured-002` - HC-4001 / billing_core - 980 chars**

```
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

**3. score 0.6965 - `HC-4001-structured-001` - HC-4001 / billing_core - 533 chars**

```
# Billing Migration Overview and Cutover Timeline

## What changed

On 1 June 2026 we moved every customer account from the legacy billing ledger
(internally "BL1") to the new metered billing ledger ("BL2"). BL2 stores invoices,
credit notes, tax lines and subscription state in one double-entry ledger. The
legacy system kept invoices and subscriptions in two separate databases that were
reconciled once a night. That nightly reconciliation is the reason customers
sometimes saw an invoice before the matching plan change appeared.
```

**4. score 0.6746 - `HC-4003-structured-004` - HC-4003 / payments - 928 chars [right-article-wrong-chunk, hdr]**

```
## Decline and token error codes

| Error code | Cause | Fix |
|---|---|---|
| ERR-5101 | Generic decline returned by the issuing bank with no reason given. | Ask the customer to contact their bank. Do not retry more than once, because repeated attempts can trigger a fraud block. |
| ERR-5108 | The saved card token was not re-tokenised during cutover. The token reference points at a BL1 record that no longer resolves. | Ask the customer to re-enter the card once. The new token is created automatically and the failed renewal retries within the hour. |
| ERR-5114 | Insufficient funds. Returned verbatim by the issuer. | Advise the customer to retry after funding the account. The dunning schedule will retry on its own. |
| ERR-5127 | 3-D Secure authentication was required but the session expired before the customer completed it. | Send the customer a fresh payment link from the invoice. Links expire after 30 minutes. |
```

**5. score 0.6698 - `HC-4003-structured-005` - HC-4003 / payments - 625 chars [right-article-wrong-chunk, hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-5133 | The card is valid but the billing country on the card does not match the account tax country. | Correct the account tax country, or ask the customer to use a card issued in the account country. |
| ERR-5140 | The payment method is a wallet token bound to a device that is no longer registered. | Ask the customer to pay once from the original device, or to add a normal card. |
| ERR-5199 | The processor rejected the request because the account is flagged for manual review. | Do not retry. Escalate to Payments Ops. Retrying while flagged extends the review window. |
```

---

## Q8 (prose)

**Question:** When does the v1 billing API stop working, and what do callers get after that date?

**Known-correct location:** `HC-4006` -> Versioning and sunset (prose)

**Known answer:** The v1 endpoints stop responding on 30 September 2026. After that date a v1 request returns HTTP 410 with no body.

**Hit requires the chunk to contain:** `30 September 2026`, `410`

### Q8 / baseline -> HIT at rank 1

**1. score 0.8272 - `HC-4006-baseline-001` - HC-4006 / api - 769 chars [HIT]**

```
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

## Endpoint mapping
```

**2. score 0.7798 - `HC-4006-baseline-004` - HC-4006 / api - 944 chars [right-article-wrong-chunk, hdr]**

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

## Webhook delivery and retries
```

**3. score 0.7790 - `HC-4006-baseline-002` - HC-4006 / api - 880 chars [right-article-wrong-chunk, hdr]**

```
| v1 endpoint | v2 endpoint | Breaking change |
|---|---|---|
| `GET /v1/invoices` | `GET /v2/billing/invoices` | Pagination is cursor-based. The `page` parameter is ignored and returns the first page silently. |
| `GET /v1/invoices/{id}` | `GET /v2/billing/invoices/{id}` | The `number` field now includes a revision suffix on reissued invoices. |
| `POST /v1/invoices/{id}/pay` | `POST /v2/billing/invoices/{id}/payments` | Returns 202 and settles asynchronously. Callers that assumed a synchronous 200 will misreport failures. |
| `GET /v1/subscriptions` | `GET /v2/billing/subscriptions` | The `plan` field returns the new capability-tier name, not the legacy seat-count name. |
| `POST /v1/subscriptions/{id}/cancel` | `POST /v2/billing/subscriptions/{id}/cancellations` | Cancellation is now scheduled at period end by default. Pass `immediate=true` for the old behaviour. |
```

**4. score 0.7674 - `HC-4001-baseline-002` - HC-4001 / billing_core - 980 chars**

```
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

**5. score 0.7552 - `HC-4004-baseline-004` - HC-4004 / subscriptions - 852 chars [hdr]**

```
Renewal retries and payment retries are the same schedule. Agents sometimes assume
subscriptions have their own retry timer. They do not.

## Plan change errors

| Error code | Cause | Fix |
|---|---|---|
| ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued. |
| ERR-6210 | The account is on a contract-term plan and cannot self-serve a change. | Route to the account manager. Agents cannot override a contract term. |
| ERR-6244 | A plan change was attempted while an invoice for the current period is still in draft. | Wait for the hourly finalisation run, then retry the change. |
| ERR-6250 | The account is suspended for non-payment. | Collect payment first. Plan changes are blocked while suspended. |
```

### Q8 / structured -> HIT at rank 1

**1. score 0.8326 - `HC-4006-structured-001` - HC-4006 / api - 748 chars [HIT]**

```
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
```

**2. score 0.7818 - `HC-4006-structured-004` - HC-4006 / api - 911 chars [right-article-wrong-chunk, hdr]**

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

**3. score 0.7674 - `HC-4001-structured-002` - HC-4001 / billing_core - 980 chars**

```
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

**4. score 0.7550 - `HC-4006-structured-002` - HC-4006 / api - 901 chars [right-article-wrong-chunk, hdr]**

```
## Endpoint mapping

| v1 endpoint | v2 endpoint | Breaking change |
|---|---|---|
| `GET /v1/invoices` | `GET /v2/billing/invoices` | Pagination is cursor-based. The `page` parameter is ignored and returns the first page silently. |
| `GET /v1/invoices/{id}` | `GET /v2/billing/invoices/{id}` | The `number` field now includes a revision suffix on reissued invoices. |
| `POST /v1/invoices/{id}/pay` | `POST /v2/billing/invoices/{id}/payments` | Returns 202 and settles asynchronously. Callers that assumed a synchronous 200 will misreport failures. |
| `GET /v1/subscriptions` | `GET /v2/billing/subscriptions` | The `plan` field returns the new capability-tier name, not the legacy seat-count name. |
| `POST /v1/subscriptions/{id}/cancel` | `POST /v2/billing/subscriptions/{id}/cancellations` | Cancellation is now scheduled at period end by default. Pass `immediate=true` for the old behaviour. |
```

**5. score 0.7339 - `HC-4002-structured-005` - HC-4002 / invoicing - 761 chars [hdr]**

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. |
| ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Confirm the customer has not been charged twice before closing the ticket. |
| ERR-4061 | The invoice currency does not match the account currency. Caused by a mid-cycle currency change in the legacy system. | Escalate to Billing Ops. Agents cannot change invoice currency, and editing the account currency will not fix the existing invoice. |
```
