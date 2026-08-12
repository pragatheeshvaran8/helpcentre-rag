---
article_id: HC-4001
title: Billing Migration Overview and Cutover Timeline
product_area: billing_core
last_updated: 2026-06-02
---

# Billing Migration Overview and Cutover Timeline

## What changed

On 1 June 2026 we moved every customer account from the legacy billing ledger
(internally "BL1") to the new metered billing ledger ("BL2"). BL2 stores invoices,
credit notes, tax lines and subscription state in one double-entry ledger. The
legacy system kept invoices and subscriptions in two separate databases that were
reconciled once a night. That nightly reconciliation is the reason customers
sometimes saw an invoice before the matching plan change appeared.

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

## Cutover phases

| Phase | Window (UTC) | What changes | Rollback available |
|---|---|---|---|
| Phase 0 — Shadow write | 12 May, 02:00-06:00 | BL2 receives a copy of every BL1 write. Customers see no change at all. | Yes |
| Phase 1 — Balance import | 19 May, 02:00-05:00 | Open balances and credit notes are imported into BL2. Invoices are still served from BL1. | Yes |
| Phase 2 — Read mirror | 26 May, 02:00-04:00 | Invoice reads are served from BL2. Writes still land in BL1. | Yes |
| Phase 3 — Ledger cutover | 1 June, 01:00-05:00 | BL2 becomes the system of record. The ledger is read-only for four hours. | No |
| Phase 4 — Legacy freeze | 8 June, 02:00-03:00 | BL1 is set to read-only archive. No further writes are accepted. | No |

## Migration status codes on the account page

Every account carries a migration status badge on the Billing tab. The badge is
set once by the migration job and is never recalculated, so a stale badge is
possible on accounts that were repaired by hand.

| Code | Badge text | Meaning | Agent action |
|---|---|---|---|
| MIG-100 | Migrated | The account moved cleanly. Balances match to the cent. | None. Treat the account as normal. |
| MIG-140 | Migrated with rounding | Balance differs from BL1 by less than 0.05 in account currency. The difference was written off automatically. | None. Explain the write-off if the customer asks. |
| MIG-220 | Partial | Invoices moved but at least one credit note failed to import. | Open a Billing Ops ticket with the account ID. Do not reissue invoices yourself. |
| MIG-310 | Deferred | The account was skipped because a payment was in flight at cutover. It is retried nightly. | Wait one night. Escalate only if the badge is unchanged after 48 hours. |
| MIG-450 | Blocked | The account has a legacy contract term that BL2 cannot represent. | Escalate to Billing Ops immediately. These accounts cannot self-serve any plan change. |

## What to tell a customer who asks why their invoice looks different

Say that the invoice layout changed because tax is now calculated per line item
instead of once per invoice. Totals are unchanged. Point them at the invoice PDF,
which shows the same grand total as before. Do not promise a re-issue of old
invoices in the new layout, because historical invoices are served from the
archive and keep their original layout permanently.
