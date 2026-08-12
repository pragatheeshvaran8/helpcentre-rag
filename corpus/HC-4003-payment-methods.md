---
article_id: HC-4003
title: Payment Methods, Card Tokens and Decline Codes
product_area: payments
last_updated: 2026-06-18
---

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

Wallet payment methods behave differently. Apple Pay and Google Pay tokens are
device-bound and were re-issued automatically on first use. A customer using a
wallet may see one extra authentication prompt after migration. That prompt is
expected and appears once per device.

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

## Decline and token error codes

| Error code | Cause | Fix |
|---|---|---|
| ERR-5101 | Generic decline returned by the issuing bank with no reason given. | Ask the customer to contact their bank. Do not retry more than once, because repeated attempts can trigger a fraud block. |
| ERR-5108 | The saved card token was not re-tokenised during cutover. The token reference points at a BL1 record that no longer resolves. | Ask the customer to re-enter the card once. The new token is created automatically and the failed renewal retries within the hour. |
| ERR-5114 | Insufficient funds. Returned verbatim by the issuer. | Advise the customer to retry after funding the account. The dunning schedule will retry on its own. |
| ERR-5127 | 3-D Secure authentication was required but the session expired before the customer completed it. | Send the customer a fresh payment link from the invoice. Links expire after 30 minutes. |
| ERR-5133 | The card is valid but the billing country on the card does not match the account tax country. | Correct the account tax country, or ask the customer to use a card issued in the account country. |
| ERR-5140 | The payment method is a wallet token bound to a device that is no longer registered. | Ask the customer to pay once from the original device, or to add a normal card. |
| ERR-5199 | The processor rejected the request because the account is flagged for manual review. | Do not retry. Escalate to Payments Ops. Retrying while flagged extends the review window. |

## Refunds

Refunds are issued back to the original payment method whenever the original token
still resolves. If the token was dropped during migration, the refund cannot be
returned to the card and must be issued as account credit instead. Agents can
issue account credit up to 250 in account currency without approval.
