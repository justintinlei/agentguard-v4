"""Small, deterministic retriever for AgentGuard v2 - no vector database,
just word-overlap scoring against Day 3's policy corpus.

Turns text into comparable tokens, scores two token lists for
similarity, and returns the top-K best-matching policy chunks for a
query, with deterministic tie-breaking.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import asdict, dataclass

from policy_library import PolicyChunk
from scanner import ScanResult

# Matches runs of lowercase letters, digits, and underscores - the units
# compared between a query and a policy chunk. Everything else (spaces,
# punctuation) acts as a separator between tokens.
TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")

# Common English filler words that show up in almost every sentence
# regardless of topic, so they're dropped before comparing text.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "that", "the", "this", "to", "with",
}


def tokenize(text: str) -> list[str]:
    """Lowercase text, split it into word tokens, and drop stopwords."""
    all_tokens = TOKEN_PATTERN.findall(text.lower())
    return [token for token in all_tokens if token not in STOPWORDS]


def _cosine_similarity(query_tokens: list[str], chunk_tokens: list[str]) -> float:
    """Score how similar two token lists are, from 0.0 to 1.0.

    Treats each token list as a term-frequency vector - one dimension per
    unique word, the word's count as the value - and returns the cosine
    of the angle between the two vectors. Internal helper: only
    `retrieve()` (added in a later lab) is meant to call this.
    """
    if not query_tokens or not chunk_tokens:
        return 0.0

    query_counts = Counter(query_tokens)
    chunk_counts = Counter(chunk_tokens)

    shared_words = set(query_counts) & set(chunk_counts)
    dot_product = sum(query_counts[word] * chunk_counts[word] for word in shared_words)

    query_magnitude = math.sqrt(sum(count * count for count in query_counts.values()))
    chunk_magnitude = math.sqrt(sum(count * count for count in chunk_counts.values()))

    if query_magnitude == 0 or chunk_magnitude == 0:
        return 0.0

    return dot_product / (query_magnitude * chunk_magnitude)


@dataclass(frozen=True)
class RetrievalHit:
    """One PolicyChunk that matched a query, plus its score and the
    specific words the query and the chunk had in common.
    """

    chunk_id: str
    policy_id: str
    title: str
    text: str
    source_path: str
    sha256: str
    score: float
    matched_terms: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def retrieve(query: str, chunks: list[PolicyChunk], top_k: int = 3) -> list[RetrievalHit]:
    """Return the top_k chunks most similar to query, best match first.

    Ties are broken by chunk_id (ascending), so the exact same query and
    corpus always produce the exact same output order - no dependency on
    dict/set iteration order or any other incidental factor.
    """
    query_tokens = tokenize(query)
    hits: list[RetrievalHit] = []

    for chunk in chunks:
        chunk_tokens = tokenize(f"{chunk.title}\n{chunk.text}")
        score = _cosine_similarity(query_tokens, chunk_tokens)
        if score <= 0:
            continue
        matched_terms = tuple(sorted(set(query_tokens) & set(chunk_tokens)))
        hits.append(
            RetrievalHit(
                chunk_id=chunk.chunk_id,
                policy_id=chunk.policy_id,
                title=chunk.title,
                text=chunk.text,
                source_path=chunk.source_path,
                sha256=chunk.sha256,
                score=round(score, 6),
                matched_terms=matched_terms,
            )
        )

    hits.sort(key=lambda hit: (-hit.score, hit.chunk_id))
    return hits[:top_k]


def build_retrieval_query(scan_result: ScanResult) -> str:
    """Turn a v1 ScanResult into search text for retrieve().

    Joins the agent name, the risk level, and every finding's title,
    explanation, and recommendation - the natural-language parts of a
    finding - into one string. This function only reads scan_result; it
    has no way to change the score it's describing.
    """
    parts = [scan_result.agent.agent_name, scan_result.risk_level]
    for finding in scan_result.findings:
        parts.append(finding.title)
        parts.append(finding.explanation)
        parts.append(finding.recommendation)
    return " ".join(parts)


def format_hits(hits: list[RetrievalHit]) -> str:
    """Turn retrieved hits into a readable summary of why each one matched.

    For each hit: its chunk ID, similarity score, which specific words
    caused the match, and a short preview of the text - so a human can
    audit a retrieval result instead of just trusting the ranking.
    """
    if not hits:
        return "No relevant policy evidence found."

    lines = []
    for rank, hit in enumerate(hits, start=1):
        preview = hit.text if len(hit.text) <= 80 else hit.text[:77] + "..."
        lines.append(
            f"{rank}. {hit.chunk_id} (score={hit.score:.4f}) "
            f"matched: {', '.join(hit.matched_terms)}\n"
            f"   {preview}"
        )
    return "\n".join(lines)
