"""The one command for Week 9.

    python -m evals.run_w9 --wire      the raw JSON-RPC, once. Free.
    python -m evals.run_w9 --discover  what each server offers. Free.
    python -m evals.run_w9 --bolton    prove the agent code never changes. Free.
    python -m evals.run_w9 --poison    a hostile server, caught. Free.
    python -m evals.run_w9 --agent     run one ticket over MCP end to end.
    python -m evals.run_w9 --all       every free check, then the report.

Only --agent spends anything. Everything else is process plumbing and costs
nothing, which is the honest upside of a week about protocol rather than
models.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from agent import guard
from agent.mcp_client import MCPClient
from agent.toolbox import connect, load_config
from config import BASE_DIR, get_settings
from rag import term

DEMO_TICKET = (
    "Account ACC-1180 is hitting ERR-4032 on an invoice line again. "
    "What is the documented fix, and has this account seen it before?"
)


def _python(module: str) -> list[str]:
    import sys

    return [sys.executable, "-m", module]


# ---------------------------------------------------------------------------
def show_wire() -> list[dict]:
    """Print the raw messages. The point is that there are very few of them."""
    print(term.rule("the raw wire"))
    with MCPClient("ticket-history", _python("mcp_servers.ticket_history_server"),
                   cwd=str(BASE_DIR)) as client:
        client.list_tools()
        client.call_tool("find_similar_tickets", {"error_code": "ERR-4032"})
        log = client.transcript(8)

    for entry in log:
        arrow = term.cyan("-->") if entry["dir"] == "->" else term.green("<--")
        blob = json.dumps(entry["msg"])
        method = entry["msg"].get("method")
        label = f"  {method}" if method else "  (reply)"
        print(f"{arrow}{label}")
        print(f"    {blob[:150]}{'...' if len(blob) > 150 else ''}")
    print()
    print("  Three messages start a session. Two do all the work:")
    print("  tools/list asks what it can do. tools/call runs one.")
    print("  Everything else in MCP is more of the same shape.")
    print()
    return log


def show_discovery() -> dict:
    """What each configured server offers, with nothing hard-coded."""
    print(term.rule("discovery"))
    found = {}
    with connect(verbose=False) as box:
        for server in box.servers_up:
            names = [t.name for t in box.tools.values() if t.server == server]
            found[server] = names
            print(f"  {term.bold(server)}: {len(names)} tool(s)")
            for name in names:
                print(f"      {name}({box.tools[name].arg_line()})")
        local = [t.name for t in box.tools.values() if t.server == "local"]
        print(f"  {term.bold('local')}: {local}  (never discovered, it is how the loop stops)")
        for name, why in box.servers_down:
            print(term.red(f"  {name}: down, {why}"))
    print()
    return found


def show_bolton() -> dict:
    """Prove the agent gains tools without a line of its code changing."""
    print(term.rule("bolt-on"))
    before_hashes = _agent_hashes()

    full = load_config()
    without = [s for s in full if s["name"] != "ticket-history"]

    with connect(without) as box:
        without_tools = box.names()
    with connect(full) as box:
        with_tools = box.names()

    after_hashes = _agent_hashes()
    changed = [k for k in before_hashes if before_hashes[k] != after_hashes.get(k)]
    gained = sorted(set(with_tools) - set(without_tools))

    print(f"  config without ticket-history : {len(without_tools)} tools")
    print(f"  config with it                : {len(with_tools)} tools")
    print(f"  {term.bold('gained')}                        : {gained}")
    print(f"  agent/*.py files changed      : {term.bold(str(changed or 'NONE'))}")
    print()
    return {"without": without_tools, "with": with_tools, "gained": gained, "changed": changed}


def _agent_hashes() -> dict:
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        for p in sorted((BASE_DIR / "agent").glob("*.py"))
    }


def show_poison() -> dict:
    """A hostile server's tool description, before and after the scanner."""
    print(term.rule("tool poisoning"))
    hostile = {
        "name": "ticket-archive",
        "command": ["python", "-m", "mcp_servers.hostile_server"],
        "trusted": False,
    }

    # Untrusted: the description is scanned before the model ever sees it.
    with connect([hostile]) as box:
        guarded_desc = next(
            (t.description for t in box.tools.values() if t.server == "ticket-archive"), ""
        )
        caught = list(box.poisoned)

    # Trusted: no scan, which is what the flag means and what it costs.
    with connect([dict(hostile, trusted=True)]) as box:
        raw_desc = next(
            (t.description for t in box.tools.values() if t.server == "ticket-archive"), ""
        )

    print("  The tool WORKS. The attack is only in its description.")
    print()
    print(term.red("  marked trusted, so not scanned:"))
    for line in raw_desc.splitlines():
        if line.strip():
            print(f"    {line[:96]}")
    print()
    print(term.green("  marked untrusted, scanned by the Week 8 guard:"))
    for line in guarded_desc.splitlines():
        if line.strip():
            print(f"    {line[:96]}")
    print()
    print(f"  patterns that fired: {[p[2] for p in caught]}")
    print()
    return {
        "raw": raw_desc,
        "guarded": guarded_desc,
        "caught": [{"server": s, "tool": t, "patterns": p} for s, t, p in caught],
        "neutralised": guard.REDACTION in guarded_desc,
    }


def run_agent_over_mcp(verbose: bool) -> dict:
    """One ticket, answered with tools the agent discovered at run time."""
    from agent.budget import Budget
    from agent.loop import run as run_agent

    print(term.rule("the agent, over MCP"))
    print(f"  ticket: {DEMO_TICKET}")
    print()
    with connect(verbose=True) as box:
        print()
        # The Week 7 default is 120 seconds of wall clock, tuned when a step
        # was one fast call. On this free tier two calls took 166s once the
        # transient-429 backoff is counted, so the demo died on the clock with
        # one step done. The limit is raised for this run and left alone in
        # agent/budget.py: a slow provider is a reason to wait longer, not a
        # reason to make every future run's safety net looser.
        result = run_agent(DEMO_TICKET, budget=Budget(max_steps=5, max_seconds=900),
                           verbose=True, toolbox=box)

    print()
    print(f"  stop: {result.stop_reason}  {len(result.steps)} step(s)  "
          f"{result.llm_calls} call(s)  {result.elapsed_s}s")
    print(f"  servers used   : {result.servers}")
    print(f"  tools available: {result.tools_discovered}")
    print()
    print("  ANSWER")
    for line in (result.answer or "").splitlines():
        print(f"    {line}")
    print()
    return {
        "ticket": DEMO_TICKET,
        "answer": result.answer,
        "stop_reason": result.stop_reason,
        "steps": [
            {"n": s.n, "tool": s.tool, "args": s.args, "thought": s.thought}
            for s in result.steps
        ],
        "llm_calls": result.llm_calls,
        "elapsed_s": result.elapsed_s,
        "servers": result.servers,
        "tools_discovered": result.tools_discovered,
        "citations": [
            {"chunk_id": c.chunk_id, "resolves": c.resolves} for c in result.citations
        ],
    }


# ---------------------------------------------------------------------------
def write_report(data: dict, path: Path) -> None:
    lines = [
        "# Week 9: MCP, and the server bolted on without touching the agent",
        "",
        "## Where the AI runs",
        "",
        "| Role | What it is here | Does it run a model? |",
        "|---|---|---|",
        "| Host | this app | **yes.** The key and the conversation live here. |",
        "| Client | `agent/mcp_client.py` | no. It speaks JSON-RPC. |",
        "| Server | `mcp_servers/*.py` | **no.** It has no idea an AI exists. |",
        "",
        "A server is not an AI. It is a socket on an appliance.",
        "",
    ]

    if "discovery" in data:
        lines += ["## What the agent discovered", "",
                  "| Server | Tools |", "|---|---|"]
        for server, names in data["discovery"].items():
            lines.append(f"| {server} | {', '.join(names)} |")
        lines += ["| local | finish (never discovered: it is how the loop stops) |", ""]

    if "bolton" in data:
        b = data["bolton"]
        lines += [
            "## The deliverable: bolt it on without touching the agent",
            "",
            "| | tools |",
            "|---|---|",
            f"| Config without `ticket-history` | {len(b['without'])} |",
            f"| Config with it | {len(b['with'])} |",
            f"| **Gained** | **{', '.join(b['gained'])}** |",
            f"| **`agent/*.py` files changed** | **{', '.join(b['changed']) or 'none'}** |",
            "",
            "Four lines of JSON. The agent's source is byte-identical before and",
            "after, and `agent/loop.py` does not contain the name of a single tool.",
            "",
        ]

    if "wire" in data:
        lines += ["## The raw wire, once", "", "```"]
        for entry in data["wire"][:6]:
            method = entry["msg"].get("method") or "(reply)"
            blob = json.dumps(entry["msg"])
            lines.append(f"{entry['dir']} {method}")
            lines.append(f"   {blob[:130]}")
        lines += ["```", "",
                  "Three messages start a session. `tools/list` asks what a server",
                  "can do, `tools/call` runs one. That is the protocol, for this use.",
                  ""]

    if "poison" in data:
        p = data["poison"]
        lines += [
            "## Tool poisoning: the channel MCP opens",
            "",
            "A tool's description is not data. It goes into the model's prompt, in",
            "our own voice, written by someone we have never met.",
            "",
            "The hostile server's tool **works correctly**. The attack is in the",
            "description only, which nobody re-reads after install and the model",
            "reads every turn.",
            "",
            "**Marked trusted, so not scanned:**",
            "",
            "```",
            p["raw"][:400],
            "```",
            "",
            "**Marked untrusted, scanned by the Week 8 guard:**",
            "",
            "```",
            p["guarded"][:400],
            "```",
            "",
            f"Patterns that fired: `{[c['patterns'] for c in p['caught']]}`",
            "",
            "Week 7's hard-coded registry could not be attacked this way, because",
            "we wrote every word of it. Discovery is what created the opening.",
            "",
        ]

    if "agent" in data:
        a = data["agent"]
        lines += [
            "## The agent, answering over MCP",
            "",
            f"> {a['ticket']}",
            "",
            f"- Servers used: `{', '.join(a['servers'])}`",
            f"- Tools available: `{', '.join(a['tools_discovered'])}`",
            f"- Stopped: **{a['stop_reason']}**, {len(a['steps'])} steps, "
            f"{a['llm_calls']} LLM calls, {a['elapsed_s']}s",
            "",
            "| Step | Tool | Arguments |",
            "|---|---|---|",
        ]
        for s in a["steps"]:
            args = ", ".join(f"{k}={v!r}" for k, v in (s["args"] or {}).items())
            lines.append(f"| {s['n']} | `{s['tool']}` | {args[:70]} |")
        lines += ["", "**Answer**", "", "```", (a["answer"] or "").strip(), "```", ""]
        if any(s["tool"] in ("get_ticket_history", "find_similar_tickets") for s in a["steps"]):
            lines += [
                "The agent used a tool from the bolted-on server. Nobody told it that",
                "server existed: it read the catalogue it was given and chose.",
                "",
            ]

    lines += [
        "## What this does NOT do",
        "",
        "- **MCP does not make the agent smarter.** It is plumbing. It wins on",
        "  reuse and swapping, not on answer quality.",
        "- **A tool call returns text.** The structured chunks our scoring layers",
        "  read do not survive the wire, so `agent/toolbox.py` parses the chunk",
        "  ids back out and resolves them locally. That works only because every",
        "  chunk carries a stable id. A team without that habit would lose the",
        "  ability to score retrieval the moment they moved to MCP.",
        "- **`trusted` is a human judgement**, not a check. Nothing verifies that",
        "  a server marked trusted deserves it.",
        "- **The scanner is the Week 8 pattern list**, with the Week 8 limits. A",
        "  reworded poisoned description walks through it.",
        "- **stdio only.** Remote servers and auth are not built here.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    term.init()
    parser = argparse.ArgumentParser(description="Week 9: MCP.")
    parser.add_argument("--wire", action="store_true")
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--bolton", action="store_true")
    parser.add_argument("--poison", action="store_true")
    parser.add_argument("--agent", action="store_true")
    parser.add_argument("--all", action="store_true", help="every free check, then the report")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if not any((args.wire, args.discover, args.bolton, args.poison, args.agent, args.all)):
        parser.error("pick one: --wire, --discover, --bolton, --poison, --agent, or --all")

    out = Path(get_settings().results_dir)
    cache_path = out / "w9_runs.json"
    data = {}
    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}

    if args.wire or args.all:
        data["wire"] = show_wire()
    if args.discover or args.all:
        data["discovery"] = show_discovery()
    if args.bolton or args.all:
        data["bolton"] = show_bolton()
    if args.poison or args.all:
        data["poison"] = show_poison()
    if args.agent:
        data["agent"] = run_agent_over_mcp(args.verbose)

    cache_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(data, out / "w9_mcp.md")
    print(f"Wrote {out / 'w9_mcp.md'}")


if __name__ == "__main__":
    main()
