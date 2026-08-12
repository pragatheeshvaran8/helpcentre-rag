# Code diff

This is a new repository, so the second chunker and the metadata fields appear
as additions rather than as edits to an older file. The diff below is between
the first commit and the final one:

- `c25d0a0` corpus + the 8 questions only. No retriever, no chunker, no results.
- `5aad989` the whole retrieval pipeline, including the heading-only-chunk fix.

That commit order is deliberate. It is the evidence that the 8 questions were
written from the articles before any search was ever run.

## What to look at

| Requirement | File | Where |
|---|---|---|
| Second chunker | `rag/chunkers.py` | `chunk_structured()` and `_split_table()` |
| Incumbent chunker, unchanged | `rag/chunkers.py` | `chunk_baseline()` |
| Header-loss diagnostic | `rag/chunkers.py` | `table_stats()` |
| Metadata fields | `rag/documents.py` | `REQUIRED_FIELDS`, `Article.base_metadata()` |
| Metadata stamped on chunks | `rag/ingest.py` | `build_documents()`, `make_chunk_id()` |
| Two indexes side by side | `rag/vector_store.py` | `get_store()`, `COLLECTIONS` |
| Citation resolution | `rag/vector_store.py` | `get_chunk_by_id()` |
| product_area pre-filter | `rag/retriever.py` | `search(..., product_area=)` |
| Forced refusal | `rag/answerer.py` | `SYSTEM_PROMPT` rules 3, 4 and 5 |

The single most important function is `_split_table()`. It is the whole
structure-aware guarantee in about twenty lines: rows are packed into groups,
and the header row plus its separator row are prepended to every group, so a
data row can never be stored without the columns that give it meaning.

The second most important is `flush()` inside `chunk_structured()`. It refuses
to emit a buffer that holds only headings. Without that guard the index gains a
content-free chunk per article, and one of them outranked every real paragraph
on the metadata-filter query.

---

```diff
diff --git a/rag/answerer.py b/rag/answerer.py
new file mode 100644
index 0000000..eb8fadf
--- /dev/null
+++ b/rag/answerer.py
@@ -0,0 +1,202 @@
+"""Grounded generation with a FORCED refusal and a citation on every claim.
+
+The grounding prompt below never says "use your best judgement" and never says
+"if the context is insufficient, do your best". Those sentences are exactly how
+an invented fix for ERR-4032 reaches a customer. The refusal here is an
+instruction with a fixed output string, not a suggestion.
+
+Two independent layers stop an invented answer:
+
+  Layer 1 - retrieval gate (optional, off for the refusal transcripts).
+      If nothing clears the score threshold, refuse without calling the model.
+
+  Layer 2 - the prompt itself.
+      The model is shown the retrieved context and must refuse in a fixed form
+      when that context does not contain the answer.
+
+The refusal transcripts in results.md are produced with Layer 1 DISABLED on
+purpose. That means the model really did see retrieved context and still had to
+refuse. A refusal produced by a code path that never called the model would
+prove nothing about the prompt.
+"""
+from __future__ import annotations
+
+import logging
+import re
+from dataclasses import dataclass, field
+
+from config import get_settings
+from rag.retriever import format_context, search
+from rag.vector_store import get_chunk_by_id
+
+logger = logging.getLogger(__name__)
+
+# The exact string the model must emit when it cannot answer.
+REFUSAL_TOKEN = "REFUSED"
+
+# chunk_id looks like HC-4002-structured-007
+CITATION_RE = re.compile(r"\[((?:HC-\d{4})-(?:baseline|structured)-\d{3})\]")
+
+SYSTEM_PROMPT = """You are a support-desk answering assistant for a help-centre corpus.
+
+You answer ONLY from the CONTEXT BLOCKS given to you in the user message.
+Each block is labelled with a chunk_id in square brackets, like [HC-4002-structured-007].
+
+RULES. These are absolute. There is no situation in which you may break them.
+
+1. Every single sentence of your answer MUST end with a citation naming the block
+   it came from, written exactly as [chunk_id]. A sentence with no citation is a
+   rule violation.
+2. You may cite ONLY chunk_ids that appear in the CONTEXT BLOCKS below. Never
+   invent, guess, abbreviate or reformat a chunk_id.
+3. You may state ONLY facts that are written in the CONTEXT BLOCKS. You may not
+   use outside knowledge. You may not infer. You may not generalise. You may not
+   fill a gap with something that sounds reasonable.
+4. If the CONTEXT BLOCKS do not contain the information needed to answer the
+   question, you MUST reply with exactly this, and nothing else:
+
+REFUSED: The help-centre corpus does not contain this information.
+Missing: <one short line naming what was asked for and not found>
+
+5. A partial answer is a refusal. If you can answer only part of the question,
+   you must still refuse using the format in rule 4, and name the missing part.
+6. Never apologise, never offer a workaround, never suggest what the answer
+   might be, and never tell the user to check elsewhere.
+
+You are measured on refusing correctly, not on being helpful."""
+
+USER_TEMPLATE = """CONTEXT BLOCKS:
+
+{context}
+
+END OF CONTEXT BLOCKS.
+
+QUESTION: {question}"""
+
+
+@dataclass
+class Citation:
+    """One [chunk_id] the model produced, and whether it actually resolves."""
+
+    chunk_id: str
+    resolves: bool
+    was_in_context: bool
+    article_id: str | None = None
+    source_file: str | None = None
+    text: str | None = None
+
+
+@dataclass
+class Answer:
+    """The full record of one generation, enough to paste into the write-up."""
+
+    question: str
+    strategy: str
+    answer: str
+    refused: bool
+    gate_fired: bool
+    retrieved: list[dict] = field(default_factory=list)
+    citations: list[Citation] = field(default_factory=list)
+    context: str = ""
+
+    @property
+    def all_citations_resolve(self) -> bool:
+        return bool(self.citations) and all(c.resolves for c in self.citations)
+
+
+def _llm():
+    """Build the chat model. Imported lazily so search-only runs need no key."""
+    from langchain_openai import ChatOpenAI
+
+    settings = get_settings()
+    if not settings.openrouter_api_key:
+        raise RuntimeError(
+            "OPENROUTER_API_KEY is not set. Generation needs it; search-only "
+            "evaluation does not."
+        )
+    return ChatOpenAI(
+        model=settings.openrouter_model,
+        api_key=settings.openrouter_api_key,
+        base_url=settings.openrouter_base_url,
+        temperature=settings.llm_temperature,
+        max_tokens=settings.max_tokens,
+        timeout=120,
+    )
+
+
+def verify_citations(text: str, strategy: str, context_ids: set[str]) -> list[Citation]:
+    """Resolve every [chunk_id] in ``text`` against the live vector store."""
+    citations: list[Citation] = []
+    for chunk_id in dict.fromkeys(CITATION_RE.findall(text)):
+        record = get_chunk_by_id(strategy, chunk_id)
+        citations.append(
+            Citation(
+                chunk_id=chunk_id,
+                resolves=record is not None,
+                was_in_context=chunk_id in context_ids,
+                article_id=(record or {}).get("metadata", {}).get("article_id"),
+                source_file=(record or {}).get("metadata", {}).get("source_file"),
+                text=(record or {}).get("text"),
+            )
+        )
+    return citations
+
+
+def answer_question(
+    question: str,
+    strategy: str,
+    *,
+    k: int | None = None,
+    product_area: str | None = None,
+    use_gate: bool = True,
+) -> Answer:
+    """Retrieve, then answer strictly from what was retrieved, or refuse.
+
+    Args:
+        use_gate: When True, refuse without calling the model if nothing clears
+            settings.score_threshold. Set False to force the model itself to do
+            the refusing, which is what the refusal transcripts demonstrate.
+    """
+    settings = get_settings()
+    scored = search(question, strategy, k=k, product_area=product_area)
+    from rag.retriever import format_hits  # local import avoids a cycle at import time
+
+    retrieved = format_hits(scored)
+
+    above = [(d, s) for d, s in scored if s >= settings.score_threshold]
+    if use_gate and not above:
+        best = max((s for _, s in scored), default=0.0)
+        return Answer(
+            question=question,
+            strategy=strategy,
+            answer=(
+                f"{REFUSAL_TOKEN}: The help-centre corpus does not contain this "
+                f"information.\nMissing: nothing retrieved above the "
+                f"{settings.score_threshold} relevance gate (best was {best:.4f})."
+            ),
+            refused=True,
+            gate_fired=True,
+            retrieved=retrieved,
+        )
+
+    context = format_context(scored)
+    context_ids = {h["chunk_id"] for h in retrieved}
+
+    response = _llm().invoke(
+        [
+            ("system", SYSTEM_PROMPT),
+            ("human", USER_TEMPLATE.format(context=context, question=question)),
+        ]
+    )
+    text = (response.content or "").strip()
+
+    return Answer(
+        question=question,
+        strategy=strategy,
+        answer=text,
+        refused=text.upper().startswith(REFUSAL_TOKEN),
+        gate_fired=False,
+        retrieved=retrieved,
+        citations=verify_citations(text, strategy, context_ids),
+        context=context,
+    )
diff --git a/rag/chunkers.py b/rag/chunkers.py
new file mode 100644
index 0000000..68b9b6a
--- /dev/null
+++ b/rag/chunkers.py
@@ -0,0 +1,267 @@
+"""The two chunking strategies under test.
+
+STRATEGY 1 - "baseline"
+    RecursiveCharacterTextSplitter, chunk_size=1000, chunk_overlap=150, with the
+    separator list the existing Week-3 app already used. This is the incumbent.
+    It has no idea what a markdown table is. To it, a table is just a run of
+    lines separated by "\\n", so a boundary can land anywhere, including between
+    a table's header row and its data rows.
+
+STRATEGY 2 - "structured"
+    Structure-aware. It parses the article into blocks (headings, paragraphs,
+    tables) and then packs whole blocks. Its one hard guarantee is the one the
+    task asks for:
+
+        A table data row is NEVER separated from its header row.
+
+    When a table is too large for one chunk it is emitted as row-groups, and the
+    header row plus its separator row are repeated at the top of every group.
+    A single data row is never split in half.
+
+WHAT IS HELD CONSTANT
+    Same corpus, same embedding model, same top-k, same distance metric, same
+    target chunk size (1000). The only thing that differs is where a boundary is
+    allowed to fall. The baseline overlaps by 150 characters; the structure-aware
+    chunker does not overlap, because it never cuts a unit in half and so has
+    nothing to stitch back together. That difference is intrinsic to the
+    strategy, not a second knob being turned, and it is called out in the
+    write-up.
+"""
+from __future__ import annotations
+
+import re
+from dataclasses import dataclass
+
+from langchain_text_splitters import RecursiveCharacterTextSplitter
+
+from config import STRATEGY_BASELINE, STRATEGY_STRUCTURED, get_settings
+
+# A markdown table separator row, e.g. "|---|---|" or "| :--- | ---: |".
+SEPARATOR_ROW = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
+# Any markdown table line.
+TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$")
+# A markdown heading line.
+HEADING_LINE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*)$")
+
+BLOCK_HEADING = "heading"
+BLOCK_PARA = "para"
+BLOCK_TABLE = "table"
+
+
+@dataclass
+class Block:
+    """One structural unit of an article."""
+
+    kind: str
+    text: str
+    # Table blocks only: the header row and its separator row, kept together.
+    table_head: str | None = None
+    table_rows: list[str] | None = None
+
+
+# ---------------------------------------------------------------------------
+# Block parsing
+# ---------------------------------------------------------------------------
+def parse_blocks(body: str) -> list[Block]:
+    """Parse markdown ``body`` into headings, paragraphs and tables."""
+    blocks: list[Block] = []
+    lines = body.splitlines()
+    para: list[str] = []
+
+    def flush_para() -> None:
+        if para:
+            blocks.append(Block(BLOCK_PARA, "\n".join(para).strip()))
+            para.clear()
+
+    i = 0
+    while i < len(lines):
+        line = lines[i]
+
+        if HEADING_LINE.match(line):
+            flush_para()
+            blocks.append(Block(BLOCK_HEADING, line.strip()))
+            i += 1
+            continue
+
+        if TABLE_LINE.match(line):
+            flush_para()
+            table_lines: list[str] = []
+            while i < len(lines) and TABLE_LINE.match(lines[i]):
+                table_lines.append(lines[i].rstrip())
+                i += 1
+
+            # A well-formed table is: header row, separator row, then data rows.
+            if len(table_lines) >= 2 and SEPARATOR_ROW.match(table_lines[1]):
+                head = "\n".join(table_lines[:2])
+                rows = table_lines[2:]
+                blocks.append(
+                    Block(BLOCK_TABLE, "\n".join(table_lines), table_head=head, table_rows=rows)
+                )
+            else:
+                # Pipe lines that are not a real table. Treat as prose so we
+                # never invent a header that does not exist.
+                blocks.append(Block(BLOCK_PARA, "\n".join(table_lines)))
+            continue
+
+        if not line.strip():
+            flush_para()
+            i += 1
+            continue
+
+        para.append(line)
+        i += 1
+
+    flush_para()
+    return blocks
+
+
+# ---------------------------------------------------------------------------
+# Strategy 1: baseline
+# ---------------------------------------------------------------------------
+def chunk_baseline(body: str) -> list[str]:
+    """The incumbent chunker. Character-recursive, table-blind."""
+    settings = get_settings()
+    splitter = RecursiveCharacterTextSplitter(
+        chunk_size=settings.chunk_size,
+        chunk_overlap=settings.chunk_overlap,
+        separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],
+        length_function=len,
+    )
+    return [c.strip() for c in splitter.split_text(body) if c.strip()]
+
+
+# ---------------------------------------------------------------------------
+# Strategy 2: structure-aware
+# ---------------------------------------------------------------------------
+def _split_table(block: Block, chunk_size: int, *, lead: str = "") -> list[str]:
+    """Emit a table as row-groups, each carrying the header row.
+
+    ``lead`` is an optional section heading placed above the FIRST group only.
+    Later groups carry the table header row but not the heading, which keeps the
+    intervention to exactly what the task asks for: a data row never loses its
+    header row.
+    """
+    head = block.table_head or ""
+    rows = block.table_rows or []
+    groups: list[str] = []
+    current: list[str] = []
+    prefix = f"{lead}\n\n" if lead else ""
+    base_len = len(prefix) + len(head)
+    current_len = base_len
+
+    for row in rows:
+        # Start a new group when this row would overflow, but never emit an
+        # empty group: a single oversized row stays whole, with its header.
+        if current and current_len + len(row) + 1 > chunk_size:
+            groups.append(prefix + head + "\n" + "\n".join(current))
+            prefix = ""  # heading only leads the first group
+            current = []
+            current_len = len(head)
+        current.append(row)
+        current_len += len(row) + 1
+
+    if current:
+        groups.append(prefix + head + "\n" + "\n".join(current))
+    elif not groups:
+        # Header-only table, no data rows.
+        groups.append(prefix + head)
+    return groups
+
+
+def chunk_structured(body: str) -> list[str]:
+    """Structure-aware chunker. Never splits a table row from its header."""
+    settings = get_settings()
+    size = settings.chunk_size
+    blocks = parse_blocks(body)
+
+    chunks: list[str] = []
+    buf: list[str] = []
+
+    def buf_len() -> int:
+        return sum(len(p) for p in buf) + 2 * max(len(buf) - 1, 0)
+
+    def buf_is_only_headings() -> bool:
+        """True when the buffer holds headings and nothing else."""
+        return bool(buf) and all(p.lstrip().startswith("#") for p in buf)
+
+    def flush() -> None:
+        # A heading with no content under it is not a retrievable unit. Emitting
+        # it as its own chunk creates a short, high-similarity decoy that can
+        # outrank real content, so drop it instead.
+        if buf and not buf_is_only_headings():
+            chunks.append("\n\n".join(buf).strip())
+        buf.clear()
+
+    for block in blocks:
+        if block.kind == BLOCK_HEADING:
+            # A heading opens a section and stays attached to the content that
+            # follows it. Consecutive headings (an article title immediately
+            # followed by a section heading) accumulate rather than each
+            # becoming a chunk of its own.
+            if not buf_is_only_headings():
+                flush()
+            buf.append(block.text)
+            continue
+
+        if block.kind == BLOCK_TABLE:
+            whole = block.text
+            # Small table: keep it inline with the prose already buffered.
+            if len(whole) <= size and buf_len() + len(whole) + 2 <= size:
+                buf.append(whole)
+                continue
+            # Large table: it becomes its own row-groups. If only headings are
+            # buffered, carry them onto the first group instead of losing them.
+            lead = ""
+            if buf_is_only_headings():
+                lead = "\n\n".join(buf)
+                buf.clear()
+            else:
+                flush()
+            chunks.extend(_split_table(block, size, lead=lead))
+            continue
+
+        # Paragraph.
+        text = block.text
+        if len(text) > size:
+            # A single paragraph longer than the target. Rare in this corpus.
+            # Fall back to the recursive splitter for that paragraph alone.
+            flush()
+            chunks.extend(chunk_baseline(text))
+            continue
+        if buf and buf_len() + len(text) + 2 > size:
+            flush()
+        buf.append(text)
+
+    flush()
+    return [c for c in chunks if c.strip()]
+
+
+CHUNKERS = {
+    STRATEGY_BASELINE: chunk_baseline,
+    STRATEGY_STRUCTURED: chunk_structured,
+}
+
+
+# ---------------------------------------------------------------------------
+# Diagnostics used by the write-up
+# ---------------------------------------------------------------------------
+def table_stats(chunk: str) -> dict:
+    """Describe a chunk's relationship to markdown tables.
+
+    ``orphan_table_rows`` is the interesting one: the chunk carries table data
+    rows but no header row, so a reader (or a model) cannot tell what the
+    columns mean. That is the exact damage a table-blind chunker does.
+    """
+    lines = chunk.splitlines()
+    table_lines = [ln for ln in lines if TABLE_LINE.match(ln)]
+    has_separator = any(SEPARATOR_ROW.match(ln) for ln in lines)
+    data_rows = [ln for ln in table_lines if not SEPARATOR_ROW.match(ln)]
+    # With a separator present, the row directly above it is the header, so one
+    # of the "data rows" is really the header.
+    row_count = max(len(data_rows) - (1 if has_separator else 0), 0)
+    return {
+        "contains_table_rows": bool(data_rows),
+        "has_table_header": has_separator,
+        "table_row_count": row_count,
+        "orphan_table_rows": bool(data_rows) and not has_separator,
+    }
diff --git a/rag/documents.py b/rag/documents.py
new file mode 100644
index 0000000..53b8c9b
--- /dev/null
+++ b/rag/documents.py
@@ -0,0 +1,100 @@
+"""Article loading and front-matter parsing.
+
+Each help-centre article carries YAML-style front matter that supplies the
+metadata every chunk must inherit:
+
+    ---
+    article_id: HC-4002
+    title: Invoice Errors After the Billing Migration
+    product_area: invoicing
+    last_updated: 2026-06-11
+    ---
+
+An article missing any required field is a hard failure. A chunk with no
+source_file is a failed ingest, so we refuse to ingest a file we cannot label.
+"""
+from __future__ import annotations
+
+from dataclasses import dataclass
+from pathlib import Path
+
+from config import get_settings
+
+REQUIRED_FIELDS = ("article_id", "title", "product_area", "last_updated")
+
+
+@dataclass(frozen=True)
+class Article:
+    """One help-centre article: its metadata plus its body text."""
+
+    source_file: str
+    article_id: str
+    title: str
+    product_area: str
+    last_updated: str
+    body: str
+
+    def base_metadata(self) -> dict:
+        """The metadata every chunk of this article inherits."""
+        return {
+            "source_file": self.source_file,
+            "article_id": self.article_id,
+            "title": self.title,
+            "product_area": self.product_area,
+            "last_updated": self.last_updated,
+        }
+
+
+def parse_front_matter(text: str, *, source_file: str) -> tuple[dict, str]:
+    """Split ``text`` into (front-matter dict, body).
+
+    Raises ValueError when the front matter is missing or incomplete, because a
+    silently unlabelled chunk is worse than a loud failure.
+    """
+    lines = text.splitlines()
+    if not lines or lines[0].strip() != "---":
+        raise ValueError(f"{source_file}: missing front matter (no opening '---')")
+
+    try:
+        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
+    except StopIteration:
+        raise ValueError(f"{source_file}: front matter is never closed") from None
+
+    meta: dict[str, str] = {}
+    for raw in lines[1:end]:
+        if not raw.strip():
+            continue
+        if ":" not in raw:
+            raise ValueError(f"{source_file}: bad front-matter line: {raw!r}")
+        key, _, value = raw.partition(":")
+        meta[key.strip()] = value.strip()
+
+    missing = [f for f in REQUIRED_FIELDS if not meta.get(f)]
+    if missing:
+        raise ValueError(f"{source_file}: front matter missing {missing}")
+
+    body = "\n".join(lines[end + 1 :]).strip("\n")
+    return meta, body
+
+
+def load_article(path: Path) -> Article:
+    """Load and validate a single article."""
+    text = path.read_text(encoding="utf-8")
+    meta, body = parse_front_matter(text, source_file=path.name)
+    return Article(
+        source_file=path.name,
+        article_id=meta["article_id"],
+        title=meta["title"],
+        product_area=meta["product_area"],
+        last_updated=meta["last_updated"],
+        body=body,
+    )
+
+
+def load_corpus(corpus_dir: str | Path | None = None) -> list[Article]:
+    """Load every article in the corpus directory, sorted by filename."""
+    root = Path(corpus_dir or get_settings().corpus_dir)
+    paths = sorted(p for p in root.glob("*.md") if p.is_file())
+    if not paths:
+        raise FileNotFoundError(f"No .md articles found under {root}")
+    return [load_article(p) for p in paths]
diff --git a/rag/ingest.py b/rag/ingest.py
new file mode 100644
index 0000000..e9400c0
--- /dev/null
+++ b/rag/ingest.py
@@ -0,0 +1,121 @@
+"""Ingest the 6 new help-centre articles under both chunking strategies.
+
+TIME REALITY (task requirement 6)
+    This script indexes the 6 NEW articles only. There is no historical corpus
+    in this index and nothing else is re-indexed. Each strategy's collection is
+    dropped and rebuilt from those 6 files, which takes seconds, not minutes.
+
+METADATA (task requirement 1)
+    Every chunk carries source_file, article_id, product_area and last_updated,
+    inherited from the article front matter, plus a stable chunk_id used as the
+    Chroma primary key so citations can be resolved later. Ingest refuses to
+    store a chunk that is missing any of them.
+
+Run:  python -m rag.ingest
+"""
+from __future__ import annotations
+
+import argparse
+import logging
+
+from langchain_core.documents import Document
+
+from config import STRATEGIES, get_settings
+from rag.chunkers import CHUNKERS, table_stats
+from rag.documents import Article, load_corpus
+from rag.vector_store import count_chunks, get_store, reset_store
+
+logger = logging.getLogger(__name__)
+
+REQUIRED_CHUNK_METADATA = ("source_file", "article_id", "product_area", "last_updated")
+
+
+def make_chunk_id(article_id: str, strategy: str, index: int) -> str:
+    """Stable, human-readable, resolvable chunk id: HC-4002-structured-007."""
+    return f"{article_id}-{strategy}-{index:03d}"
+
+
+def build_documents(article: Article, strategy: str) -> list[Document]:
+    """Chunk one article under one strategy and attach full metadata."""
+    texts = CHUNKERS[strategy](article.body)
+    docs: list[Document] = []
+    for i, text in enumerate(texts, start=1):
+        chunk_id = make_chunk_id(article.article_id, strategy, i)
+        metadata = article.base_metadata() | {
+            "chunk_id": chunk_id,
+            "strategy": strategy,
+            "chunk_index": i,
+            "char_len": len(text),
+            **table_stats(text),
+        }
+        missing = [f for f in REQUIRED_CHUNK_METADATA if not metadata.get(f)]
+        if missing:
+            # A chunk with no source_file is a failed ingest. Fail loudly.
+            raise ValueError(f"{chunk_id}: metadata missing {missing}")
+        docs.append(Document(page_content=text, metadata=metadata))
+    return docs
+
+
+def ingest_strategy(articles: list[Article], strategy: str) -> dict:
+    """Rebuild one strategy's collection from the given articles."""
+    reset_store(strategy)
+    store = get_store(strategy)
+
+    docs: list[Document] = []
+    for article in articles:
+        docs.extend(build_documents(article, strategy))
+
+    store.add_documents(docs, ids=[d.metadata["chunk_id"] for d in docs])
+
+    orphans = sum(1 for d in docs if d.metadata["orphan_table_rows"])
+    with_rows = sum(1 for d in docs if d.metadata["contains_table_rows"])
+    lengths = [d.metadata["char_len"] for d in docs]
+
+    return {
+        "strategy": strategy,
+        "articles": len(articles),
+        "chunks": len(docs),
+        "stored": count_chunks(strategy),
+        "chunks_with_table_rows": with_rows,
+        "chunks_with_orphan_rows": orphans,
+        "orphan_rate": round(orphans / with_rows, 3) if with_rows else 0.0,
+        "mean_chars": round(sum(lengths) / len(lengths)) if lengths else 0,
+        "max_chars": max(lengths) if lengths else 0,
+    }
+
+
+def ingest_all() -> list[dict]:
+    """Ingest the 6 new articles under every strategy."""
+    settings = get_settings()
+    articles = load_corpus(settings.corpus_dir)
+    logger.info("Loaded %d new articles from %s", len(articles), settings.corpus_dir)
+    return [ingest_strategy(articles, s) for s in STRATEGIES]
+
+
+def main() -> None:
+    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
+    parser = argparse.ArgumentParser(description="Ingest the 6 new help-centre articles.")
+    parser.parse_args()
+
+    stats = ingest_all()
+    print()
+    print("Ingest complete. NEW ARTICLES ONLY - no historical corpus re-indexed.")
+    print()
+    header = (
+        f"{'strategy':<12}{'articles':>9}{'chunks':>8}{'stored':>8}"
+        f"{'tbl-chunks':>12}{'orphan':>8}{'orphan%':>9}{'mean':>7}{'max':>6}"
+    )
+    print(header)
+    print("-" * len(header))
+    for s in stats:
+        print(
+            f"{s['strategy']:<12}{s['articles']:>9}{s['chunks']:>8}{s['stored']:>8}"
+            f"{s['chunks_with_table_rows']:>12}{s['chunks_with_orphan_rows']:>8}"
+            f"{s['orphan_rate'] * 100:>8.1f}%{s['mean_chars']:>7}{s['max_chars']:>6}"
+        )
+    print()
+    print("orphan = chunk holds table data rows but has lost its header row.")
+
+
+if __name__ == "__main__":
+    main()
diff --git a/rag/retriever.py b/rag/retriever.py
new file mode 100644
index 0000000..adcd6c7
--- /dev/null
+++ b/rag/retriever.py
@@ -0,0 +1,115 @@
+"""Search-only retrieval, with an optional metadata filter.
+
+Two things matter here.
+
+1. Search-only evaluation is NEVER threshold-filtered. If a question misses, it
+   misses because the chunker put the answer somewhere retrieval could not
+   reach, not because a threshold quietly dropped it. Thresholding is applied
+   only at generation time, and it is applied explicitly.
+
+2. The product_area filter is a real pre-filter inside Chroma, not a post-filter
+   applied to the top-5. That distinction matters: a post-filter can only remove
+   results, so it can never promote a chunk that was ranked 11th into top-1. A
+   pre-filter can, and requirement 4 asks us to show exactly that.
+"""
+from __future__ import annotations
+
+import logging
+from typing import Optional
+
+from langchain_core.documents import Document
+
+from config import get_settings
+from rag.vector_store import get_store
+
+logger = logging.getLogger(__name__)
+
+ScoredDoc = tuple[Document, float]
+
+
+def search(
+    query: str,
+    strategy: str,
+    *,
+    k: Optional[int] = None,
+    product_area: Optional[str] = None,
+) -> list[ScoredDoc]:
+    """Return the top-k chunks for ``query`` from one strategy's collection.
+
+    Args:
+        query: The user question, used verbatim.
+        strategy: "baseline" or "structured".
+        k: How many results. Defaults to settings.top_k (5).
+        product_area: When given, Chroma searches only chunks whose
+            product_area metadata equals this value.
+    """
+    settings = get_settings()
+    k = k or settings.top_k
+    store = get_store(strategy)
+
+    kwargs: dict = {}
+    if product_area:
+        kwargs["filter"] = {"product_area": {"$eq": product_area}}
+
+    try:
+        return store.similarity_search_with_relevance_scores(query, k=k, **kwargs)
+    except Exception as exc:  # pragma: no cover - defensive
+        logger.error("Search failed (%s, filter=%s): %s", strategy, product_area, exc)
+        return []
+
+
+def format_hits(scored: list[ScoredDoc]) -> list[dict]:
+    """Flatten results into plain dicts for dumping into the write-up."""
+    out: list[dict] = []
+    for rank, (doc, score) in enumerate(scored, start=1):
+        md = doc.metadata
+        out.append(
+            {
+                "rank": rank,
+                "score": round(float(score), 4),
+                "chunk_id": md.get("chunk_id", "?"),
+                "article_id": md.get("article_id", "?"),
+                "source_file": md.get("source_file", "?"),
+                "product_area": md.get("product_area", "?"),
+                "last_updated": md.get("last_updated", "?"),
+                "has_table_header": bool(md.get("has_table_header")),
+                "orphan_table_rows": bool(md.get("orphan_table_rows")),
+                "char_len": md.get("char_len", len(doc.page_content)),
+                "text": doc.page_content,
+            }
+        )
+    return out
+
+
+def chunk_answers_question(text: str, must_contain: list[str]) -> bool:
+    """Does this chunk literally contain every required piece of the answer?
+
+    Case-insensitive substring match. This is the objective half of the hit
+    rule. It is deliberately unforgiving: a chunk that mentions the error code
+    but has lost the fix cannot answer the question, so it is not a hit.
+    """
+    haystack = text.lower()
+    return all(needle.lower() in haystack for needle in must_contain)
+
+
+def format_context(scored: list[ScoredDoc]) -> str:
+    """Render retrieved chunks as labelled context blocks for the prompt.
+
+    Every block is labelled with its chunk_id, because the generation prompt
+    requires the model to cite that exact id. A model cannot cite an id it was
+    never shown.
+    """
+    if not scored:
+        return "NO CONTEXT BLOCKS WERE RETRIEVED."
+    blocks: list[str] = []
+    for doc, score in scored:
+        md = doc.metadata
+        blocks.append(
+            f"[{md.get('chunk_id', '?')}] "
+            f"(article {md.get('article_id', '?')}, "
+            f"file {md.get('source_file', '?')}, "
+            f"area {md.get('product_area', '?')}, "
+            f"updated {md.get('last_updated', '?')}, "
+            f"score {float(score):.4f})\n{doc.page_content.strip()}"
+        )
+    return "\n\n---\n\n".join(blocks)
diff --git a/rag/vector_store.py b/rag/vector_store.py
new file mode 100644
index 0000000..8e77882
--- /dev/null
+++ b/rag/vector_store.py
@@ -0,0 +1,86 @@
+"""Chroma vector stores, one collection per chunking strategy.
+
+Both collections live in the same persist directory and share one embedding
+model. Keeping them side by side is what lets the evaluation run the same 8
+questions against both strategies in a single process, with no re-indexing
+between runs.
+"""
+from __future__ import annotations
+
+import logging
+from functools import lru_cache
+
+from langchain_chroma import Chroma
+
+from config import COLLECTIONS, get_settings
+from rag.embeddings import get_embeddings
+
+logger = logging.getLogger(__name__)
+
+
+def _collection_name(strategy: str) -> str:
+    try:
+        return COLLECTIONS[strategy]
+    except KeyError:
+        raise ValueError(
+            f"Unknown strategy {strategy!r}. Expected one of {list(COLLECTIONS)}."
+        ) from None
+
+
+@lru_cache
+def get_store(strategy: str) -> Chroma:
+    """Return the cached Chroma store for one chunking strategy."""
+    settings = get_settings()
+    settings.ensure_dirs()
+    return Chroma(
+        collection_name=_collection_name(strategy),
+        embedding_function=get_embeddings(),
+        persist_directory=settings.chroma_dir,
+        # Cosine keeps the relevance score readable as 1 - distance, so the
+        # numbers pasted into results.md mean something.
+        collection_metadata={"hnsw:space": settings.distance_metric},
+    )
+
+
+def count_chunks(strategy: str) -> int:
+    try:
+        return get_store(strategy)._collection.count()
+    except Exception as exc:  # pragma: no cover - defensive
+        logger.warning("Could not count %s: %s", strategy, exc)
+        return 0
+
+
+def reset_store(strategy: str) -> Chroma:
+    """Drop and recreate one strategy's collection.
+
+    Scoped to a single strategy on purpose. Nothing here touches any other
+    collection, and nothing here re-indexes a historical corpus.
+    """
+    store = get_store(strategy)
+    try:
+        store.delete_collection()
+    except Exception as exc:  # pragma: no cover - defensive
+        logger.warning("delete_collection(%s) failed, continuing: %s", strategy, exc)
+    get_store.cache_clear()
+    return get_store(strategy)
+
+
+def get_chunk_by_id(strategy: str, chunk_id: str) -> dict | None:
+    """Resolve a chunk_id back to its text and metadata.
+
+    This is what makes a citation checkable. If a citation does not resolve
+    here, it is a fabricated citation.
+    """
+    store = get_store(strategy)
+    try:
+        got = store._collection.get(ids=[chunk_id], include=["documents", "metadatas"])
+    except Exception as exc:  # pragma: no cover - defensive
+        logger.warning("get(%s) failed: %s", chunk_id, exc)
+        return None
+    if not got or not got.get("ids"):
+        return None
+    return {
+        "chunk_id": got["ids"][0],
+        "text": got["documents"][0],
+        "metadata": got["metadatas"][0],
+    }
```
