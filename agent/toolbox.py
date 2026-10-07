"""Every tool the agent can reach, discovered rather than imported.

WHAT CHANGED THIS WEEK
    Before: agent/tools.py held a dict called TOOLS. Adding a capability meant
    writing a Python function, registering it, writing its description, and
    shipping the agent again.

    Now: this file starts the servers listed in mcp_servers.json, asks each one
    what it can do, and builds the catalogue from the answers. Adding a
    capability means four lines of JSON. The agent's code does not change, and
    nothing in agent/loop.py names a tool.

    That is the whole Week 9 deliverable, and it is checkable: delete the
    ticket-history block from the config and the agent loses two tools and
    keeps working.

WHAT STAYS LOCAL, AND WHY
    `finish` is not discovered and never will be. It is not a capability, it is
    the agent's own control flow: the way the loop stops. A server offering a
    tool called "finish" would be claiming the right to end our conversation.
    It stays in this process, defined by us.

THE THING MCP TAKES AWAY
    A tool call over MCP returns TEXT. That is the whole contract. Our local
    tools used to hand back the retrieved chunks as objects, and the Week 6
    checks read `article_id` and the chunk body off them to decide whether
    retrieval actually put the answer on screen.

    Those objects do not survive the wire. So the chunk ids are parsed back out
    of the returned text and resolved locally. That works only because the
    corpus labels every chunk with a stable id and the servers print it. If the
    text had said "according to the billing article", nothing downstream could
    have been scored.

    Worth being blunt about: going through a standard protocol cost us the
    structured half of the tool result. The citation discipline from Week 3
    bought it back. A team without that discipline would have discovered this
    the hard way.

TRUST
    A tool's DESCRIPTION is not data. It goes into the model's prompt, and the
    model acts on it. A server we do not control can therefore write
    instructions into our agent's head, which is the tool-poisoning attack.
    Descriptions from any server not marked trusted in the config are scanned
    by the Week 8 guard before the model ever sees them.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from agent import guard
from agent.mcp_client import MCPClient, MCPError, RemoteTool
from agent.tools import FINISH_DESCRIPTION, ToolResult
from config import BASE_DIR, STRATEGY_STRUCTURED

CONFIG_PATH = BASE_DIR / "mcp_servers.json"

FINISH = "finish"
_CHUNK_RE = re.compile(r"\[((?:HC-\d{4})-(?:baseline|structured)-\d{3})\]")


@dataclass
class Toolbox:
    """The agent's tools for one run: discovered, plus the local `finish`."""

    tools: dict[str, RemoteTool] = field(default_factory=dict)
    clients: dict[str, MCPClient] = field(default_factory=dict)
    servers_up: list[str] = field(default_factory=list)
    servers_down: list[tuple[str, str]] = field(default_factory=list)
    poisoned: list[tuple[str, str, list[str]]] = field(default_factory=list)

    # -- lifecycle --------------------------------------------------------
    def close(self) -> None:
        for client in self.clients.values():
            client.stop()
        self.clients.clear()

    def __enter__(self) -> "Toolbox":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- what the model sees ----------------------------------------------
    def catalogue(self) -> str:
        """The tool list, exactly as the model reads it.

        Grouped by server, because the model should know a tool came from
        somewhere else. It is the same reason a person reads a citation.
        """
        by_server: dict[str, list[RemoteTool]] = {}
        for tool in self.tools.values():
            by_server.setdefault(tool.server, []).append(tool)

        blocks = []
        for server, tools in by_server.items():
            label = "built in" if server == "local" else f"from the {server} server"
            blocks.append(f"-- {label} --")
            for tool in tools:
                blocks.append(f"{tool.name}({tool.arg_line()})\n    {tool.description}")
        return "\n\n".join(blocks)

    def names(self) -> list[str]:
        return sorted(self.tools)

    # -- running one ------------------------------------------------------
    def execute(self, name: str, args: dict) -> ToolResult:
        """Run one tool, wherever it lives, and never raise.

        A dead server, a bad argument, an unknown name: all come back as an
        observation the model can read and react to. That is the same rule
        agent/tools.py already followed, extended across a process boundary
        where there is far more that can go wrong.
        """
        tool = self.tools.get(name)
        if tool is None:
            return ToolResult(
                f"There is no tool called {name!r}. Available: {', '.join(self.names())}.",
                ok=False,
            )

        if name == FINISH:
            return ToolResult(str(args.get("answer") or ""))

        client = self.clients.get(tool.server)
        if client is None:
            return ToolResult(f"The {tool.server} server is not running.", ok=False)

        try:
            text = client.call_tool(tool.remote_name, args)
        except MCPError as exc:
            return ToolResult(f"{tool.server} could not run {name}: {exc}", ok=False)
        except Exception as exc:
            return ToolResult(f"{tool.server} failed on {name}: {type(exc).__name__}", ok=False)

        return ToolResult(text, _chunks_from(text), ok=bool(text.strip()))


def _chunks_from(text: str) -> list[dict]:
    """Recover the chunk objects MCP could not carry.

    Every chunk id the server printed is looked up in the local index, so the
    scoring layers keep working across the protocol boundary. Ids the corpus
    does not know are skipped rather than faked.
    """
    from rag.keyword import get_record

    out, seen = [], set()
    for chunk_id in _CHUNK_RE.findall(text or ""):
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        record = get_record(STRATEGY_STRUCTURED, chunk_id)
        if record is None:
            continue
        body, md = record
        out.append(
            {
                "rank": len(out) + 1,
                "score": 0.0,
                "chunk_id": chunk_id,
                "article_id": md.get("article_id", "?"),
                "source_file": md.get("source_file", "?"),
                "product_area": md.get("product_area", "?"),
                "text": body,
                "found_by": "mcp",
            }
        )
    return out


# ---------------------------------------------------------------------------
def load_config(path: Path | None = None) -> list[dict]:
    """The servers to connect to. Comment keys are ignored."""
    path = path or CONFIG_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    return [s for s in data.get("servers", []) if not s.get("disabled")]


def _command(server: dict) -> list[str]:
    """Resolve the command, using this interpreter for our own servers."""
    import sys

    command = list(server["command"])
    if command and command[0] == "python":
        command[0] = sys.executable
    return command


def connect(servers: list[dict] | None = None, *, verbose: bool = False) -> Toolbox:
    """Start every configured server and discover what it offers.

    A server that will not start is recorded and skipped. One broken server
    must not take the agent down: it should lose that server's tools and carry
    on with the rest, which is exactly what a person would do.
    """
    box = Toolbox()
    box.tools[FINISH] = RemoteTool(
        name=FINISH,
        description=FINISH_DESCRIPTION,
        schema={"type": "object", "properties": {"answer": {"type": "string"}},
                "required": ["answer"]},
        server="local",
    )

    for server in servers if servers is not None else load_config():
        name = server["name"]
        client = MCPClient(name, _command(server), cwd=str(BASE_DIR))
        try:
            client.start()
            discovered = client.list_tools()
        except Exception as exc:
            box.servers_down.append((name, f"{type(exc).__name__}: {exc}"[:120]))
            client.stop()
            if verbose:
                print(f"  {name}: did not start, skipping")
            continue

        box.clients[name] = client
        box.servers_up.append(name)

        for tool in discovered:
            if not server.get("trusted"):
                scanned = guard.scan(tool.description)
                if scanned.hits:
                    box.poisoned.append((name, tool.name, scanned.hits))
                    tool.description = scanned.text
            if tool.name in box.tools:
                # A name collision is not a merge. Namespace the newcomer so
                # both stay reachable and the agent can tell them apart.
                # remote_name is untouched, so the call still reaches the server
                # under the name it knows.
                tool.name = f"{name}__{tool.name}"
            box.tools[tool.name] = tool

        if verbose:
            print(f"  {name}: {len(discovered)} tool(s) discovered")

    return box
