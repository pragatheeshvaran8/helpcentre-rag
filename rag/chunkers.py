"""The two chunking strategies under test.

STRATEGY 1 - "baseline"
    RecursiveCharacterTextSplitter, chunk_size=1000, chunk_overlap=150, with the
    separator list the existing Week-3 app already used. This is the incumbent.
    It has no idea what a markdown table is. To it, a table is just a run of
    lines separated by "\\n", so a boundary can land anywhere, including between
    a table's header row and its data rows.

STRATEGY 2 - "structured"
    Structure-aware. It parses the article into blocks (headings, paragraphs,
    tables) and then packs whole blocks. Its one hard guarantee is the one the
    task asks for:

        A table data row is NEVER separated from its header row.

    When a table is too large for one chunk it is emitted as row-groups, and the
    header row plus its separator row are repeated at the top of every group.
    A single data row is never split in half.

WHAT IS HELD CONSTANT
    Same corpus, same embedding model, same top-k, same distance metric, same
    target chunk size (1000). The only thing that differs is where a boundary is
    allowed to fall. The baseline overlaps by 150 characters; the structure-aware
    chunker does not overlap, because it never cuts a unit in half and so has
    nothing to stitch back together. That difference is intrinsic to the
    strategy, not a second knob being turned, and it is called out in the
    write-up.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import STRATEGY_BASELINE, STRATEGY_STRUCTURED, get_settings

# A markdown table separator row, e.g. "|---|---|" or "| :--- | ---: |".
SEPARATOR_ROW = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
# Any markdown table line.
TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$")
# A markdown heading line.
HEADING_LINE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*)$")

BLOCK_HEADING = "heading"
BLOCK_PARA = "para"
BLOCK_TABLE = "table"


@dataclass
class Block:
    """One structural unit of an article."""

    kind: str
    text: str
    # Table blocks only: the header row and its separator row, kept together.
    table_head: str | None = None
    table_rows: list[str] | None = None


# ---------------------------------------------------------------------------
# Block parsing
# ---------------------------------------------------------------------------
def parse_blocks(body: str) -> list[Block]:
    """Parse markdown ``body`` into headings, paragraphs and tables."""
    blocks: list[Block] = []
    lines = body.splitlines()
    para: list[str] = []

    def flush_para() -> None:
        if para:
            blocks.append(Block(BLOCK_PARA, "\n".join(para).strip()))
            para.clear()

    i = 0
    while i < len(lines):
        line = lines[i]

        if HEADING_LINE.match(line):
            flush_para()
            blocks.append(Block(BLOCK_HEADING, line.strip()))
            i += 1
            continue

        if TABLE_LINE.match(line):
            flush_para()
            table_lines: list[str] = []
            while i < len(lines) and TABLE_LINE.match(lines[i]):
                table_lines.append(lines[i].rstrip())
                i += 1

            # A well-formed table is: header row, separator row, then data rows.
            if len(table_lines) >= 2 and SEPARATOR_ROW.match(table_lines[1]):
                head = "\n".join(table_lines[:2])
                rows = table_lines[2:]
                blocks.append(
                    Block(BLOCK_TABLE, "\n".join(table_lines), table_head=head, table_rows=rows)
                )
            else:
                # Pipe lines that are not a real table. Treat as prose so we
                # never invent a header that does not exist.
                blocks.append(Block(BLOCK_PARA, "\n".join(table_lines)))
            continue

        if not line.strip():
            flush_para()
            i += 1
            continue

        para.append(line)
        i += 1

    flush_para()
    return blocks


# ---------------------------------------------------------------------------
# Strategy 1: baseline
# ---------------------------------------------------------------------------
def chunk_baseline(body: str) -> list[str]:
    """The incumbent chunker. Character-recursive, table-blind."""
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],
        length_function=len,
    )
    return [c.strip() for c in splitter.split_text(body) if c.strip()]


# ---------------------------------------------------------------------------
# Strategy 2: structure-aware
# ---------------------------------------------------------------------------
def _split_table(block: Block, chunk_size: int, *, lead: str = "") -> list[str]:
    """Emit a table as row-groups, each carrying the header row.

    ``lead`` is an optional section heading placed above the FIRST group only.
    Later groups carry the table header row but not the heading, which keeps the
    intervention to exactly what the task asks for: a data row never loses its
    header row.
    """
    head = block.table_head or ""
    rows = block.table_rows or []
    groups: list[str] = []
    current: list[str] = []
    prefix = f"{lead}\n\n" if lead else ""
    base_len = len(prefix) + len(head)
    current_len = base_len

    for row in rows:
        # Start a new group when this row would overflow, but never emit an
        # empty group: a single oversized row stays whole, with its header.
        if current and current_len + len(row) + 1 > chunk_size:
            groups.append(prefix + head + "\n" + "\n".join(current))
            prefix = ""  # heading only leads the first group
            current = []
            current_len = len(head)
        current.append(row)
        current_len += len(row) + 1

    if current:
        groups.append(prefix + head + "\n" + "\n".join(current))
    elif not groups:
        # Header-only table, no data rows.
        groups.append(prefix + head)
    return groups


def chunk_structured(body: str) -> list[str]:
    """Structure-aware chunker. Never splits a table row from its header."""
    settings = get_settings()
    size = settings.chunk_size
    blocks = parse_blocks(body)

    chunks: list[str] = []
    buf: list[str] = []

    def buf_len() -> int:
        return sum(len(p) for p in buf) + 2 * max(len(buf) - 1, 0)

    def flush() -> None:
        if buf:
            chunks.append("\n\n".join(buf).strip())
            buf.clear()

    for block in blocks:
        if block.kind == BLOCK_HEADING:
            # A heading opens a section, so it starts a new chunk and stays
            # attached to the content that follows it.
            flush()
            buf.append(block.text)
            continue

        if block.kind == BLOCK_TABLE:
            whole = block.text
            # Small table: keep it inline with the prose already buffered.
            if len(whole) <= size and buf_len() + len(whole) + 2 <= size:
                buf.append(whole)
                continue
            # Large table: it becomes its own row-groups. If only a heading is
            # buffered, carry that heading onto the first group instead of
            # emitting a heading-only chunk.
            lead = ""
            if len(buf) == 1 and buf[0].lstrip().startswith("#"):
                lead = buf[0]
                buf.clear()
            else:
                flush()
            chunks.extend(_split_table(block, size, lead=lead))
            continue

        # Paragraph.
        text = block.text
        if len(text) > size:
            # A single paragraph longer than the target. Rare in this corpus.
            # Fall back to the recursive splitter for that paragraph alone.
            flush()
            chunks.extend(chunk_baseline(text))
            continue
        if buf and buf_len() + len(text) + 2 > size:
            flush()
        buf.append(text)

    flush()
    return [c for c in chunks if c.strip()]


CHUNKERS = {
    STRATEGY_BASELINE: chunk_baseline,
    STRATEGY_STRUCTURED: chunk_structured,
}


# ---------------------------------------------------------------------------
# Diagnostics used by the write-up
# ---------------------------------------------------------------------------
def table_stats(chunk: str) -> dict:
    """Describe a chunk's relationship to markdown tables.

    ``orphan_table_rows`` is the interesting one: the chunk carries table data
    rows but no header row, so a reader (or a model) cannot tell what the
    columns mean. That is the exact damage a table-blind chunker does.
    """
    lines = chunk.splitlines()
    table_lines = [ln for ln in lines if TABLE_LINE.match(ln)]
    has_separator = any(SEPARATOR_ROW.match(ln) for ln in lines)
    data_rows = [ln for ln in table_lines if not SEPARATOR_ROW.match(ln)]
    # With a separator present, the row directly above it is the header, so one
    # of the "data rows" is really the header.
    row_count = max(len(data_rows) - (1 if has_separator else 0), 0)
    return {
        "contains_table_rows": bool(data_rows),
        "has_table_header": has_separator,
        "table_row_count": row_count,
        "orphan_table_rows": bool(data_rows) and not has_separator,
    }
