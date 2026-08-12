"""Article loading and front-matter parsing.

Each help-centre article carries YAML-style front matter that supplies the
metadata every chunk must inherit:

    ---
    article_id: HC-4002
    title: Invoice Errors After the Billing Migration
    product_area: invoicing
    last_updated: 2026-06-11
    ---

An article missing any required field is a hard failure. A chunk with no
source_file is a failed ingest, so we refuse to ingest a file we cannot label.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import get_settings

REQUIRED_FIELDS = ("article_id", "title", "product_area", "last_updated")


@dataclass(frozen=True)
class Article:
    """One help-centre article: its metadata plus its body text."""

    source_file: str
    article_id: str
    title: str
    product_area: str
    last_updated: str
    body: str

    def base_metadata(self) -> dict:
        """The metadata every chunk of this article inherits."""
        return {
            "source_file": self.source_file,
            "article_id": self.article_id,
            "title": self.title,
            "product_area": self.product_area,
            "last_updated": self.last_updated,
        }


def parse_front_matter(text: str, *, source_file: str) -> tuple[dict, str]:
    """Split ``text`` into (front-matter dict, body).

    Raises ValueError when the front matter is missing or incomplete, because a
    silently unlabelled chunk is worse than a loud failure.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{source_file}: missing front matter (no opening '---')")

    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError(f"{source_file}: front matter is never closed") from None

    meta: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip():
            continue
        if ":" not in raw:
            raise ValueError(f"{source_file}: bad front-matter line: {raw!r}")
        key, _, value = raw.partition(":")
        meta[key.strip()] = value.strip()

    missing = [f for f in REQUIRED_FIELDS if not meta.get(f)]
    if missing:
        raise ValueError(f"{source_file}: front matter missing {missing}")

    body = "\n".join(lines[end + 1 :]).strip("\n")
    return meta, body


def load_article(path: Path) -> Article:
    """Load and validate a single article."""
    text = path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text, source_file=path.name)
    return Article(
        source_file=path.name,
        article_id=meta["article_id"],
        title=meta["title"],
        product_area=meta["product_area"],
        last_updated=meta["last_updated"],
        body=body,
    )


def load_corpus(corpus_dir: str | Path | None = None) -> list[Article]:
    """Load every article in the corpus directory, sorted by filename."""
    root = Path(corpus_dir or get_settings().corpus_dir)
    paths = sorted(p for p in root.glob("*.md") if p.is_file())
    if not paths:
        raise FileNotFoundError(f"No .md articles found under {root}")
    return [load_article(p) for p in paths]
