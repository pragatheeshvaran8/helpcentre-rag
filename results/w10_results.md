# Week 10 — Multi-agent, with evidence

The task was to build a manager plus two specialists, race it against the
single agent on the same tests, report quality, speed, tokens and cost, and
give an honest verdict.

**The verdict is keep the single agent.** It answers more of the tickets, it is
faster, and it makes 40 calls to the squad's 64. The squad does one thing
better than expected and one thing much worse, and both are in section 3.

**The race is complete: all twelve tickets, both sides.**

---

## 0. What this week produced

| | |
|---|---|
| Token and cost accounting | `agent/meter.py` |
| A manager and two specialists | `agent/squad.py` |
| The race | `evals/run_w10.py` |
| 48 new acceptance checks | `test_acceptance.py`, now 248 |

---

## 1. What makes the race fair

The mentor's first question is whether both sides ran on the same tests. Six
things are held identical, and a test asserts each one:

| Held constant | How |
|---|---|
| The tickets | the same twelve from `evals/w7_tickets.py`, untouched |
| The model | one setting, read once |
| The corpus | one chunk index |
| **The tools** | **one MCP toolbox, started once and handed to both** |
| Quality scoring | `evals/w7_race.py`, the same scorer |
| Path scoring | `evals/w8_trajectory.py`, the same scorer |

**The shared toolbox matters.** Starting a second set of MCP servers for the
squad would have charged it for a start-up the single agent never paid. A test
asserts `connect()` appears exactly once in the race file.

**The only difference is the topology.** One agent, or a manager and two
specialists.

---

## 2. The four numbers

Over all **twelve tickets**, both sides.

| | single agent | squad |
|---|---|---|
| **Quality** passed | **11/12** | 10/12 |
| Parts of the ticket cited | **100%** | 94% |
| Multi-part fully answered | **6/6** | 5/6 |
| **Speed** median s/ticket | **19.16s** | 28.32s |
| **Tokens** total | 61,478 | **41,832** |
| Input tokens | 56,854 | **36,338** |
| Output tokens | **4,624** | 5,494 |
| **Cost** reported | $0.00 | $0.00 |
| Cost, priced estimate | $0.0113 | **$0.0087** |
| **LLM calls** | **40** | 64 |

The provider reports $0.00 because the model is `:free`. That is true and
useless for a comparison, so the priced row applies a published rate to the
real token counts. **It is arithmetic on a rate card, not a bill**, and the
ratio is what matters rather than the figure.

---

## 3. Two findings, one of them against expectation

### The squad used FEWER tokens, not more

The brief says every hand-off re-sends everything, so a team costs several
times more. **On this app, measured over all twelve tickets, the opposite
happened: the squad spent 32% fewer tokens.**

The reason is the single agent's own shape:

- The single agent re-sends its **growing scratchpad** on every step, plus the
  **full five-tool catalogue**, every turn.
- A specialist gets a small focused prompt, its one question, and **only its own
  one to three tools**.

**The specialists' narrowness saves more than the hand-offs cost.** The hand-off
re-send is real and visible in the per-participant table below; it is simply
smaller than the context the single agent was already carrying.

| Participant | calls | input tokens | output tokens |
|---|---|---|---|
| policy_desk | 14 | 13,982 | 1,373 |
| code_desk | 26 | 12,637 | 2,042 |
| manager | 24 | 9,719 | 2,079 |

**The manager spends 9,719 input tokens producing no answer at all.** It splits
and it assembles. That is the pure overhead of having a team, and it is 27% of
the squad's input budget.

### But the squad made nearly twice the calls, and calls are what is rationed

| | single | squad |
|---|---|---|
| LLM calls on twelve tickets | 40 | **64** |

**On this provider the binding limit is calls per day, not tokens.** The race
hit the daily cap twice before it finished, and the squad is why: it burns the
quota at 1.6x the rate for the same work.

**So "cheaper in tokens" and "cheaper" are not the same sentence.** Which one
matters depends on how you are billed, and it is worth measuring both rather
than assuming.

---

## 4. The failure the topology created

The squad's one quality loss is T03, and it is the most instructive thing in
the week.

**The ticket asks two things:**

> A renewal failed and the subscription is showing past due. **Which dunning
> attempt is that?** Also their webhook endpoint was down for a few hours and
> they want to know **if they lost the events.**

**The manager split it into one task.** It handed the dunning half to
`policy_desk` and **dropped the webhook half entirely**.

No specialist ever saw it. The manager then appended a refusal for the part it
had itself discarded, producing an answer that both answers and refuses.

**The single agent answered both parts.** It had no bottleneck: it re-reads the
whole ticket on every turn.

**This is a failure mode the single agent cannot have.** A manager is a lossy
funnel. Whatever it drops at the split is gone, and no later step can recover
it, because the specialists only ever see what the manager chose to write down.

Adding a team did not just add cost. **It added a way to lose information.**

---

## 5. The verdict

**Keep the single agent.**

The rule that picked this is `verdict()` in `evals/run_w10.py`. It was written
before the race ran, and it can return either side:

1. **Quality decides first.** A cheaper wrong answer is not a saving.
2. "Materially" is one whole ticket. A smaller gap is noise on this set.
3. **If quality ties, cost decides**, in tokens rather than calls.

Here quality does not tie: 6/6 against 5/6. The squad is worse, slower, and
makes twice the calls, while saving tokens that this provider does not charge
for. **There is nothing to weigh.**

A test asserts the rule can pick the squad, so this is a result rather than a
foregone conclusion.

---

## 6. When a squad WOULD be worth it

Not here, and the reasons are specific rather than general:

- **The parts are not independent in a useful way.** Looking up ERR-4032 tells
  you nothing that changes how you look up ERR-7215. Splitting them buys no
  information the single agent lacked.
- **Nothing runs in parallel.** The specialists run one after another in one
  process, so the wall clock pays every hand-off and gets none of the
  concurrency that would justify it. This is the biggest single thing that
  would change the answer.
- **The instructions are not truly different.** Both specialists ground, cite
  and refuse by the same rules. The split is by **tool**, and a tool catalogue
  is cheap to hand to one agent.
- **The ticket is small.** A manager's split only pays when the thing being
  split is too big for one context. Twelve support tickets are not.

**A squad earns its keep when the parts are genuinely independent AND run at
the same time, or when one part needs instructions so different that putting
them in the same prompt would damage the rest.** On a support ticket against
one corpus, neither is true.

---

## 7. What this does NOT tell you

- **One ticket decides the quality verdict.** 11/12 against 10/12 is a
  one-ticket gap. The rule treats one whole ticket as material by design, and
  on twelve runs it is also close to noise. The supporting numbers point the
  same way (parts cited 100% against 94%, multi-part fully answered 6/6 against
  5/6), but a single ticket is doing a lot of work in the headline.
- **Twelve tickets is a small set.** A different mix would move this. The
  per-shape table is the honest view: the squad ties on single-part tickets and
  loses one multi-part and one out-of-corpus.
- **Nothing runs concurrently.** A squad whose specialists ran in parallel
  would have a completely different speed number. That is the honest caveat on
  the speed row.
- **One topology, chosen by me.** Manager plus two specialists split by tool.
  A different split, or three specialists, or a reviewer agent, would measure
  differently.
- **The cost figures are not a bill.** The model is free. The priced row is a
  rate card applied to real token counts.
- **A2A is implemented as concepts, not as a protocol.** Agent cards and the
  task lifecycle are real and tested. The wire format, HTTP discovery and
  streaming are not built, because they would be a second variable.

---

## 8. What was built, and what A2A means here

**Agent cards.** Each specialist publishes what it is for, what it is good at,
and which tools it may use. **The manager routes by reading cards**, and a test
asserts the manager's code names no specialist. Swap a card and the routing
changes with no manager edit. This is the same trick Week 9 played with tool
discovery.

**Task lifecycle.** Every hand-off is a task with a state: `submitted`,
`working`, then `completed` or `failed`. A specialist that fails fails its own
task; the manager carries on with the rest.

**Narrow specialists.** A specialist sees only its own instruction and only its
own tools. Reaching for another specialist's tool is refused and it gets
another turn. A specialist that could do everything would just be the single
agent with a longer prompt.

**MCP versus A2A, in one line:** MCP connects an agent to **tools**; A2A
connects an agent to **other agents**. This project now has both.

---

## 9. Reproducing it

```bash
python -m evals.run_w10 --race            # both sides, same tickets
python -m evals.run_w10 --ticket T01 -v   # watch one ticket, both ways
python -m evals.run_w10 --report          # rescore the cache. Free.
python test_acceptance.py                 # 248 checks
```

Every completed run is cached per side, so the race resumes after a rate limit
and pays only for what is missing. `--report` recomputes every number from the
cache and costs nothing.

---

## 10. Files

| File | What it is |
|---|---|
| `agent/meter.py` | Tokens and cost, from the provider's own report |
| `agent/squad.py` | Agent cards, task lifecycle, manager and specialists |
| `evals/run_w10.py` | The race, the scoring, and the verdict rule |
| `results/w10_race.md` | The generated comparison |
| `results/w10_handoffs.md` | Every split and every hand-off |

---

## 11. The one-line answer to the week's question

A team of agents cost us 17% fewer tokens, twice the calls, 40% more wall
clock, and one dropped half of one ticket, so we kept the single agent, and the
measurement that mattered most was not the one the hype warns about.
