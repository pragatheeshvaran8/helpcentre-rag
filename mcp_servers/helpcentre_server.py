"""Our MCP server: the help-centre search, offered to anyone's agent.

    python -m mcp_servers.helpcentre_server

WHAT THIS EXPOSES
    The one thing this app genuinely does well, built over Weeks 3 to 6:
    hybrid retrieval over a structure-aware chunked corpus, plus an exact
    error-code lookup that never drifts onto a neighbouring code.

    Before this file, that capability was reachable only by our own agent,
    through a Python import. Now any MCP client can call it: another team's
    agent, Claude Desktop, a CLI, something written next year in a language
    that does not exist yet.

WHERE THE AI RUNS
    Not here. This process has no model, no API key, and no idea who is
    calling. It receives a tool name and some arguments, it runs a search, it
    returns text. The thinking happens in the host, on the caller's side.

    That is worth being blunt about, because it is the single most
    misunderstood thing about MCP. A server is not an AI. It is a socket on an
    appliance.

WHY THE OFFICIAL SDK HERE AND A HAND-WRITTEN CLIENT THERE
    A server has to be exactly right or nobody else's client can talk to it, so
    this uses the real SDK and the real schema. The client in agent/mcp_client.py
    is hand-written instead, because the point of reading the raw JSON-RPC once
    is that the protocol stops being magic, and an SDK hides exactly the part
    worth seeing.

WHAT A CALLER GETS BACK
    Text, formatted for a model to read, with every chunk labelled by its
    chunk_id. The ids matter: a caller that wants to cite its sources needs a
    stable handle for them, and inventing one at the client would break the
    moment the corpus changed.
"""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

server = MCPServer(
    name="helpcentre",
    instructions=(
        "Search a billing-migration help centre. Use lookup_error_code when you "
        "have a literal code such as ERR-4032 or MIG-220, because it matches "
        "exactly. Use search_help_centre for anything described in words."
    ),
)


@server.tool(
    description=(
        "Search the help centre by meaning. Use this for anything described in "
        "words: a symptom, a policy question, what an agent is allowed to do, "
        "why something changed. Pass a short focused query about ONE thing, not "
        "the customer's whole message. If you have a literal error code, use "
        "lookup_error_code instead, it is exact."
    )
)
def search_help_centre(query: str, k: int = 3) -> str:
    """Hybrid search over the corpus. Returns labelled chunks."""
    # Imported inside the tool so the server starts fast and a client can list
    # tools without paying to load an embedding model.
    from agent.tools import search_help_centre as _search

    return _search(query=query, k=k).observation


@server.tool(
    description=(
        "Look up one error code and get its cause and fix. Use this the moment "
        "you see a code like ERR-4032 or MIG-220. It matches the code exactly, "
        "so it will not drift onto a neighbouring code the way a worded search "
        "can. It takes one code at a time. It cannot answer anything that is "
        "not a code: for a symptom, a policy or a question in words, use "
        "search_help_centre."
    )
)
def lookup_error_code(code: str) -> str:
    """Exact lookup for one error code, via the BM25 arm."""
    from agent.tools import lookup_error_code as _lookup

    return _lookup(code=code).observation


def _warm() -> None:
    """Pay the start-up cost before serving, not on the first caller's request.

    This server needs a BM25 index (about 21s to build) and an embedding model
    (about 5s to load). Left lazy, the first tools/call paid all 26s, and a
    client with a 30s timeout gave up before the answer came back. The delay
    was always there; leaving it lazy turned it into a failure.

    A server initialises before it says it is ready. That is not an MCP rule,
    it is just what a server is.
    """
    from config import STRATEGY_STRUCTURED
    from rag.hybrid import search_by_mode
    from rag.keyword import build_index

    build_index(STRATEGY_STRUCTURED)
    search_by_mode("warm up", STRATEGY_STRUCTURED, mode="hybrid", k=1)


if __name__ == "__main__":
    _warm()
    # stdio: the host starts this as a subprocess and talks over its pipes.
    # No port, no network, no auth to get wrong. It is the transport to reach
    # for when the server runs on the same machine as the host.
    server.run(transport="stdio")
