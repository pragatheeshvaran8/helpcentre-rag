---
article_id: HC-4002
title: Invoice Errors After the Billing Migration
product_area: invoicing
last_updated: 2026-06-11
---

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

Draft invoices behave differently from the legacy system. A draft has no number at
all until it is finalised. If a customer sends a screenshot with an empty invoice
number field, the invoice is still a draft and no payment is due yet.

## Invoice error codes

These codes appear in the Billing tab, in the invoice PDF footer, and in API
responses. The code is authoritative. The human-readable message attached to it
was rewritten during migration and may not match older support macros.

| Error code | Cause | Fix |
|---|---|---|
| ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. |
| ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that had overlapping legacy subscriptions. | Void the invoice, then run Rebuild Usage for the period. Never delete the usage record directly. |
| ERR-4032 | The invoice line item references a legacy tax code that no longer exists in BL2. The migration could not map it automatically. | Re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. |
| ERR-4044 | The invoice total is negative because an imported credit note exceeded the invoice value. | Convert the remainder to account credit using Apply as Credit. Do not issue a refund for the difference. |
| ERR-4055 | The billing period on the invoice overlaps a period that is already invoiced and paid. | Void the newer invoice. The paid invoice is the correct one. Confirm the customer has not been charged twice before closing the ticket. |
| ERR-4061 | The invoice currency does not match the account currency. Caused by a mid-cycle currency change in the legacy system. | Escalate to Billing Ops. Agents cannot change invoice currency, and editing the account currency will not fix the existing invoice. |
| ERR-4077 | PDF rendering failed because a line item description contains an unsupported control character. | Edit the line item description to remove the character, then click Regenerate PDF. The invoice itself is valid and payable meanwhile. |
| ERR-4090 | The invoice was finalised while the ledger was read-only during Phase 3 cutover. It has no ledger entry. | Do not void it. Open a Billing Ops ticket quoting the invoice number so the ledger entry can be backfilled. |

## What agents must not do

Never void an invoice that a customer has already paid, even if it shows an error
code. Voiding a paid invoice creates an orphaned payment that has to be repaired
by hand in the ledger. If the invoice is paid and shows an error, the correct
route is always a Billing Ops ticket.

Never edit tax codes on a historical invoice to "make the total match". The tax
code drives the ledger entry, and changing it after payment causes the account to
drift out of reconciliation.
