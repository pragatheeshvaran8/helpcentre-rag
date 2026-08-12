# Every chunk in the `structured` index

34 chunks, read back from the live vector store. Each heading
carries an anchor equal to its chunk_id, so citations elsewhere in the
write-up link straight to the chunk they claim to come from.

<a id="hc-4001-structured-001"></a>
## `HC-4001-structured-001`

- source_file: `HC-4001-billing-migration-overview.md`
- article_id: `HC-4001`
- product_area: `billing_core`
- last_updated: `2026-06-02`
- chars: 533, table rows: 0, header kept: False, orphan rows: False

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

<a id="hc-4001-structured-002"></a>
## `HC-4001-structured-002`

- source_file: `HC-4001-billing-migration-overview.md`
- article_id: `HC-4001`
- product_area: `billing_core`
- last_updated: `2026-06-02`
- chars: 980, table rows: 0, header kept: False, orphan rows: False

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

<a id="hc-4001-structured-003"></a>
## `HC-4001-structured-003`

- source_file: `HC-4001-billing-migration-overview.md`
- article_id: `HC-4001`
- product_area: `billing_core`
- last_updated: `2026-06-02`
- chars: 746, table rows: 5, header kept: True, orphan rows: False

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

<a id="hc-4001-structured-004"></a>
## `HC-4001-structured-004`

- source_file: `HC-4001-billing-migration-overview.md`
- article_id: `HC-4001`
- product_area: `billing_core`
- last_updated: `2026-06-02`
- chars: 252, table rows: 0, header kept: False, orphan rows: False

```
## Migration status codes on the account page

Every account carries a migration status badge on the Billing tab. The badge is
set once by the migration job and is never recalculated, so a stale badge is
possible on accounts that were repaired by hand.
```

<a id="hc-4001-structured-005"></a>
## `HC-4001-structured-005`

- source_file: `HC-4001-billing-migration-overview.md`
- article_id: `HC-4001`
- product_area: `billing_core`
- last_updated: `2026-06-02`
- chars: 920, table rows: 5, header kept: True, orphan rows: False

```
| Code | Badge text | Meaning | Agent action |
|---|---|---|---|
| MIG-100 | Migrated | The account moved cleanly. Balances match to the cent. | None. Treat the account as normal. |
| MIG-140 | Migrated with rounding | Balance differs from BL1 by less than 0.05 in account currency. The difference was written off automatically. | None. Explain the write-off if the customer asks. |
| MIG-220 | Partial | Invoices moved but at least one credit note failed to import. | Open a Billing Ops ticket with the account ID. Do not reissue invoices yourself. |
| MIG-310 | Deferred | The account was skipped because a payment was in flight at cutover. It is retried nightly. | Wait one night. Escalate only if the badge is unchanged after 48 hours. |
| MIG-450 | Blocked | The account has a legacy contract term that BL2 cannot represent. | Escalate to Billing Ops immediately. These accounts cannot self-serve any plan change. |
```

<a id="hc-4001-structured-006"></a>
## `HC-4001-structured-006`

- source_file: `HC-4001-billing-migration-overview.md`
- article_id: `HC-4001`
- product_area: `billing_core`
- last_updated: `2026-06-02`
- chars: 437, table rows: 0, header kept: False, orphan rows: False

```
## What to tell a customer who asks why their invoice looks different

Say that the invoice layout changed because tax is now calculated per line item
instead of once per invoice. Totals are unchanged. Point them at the invoice PDF,
which shows the same grand total as before. Do not promise a re-issue of old
invoices in the new layout, because historical invoices are served from the
archive and keep their original layout permanently.
```

<a id="hc-4002-structured-001"></a>
## `HC-4002-structured-001`

- source_file: `HC-4002-invoice-errors.md`
- article_id: `HC-4002`
- product_area: `invoicing`
- last_updated: `2026-06-11`
- chars: 806, table rows: 0, header kept: False, orphan rows: False

```
# Invoice Errors After the Billing Migration

## How invoice numbering works now

Invoice numbers are no longer sequential per account. BL2 issues numbers from a
single global sequence with a regional prefix, for example `EU-2026-0004417`.
Customers who reconcile by number will see gaps in their own sequence. That is
expected and is not a sign of a missing invoice.

When an invoice is corrected, BL2 does not allocate a new number. A reissued
invoice keeps the original invoice number and gains a revision suffix, such as
`EU-2026-0004417-R2`. The revision suffix increments on every reissue. Accounting
teams should treat the highest revision as the valid document and should ignore
lower revisions. Credit notes are separate documents with their own `CN-` prefix
and are never revisions of an invoice.
```

<a id="hc-4002-structured-002"></a>
## `HC-4002-structured-002`

- source_file: `HC-4002-invoice-errors.md`
- article_id: `HC-4002`
- product_area: `invoicing`
- last_updated: `2026-06-11`
- chars: 234, table rows: 0, header kept: False, orphan rows: False

```
Draft invoices behave differently from the legacy system. A draft has no number at
all until it is finalised. If a customer sends a screenshot with an empty invoice
number field, the invoice is still a draft and no payment is due yet.
```

<a id="hc-4002-structured-003"></a>
## `HC-4002-structured-003`

- source_file: `HC-4002-invoice-errors.md`
- article_id: `HC-4002`
- product_area: `invoicing`
- last_updated: `2026-06-11`
- chars: 251, table rows: 0, header kept: False, orphan rows: False

```
## Invoice error codes

These codes appear in the Billing tab, in the invoice PDF footer, and in API
responses. The code is authoritative. The human-readable message attached to it
was rewritten during migration and may not match older support macros.
```

<a id="hc-4002-structured-004"></a>
## `HC-4002-structured-004`

- source_file: `HC-4002-invoice-errors.md`
- article_id: `HC-4002`
- product_area: `invoicing`
- last_updated: `2026-06-11`
- chars: 802, table rows: 3, header kept: True, orphan rows: False

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. |
| ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that had overlapping legacy subscriptions. | Void the invoice, then run Rebuild Usage for the period. Never delete the usage record directly. |
| ERR-4032 | The invoice line item references a legacy tax code that no longer exists in BL2. The migration could not map it automatically. | Re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. |
```

<a id="hc-4002-structured-005"></a>
## `HC-4002-structured-005`

- source_file: `HC-4002-invoice-errors.md`
- article_id: `HC-4002`
- product_area: `invoicing`
- last_updated: `2026-06-11`
- chars: 761, table rows: 3, header kept: True, orphan rows: False

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. |
| ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Confirm the customer has not been charged twice before closing the ticket. |
| ERR-4061 | The invoice currency does not match the account currency. Caused by a mid-cycle currency change in the legacy system. | Escalate to Billing Ops. Agents cannot change invoice currency, and editing the account currency will not fix the existing invoice. |
```

<a id="hc-4002-structured-006"></a>
## `HC-4002-structured-006`

- source_file: `HC-4002-invoice-errors.md`
- article_id: `HC-4002`
- product_area: `invoicing`
- last_updated: `2026-06-11`
- chars: 519, table rows: 2, header kept: True, orphan rows: False

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-4077 | PDF rendering failed because a line item description contains an unsupported control character. | Edit the line item description to remove the character, then click Regenerate PDF. The invoice itself is valid and payable meanwhile. |
| ERR-4090 | The invoice was finalised while the ledger was read-only during Phase 3 cutover. It has no ledger entry. | Do not void it. Open a Billing Ops ticket quoting the invoice number so the ledger entry can be backfilled. |
```

<a id="hc-4002-structured-007"></a>
## `HC-4002-structured-007`

- source_file: `HC-4002-invoice-errors.md`
- article_id: `HC-4002`
- product_area: `invoicing`
- last_updated: `2026-06-11`
- chars: 498, table rows: 0, header kept: False, orphan rows: False

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

<a id="hc-4003-structured-001"></a>
## `HC-4003-structured-001`

- source_file: `HC-4003-payment-methods.md`
- article_id: `HC-4003`
- product_area: `payments`
- last_updated: `2026-06-18`
- chars: 786, table rows: 0, header kept: False, orphan rows: False

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

<a id="hc-4003-structured-002"></a>
## `HC-4003-structured-002`

- source_file: `HC-4003-payment-methods.md`
- article_id: `HC-4003`
- product_area: `payments`
- last_updated: `2026-06-18`
- chars: 274, table rows: 0, header kept: False, orphan rows: False

```
Wallet payment methods behave differently. Apple Pay and Google Pay tokens are
device-bound and were re-issued automatically on first use. A customer using a
wallet may see one extra authentication prompt after migration. That prompt is
expected and appears once per device.
```

<a id="hc-4003-structured-003"></a>
## `HC-4003-structured-003`

- source_file: `HC-4003-payment-methods.md`
- article_id: `HC-4003`
- product_area: `payments`
- last_updated: `2026-06-18`
- chars: 699, table rows: 5, header kept: True, orphan rows: False

```
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
```

<a id="hc-4003-structured-004"></a>
## `HC-4003-structured-004`

- source_file: `HC-4003-payment-methods.md`
- article_id: `HC-4003`
- product_area: `payments`
- last_updated: `2026-06-18`
- chars: 928, table rows: 4, header kept: True, orphan rows: False

```
## Decline and token error codes

| Error code | Cause | Fix |
|---|---|---|
| ERR-5101 | Generic decline returned by the issuing bank with no reason given. | Ask the customer to contact their bank. Do not retry more than once, because repeated attempts can trigger a fraud block. |
| ERR-5108 | The saved card token was not re-tokenised during cutover. The token reference points at a BL1 record that no longer resolves. | Ask the customer to re-enter the card once. The new token is created automatically and the failed renewal retries within the hour. |
| ERR-5114 | Insufficient funds. Returned verbatim by the issuer. | Advise the customer to retry after funding the account. The dunning schedule will retry on its own. |
| ERR-5127 | 3-D Secure authentication was required but the session expired before the customer completed it. | Send the customer a fresh payment link from the invoice. Links expire after 30 minutes. |
```

<a id="hc-4003-structured-005"></a>
## `HC-4003-structured-005`

- source_file: `HC-4003-payment-methods.md`
- article_id: `HC-4003`
- product_area: `payments`
- last_updated: `2026-06-18`
- chars: 625, table rows: 3, header kept: True, orphan rows: False

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-5133 | The card is valid but the billing country on the card does not match the account tax country. | Correct the account tax country, or ask the customer to use a card issued in the account country. |
| ERR-5140 | The payment method is a wallet token bound to a device that is no longer registered. | Ask the customer to pay once from the original device, or to add a normal card. |
| ERR-5199 | The processor rejected the request because the account is flagged for manual review. | Do not retry. Escalate to Payments Ops. Retrying while flagged extends the review window. |
```

<a id="hc-4003-structured-006"></a>
## `HC-4003-structured-006`

- source_file: `HC-4003-payment-methods.md`
- article_id: `HC-4003`
- product_area: `payments`
- last_updated: `2026-06-18`
- chars: 321, table rows: 0, header kept: False, orphan rows: False

```
## Refunds

Refunds are issued back to the original payment method whenever the original token
still resolves. If the token was dropped during migration, the refund cannot be
returned to the card and must be issued as account credit instead. Agents can
issue account credit up to 250 in account currency without approval.
```

<a id="hc-4004-structured-001"></a>
## `HC-4004-structured-001`

- source_file: `HC-4004-subscription-plan-mapping.md`
- article_id: `HC-4004`
- product_area: `subscriptions`
- last_updated: `2026-05-29`
- chars: 730, table rows: 0, header kept: False, orphan rows: False

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

<a id="hc-4004-structured-002"></a>
## `HC-4004-structured-002`

- source_file: `HC-4004-subscription-plan-mapping.md`
- article_id: `HC-4004`
- product_area: `subscriptions`
- last_updated: `2026-05-29`
- chars: 810, table rows: 7, header kept: True, orphan rows: False

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

<a id="hc-4004-structured-003"></a>
## `HC-4004-structured-003`

- source_file: `HC-4004-subscription-plan-mapping.md`
- article_id: `HC-4004`
- product_area: `subscriptions`
- last_updated: `2026-05-29`
- chars: 629, table rows: 0, header kept: False, orphan rows: False

```
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

<a id="hc-4004-structured-004"></a>
## `HC-4004-structured-004`

- source_file: `HC-4004-subscription-plan-mapping.md`
- article_id: `HC-4004`
- product_area: `subscriptions`
- last_updated: `2026-05-29`
- chars: 477, table rows: 0, header kept: False, orphan rows: False

```
## Renewal failures

A renewal that cannot be charged does not cancel the subscription. It moves the
subscription through the dunning schedule described in the payments article, then
suspends it. A suspended subscription keeps customer data for 60 days. After 60
days the data is deleted and cannot be restored, even if the customer pays.

Renewal retries and payment retries are the same schedule. Agents sometimes assume
subscriptions have their own retry timer. They do not.
```

<a id="hc-4004-structured-005"></a>
## `HC-4004-structured-005`

- source_file: `HC-4004-subscription-plan-mapping.md`
- article_id: `HC-4004`
- product_area: `subscriptions`
- last_updated: `2026-05-29`
- chars: 713, table rows: 4, header kept: True, orphan rows: False

```
## Plan change errors

| Error code | Cause | Fix |
|---|---|---|
| ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued. |
| ERR-6210 | The account is on a contract-term plan and cannot self-serve a change. | Route to the account manager. Agents cannot override a contract term. |
| ERR-6244 | A plan change was attempted while an invoice for the current period is still in draft. | Wait for the hourly finalisation run, then retry the change. |
| ERR-6250 | The account is suspended for non-payment. | Collect payment first. Plan changes are blocked while suspended. |
```

<a id="hc-4005-structured-001"></a>
## `HC-4005-structured-001`

- source_file: `HC-4005-tax-and-vat.md`
- article_id: `HC-4005`
- product_area: `tax`
- last_updated: `2026-06-05`
- chars: 991, table rows: 0, header kept: False, orphan rows: False

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

<a id="hc-4005-structured-002"></a>
## `HC-4005-structured-002`

- source_file: `HC-4005-tax-and-vat.md`
- article_id: `HC-4005`
- product_area: `tax`
- last_updated: `2026-06-05`
- chars: 538, table rows: 5, header kept: True, orphan rows: False

```
## Accepted tax ID formats

| Region | Field name | Format | Validated against |
|---|---|---|---|
| European Union | VAT ID | Two-letter country code followed by 8 to 12 characters, no spaces | VIES, in real time |
| United Kingdom | VAT registration number | GB followed by 9 or 12 digits | HMRC service |
| India | GSTIN | 15 characters, state code first | GSTN portal |
| Australia | ABN | 11 digits | ABR lookup |
| United States | Tax exemption certificate | Uploaded document, no automatic format check | Manual review by Tax Ops |
```

<a id="hc-4005-structured-003"></a>
## `HC-4005-structured-003`

- source_file: `HC-4005-tax-and-vat.md`
- article_id: `HC-4005`
- product_area: `tax`
- last_updated: `2026-06-05`
- chars: 999, table rows: 4, header kept: True, orphan rows: False

```
## Tax validation error codes

| Error code | Cause | Fix |
|---|---|---|
| ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. |
| ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid for cross-border trade. | Ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab. |
| ERR-7208 | VIES was unreachable when validation ran. This is a temporary outage on the tax authority side, not a customer problem. | Retry after one hour. Do not remove the customer's VAT ID. Invoices finalise with the last known good status. |
| ERR-7215 | The customer name on the account does not match the name registered against the VAT ID. | Update the legal entity name on the account to match the registration exactly, then revalidate. |
```

<a id="hc-4005-structured-004"></a>
## `HC-4005-structured-004`

- source_file: `HC-4005-tax-and-vat.md`
- article_id: `HC-4005`
- product_area: `tax`
- last_updated: `2026-06-05`
- chars: 446, table rows: 2, header kept: True, orphan rows: False

```
| Error code | Cause | Fix |
|---|---|---|
| ERR-7302 | An invoice line item has no tax code and no default could be inferred from the product. | Set a tax code on the product, then rebuild the invoice. Escalate to Tax Ops if the product has no correct code. |
| ERR-7310 | A United States exemption certificate has expired. | Ask the customer to upload a current certificate. Tax is charged in the meantime and is not refundable once remitted. |
```

<a id="hc-4005-structured-005"></a>
## `HC-4005-structured-005`

- source_file: `HC-4005-tax-and-vat.md`
- article_id: `HC-4005`
- product_area: `tax`
- last_updated: `2026-06-05`
- chars: 329, table rows: 0, header kept: False, orphan rows: False

```
## What agents must not do

Never mark an account as tax exempt to clear an error. Exemption is a legal status
and is set only by Tax Ops after reviewing a certificate. Never edit a tax code on
a finalised invoice. Corrections are made by reissuing the invoice, which keeps the
original invoice number and adds a revision suffix.
```

<a id="hc-4006-structured-001"></a>
## `HC-4006-structured-001`

- source_file: `HC-4006-billing-api-and-webhooks.md`
- article_id: `HC-4006`
- product_area: `api`
- last_updated: `2026-06-20`
- chars: 748, table rows: 0, header kept: False, orphan rows: False

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

<a id="hc-4006-structured-002"></a>
## `HC-4006-structured-002`

- source_file: `HC-4006-billing-api-and-webhooks.md`
- article_id: `HC-4006`
- product_area: `api`
- last_updated: `2026-06-20`
- chars: 901, table rows: 5, header kept: True, orphan rows: False

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

<a id="hc-4006-structured-003"></a>
## `HC-4006-structured-003`

- source_file: `HC-4006-billing-api-and-webhooks.md`
- article_id: `HC-4006`
- product_area: `api`
- last_updated: `2026-06-20`
- chars: 404, table rows: 3, header kept: True, orphan rows: False

```
| v1 endpoint | v2 endpoint | Breaking change |
|---|---|---|
| `GET /v1/customers/{id}/balance` | removed | Balance is derived from the ledger. Use `GET /v2/billing/ledger/entries` and sum the open entries. |
| `POST /v1/credits` | removed | Credit notes are created through the invoice, not directly. |
| `GET /v1/plans` | removed | Plans are now a catalogue object. Use `GET /v2/catalogue/products`. |
```

<a id="hc-4006-structured-004"></a>
## `HC-4006-structured-004`

- source_file: `HC-4006-billing-api-and-webhooks.md`
- article_id: `HC-4006`
- product_area: `api`
- last_updated: `2026-06-20`
- chars: 911, table rows: 5, header kept: True, orphan rows: False

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

<a id="hc-4006-structured-005"></a>
## `HC-4006-structured-005`

- source_file: `HC-4006-billing-api-and-webhooks.md`
- article_id: `HC-4006`
- product_area: `api`
- last_updated: `2026-06-20`
- chars: 805, table rows: 0, header kept: False, orphan rows: False

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
