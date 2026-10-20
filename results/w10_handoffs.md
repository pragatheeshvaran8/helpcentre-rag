# Week 10: how the manager split each ticket

Each hand-off is a task with a lifecycle: submitted, working, then
completed or failed. The manager routes by reading agent cards, so
nothing in its code names a specialist.

## T01 (multi, 2 part(s))

> Two separate problems on one account. An invoice line is throwing ERR-4032, and separately the customer's VAT ID stopped validating with ERR-7215. What do I do about each?

Split into **2 task(s)**. 6 LLM calls, 3,376 tokens, 27.01s.

- `t1` to **code_desk** [completed]
  - asked: An invoice line is throwing ERR-4032. What is the cause and documented fix for this error code?
  - tools: lookup_error_code, finish
- `t2` to **code_desk** [completed]
  - asked: A customer's VAT ID stopped validating with ERR-7215. What is the cause and documented fix for this error code?
  - tools: lookup_error_code, finish

**Final answer**

```
ERR-4032: The invoice line item references a legacy tax code that no longer exists in BL2, and the migration could not map it automatically [HC-4002-structured-004]. Fix: re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice [HC-4002-structured-004].

ERR-7215: The customer name on the account does not match the name registered against the VAT ID. Fix: update the legal entity name on the account to match the registration exactly, then revalidate [HC-4005-structured-003].
```

## T02 (multi, 2 part(s))

> Customer's card was declined with ERR-5108 on renewal. While I had them on the phone they also said their plan change is blocked with ERR-6203. Can you sort both out?

Split into **2 task(s)**. 6 LLM calls, 3,373 tokens, 29.63s.

- `t1` to **code_desk** [completed]
  - asked: What is the cause and documented fix for error code ERR-5108?
  - tools: lookup_error_code, finish
- `t2` to **code_desk** [completed]
  - asked: What is the cause and documented fix for error code ERR-6203?
  - tools: lookup_error_code, finish

**Final answer**

```
Both errors can be resolved as follows:

**ERR-5108 (card declined on renewal):** The saved card token was not re-tokenised during cutover, and the token reference points at a BL1 record that no longer resolves [HC-4003-structured-004]. The documented fix is to ask the customer to re-enter the card once, as the new token is created automatically and the failed renewal retries within the hour [HC-4003-structured-004].

**ERR-6203 (plan change blocked):** The target plan does not include enough seats for the account's current active users. The documented fix is to remove users first, or choose a plan with a higher seat count. The change is blocked, not queued [HC-4004-structured-005].
```

## T03 (multi, 2 part(s))

> A renewal failed and the subscription is showing past due. Which dunning attempt is that? Also their webhook endpoint was down for a few hours and they want to know if they lost the events.

Split into **1 task(s)**. 4 LLM calls, 2,934 tokens, 24.82s.

- `t1` to **policy_desk** [completed]
  - asked: A renewal failed and the subscription is showing past due. Which dunning attempt is that?
  - tools: search_help_centre, finish

**Final answer**

```
A renewal failure that leaves the subscription showing as past due corresponds to dunning Attempt 4, which occurs 7 days after the initial renewal attempt and triggers an email plus an in-app blocking modal [HC-4003-structured-003].

REFUSED: The help-centre corpus does not contain this information.
Missing: Whether missed webhook events are recovered when the endpoint is down
```

## T04 (multi, 2 part(s))

> Account badge says MIG-220 and I am not sure what to do with it. The same customer is also asking for an extension on the v1 API sunset because they will not be ready in time.

Split into **2 task(s)**. 6 LLM calls, 4,182 tokens, 26.53s.

- `t1` to **code_desk** [completed]
  - asked: What does the error code MIG-220 mean and what is the documented fix for it?
  - tools: lookup_error_code, finish
- `t2` to **policy_desk** [completed]
  - asked: What is the policy on granting extensions for the v1 API sunset, and what can an agent do when a customer says they will not be ready in time?
  - tools: search_help_centre, finish

**Final answer**

```
The account badge error code MIG-220 means that invoices were moved successfully but at least one credit note failed to import. The documented fix is to open a Billing Ops ticket with the account ID and not to reissue invoices yourself. [HC-4001-structured-005]

Regarding the v1 API sunset extension request, there is no extension process for the v1 API sunset. The v1 endpoints stop responding on 30 September 2026, after which a v1 request returns HTTP 410 with no body. When a customer says they will not be ready in time, an agent should not tell them no but should route them to their account manager. [HC-4006-structured-001]
```

## T05 (multi, 3 part(s))

> Messy one. Tax is failing with ERR-7208, a payment is stuck on ERR-5199, and the customer is asking me to void an invoice they have already paid. Three things, what is the right action on each?

Split into **3 task(s)**. 8 LLM calls, 5,360 tokens, 44.86s.

- `t1` to **code_desk** [completed]
  - asked: What is the cause and documented fix for error code ERR-7208?
  - tools: lookup_error_code, finish
- `t2` to **code_desk** [completed]
  - asked: What is the cause and documented fix for error code ERR-5199?
  - tools: lookup_error_code, finish
- `t3` to **policy_desk** [completed]
  - asked: What is the correct action when a customer asks to void an invoice that has already been paid?
  - tools: search_help_centre, finish

**Final answer**

```
1. ERR-7208: The cause is that VIES was unreachable when validation ran, which is a temporary outage on the tax authority side, not a customer problem [HC-4005-structured-003]. The documented fix is to retry after one hour, do not remove the customer's VAT ID, and invoices will finalise with the last known good status [HC-4005-structured-003].

2. ERR-5199: The cause is that the processor rejected the request because the account is flagged for manual review [HC-4003-structured-005]. The documented fix is to not retry, escalate to Payments Ops, and note that retrying while flagged extends the review window [HC-4003-structured-005].

3. Voiding a paid invoice: Never void an invoice that a customer has already paid, even if it shows an error code, because voiding a paid invoice creates an orphaned payment that has to be repaired by hand in the ledger. If the invoice is paid and shows an err
```

## T06 (multi, 2 part(s))

> Customer downgraded mid-term and wants a credit note. They are also hitting ERR-6250 when they try to change plan. Do they get the credit, and why is the change blocked?

Split into **2 task(s)**. 6 LLM calls, 4,134 tokens, 34.59s.

- `t1` to **policy_desk** [completed]
  - asked: A customer downgraded mid-term and is requesting a credit note. Are they entitled to a credit note, and what is the policy on credits for mid-term downgrades?
  - tools: search_help_centre, finish
- `t2` to **code_desk** [completed]
  - asked: What is the cause and documented fix for error code ERR-6250 that occurs when a customer tries to change plan?
  - tools: lookup_error_code, finish

**Final answer**

```
No credit note is due. Per the help centre policy [HC-4004-structured-003], downgrades never prorate; a downgrade takes effect at the next renewal and the customer keeps the higher tier until then. The legacy system issued a partial credit note on downgrade, but the current system (BL2) does not, and no credit is due [HC-4004-structured-003].

The change is blocked because error code ERR-6250 indicates the account is suspended for non-payment. The documented fix is to collect payment first, as plan changes are blocked while the account is suspended [HC-4004-structured-005].
```

## T07 (single, 1 part(s))

> Getting ERR-4032 on an invoice line. What is the fix?

Split into **1 task(s)**. 4 LLM calls, 1,987 tokens, 47.1s.

- `t1` to **code_desk** [completed]
  - asked: What is the cause and documented fix for error code ERR-4032 on an invoice line?
  - tools: lookup_error_code, finish

**Final answer**

```
ERR-4032 on an invoice line occurs because the line item references a legacy tax code that no longer exists in BL2, and the migration could not map it automatically [HC-4002-structured-004]. The documented fix is to re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice [HC-4002-structured-004].
```

## T08 (single, 1 part(s))

> ERR-5114 insufficient funds. Do we retry it?

Split into **1 task(s)**. 4 LLM calls, 1,870 tokens, 20.09s.

- `t1` to **code_desk** [completed]
  - asked: What does error code ERR-5114 mean and what is the documented fix for it?
  - tools: lookup_error_code, finish

**Final answer**

```
ERR-5114 indicates insufficient funds, returned verbatim by the issuer. The documented fix is to advise the customer to retry after funding the account, as the dunning schedule will retry on its own. [HC-4003-structured-004]
```

## T09 (single, 1 part(s))

> MIG-310 badge on the account, what do I do?

Split into **1 task(s)**. 4 LLM calls, 1,893 tokens, 25.26s.

- `t1` to **code_desk** [completed]
  - asked: What does the MIG-310 error code mean and what is the documented fix for it?
  - tools: lookup_error_code, finish

**Final answer**

```
MIG-310 means the account was skipped because a payment was in flight at cutover, and it is retried nightly. The documented fix is to wait one night, and escalate only if the badge is unchanged after 48 hours. [HC-4001-structured-005]
```

## T10 (single, 1 part(s))

> A VAT ID failed VIES validation with ERR-7203. What is the fix?

Split into **1 task(s)**. 4 LLM calls, 2,027 tokens, 12.47s.

- `t1` to **code_desk** [completed]
  - asked: What is the cause and documented fix for error code ERR-7203 when a VAT ID fails VIES validation?
  - tools: lookup_error_code, finish

**Final answer**

```
ERR-7203 occurs because the VAT ID failed real-time validation against VIES — the number is well-formed but is not registered or is not valid for cross-border trade [HC-4005-structured-003]. The documented fix is to ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab [HC-4005-structured-003].
```

## T11 (refuse, 1 part(s))

> What is our SLA for a P1 billing incident, and who is on call tonight?

Split into **1 task(s)**. 5 LLM calls, 5,141 tokens, 53.85s.

- `t1` to **policy_desk** [completed]
  - asked: What is the SLA for a P1 billing incident, and who is on call tonight?
  - tools: search_help_centre, search_help_centre, search_help_centre

**Final answer**

```
REFUSED: The help-centre corpus does not contain this information.
Missing: SLA for a P1 billing incident and who is on call tonight
```

## T12 (refuse, 1 part(s))

> Customer is on ERR-4032 and also wants me to issue the refund through the Stripe dashboard. Walk me through the Stripe side.

Split into **2 task(s)**. 7 LLM calls, 5,555 tokens, 62.04s.

- `t1` to **code_desk** [completed]
  - asked: What does error code ERR-4032 mean and what is the documented fix for it?
  - tools: lookup_error_code, finish
- `t2` to **policy_desk** [**failed**]
  - asked: Walk me through how to issue a refund through the Stripe dashboard.
  - tools: search_help_centre, search_help_centre
  - error: ValueError: no 'tool' field

**Final answer**

```
ERR-4032 occurs when an invoice line item references a legacy tax code that no longer exists in BL2, and the migration could not map it automatically. The documented fix is to re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. [HC-4002-structured-004]

Regarding issuing a refund through the Stripe dashboard: the help-centre corpus does not contain this information.
Missing: instructions for issuing a refund through the Stripe dashboard
```

