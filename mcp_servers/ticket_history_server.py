"""The ticket-history server. The one that gets bolted on.

    python -m mcp_servers.ticket_history_server

WHY THIS IS A SEPARATE SERVER AND NOT ANOTHER FUNCTION
    Ticket history is a different system. In a real company it is Zendesk or
    Jira or something internal, owned by another team, behind its own auth,
    with its own release schedule. It is not in the help-centre corpus and it
    never will be.

    That is exactly the case MCP is for. Before this week, adding it meant
    editing agent/tools.py: a new function, a new entry in the registry, a new
    description, a redeploy of the agent. Now it means adding four lines to
    mcp_servers.json and restarting. The agent's code does not change at all,
    and this file proves it.

WHAT IS IN HERE
    A small fixed store of past tickets. Invented, obviously, but shaped like
    the real thing: an account, an error code, what the agent did, and whether
    it worked. Two tools over it:

      get_ticket_history   everything logged for one account
      find_similar_tickets what other agents did about this error code

    The second is the interesting one. It answers a question the help centre
    cannot: the article says what the fix IS, and history says whether it
    actually worked last time.

WHERE THE AI RUNS
    Still not here. This process is a lookup over a dict.
"""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

server = MCPServer(
    name="ticket-history",
    instructions=(
        "Past support tickets for this billing product. Use it to see what was "
        "already tried on an account, or what other agents did about an error "
        "code and whether it worked."
    ),
)

# A stand-in for the ticketing system. Deliberately small and readable: the
# point of this week is the plumbing, not the data.
TICKETS: list[dict] = [
    {
        "ticket": "SUP-2041",
        "account": "ACC-1180",
        "opened": "2026-08-14",
        "code": "ERR-4032",
        "summary": "Invoice line rejected after migration.",
        "action": "Re-mapped the line to a current tax code, reissued.",
        "outcome": "resolved",
    },
    {
        "ticket": "SUP-2088",
        "account": "ACC-1180",
        "opened": "2026-08-29",
        "code": "ERR-7215",
        "summary": "VAT ID stopped validating.",
        "action": "Updated the legal entity name to match the registration.",
        "outcome": "resolved",
    },
    {
        "ticket": "SUP-2114",
        "account": "ACC-1180",
        "opened": "2026-09-02",
        "code": "ERR-4032",
        "summary": "Same invoice line failed again on the next run.",
        "action": "Re-mapped again. Root cause was an unmapped legacy code on the product.",
        "outcome": "escalated to Billing Ops",
    },
    {
        "ticket": "SUP-1902",
        "account": "ACC-2276",
        "opened": "2026-07-30",
        "code": "ERR-5199",
        "summary": "Payment stuck, agent retried four times.",
        "action": "Retried. Extended the review window and made it worse.",
        "outcome": "escalated to Payments Ops",
    },
    {
        "ticket": "SUP-2203",
        "account": "ACC-2276",
        "opened": "2026-09-11",
        "code": "ERR-5108",
        "summary": "Card declined on renewal.",
        "action": "Asked the customer to re-enter the card once.",
        "outcome": "resolved",
    },
    {
        "ticket": "SUP-2250",
        "account": "ACC-3391",
        "opened": "2026-09-18",
        "code": "MIG-220",
        "summary": "Partial migration badge, customer chasing a credit note.",
        "action": "Opened a Billing Ops ticket with the account ID.",
        "outcome": "open",
    },
]


def _render(rows: list[dict], header: str) -> str:
    if not rows:
        return f"{header}\nNo matching tickets."
    lines = [header]
    for t in rows:
        lines.append(
            f"\n[{t['ticket']}] {t['opened']}  account {t['account']}  {t['code']}"
            f"\n  what happened: {t['summary']}"
            f"\n  what the agent did: {t['action']}"
            f"\n  outcome: {t['outcome']}"
        )
    return "\n".join(lines)


@server.tool(
    description=(
        "Past support tickets for one account, newest last. Use this when the "
        "customer says a problem has happened before, or when you need to know "
        "what has already been tried on their account. Takes an account id like "
        "ACC-1180. It knows nothing about accounts it has no tickets for."
    )
)
def get_ticket_history(account_id: str) -> str:
    """Every logged ticket for one account."""
    acc = (account_id or "").strip().upper()
    rows = sorted((t for t in TICKETS if t["account"] == acc), key=lambda t: t["opened"])
    return _render(rows, f"Ticket history for {acc}:")


@server.tool(
    description=(
        "What other agents did about one error code, and whether it worked. Use "
        "this after you know the documented fix, to check whether that fix has "
        "actually held before. Takes one code like ERR-4032. This is history, "
        "not policy: the help centre says what the fix is, this says how it went."
    )
)
def find_similar_tickets(error_code: str) -> str:
    """Past tickets that carried this error code."""
    code = (error_code or "").strip().upper().replace(" ", "")
    if code and "-" not in code and len(code) > 3:
        code = f"{code[:3]}-{code[3:]}"
    rows = sorted((t for t in TICKETS if t["code"] == code), key=lambda t: t["opened"])
    return _render(rows, f"Past tickets mentioning {code}:")


if __name__ == "__main__":
    server.run(transport="stdio")
