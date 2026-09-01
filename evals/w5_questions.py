"""Week 5 trace pool: what a support desk actually types at this app.

WHY A THIRD QUESTION SET
    Week 3 measured a chunker. Week 4 measured one retrieval change. Both used
    question sets built around a known-correct location, and Week 4's set is one
    clean question per error code. Real agents do not type like that.

    Week 5 is error analysis, and error analysis is only worth anything if the
    sample resembles real traffic. So this pool is written the way support
    agents actually ask: pasted codes, customer wording with no code at all,
    two questions in one message, typos, and questions the corpus simply cannot
    answer.

HOW THIS POOL WAS BUILT, AND THE HONEST LIMITS OF IT
    The pool is invented, like the corpus. There is no real ticket queue behind
    it. It was written in one sitting, from the six articles, BEFORE any of it
    was run through the app, and it has not been edited since the first trace
    was collected. That last part matters more than it sounds: a pool tuned
    after seeing results is a pool that flatters the app.

    It was NOT written to break the app and NOT written to flatter it. Each
    entry answers one question: would a billing support agent plausibly send
    this? Whether the app can handle it was not considered while writing.

    The pool is 60 questions and the sample is 20. Sampling is uniform and
    random from all 60, with a fixed seed. The ``kind`` field below is
    descriptive only; it is NEVER used to stratify the draw, because a
    stratified draw is a curated draw wearing a lab coat. See evals/w5_sample.py.

WHAT "CORRECT" MEANS FOR EACH ENTRY
    expected_behaviour = "answer"
        The corpus can answer it. Every requirement in ``requirements`` must be
        satisfied. One requirement is (article_id, [strings]) and it is met when
        a single chunk has that article_id and literally contains every string.

        Multi-part and cross-article questions carry two requirements on
        purpose. Answering half of a two-part question is not a pass, because a
        half answer sent to a customer is a wrong answer.

    expected_behaviour = "refuse"
        The corpus cannot answer it, or the question is too under-specified to
        have one answer. The right behaviour is the fixed refusal, naming what
        is missing. Answering anyway is the failure.

        Calling an under-specified question a refusal is a JUDGEMENT, and it is
        written down here rather than applied silently later. It follows the
        shipped prompt, which says a partial answer is a refusal.

EVERY REQUIRED STRING IS VERBATIM FROM THE CORPUS
    The acceptance suite asserts this, so a typo here cannot invent a failure
    that the app never had. Strings are kept short and inside a single source
    line, because the articles are hard-wrapped and a needle that spans a line
    break would never match.
"""
from __future__ import annotations

# Retrieval depth for every Week 5 trace. Same k as Week 4, so the two weeks
# stay comparable and Week 5 is not quietly measuring a wider window.
W5_K = 3

ANSWER = "answer"
REFUSE = "refuse"

# The traffic kinds in the pool. Descriptive only. Never used for sampling.
KINDS = (
    "code_lookup",
    "symptom",
    "policy",
    "procedure",
    "multi_part",
    "noisy",
    "vague",
    "cross_article",
    "out_of_corpus",
)

# id, kind, question, expected_behaviour, requirements
# A requirement is (article_id, [must_contain, ...]). ALL must be satisfied.
_RAW: list[tuple[str, str, str, str, list[tuple[str, list[str]]]]] = [

    # --- code_lookup: an agent pastes the code out of the Billing tab -------
    ("P01", "code_lookup",
     "Invoice is stuck on ERR-4010. What do I do?",
     ANSWER, [("HC-4002", ["ERR-4010", "Revalidate"])]),
    ("P02", "code_lookup",
     "Getting ERR-4032 on an invoice line. What is the fix?",
     ANSWER, [("HC-4002", ["ERR-4032", "Tax Codes"])]),
    ("P03", "code_lookup",
     "ERR-4044 on an invoice, the total has gone negative. What now?",
     ANSWER, [("HC-4002", ["ERR-4044", "Apply as Credit"])]),
    ("P04", "code_lookup",
     "What does ERR-4055 mean and which invoice do I keep?",
     ANSWER, [("HC-4002", ["ERR-4055", "Void the newer invoice"])]),
    ("P05", "code_lookup",
     "ERR-4061, wrong currency on the invoice. Can I fix it myself?",
     ANSWER, [("HC-4002", ["ERR-4061", "Escalate to Billing Ops"])]),
    ("P06", "code_lookup",
     "Invoice PDF will not render, code is ERR-4077. Is the invoice still payable?",
     ANSWER, [("HC-4002", ["ERR-4077", "Regenerate PDF"])]),
    ("P07", "code_lookup",
     "ERR-4090 on an invoice from cutover night. Should I void it?",
     ANSWER, [("HC-4002", ["ERR-4090", "Do not void it"])]),
    ("P08", "code_lookup",
     "Card declined with ERR-5101 and no reason given. What do I tell the customer?",
     ANSWER, [("HC-4003", ["ERR-5101", "contact their bank"])]),
    ("P09", "code_lookup",
     "ERR-5127 on a payment. What is the next step?",
     ANSWER, [("HC-4003", ["ERR-5127", "fresh payment link"])]),
    ("P10", "code_lookup",
     "What causes ERR-5133 on a card payment?",
     ANSWER, [("HC-4003", ["ERR-5133", "billing country"])]),
    ("P11", "code_lookup",
     "Wallet payment failing with ERR-5140. How does the customer pay?",
     ANSWER, [("HC-4003", ["ERR-5140", "original device"])]),
    ("P12", "code_lookup",
     "ERR-5199 on every retry. Should I keep retrying?",
     ANSWER, [("HC-4003", ["ERR-5199", "Payments Ops"])]),
    ("P13", "code_lookup",
     "Plan change blocked with ERR-6203. What is the fix?",
     ANSWER, [("HC-4004", ["ERR-6203", "Remove users first"])]),
    ("P14", "code_lookup",
     "ERR-6210 when changing plan. Can an agent override it?",
     ANSWER, [("HC-4004", ["ERR-6210", "account manager"])]),
    ("P15", "code_lookup",
     "ERR-6244 on a plan change. How long do I wait?",
     ANSWER, [("HC-4004", ["ERR-6244", "hourly finalisation run"])]),
    ("P16", "code_lookup",
     "Tax ID rejected with ERR-7101. Is any invoice affected?",
     ANSWER, [("HC-4005", ["ERR-7101", "Tax tab"])]),
    ("P17", "code_lookup",
     "ERR-7215 on VAT validation. What has to change?",
     ANSWER, [("HC-4005", ["ERR-7215", "legal entity name"])]),
    ("P18", "code_lookup",
     "US customer getting ERR-7310. What do I ask them for?",
     ANSWER, [("HC-4005", ["ERR-7310", "current certificate"])]),

    # --- symptom: customer wording, no code anywhere in the message --------
    ("P19", "symptom",
     "Customer says the pay button does nothing. It happened on 1 June at 03:12 UTC. "
     "Do I raise a payments incident?",
     ANSWER, [("HC-4001", ["read-only for four hours"])]),
    ("P20", "symptom",
     "Renewal keeps failing and the account shows no default payment method. "
     "The card was old. What happened?",
     ANSWER, [("HC-4003", ["24 months were dropped", "add a payment method again"])]),
    ("P21", "symptom",
     "Customer says their webhooks stopped working after the migration. "
     "They see no errors at all on their side.",
     ANSWER, [("HC-4006", ["goes quiet rather than erroring"])]),
    ("P22", "symptom",
     "Customer says invoice numbers have gaps and thinks an invoice is missing.",
     ANSWER, [("HC-4002", ["see gaps in their own sequence"])]),
    ("P23", "symptom",
     "Customer sent a screenshot where the invoice number field is empty. "
     "Is payment due?",
     ANSWER, [("HC-4002", ["still a draft and no payment is due yet"])]),
    ("P24", "symptom",
     "Customer is upset that their VAT number is suddenly invalid after years of working.",
     ANSWER, [("HC-4005", ["The number really is invalid"])]),
    ("P25", "symptom",
     "Customer says a tiny proration charge on their upgrade looks wrong.",
     ANSWER, [("HC-4004", ["by the second rather than by the day"])]),
    ("P26", "symptom",
     "Customer got an extra authentication prompt paying with Apple Pay after migration. "
     "Is something wrong?",
     ANSWER, [("HC-4003", ["once per device"])]),

    # --- policy: can I do this, may I do this ------------------------------
    ("P27", "policy",
     "The invoice is already paid but it shows an error code. Can I void it?",
     ANSWER, [("HC-4002", ["Never void an invoice that a customer has already paid"])]),
    ("P28", "policy",
     "Can I just mark the account tax exempt to clear the tax error?",
     ANSWER, [("HC-4005", ["Never mark an account as tax exempt to clear an error"])]),
    ("P29", "policy",
     "Customer downgraded mid-term. Do they get a credit note?",
     ANSWER, [("HC-4004", ["Downgrades never prorate", "no credit is due"])]),
    ("P30", "policy",
     "How much account credit can I issue without asking for approval?",
     ANSWER, [("HC-4003", ["250 in account currency"])]),
    ("P31", "policy",
     "Customer wants an extension on the v1 API sunset. Can I give them one?",
     ANSWER, [("HC-4006", ["There is no extension process", "routed to their account manager"])]),
    ("P32", "policy",
     "Customer removed a seat mid-term. Does the current invoice go down?",
     ANSWER, [("HC-4004", ["does not reduce the current invoice"])]),
    ("P33", "policy",
     "Can I edit the tax code on a finalised invoice so the total matches?",
     ANSWER, [("HC-4002", ["Never edit tax codes on a historical invoice"])]),

    # --- procedure: how do I actually do it --------------------------------
    ("P34", "procedure",
     "A VAT ID failed VIES validation. Walk me through correcting it.",
     ANSWER, [("HC-4005", ["ERR-7203", "Revalidate on the Tax tab"])]),
    ("P35", "procedure",
     "I need to reissue a corrected invoice. Does it get a new invoice number?",
     ANSWER, [("HC-4002", ["keeps the original invoice number", "revision suffix"])]),
    ("P36", "procedure",
     "The balance endpoint is gone from the API. How does the customer get a balance now?",
     ANSWER, [("HC-4006", ["GET /v2/billing/ledger/entries", "sum the open entries"])]),
    ("P37", "procedure",
     "A subscription got suspended for non-payment. How long is the data kept?",
     ANSWER, [("HC-4004", ["data for 60 days", "cannot be restored"])]),
    ("P38", "procedure",
     "Customer's webhook endpoint was down and they have fixed it. "
     "Do the queued events fire straight away?",
     ANSWER, [("HC-4006", ["per endpoint, not per event", "not immediately"])]),
    ("P39", "procedure",
     "How many payment attempts happen before we suspend the subscription?",
     ANSWER, [("HC-4003", ["14 days after attempt 1", "Suspension email"])]),

    # --- multi_part: two questions in one message, which agents always send -
    ("P40", "multi_part",
     "Two things. What causes ERR-4021, and can I just delete the duplicate usage record?",
     ANSWER, [("HC-4002", ["ERR-4021", "Never delete the usage record directly"])]),
    ("P41", "multi_part",
     "Customer has ERR-5108 on renewal and also wants to know why their invoice "
     "layout looks different now.",
     ANSWER, [
         ("HC-4003", ["ERR-5108", "re-enter the card once"]),
         ("HC-4001", ["tax is now calculated per line item"]),
     ]),
    ("P42", "multi_part",
     "Account badge says MIG-220. What does that mean and what is my action?",
     ANSWER, [("HC-4001", ["MIG-220", "Do not reissue invoices yourself"])]),
    ("P43", "multi_part",
     "Can I refund this to the original card, and if not, what do I do instead?",
     ANSWER, [("HC-4003", ["token was dropped during migration", "issued as account credit instead"])]),
    ("P44", "multi_part",
     "Customer hit ERR-7208 yesterday and ERR-7302 today. What are both and what do I do?",
     ANSWER, [
         ("HC-4005", ["ERR-7208", "Retry after one hour"]),
         ("HC-4005", ["ERR-7302", "Set a tax code on the product"]),
     ]),
    ("P45", "multi_part",
     "Their integration broke on two things: the pay call and the plan field. "
     "What changed in v2 for each?",
     ANSWER, [
         ("HC-4006", ["POST /v2/billing/invoices/{id}/payments", "settles asynchronously"]),
         ("HC-4006", ["capability-tier name"]),
     ]),

    # --- noisy: how the message actually arrives, typos and all ------------
    ("P46", "noisy",
     "err 4032 pls",
     ANSWER, [("HC-4002", ["ERR-4032", "Tax Codes"])]),
    ("P47", "noisy",
     "MIG310 what to do",
     ANSWER, [("HC-4001", ["MIG-310", "Wait one night"])]),
    ("P48", "noisy",
     "5114 insufficent funds? do we retry",
     ANSWER, [("HC-4003", ["ERR-5114", "dunning schedule will retry"])]),
    ("P49", "noisy",
     "invocie error 4010 addres missing",
     ANSWER, [("HC-4002", ["ERR-4010", "Customer Details"])]),
    ("P50", "noisy",
     "gstin format india?",
     ANSWER, [("HC-4005", ["GSTIN", "15 characters"])]),

    # --- vague: under-specified. The right answer names what is missing ----
    ("P51", "vague",
     "invoice error, what do I do?",
     REFUSE, []),
    ("P52", "vague",
     "Customer is angry about their bill. What should I say?",
     REFUSE, []),
    ("P53", "vague",
     "it's broken since the migration",
     REFUSE, []),
    ("P54", "vague",
     "what's the code for this?",
     REFUSE, []),

    # --- cross_article: the answer lives in two different articles ---------
    ("P55", "cross_article",
     "A renewal failed and the subscription is now past due. Which dunning attempt "
     "is that, and does the subscription cancel?",
     ANSWER, [
         ("HC-4003", ["7 days after attempt 1", "Past due"]),
         ("HC-4004", ["does not cancel the subscription"]),
     ]),
    ("P56", "cross_article",
     "Customer was on Business 100 and their card was declined with ERR-5199. "
     "What plan are they on now, and what do I do about the decline?",
     ANSWER, [
         ("HC-4004", ["Business 100", "Scale"]),
         ("HC-4003", ["ERR-5199", "Payments Ops"]),
     ]),
    ("P57", "cross_article",
     "An invoice failed with ERR-4032 and the customer also has ERR-7203 on their "
     "VAT ID. Are the two related?",
     ANSWER, [
         ("HC-4002", ["ERR-4032", "Tax Codes"]),
         ("HC-4005", ["ERR-7203", "VIES"]),
     ]),

    # --- out_of_corpus: genuinely not in the six articles ------------------
    ("P58", "out_of_corpus",
     "What is our SLA for a P1 billing incident?",
     REFUSE, []),
    ("P59", "out_of_corpus",
     "How do I issue this refund from the Stripe dashboard?",
     REFUSE, []),
    ("P60", "out_of_corpus",
     "What is the list price of the Growth plan in euros?",
     REFUSE, []),
]


W5_POOL: list[dict] = [
    {
        "id": qid,
        "kind": kind,
        "question": question,
        "expected_behaviour": behaviour,
        "requirements": [
            {"article_id": article, "must_contain": list(strings)}
            for article, strings in requirements
        ],
    }
    for qid, kind, question, behaviour, requirements in _RAW
]

POOL_BY_ID: dict[str, dict] = {q["id"]: q for q in W5_POOL}


def pool_composition() -> dict[str, int]:
    """How many of each traffic kind the pool holds."""
    counts: dict[str, int] = {kind: 0 for kind in KINDS}
    for q in W5_POOL:
        counts[q["kind"]] += 1
    return counts


def _self_check() -> None:
    """Structural checks that do not need the corpus or an index."""
    ids = [q["id"] for q in W5_POOL]
    assert len(ids) == len(set(ids)), "duplicate question id in the pool"
    assert len(W5_POOL) == 60, f"pool is {len(W5_POOL)}, expected 60"
    for q in W5_POOL:
        assert q["kind"] in KINDS, f"{q['id']}: unknown kind {q['kind']}"
        assert q["expected_behaviour"] in (ANSWER, REFUSE), q["id"]
        if q["expected_behaviour"] == ANSWER:
            assert q["requirements"], f"{q['id']}: answerable but no requirements"
            for req in q["requirements"]:
                assert req["must_contain"], f"{q['id']}: empty must_contain"
        else:
            assert not q["requirements"], f"{q['id']}: refusal must have no requirements"


_self_check()


if __name__ == "__main__":
    print(f"pool: {len(W5_POOL)} questions")
    for kind, count in pool_composition().items():
        print(f"  {kind:<15} {count}")
    answerable = sum(1 for q in W5_POOL if q["expected_behaviour"] == ANSWER)
    print(f"  {'-' * 22}")
    print(f"  expect answer   {answerable}")
    print(f"  expect refusal  {len(W5_POOL) - answerable}")
