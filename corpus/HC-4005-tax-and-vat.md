---
article_id: HC-4005
title: Tax IDs, VAT Numbers and Tax Validation Errors
product_area: tax
last_updated: 2026-06-05
---

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

## Accepted tax ID formats

| Region | Field name | Format | Validated against |
|---|---|---|---|
| European Union | VAT ID | Two-letter country code followed by 8 to 12 characters, no spaces | VIES, in real time |
| United Kingdom | VAT registration number | GB followed by 9 or 12 digits | HMRC service |
| India | GSTIN | 15 characters, state code first | GSTN portal |
| Australia | ABN | 11 digits | ABR lookup |
| United States | Tax exemption certificate | Uploaded document, no automatic format check | Manual review by Tax Ops |

## Tax validation error codes

| Error code | Cause | Fix |
|---|---|---|
| ERR-7101 | The tax ID format is wrong for the selected country. Usually the country prefix was typed twice. | Correct the format on the Tax tab. The field rejects the value on save, so no invoice is affected yet. |
| ERR-7203 | The VAT ID failed real-time validation against VIES. The number is well-formed but is not registered or is not valid for cross-border trade. | Ask the customer to confirm the VAT ID with their tax authority, then click Revalidate on the Tax tab. |
| ERR-7208 | VIES was unreachable when validation ran. This is a temporary outage on the tax authority side, not a customer problem. | Retry after one hour. Do not remove the customer's VAT ID. Invoices finalise with the last known good status. |
| ERR-7215 | The customer name on the account does not match the name registered against the VAT ID. | Update the legal entity name on the account to match the registration exactly, then revalidate. |
| ERR-7302 | An invoice line item has no tax code and no default could be inferred from the product. | Set a tax code on the product, then rebuild the invoice. Escalate to Tax Ops if the product has no correct code. |
| ERR-7310 | A United States exemption certificate has expired. | Ask the customer to upload a current certificate. Tax is charged in the meantime and is not refundable once remitted. |

## What agents must not do

Never mark an account as tax exempt to clear an error. Exemption is a legal status
and is set only by Tax Ops after reviewing a certificate. Never edit a tax code on
a finalised invoice. Corrections are made by reissuing the invoice, which keeps the
original invoice number and adds a revision suffix.
