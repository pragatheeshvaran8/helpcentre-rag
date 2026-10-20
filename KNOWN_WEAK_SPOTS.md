# Known weak spots

This is the list of things that are wrong with this app, written by the person
who built it, before anyone asked.

The point is not modesty. A weak spot you found yourself comes with a
measurement and a fix. A weak spot someone else finds in a demo comes with a
guess. Everything here is the first kind.

Each entry says what is wrong, why it matters, and what the fix would be. None
of them are blockers for the demo. All of them are real.

---

### The eval set is 60 questions, written by one person

**Why it matters:** Every accuracy number in this project rests on 60 cases.
I wrote all of them. I knew what the corpus said while writing them, so the
questions are more answerable than real tickets are. A different set would move
the headline figure, and I cannot say by how much.

**Fix:** Take 100 real tier-1 tickets, strip the account details, and score
against those instead. Keep the 60 as a regression set.

---

### The judge agrees with itself, not with a second opinion

**Why it matters:** Week 6 measured the judge against my own grading and found
95% agreement on relevance. That number is worthless, because the judge said
"relevant" every single time. With no variance there is nothing to agree about.
Faithfulness scored 20/20 with kappa 1.0, which is real. Relevance is not.

**Fix:** Grade a batch where some answers are deliberately off-topic, so the
judge has a chance to disagree. Until then, trust the faithfulness number and
ignore the relevance one.

---

### Retrieval is tuned on one corpus of six articles

**Why it matters:** The hybrid retriever went from 0.75 to 0.95 hit-rate@3 on
this corpus. Six articles is small enough that BM25's rare-word scoring has
very little to get wrong. On 600 articles the same settings would need
rechecking, in particular the RRF constant and the score threshold that decides
a refusal.

**Fix:** Re-run the Week 4 search evaluation after any real corpus is loaded.
The command does not change; only the numbers do.

---

### The injection guard is a list of patterns, and lists are beatable

**Why it matters:** Six regular expressions catch the six attack shapes I
tested. A phrasing I did not think of walks through. The guard is a speed bump,
not a wall, and I would not describe it as a security control.

**Why it is still worth having:** the real containment is that the tools can
only read the help centre. An injection that succeeds completely can make the
app say something wrong. It cannot make it refund money, email anyone, or
reach a system that is not the corpus. That is least privilege doing the work,
not the regexes.

**Fix:** Keep the tools read-only. Treat every new tool as the thing that
changes the risk, and review the tool list rather than the pattern list.

---

### The answer cache matches on word overlap, not meaning

**Why it matters:** Two tickets that share 80% of their words are treated as
the same question. Measured on real traffic that served 0 wrong answers out of
48, at four different thresholds. That is a measurement on this traffic, not a
guarantee. A pair like "can I refund to the card" and "can I not refund to the
card" is exactly the shape that would slip through, and my set did not contain
one.

**Fix:** Add negation detection before the overlap test, or move to an
embedding similarity with the same fenced config. Keep the risk measurement
beside the saving either way.

---

### Nothing runs at the same time

**Why it matters:** The Week 10 squad ran its specialists one after another in
one process. The speed comparison therefore pays every hand-off and collects
none of the concurrency that would justify one. The verdict "keep the single
agent" is honest for this setup, and it is the single biggest thing that could
change if the specialists ran in parallel.

**Fix:** Run the specialists concurrently and re-race. Until that is done, the
speed row is a fact about this implementation, not about multi-agent systems.

---

### The free tier caps the app at 50 calls a day

**Why it matters:** This is not a flaw in the design, but it shapes everything.
Every expensive path caches, resumes and reports from cache, because a run that
cannot be resumed is a run that cannot be finished. It also means no number
here comes from a large sample.

**Fix:** A paid key. Nothing in the code changes.

---

### Twenty Week 5 traces were recorded under the old prompt

**Why it matters:** The prompt moved from v1 to v2 in Week 6. Those traces
record what v1 did. They are still replayable, because v1 is still in the file
and the corpus hash has not moved, and the test suite now checks those two
things rather than checking that every trace matches the current prompt.

**Fix:** None needed. It is listed here because "0 of 20 traces are on the
current prompt" looks alarming in the test output and deserves an answer.

---

## What I would do first

1. Replace the 60 hand-written cases with real tickets. Every other number
   depends on this one.
2. Give the judge something to disagree with, then re-measure relevance.
3. Run the squad specialists in parallel and re-race.

Everything else on this page can wait.
