---
article_id: HC-4004
title: Subscription and Plan Mapping After Migration
product_area: subscriptions
last_updated: 2026-05-29
---

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

Proration is now calculated by the second rather than by the day. An upgrade made
at 14:30 is charged from 14:30, not from midnight. This makes small proration
amounts look unfamiliar, and customers occasionally report them as errors. They
are not errors.

Downgrades never prorate. A downgrade takes effect at the next renewal and the
customer keeps the higher tier until then. The legacy system issued a partial
credit note on downgrade. BL2 does not, and no credit is due.

Seat reductions follow the downgrade rule. Removing a seat mid-term frees the
licence immediately but does not reduce the current invoice.

## Renewal failures

A renewal that cannot be charged does not cancel the subscription. It moves the
subscription through the dunning schedule described in the payments article, then
suspends it. A suspended subscription keeps customer data for 60 days. After 60
days the data is deleted and cannot be restored, even if the customer pays.

Renewal retries and payment retries are the same schedule. Agents sometimes assume
subscriptions have their own retry timer. They do not.

## Plan change errors

| Error code | Cause | Fix |
|---|---|---|
| ERR-6203 | The target plan does not include enough seats for the account's current active users. | Remove users first, or choose a plan with a higher seat count. The change is blocked, not queued. |
| ERR-6210 | The account is on a contract-term plan and cannot self-serve a change. | Route to the account manager. Agents cannot override a contract term. |
| ERR-6244 | A plan change was attempted while an invoice for the current period is still in draft. | Wait for the hourly finalisation run, then retry the change. |
| ERR-6250 | The account is suspended for non-payment. | Collect payment first. Plan changes are blocked while suspended. |
