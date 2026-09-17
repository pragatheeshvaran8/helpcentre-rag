"""The tickets the two runners race on.

WHY THESE ARE TICKETS AND NOT THE WEEK 5 QUESTIONS
    Every question in the Week 5 pool asks one thing. A one-thing question is
    exactly where a loop has nothing to add, so racing on that pool would only
    prove that an agent is slower, which nobody doubts. These tickets are what a
    support queue actually looks like: one message, several unrelated problems,
    written by someone who does not know which article each part lives in.

THE THREE SHAPES, AND WHY ALL THREE ARE HERE
    multi    Two or three separate problems, in DIFFERENT articles. One
             retrieval on the whole ticket has to cover several topics at once
             with a fixed top-k. This is where a loop should win, because it can
             look things up one at a time.
    single   One problem, one article. This is where the loop should lose: it
             pays three or four model calls to reach the same place a fixed
             sequence reaches in one.
    refuse   The corpus does not hold it. Both runners must refuse, and neither
             may invent. A loop is more dangerous here, not less, because it has
             more turns in which to talk itself into an answer.

    A race made only of `multi` would be rigged. The whole question the week
    asks is when NOT to use an agent, and that answer lives in `single`.

WHY EVERY REQUIREMENT IS A LITERAL STRING FROM THE CORPUS
    `must_contain` is checked by substring, case-insensitively, by the same
    Week 6 code that scored the last two runs. A requirement nobody can check
    by hand is a requirement that quietly drifts.

WHY article_id IS PART OF THE REQUIREMENT
    A ticket part is only covered when the answer comes from the article that
    actually documents it. Two articles in this corpus state the tax-code rule
    in different words, so naming the article is what stops a near-miss from
    scoring as a hit.
"""
from __future__ import annotations

MULTI = "multi"
SINGLE = "single"
REFUSE = "refuse"

ANSWER_EXPECTED = "answer"
REFUSE_EXPECTED = "refuse"

TICKETS = [
    # ---- multi-part: the case for a loop ---------------------------------
    {
        "id": "T01",
        "shape": MULTI,
        "parts": 2,
        "expected_behaviour": ANSWER_EXPECTED,
        "question": (
            "Two separate problems on one account. An invoice line is throwing "
            "ERR-4032, and separately the customer's VAT ID stopped validating "
            "with ERR-7215. What do I do about each?"
        ),
        "requirements": [
            {"article_id": "HC-4002", "must_contain": ["ERR-4032", "Tax Codes"]},
            {"article_id": "HC-4005", "must_contain": ["ERR-7215", "legal entity name"]},
        ],
    },
    {
        "id": "T02",
        "shape": MULTI,
        "parts": 2,
        "expected_behaviour": ANSWER_EXPECTED,
        "question": (
            "Customer's card was declined with ERR-5108 on renewal. While I had "
            "them on the phone they also said their plan change is blocked with "
            "ERR-6203. Can you sort both out?"
        ),
        "requirements": [
            {"article_id": "HC-4003", "must_contain": ["ERR-5108", "re-enter the card once"]},
            {"article_id": "HC-4004", "must_contain": ["ERR-6203", "Remove users first"]},
        ],
    },
    {
        "id": "T03",
        "shape": MULTI,
        "parts": 2,
        "expected_behaviour": ANSWER_EXPECTED,
        "question": (
            "A renewal failed and the subscription is showing past due. Which "
            "dunning attempt is that? Also their webhook endpoint was down for a "
            "few hours and they want to know if they lost the events."
        ),
        "requirements": [
            {"article_id": "HC-4003", "must_contain": ["7 days after attempt 1", "Past due"]},
            {"article_id": "HC-4006", "must_contain": ["exponential backoff", "is not recoverable"]},
        ],
    },
    {
        "id": "T04",
        "shape": MULTI,
        "parts": 2,
        "expected_behaviour": ANSWER_EXPECTED,
        "question": (
            "Account badge says MIG-220 and I am not sure what to do with it. The "
            "same customer is also asking for an extension on the v1 API sunset "
            "because they will not be ready in time."
        ),
        "requirements": [
            {
                "article_id": "HC-4001",
                "must_contain": ["MIG-220", "Do not reissue invoices yourself"],
            },
            {"article_id": "HC-4006", "must_contain": ["There is no extension process"]},
        ],
    },
    {
        "id": "T05",
        "shape": MULTI,
        "parts": 3,
        "expected_behaviour": ANSWER_EXPECTED,
        "question": (
            "Messy one. Tax is failing with ERR-7208, a payment is stuck on "
            "ERR-5199, and the customer is asking me to void an invoice they have "
            "already paid. Three things, what is the right action on each?"
        ),
        "requirements": [
            {"article_id": "HC-4005", "must_contain": ["ERR-7208", "Retry after one hour"]},
            {"article_id": "HC-4003", "must_contain": ["ERR-5199", "Escalate to Payments Ops"]},
            {
                "article_id": "HC-4002",
                "must_contain": ["Never void an invoice that a customer has already paid"],
            },
        ],
    },
    {
        "id": "T06",
        "shape": MULTI,
        "parts": 2,
        "expected_behaviour": ANSWER_EXPECTED,
        "question": (
            "Customer downgraded mid-term and wants a credit note. They are also "
            "hitting ERR-6250 when they try to change plan. Do they get the credit, "
            "and why is the change blocked?"
        ),
        "requirements": [
            {"article_id": "HC-4004", "must_contain": ["no credit is due"]},
            {"article_id": "HC-4004", "must_contain": ["ERR-6250", "Collect payment first"]},
        ],
    },
    # ---- single-part: the case against a loop ----------------------------
    {
        "id": "T07",
        "shape": SINGLE,
        "parts": 1,
        "expected_behaviour": ANSWER_EXPECTED,
        "question": "Getting ERR-4032 on an invoice line. What is the fix?",
        "requirements": [{"article_id": "HC-4002", "must_contain": ["ERR-4032", "Tax Codes"]}],
    },
    {
        "id": "T08",
        "shape": SINGLE,
        "parts": 1,
        "expected_behaviour": ANSWER_EXPECTED,
        "question": "ERR-5114 insufficient funds. Do we retry it?",
        "requirements": [
            {"article_id": "HC-4003", "must_contain": ["ERR-5114", "retry on its own"]}
        ],
    },
    {
        "id": "T09",
        "shape": SINGLE,
        "parts": 1,
        "expected_behaviour": ANSWER_EXPECTED,
        "question": "MIG-310 badge on the account, what do I do?",
        "requirements": [{"article_id": "HC-4001", "must_contain": ["MIG-310", "Wait one night"]}],
    },
    {
        "id": "T10",
        "shape": SINGLE,
        "parts": 1,
        "expected_behaviour": ANSWER_EXPECTED,
        "question": "A VAT ID failed VIES validation with ERR-7203. What is the fix?",
        "requirements": [
            {"article_id": "HC-4005", "must_contain": ["ERR-7203", "Revalidate on the Tax tab"]}
        ],
    },
    # ---- not in the corpus: both must refuse -----------------------------
    {
        "id": "T11",
        "shape": REFUSE,
        "parts": 1,
        "expected_behaviour": REFUSE_EXPECTED,
        "question": "What is our SLA for a P1 billing incident, and who is on call tonight?",
        "requirements": [],
    },
    {
        "id": "T12",
        "shape": REFUSE,
        "parts": 1,
        "expected_behaviour": REFUSE_EXPECTED,
        "question": (
            "Customer is on ERR-4032 and also wants me to issue the refund through "
            "the Stripe dashboard. Walk me through the Stripe side."
        ),
        "requirements": [],
    },
]

TICKETS_BY_ID = {t["id"]: t for t in TICKETS}
SHAPES = (MULTI, SINGLE, REFUSE)


def ticket_set() -> list[dict]:
    """The tickets, annotated with the `kind` key the Week 6 checks expect.

    The scorer keys on `kind`. Reusing `shape` for it means the per-shape
    breakdown in the race report and the per-kind breakdown in the check
    aggregate are the same numbers, rather than two views that can disagree.
    """
    return [dict(t, kind=t["shape"]) for t in TICKETS]


def counts() -> dict:
    return {shape: sum(1 for t in TICKETS if t["shape"] == shape) for shape in SHAPES}
