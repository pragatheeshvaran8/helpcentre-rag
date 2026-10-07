"""The tools the agent may call, and the descriptions it picks from.

WHY THE DESCRIPTION IS THE HARD PART
    The model never sees this code. It sees the name, the argument line and the
    description string, and nothing else. A tool that works perfectly is still
    useless if the description does not say when to reach for it.

    The two search tools here overlap on purpose, because that is the real
    design problem. `search_help_centre` and `lookup_error_code` both return
    corpus text. If their descriptions only said "searches the help centre",
    the model would flip a coin. So each one states the shape of the input it
    wants, and says what the other is for.

WHY A TOOL NEVER RAISES
    A tool that throws kills the loop. Every failure comes back as a normal
    observation the model can read and react to, because reacting to a bad
    result is the whole reason the loop exists.

WHY OBSERVATIONS ARE TRUNCATED
    Every observation is fed back into the next prompt. Untruncated chunks make
    the context grow with every step, and the run dies on token budget around
    step four. `_OBSERVATION_CHARS` caps what the model reads. The full chunk
    is still recorded for scoring, so truncation never hides a retrieval hit
    from the checks.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from config import STRATEGY_STRUCTURED, get_settings

# What the model reads back from one tool call. Long enough to hold a table row
# with its header, short enough that six steps still fit in one context.
_OBSERVATION_CHARS = 900

# ERR-4032, MIG-220, and the sloppy forms agents actually type: "err 4032",
# "MIG310", "4032".
_CODE_RE = re.compile(r"\b((?:ERR|MIG)[\s-]?\d{3,4}|\b\d{4}\b)", re.IGNORECASE)


@dataclass
class ToolResult:
    """One tool call's outcome.

    `observation` is what the model reads. `chunks` is what the scorer reads.
    They are deliberately different: the model gets a truncated, readable view,
    and the checks get every full chunk the tool surfaced, so a retrieval hit
    can never be hidden by a display limit.
    """

    observation: str
    chunks: list[dict] = field(default_factory=list)
    ok: bool = True


@dataclass
class Tool:
    name: str
    args: str
    description: str
    run: Callable[..., ToolResult]


def _clip(text: str, limit: int = _OBSERVATION_CHARS) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + f"\n... [{len(text) - limit} more characters]"


def _render(hits: list[dict], header: str) -> str:
    """One observation block, labelled by chunk_id so the model can cite it."""
    if not hits:
        return f"{header}\nNo matching text in the help centre."
    lines = [header]
    for hit in hits:
        lines.append(f"\n[{hit['chunk_id']}] (article {hit['article_id']})")
        lines.append(_clip(hit["text"]))
    return "\n".join(lines)


def _table_row(text: str, code: str) -> str | None:
    """The header rows of a markdown table plus the one row naming `code`.

    An exact lookup should return the thing that was looked up. Handing back
    the whole chunk went wrong twice in one live run: the chunk holding
    ERR-7215 is 999 characters, the display clip was 900, and the 99 characters
    it removed were the fix. The model could see the code and not its answer,
    said so, and spent two more steps searching for what it had already been
    given.

    Returns None when the text is not a table, so prose chunks fall back to
    being shown whole.
    """
    rows = [line for line in text.splitlines() if line.strip().startswith("|")]
    if len(rows) < 3:
        return None
    match = next((r for r in rows if code.lower() in r.lower()), None)
    if match is None:
        return None
    # The first two table lines are the column names and the separator. Keeping
    # them is what makes the row readable, and is the same rule the Week 3
    # chunker uses when it refuses to split a row from its header.
    return "\n".join(rows[:2] + [match])


# ---------------------------------------------------------------------------
# The tools
# ---------------------------------------------------------------------------
def search_help_centre(query: str, k: int = 3) -> ToolResult:
    """Hybrid search over the corpus. The Week 4 retrieval, reused unchanged."""
    from rag.hybrid import search_by_mode
    from rag.retriever import format_hits

    query = (query or "").strip()
    if not query:
        return ToolResult("search_help_centre needs a non-empty query.", ok=False)

    settings = get_settings()
    scored = search_by_mode(query, STRATEGY_STRUCTURED, mode=settings.retrieval_mode, k=k)
    hits = format_hits(scored)
    return ToolResult(_render(hits, f'Top {len(hits)} results for "{query}":'), hits)


def lookup_error_code(code: str) -> ToolResult:
    """Exact lookup for one error code, via the BM25 arm.

    The Week 4 tokeniser keeps `err-4032` whole as well as splitting it, so a
    code query lands on the row that defines it rather than on every row that
    mentions a neighbouring code. That is why this is a separate tool from the
    semantic search rather than a special case inside it.
    """
    from rag.keyword import get_record, search_keyword

    raw = (code or "").strip()
    match = _CODE_RE.search(raw)
    if not match:
        return ToolResult(
            f"{raw!r} is not an error code. Codes look like ERR-4032 or MIG-220. "
            "Use search_help_centre for anything described in words.",
            ok=False,
        )

    # Normalise "err 4032", "ERR4032" and a bare "4032" to the corpus spelling.
    token = re.sub(r"[\s-]", "", match.group(1)).upper()
    digits = re.sub(r"\D", "", token)
    prefix = "MIG" if token.startswith("MIG") else "ERR"
    normalised = f"{prefix}-{digits}"

    ranked = search_keyword(normalised, STRATEGY_STRUCTURED, k=3)
    hits = []
    for chunk_id, score in ranked:
        record = get_record(STRATEGY_STRUCTURED, chunk_id)
        if record is None:
            continue
        text, md = record
        hits.append(
            {
                "rank": len(hits) + 1,
                "score": round(float(score), 4),
                "chunk_id": chunk_id,
                "article_id": md.get("article_id", "?"),
                "source_file": md.get("source_file", "?"),
                "product_area": md.get("product_area", "?"),
                "text": text,
                "found_by": "keyword",
            }
        )

    if not hits:
        return ToolResult(f"{normalised} does not appear anywhere in the help centre.", hits)

    # Show only the chunks that actually name this code, and inside each one,
    # only the row that does. BM25 ranks the right chunk first but still
    # returns neighbours, and on the live ERR-7215 run two of the three were
    # payment-code tables from another article. That is noise, it filled the
    # context, and it pushed the answer past the display limit.
    naming = [h for h in hits if normalised.lower() in h["text"].lower()] or hits[:1]
    blocks = [f"Help-centre entry for {normalised}:"]
    for hit in naming:
        row = _table_row(hit["text"], normalised)
        blocks.append(f"\n[{hit['chunk_id']}] (article {hit['article_id']})")
        blocks.append(row if row else _clip(hit["text"]))

    # Every chunk stays in `chunks`, including the ones not displayed, so the
    # scorer still sees everything retrieval put within reach.
    return ToolResult("\n".join(blocks), hits)


# Lifted out of the registry so agent/toolbox.py can reuse the exact wording.
# `finish` is the only tool that is never discovered: it is not a capability,
# it is how the loop stops, and a remote server has no business owning that.
FINISH_DESCRIPTION = (
    "Give the final answer to the customer's ticket and stop. Every sentence "
    "must end with the [chunk_id] it came from. Call this as soon as you have "
    "the facts for every part of the ticket. Do not call it before you have "
    "looked something up."
)


def finish(answer: str) -> ToolResult:
    """Terminal tool. Calling it ends the loop with this text as the answer."""
    return ToolResult(answer or "")


TOOLS: dict[str, Tool] = {
    "search_help_centre": Tool(
        name="search_help_centre",
        args="query: str",
        description=(
            "Search the help centre by meaning. Use this for anything described "
            "in words: a symptom, a policy question, what an agent is allowed to "
            "do, why something changed. Pass a short focused query about ONE "
            "thing, not the customer's whole message. If you have a literal "
            "error code, use lookup_error_code instead, it is exact."
        ),
        run=search_help_centre,
    ),
    "lookup_error_code": Tool(
        name="lookup_error_code",
        args="code: str",
        description=(
            "Look up one error code and get its cause and fix. Use this the "
            "moment you see a code like ERR-4032 or MIG-220. It matches the code "
            "exactly, so it will not drift onto a neighbouring code the way a "
            "worded search can. It takes one code at a time. It cannot answer "
            "anything that is not a code: for a symptom, a policy or a question "
            "in words, use search_help_centre."
        ),
        run=lookup_error_code,
    ),
    "finish": Tool(
        name="finish",
        args="answer: str",
        description=FINISH_DESCRIPTION,
        run=finish,
    ),
}


class LocalToolbox:
    """The Week 7 in-process tools, behind the Week 9 toolbox interface.

    agent/loop.py no longer imports tools directly. It is handed something with
    catalogue(), execute() and names(), and it cannot tell whether the tools
    live in this process or in three subprocesses on the other side of a pipe.
    That indifference is the point: it is what lets a server be bolted on
    without the agent changing.

    This exists so the acceptance tests can drive the loop without starting
    subprocesses. The DEFAULT path is MCP.
    """

    server = "local"

    def catalogue(self) -> str:
        return catalogue()

    def names(self) -> list[str]:
        return sorted(TOOLS)

    def execute(self, name: str, args: dict) -> ToolResult:
        return execute(name, args)

    def close(self) -> None:
        pass

    def __enter__(self) -> "LocalToolbox":
        return self

    def __exit__(self, *exc) -> None:
        pass


def local_toolbox() -> LocalToolbox:
    return LocalToolbox()


def catalogue() -> str:
    """The tool list exactly as the model sees it."""
    return "\n\n".join(
        f"{tool.name}({tool.args})\n    {tool.description}" for tool in TOOLS.values()
    )


def execute(name: str, args: dict) -> ToolResult:
    """Run one tool by name, turning every failure into a readable observation.

    An unknown name or a bad argument is a normal observation, not an
    exception. The model chose wrongly, it should be told so and get another
    turn, exactly as it would after an empty search result.
    """
    tool = TOOLS.get(name)
    if tool is None:
        return ToolResult(
            f"There is no tool called {name!r}. Available: {', '.join(TOOLS)}.", ok=False
        )
    try:
        return tool.run(**args)
    except TypeError as exc:
        return ToolResult(f"{name} was called with the wrong arguments: {exc}", ok=False)
    except Exception as exc:  # a tool must never kill the loop
        return ToolResult(f"{name} failed: {type(exc).__name__}: {exc}", ok=False)
