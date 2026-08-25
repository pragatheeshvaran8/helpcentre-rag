"""Week 4 question set: one question per code in the corpus.

WHY A NEW SET
    The Week 3 set has 8 questions and every one passes, at k=5 and at k=3, on
    both chunkers. A set with no failures cannot be used to study failures.
    Week 4 needs questions that break.

    So this set covers every code in the 6 articles: 25 ERR codes and 5 MIG
    codes, 30 in total. Every answer was copied out of an article table, so
    every question has a known-correct location. Nothing here was tuned by
    looking at search output. The file is written before the hybrid retriever
    exists, exactly as in Week 3.

    These questions are deliberately hard for dense retrieval, and that is the
    point. A code like ERR-7208 is a rare token sitting in a table that looks
    almost identical to five other tables. Week 3 found one such failure by
    hand. This set finds all of them.

HIT RULE
    Same rule as Week 3, so the two weeks stay comparable. A question is a hit
    at k when one of the top k chunks has the expected article_id AND literally
    contains every must_contain string.

    must_contain is always the code plus one phrase unique to that row's fix.
    A chunk that holds the code but not the fix cannot answer the question, so
    it does not count.
"""
from __future__ import annotations

# id, code, question, article, section, must_contain
_RAW: list[tuple[str, str, str, str, str, list[str]]] = [
    # --- HC-4001, migration status codes -----------------------------------
    ("W1", "MIG-100",
     "An account shows the MIG-100 badge. What does it mean and what should the agent do?",
     "HC-4001", "Migration status codes -> MIG-100",
     ["MIG-100", "Treat the account as normal"]),
    ("W2", "MIG-140",
     "What does the MIG-140 badge mean, and do we need to do anything about it?",
     "HC-4001", "Migration status codes -> MIG-140",
     ["MIG-140", "Explain the write-off"]),
    ("W3", "MIG-220",
     "An account is showing MIG-220. What went wrong and what is the agent action?",
     "HC-4001", "Migration status codes -> MIG-220",
     ["MIG-220", "Do not reissue invoices yourself"]),
    ("W4", "MIG-310",
     "A customer badge says MIG-310. How long should we wait before escalating?",
     "HC-4001", "Migration status codes -> MIG-310",
     ["MIG-310", "Wait one night"]),
    ("W5", "MIG-450",
     "What does MIG-450 mean, and can the customer still change their plan?",
     "HC-4001", "Migration status codes -> MIG-450",
     ["MIG-450", "Escalate to Billing Ops immediately"]),

    # --- HC-4002, invoice error codes ---------------------------------------
    ("W6", "ERR-4010",
     "An invoice is stuck on ERR-4010. What is the cause and how do we clear it?",
     "HC-4002", "Invoice error codes -> ERR-4010",
     ["ERR-4010", "Customer Details"]),
    ("W7", "ERR-4021",
     "What causes ERR-4021 on an invoice, and what is the correct fix?",
     "HC-4002", "Invoice error codes -> ERR-4021",
     ["ERR-4021", "Rebuild Usage"]),
    ("W8", "ERR-4032",
     "A customer sees ERR-4032 on their invoice. What is the cause and the fix?",
     "HC-4002", "Invoice error codes -> ERR-4032",
     ["ERR-4032", "reissue the invoice"]),
    ("W9", "ERR-4044",
     "An invoice shows ERR-4044 with a negative total. What should the agent do?",
     "HC-4002", "Invoice error codes -> ERR-4044",
     ["ERR-4044", "Apply as Credit"]),
    ("W10", "ERR-4055",
     "We are seeing ERR-4055 on overlapping billing periods. Which invoice do we void?",
     "HC-4002", "Invoice error codes -> ERR-4055",
     ["ERR-4055", "Void the newer invoice"]),
    ("W11", "ERR-4061",
     "What does ERR-4061 mean, and can an agent fix it themselves?",
     "HC-4002", "Invoice error codes -> ERR-4061",
     ["ERR-4061", "cannot change invoice currency"]),
    ("W12", "ERR-4077",
     "An invoice PDF will not render and reports ERR-4077. How do we resolve it?",
     "HC-4002", "Invoice error codes -> ERR-4077",
     ["ERR-4077", "Regenerate PDF"]),
    ("W13", "ERR-4090",
     "An invoice has ERR-4090 and no ledger entry. Should we void it?",
     "HC-4002", "Invoice error codes -> ERR-4090",
     ["ERR-4090", "backfilled"]),

    # --- HC-4003, decline and token error codes -----------------------------
    ("W14", "ERR-5101",
     "A card was declined with ERR-5101. How many times should we retry?",
     "HC-4003", "Decline and token error codes -> ERR-5101",
     ["ERR-5101", "fraud block"]),
    ("W15", "ERR-5108",
     "A renewal failed with ERR-5108. What should the agent ask the customer to do?",
     "HC-4003", "Decline and token error codes -> ERR-5108",
     ["ERR-5108", "re-enter the card"]),
    ("W16", "ERR-5114",
     "What does ERR-5114 mean, and do we need to retry the payment manually?",
     "HC-4003", "Decline and token error codes -> ERR-5114",
     ["ERR-5114", "dunning schedule will retry"]),
    ("W17", "ERR-5127",
     "A payment failed with ERR-5127 after 3-D Secure. How long is the new link valid?",
     "HC-4003", "Decline and token error codes -> ERR-5127",
     ["ERR-5127", "Links expire after 30 minutes"]),
    ("W18", "ERR-5133",
     "A valid card is failing with ERR-5133. What is mismatched and how do we fix it?",
     "HC-4003", "Decline and token error codes -> ERR-5133",
     ["ERR-5133", "account tax country"]),
    ("W19", "ERR-5140",
     "A wallet payment is failing with ERR-5140. What are the customer's options?",
     "HC-4003", "Decline and token error codes -> ERR-5140",
     ["ERR-5140", "original device"]),
    ("W20", "ERR-5199",
     "We got ERR-5199 from the processor. Should the agent retry the charge?",
     "HC-4003", "Decline and token error codes -> ERR-5199",
     ["ERR-5199", "Escalate to Payments Ops"]),

    # --- HC-4004, plan change errors ----------------------------------------
    ("W21", "ERR-6203",
     "A plan change was rejected with ERR-6203. What is the cause and the fix?",
     "HC-4004", "Plan change errors -> ERR-6203",
     ["ERR-6203", "higher seat count"]),
    ("W22", "ERR-6210",
     "A customer cannot change plan and sees ERR-6210. Who handles it?",
     "HC-4004", "Plan change errors -> ERR-6210",
     ["ERR-6210", "Route to the account manager"]),
    ("W23", "ERR-6244",
     "What causes ERR-6244 on a plan change, and what should we wait for?",
     "HC-4004", "Plan change errors -> ERR-6244",
     ["ERR-6244", "hourly finalisation run"]),
    ("W24", "ERR-6250",
     "A plan change is blocked with ERR-6250. What has to happen first?",
     "HC-4004", "Plan change errors -> ERR-6250",
     ["ERR-6250", "Collect payment first"]),

    # --- HC-4005, tax validation error codes --------------------------------
    ("W25", "ERR-7101",
     "A tax ID was rejected with ERR-7101. What is usually wrong with it?",
     "HC-4005", "Tax validation error codes -> ERR-7101",
     ["ERR-7101", "Correct the format on the Tax tab"]),
    ("W26", "ERR-7203",
     "A VAT number is failing with ERR-7203. What causes it and how do we clear it?",
     "HC-4005", "Tax validation error codes -> ERR-7203",
     ["ERR-7203", "Revalidate on the Tax tab"]),
    ("W27", "ERR-7208",
     "What does ERR-7208 mean, and should we remove the customer's VAT ID?",
     "HC-4005", "Tax validation error codes -> ERR-7208",
     ["ERR-7208", "Retry after one hour"]),
    ("W28", "ERR-7215",
     "A VAT ID check returns ERR-7215. What do we need to change on the account?",
     "HC-4005", "Tax validation error codes -> ERR-7215",
     ["ERR-7215", "legal entity name"]),
    ("W29", "ERR-7302",
     "An invoice line item reports ERR-7302. What is missing and how do we fix it?",
     "HC-4005", "Tax validation error codes -> ERR-7302",
     ["ERR-7302", "Set a tax code on the product"]),
    ("W30", "ERR-7310",
     "A US customer is being charged tax and we see ERR-7310. What do we ask for?",
     "HC-4005", "Tax validation error codes -> ERR-7310",
     ["ERR-7310", "upload a current certificate"]),
]

W4_QUESTIONS: list[dict] = [
    {
        "id": qid,
        "code": code,
        "question": question,
        "expected_article_id": article,
        "expected_section": section,
        "must_contain": must_contain,
    }
    for qid, code, question, article, section, must_contain in _RAW
]

# The metric Week 4 is graded on.
W4_K = 3


def get_question(qid: str) -> dict:
    for q in W4_QUESTIONS:
        if q["id"] == qid:
            return q
    raise KeyError(f"Unknown question id: {qid}")
