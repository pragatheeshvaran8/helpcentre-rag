"""The 8 known-answer evaluation questions.

READ THIS BEFORE CHANGING ANYTHING IN THIS FILE.

These questions were written by reading the 6 articles, BEFORE any retrieval code
existed and before a single search was run. That ordering is the whole point. If
you write questions after looking at what retrieval returns, your hit-rate
measures your question-writing, not your chunker.

The git history is the evidence: this file is committed together with the corpus,
in a commit that contains no retriever, no vector store and no results.

--------------------------------------------------------------------------------
How a "hit" is decided (objective, no human judgement)
--------------------------------------------------------------------------------
A question counts as a hit-in-top-5 when at least one of the 5 retrieved chunks
satisfies BOTH conditions:

  1. chunk.metadata["article_id"] == expected_article_id
  2. every string in must_contain appears in the chunk text (case-insensitive)

Condition 2 is what makes this a test of chunking rather than a test of vague
topical similarity. Retrieving a chunk that mentions ERR-4032 but has lost the
"fix" half of the row is NOT a hit, because that chunk cannot answer the
question. That is exactly the failure mode a table-splitting chunker produces.

`must_contain` strings are copied verbatim from the articles.
"""
from __future__ import annotations

# Answer types, recorded so the write-up can separate table questions from prose.
TABLE = "table_row"
PROSE = "prose"

QUESTIONS: list[dict] = [
    {
        "id": "Q1",
        "type": TABLE,
        "question": "What does ERR-4032 mean on an invoice, and what is the fix?",
        "expected_article_id": "HC-4002",
        "expected_section": "Invoice error codes -> table row ERR-4032",
        "known_answer": (
            "The invoice line item references a legacy tax code that no longer "
            "exists in BL2, and the migration could not map it automatically. "
            "Fix: re-map the line item to a current tax code under Billing then "
            "Tax Codes, then reissue the invoice."
        ),
        "must_contain": ["ERR-4032", "reissue the invoice"],
    },
    {
        "id": "Q2",
        "type": TABLE,
        "question": (
            "A renewal failed with a token error because the saved card was not "
            "re-tokenised at cutover. Which error code is that, and what should "
            "the agent ask the customer to do?"
        ),
        "expected_article_id": "HC-4003",
        "expected_section": "Decline and token error codes -> table row ERR-5108",
        "known_answer": (
            "ERR-5108. The saved card token was not re-tokenised during cutover. "
            "Ask the customer to re-enter the card once; the new token is created "
            "automatically and the failed renewal retries within the hour."
        ),
        "must_contain": ["ERR-5108", "re-enter the card"],
    },
    {
        "id": "Q3",
        "type": TABLE,
        "question": (
            "A German business customer is getting ERR-7203 on their VAT number. "
            "What causes it and how do we clear it?"
        ),
        "expected_article_id": "HC-4005",
        "expected_section": "Tax validation error codes -> table row ERR-7203",
        "known_answer": (
            "The VAT ID failed real-time validation against VIES. The number is "
            "well-formed but is not registered or is not valid for cross-border "
            "trade. Ask the customer to confirm the VAT ID with their tax "
            "authority, then click Revalidate on the Tax tab."
        ),
        "must_contain": ["ERR-7203", "Revalidate on the Tax tab"],
    },
    {
        "id": "Q4",
        "type": TABLE,
        "question": (
            "Our webhook listener for invoice.payment_succeeded went silent after "
            "the migration. Which v2 event replaced it?"
        ),
        "expected_article_id": "HC-4006",
        "expected_section": "Webhook event renames -> table row invoice.payment_succeeded",
        "known_answer": (
            "It was renamed to billing.invoice.paid. It fires once, after ledger "
            "settlement, not on processor approval."
        ),
        "must_contain": ["invoice.payment_succeeded", "billing.invoice.paid"],
    },
    {
        "id": "Q5",
        "type": TABLE,
        "question": (
            "A customer was on the legacy Team 10 plan. Which new plan did they "
            "move to, and what is the seat rule on it?"
        ),
        "expected_article_id": "HC-4004",
        "expected_section": "Legacy to new plan map -> table row Team 10",
        "known_answer": (
            "Team 10 maps to Growth. Seat rule: 10 included, overflow billed per "
            "seat at renewal."
        ),
        "must_contain": [
            "Team 10",
            "Growth",
            "10 included, overflow billed per seat at renewal",
        ],
    },
    {
        "id": "Q6",
        "type": PROSE,
        "question": (
            "How long is the billing ledger read-only during the cutover, and can "
            "customers pay during that time?"
        ),
        "expected_article_id": "HC-4001",
        "expected_section": "What changed (prose) / Cutover phases -> Phase 3 row",
        "known_answer": (
            "Four hours. During the freeze a customer can view invoices but cannot "
            "pay, change a plan, or update a card."
        ),
        "must_contain": ["read-only for four hours"],
    },
    {
        "id": "Q7",
        "type": PROSE,
        "question": (
            "What happened to stored cards that had not been used for a long time, "
            "and what do those customers need to do?"
        ),
        "expected_article_id": "HC-4003",
        "expected_section": "What happened to stored cards (prose)",
        "known_answer": (
            "Cards unused for more than 24 months were dropped, because the "
            "processor will not re-tokenise a dormant card. Those customers must "
            "add a payment method again before their next renewal."
        ),
        "must_contain": ["24 months", "add a payment method again"],
    },
    {
        "id": "Q8",
        "type": PROSE,
        "question": (
            "When does the v1 billing API stop working, and what do callers get "
            "after that date?"
        ),
        "expected_article_id": "HC-4006",
        "expected_section": "Versioning and sunset (prose)",
        "known_answer": (
            "The v1 endpoints stop responding on 30 September 2026. After that "
            "date a v1 request returns HTTP 410 with no body."
        ),
        "must_contain": ["30 September 2026", "410"],
    },
]


# ---------------------------------------------------------------------------
# Generation set (requirement 5). Also fixed before any run.
# ---------------------------------------------------------------------------

# Three questions the corpus CAN answer. Used for cited generation.
ANSWERABLE = ["Q1", "Q3", "Q4"]

# Three questions the corpus CANNOT answer. These must be refused, not invented.
# Each one is deliberately adjacent to real content, so a weak grounding prompt
# will happily hallucinate a plausible answer.
OUT_OF_CORPUS: list[dict] = [
    {
        "id": "R1",
        "question": (
            "What is the refund SLA? How many business days does a refund take to "
            "reach the customer's bank?"
        ),
        "why_unanswerable": (
            "HC-4003 explains how refunds are routed (original token, else "
            "account credit) but never states any timeline or SLA anywhere in the "
            "corpus."
        ),
    },
    {
        "id": "R2",
        "question": "What is the chargeback fee we pass on to the customer?",
        "why_unanswerable": (
            "Chargebacks are not covered by any of the 6 articles. HC-4003 "
            "mentions fraud blocks and manual review, which is close enough to "
            "tempt a model into inventing a fee."
        ),
    },
    {
        "id": "R3",
        "question": (
            "Which SSO providers does the new billing portal support, and can we "
            "enforce SAML for the billing role?"
        ),
        "why_unanswerable": (
            "HC-4006 covers API keys and says authentication did not change, but "
            "no article mentions SSO, SAML or portal login at all."
        ),
    },
]


# ---------------------------------------------------------------------------
# Bonus challenge (section 5 of the task). Fixed before any run.
# ---------------------------------------------------------------------------
# Q1 asks only what ERR-4032 is and how to fix it. BONUS_QUESTION adds a third
# part whose answer lives in the article PROSE, not in the table row. Prediction
# written before running: the structure-aware chunker retrieves the tight table
# row and answers parts 1 and 2 precisely, but has no prose in context and cannot
# answer part 3.
BONUS_QUESTION = {
    "id": "B1",
    "question": (
        "What does ERR-4032 mean, what is the fix, and what happens to the "
        "invoice number after I reissue the invoice?"
    ),
    "expected_article_id": "HC-4002",
    "answer_parts": {
        "meaning": "Line item references a legacy tax code that no longer exists in BL2.",
        "fix": "Re-map to a current tax code under Billing then Tax Codes, then reissue.",
        "numbering": (
            "The reissued invoice keeps the original invoice number and gains a "
            "revision suffix, such as EU-2026-0004417-R2."
        ),
    },
}


# ---------------------------------------------------------------------------
# Metadata filter demonstration (requirement 4). Fixed before any run.
# ---------------------------------------------------------------------------
# "Retries" is described in three different product areas: payments (dunning),
# subscriptions (renewal) and api (webhook backoff). The unfiltered query should
# surface one of them. Filtering to product_area="api" should change top-1.
FILTER_DEMO = {
    "query": "How do retries work after the migration?",
    "filter_field": "product_area",
    "filter_value": "api",
}


def get_question(qid: str) -> dict:
    """Look up one question by its id."""
    for q in QUESTIONS:
        if q["id"] == qid:
            return q
    raise KeyError(f"Unknown question id: {qid}")
