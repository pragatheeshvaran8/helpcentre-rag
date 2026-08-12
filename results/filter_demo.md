# Metadata filter on product_area

- Query: **How do retries work after the migration?**
- Strategy searched: `structured`
- Filter: `{"product_area": "api"}` (Chroma pre-filter, applied inside the search)
- Top-1 changed: **YES**

Unfiltered top-1: `HC-4001-structured-002` from HC-4001 (product_area `billing_core`), score 0.7281.

Filtered top-1: `HC-4006-structured-005` from HC-4006 (product_area `api`), score 0.7172.

Product areas present unfiltered: api, billing_core, payments.
Product areas present filtered: api.

## Result list A - UNFILTERED

| rank | score | chunk_id | article | product_area | last_updated |
|---|---|---|---|---|---|
| 1 | 0.7281 | `HC-4001-structured-002` | HC-4001 | billing_core | 2026-06-02 |
| 2 | 0.7172 | `HC-4006-structured-005` | HC-4006 | api | 2026-06-20 |
| 3 | 0.7103 | `HC-4001-structured-004` | HC-4001 | billing_core | 2026-06-02 |
| 4 | 0.6824 | `HC-4003-structured-001` | HC-4003 | payments | 2026-06-18 |
| 5 | 0.6759 | `HC-4001-structured-005` | HC-4001 | billing_core | 2026-06-02 |

**1. score 0.7281 - `HC-4001-structured-002` - HC-4001 / billing_core**

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

**2. score 0.7172 - `HC-4006-structured-005` - HC-4006 / api**

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

**3. score 0.7103 - `HC-4001-structured-004` - HC-4001 / billing_core**

```
## Migration status codes on the account page

Every account carries a migration status badge on the Billing tab. The badge is
set once by the migration job and is never recalculated, so a stale badge is
possible on accounts that were repaired by hand.
```

**4. score 0.6824 - `HC-4003-structured-001` - HC-4003 / payments**

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

**5. score 0.6759 - `HC-4001-structured-005` - HC-4001 / billing_core**

```
| Code | Badge text | Meaning | Agent action |
|---|---|---|---|
| MIG-100 | Migrated | The account moved cleanly. Balances match to the cent. | None. Treat the account as normal. |
| MIG-140 | Migrated with rounding | Balance differs from BL1 by less than 0.05 in account currency. The difference was written off automatically. | None. Explain the write-off if the customer asks. |
| MIG-220 | Partial | Invoices moved but at least one credit note failed to import. | Open a Billing Ops ticket with the account ID. Do not reissue invoices yourself. |
| MIG-310 | Deferred | The account was skipped because a payment was in flight at cutover. It is retried nightly. | Wait one night. Escalate only if the badge is unchanged after 48 hours. |
| MIG-450 | Blocked | The account has a legacy contract term that BL2 cannot represent. | Escalate to Billing Ops immediately. These accounts cannot self-serve any plan change. |
```

## Result list B - FILTERED to product_area = `api`

| rank | score | chunk_id | article | product_area | last_updated |
|---|---|---|---|---|---|
| 1 | 0.7172 | `HC-4006-structured-005` | HC-4006 | api | 2026-06-20 |
| 2 | 0.6690 | `HC-4006-structured-003` | HC-4006 | api | 2026-06-20 |
| 3 | 0.6503 | `HC-4006-structured-004` | HC-4006 | api | 2026-06-20 |
| 4 | 0.6442 | `HC-4006-structured-002` | HC-4006 | api | 2026-06-20 |
| 5 | 0.6407 | `HC-4006-structured-001` | HC-4006 | api | 2026-06-20 |

**1. score 0.7172 - `HC-4006-structured-005` - HC-4006 / api**

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

**2. score 0.6690 - `HC-4006-structured-003` - HC-4006 / api**

```
| v1 endpoint | v2 endpoint | Breaking change |
|---|---|---|
| `GET /v1/customers/{id}/balance` | removed | Balance is derived from the ledger. Use `GET /v2/billing/ledger/entries` and sum the open entries. |
| `POST /v1/credits` | removed | Credit notes are created through the invoice, not directly. |
| `GET /v1/plans` | removed | Plans are now a catalogue object. Use `GET /v2/catalogue/products`. |
```

**3. score 0.6503 - `HC-4006-structured-004` - HC-4006 / api**

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

**4. score 0.6442 - `HC-4006-structured-002` - HC-4006 / api**

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

**5. score 0.6407 - `HC-4006-structured-001` - HC-4006 / api**

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
