# Week 10: the squad against the single agent

- Tickets: 12, the same set both sides, from `evals/w7_tickets.py`
- Model: `poolside/laguna-s-2.1:free`
- One MCP toolbox, started once and handed to both, so neither pays a
  start-up the other avoided.
- The squad is a manager plus two specialists: `code_desk` and `policy_desk`.
- **Every number below covers the 12 ticket(s) BOTH sides
  completed**: T01, T02, T03, T04, T05, T06, T07, T08, T09, T10, T11, T12. A run only one side
  finished is excluded, because two different case sets in one row is not
  a comparison.

## The four numbers

| | single agent | squad | squad vs single |
|---|---|---|---|
| **Quality** passed | 11/12 | 10/12 | -1 |
| Parts of the ticket cited | 100% | 94% | -6 pts |
| Multi-part fully answered | 6/6 | 5/6 | -1 |
| **Speed** median s/ticket | 19.16 | 28.32 | 1.5x |
| **Tokens** total | 61,478 | 41,832 | 0.7x |
| Input tokens | 56,854 | 36,338 | 0.6x |
| Output tokens | 4,624 | 5,494 | 1.2x |
| **Cost** reported by provider | $0.0000 | $0.0000 | free tier |
| Cost, priced estimate | $0.0113 | $0.0087 | 0.8x |
| LLM calls | 40 | 64 | 1.6x |

The provider reports a cost of exactly $0 because the model is `:free`.
That is true and useless for a comparison, so the priced row applies a
published rate to the real token counts. It is arithmetic on a rate
card, not a bill, and the ratio is what matters rather than the figure.

## Where the squad's tokens went

| Participant | calls | input tokens | output tokens |
|---|---|---|---|
| policy_desk | 14 | 13,982 | 1,373 |
| code_desk | 26 | 12,637 | 2,042 |
| manager | 24 | 9,719 | 2,079 |

Input tokens are the interesting column. Every hand-off re-sends the
ticket, the specialist's own system prompt and its tool catalogue, and
the specialists' findings then go into the manager's final prompt as
well. The same ticket text is paid for three or four times.

## By ticket shape

| Shape | single passed | squad passed | single tokens | squad tokens |
|---|---|---|---|---|
| multi | 6/6 | 5/6 | 28,221 | 23,359 |
| single | 4/4 | 4/4 | 11,770 | 7,777 |
| refuse | 1/2 | 1/2 | 21,487 | 10,696 |

## Per ticket

| Ticket | shape | single pass | squad pass | single tokens | squad tokens | squad parts |
|---|---|---|---|---|---|---|
| T01 | multi | yes | yes | 3,770 | 3,376 | 2 |
| T02 | multi | yes | yes | 3,825 | 3,373 | 2 |
| T03 | multi | yes | no | 5,516 | 2,934 | 1 |
| T04 | multi | yes | yes | 4,286 | 4,182 | 2 |
| T05 | multi | yes | yes | 6,091 | 5,360 | 3 |
| T06 | multi | yes | yes | 4,733 | 4,134 | 2 |
| T07 | single | yes | yes | 3,741 | 1,987 | 1 |
| T08 | single | yes | yes | 2,220 | 1,870 | 1 |
| T09 | single | yes | yes | 2,240 | 1,893 | 1 |
| T10 | single | yes | yes | 3,569 | 2,027 | 1 |
| T11 | refuse | yes | yes | 6,211 | 5,141 | 1 |
| T12 | refuse | no | no | 15,276 | 5,555 | 2 |

## The verdict

**Keep the single.**

The single agent passes 11 tickets against 10. The squad is both worse and 0.7x more expensive in tokens. There is nothing to weigh.

The rule that picked this is `verdict()` in `evals/run_w10.py`. It was
written before the race ran, quality decides before cost, and a gap
smaller than one whole ticket counts as no gap on a set this size.

## When a squad WOULD be worth it

Not here, and the reasons are specific rather than general:

- **The parts are not independent.** Looking up ERR-4032 tells you
  nothing that changes how you look up ERR-7215, so splitting them
  buys no information the single agent lacked.
- **Nothing runs in parallel.** The specialists run one after another
  in one process, so the wall clock gets the hand-off cost with none
  of the concurrency that would pay for it.
- **The instructions are not truly different.** Both specialists
  ground, cite and refuse by the same rules. The split is by TOOL,
  and a tool catalogue is cheap to hand one agent.

A squad earns its keep when parts are genuinely independent AND run
at the same time, or when a part needs instructions so different
that putting them in one prompt would damage the rest. On a support
ticket against one corpus, neither is true.

