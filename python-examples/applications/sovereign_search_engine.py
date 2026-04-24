"""
Zhilicon Example - Sovereign Search Engine
============================================
Complete sovereign search engine: document ingestion, indexing, BM25 + semantic
search with embeddings, result ranking, snippet generation, search analytics --
all within sovereign boundary.  Like Elasticsearch but sovereign.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums / config
# ---------------------------------------------------------------------------

class IndexStatus(Enum):
    BUILDING = "building"
    READY = "ready"
    UPDATING = "updating"
    ERROR = "error"


class SearchMode(Enum):
    BM25 = "bm25"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


@dataclass
class SearchConfig:
    zone_id: str = "eu-sovereign"
    max_results: int = 20
    snippet_length: int = 200
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    semantic_weight: float = 0.5
    min_score: float = 0.01
    enable_analytics: bool = True
    embedding_dim: int = 128


# ---------------------------------------------------------------------------
# Document model
# ---------------------------------------------------------------------------

@dataclass
class Document:
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    title: str = ""
    body: str = ""
    url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    zone_id: str = ""


@dataclass
class SearchResult:
    doc_id: str
    title: str
    snippet: str
    score: float
    url: str = ""
    bm25_score: float = 0.0
    semantic_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)


@dataclass
class SearchResponse:
    query: str
    results: List[SearchResult]
    total_hits: int
    took_ms: float
    mode: SearchMode = SearchMode.HYBRID
    zone_id: str = ""


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

class SimpleTokenizer:
    """Simple whitespace + punctuation tokenizer with stop-word removal."""

    STOP_WORDS = frozenset(
        "a an the is are was were be been being have has had do does did "
        "will would shall should may might can could of in to for on with "
        "at by from as into through during before after above below and "
        "but or nor not so yet both either neither each every all any few "
        "more most other some such no only own same than too very it its "
        "this that these those he she we they i me him her us them my his "
        "your our their what which who whom where when how".split()
    )

    def tokenize(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()
        return [t for t in tokens if t not in self.STOP_WORDS and len(t) > 1]

    def ngrams(self, text: str, n: int = 2) -> List[str]:
        tokens = self.tokenize(text)
        return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


# ---------------------------------------------------------------------------
# BM25 index
# ---------------------------------------------------------------------------

class BM25Index:
    """Okapi BM25 inverted index."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._tokenizer = SimpleTokenizer()
        self._doc_lengths: Dict[str, int] = {}
        self._avg_dl: float = 0.0
        self._N: int = 0
        self._tf: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._df: Dict[str, int] = defaultdict(int)
        self._doc_tokens: Dict[str, List[str]] = {}

    def add_document(self, doc_id: str, text: str) -> None:
        tokens = self._tokenizer.tokenize(text)
        self._doc_tokens[doc_id] = tokens
        self._doc_lengths[doc_id] = len(tokens)
        self._N += 1
        self._avg_dl = sum(self._doc_lengths.values()) / self._N if self._N else 0
        seen: Set[str] = set()
        for t in tokens:
            self._tf[doc_id][t] += 1
            if t not in seen:
                self._df[t] += 1
                seen.add(t)

    def remove_document(self, doc_id: str) -> None:
        if doc_id not in self._doc_tokens:
            return
        tokens = self._doc_tokens.pop(doc_id)
        self._doc_lengths.pop(doc_id, None)
        seen: Set[str] = set()
        for t in tokens:
            if t not in seen:
                self._df[t] = max(0, self._df.get(t, 0) - 1)
                seen.add(t)
        self._tf.pop(doc_id, None)
        self._N -= 1
        self._avg_dl = sum(self._doc_lengths.values()) / self._N if self._N else 0

    def search(self, query: str, top_k: int = 20) -> List[Tuple[str, float]]:
        tokens = self._tokenizer.tokenize(query)
        scores: Dict[str, float] = defaultdict(float)
        for term in tokens:
            if term not in self._df:
                continue
            df_t = self._df[term]
            idf = math.log((self._N - df_t + 0.5) / (df_t + 0.5) + 1)
            for doc_id, tf_map in self._tf.items():
                tf = tf_map.get(term, 0)
                if tf == 0:
                    continue
                dl = self._doc_lengths.get(doc_id, 0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self._avg_dl) \
                    if self._avg_dl > 0 else tf + self.k1
                scores[doc_id] += idf * numerator / denominator
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return ranked[:top_k]


# ---------------------------------------------------------------------------
# Simple embedding model (synthetic for demo)
# ---------------------------------------------------------------------------

class SimpleEmbeddingModel:
    """Produces deterministic pseudo-embeddings for text (demo only)."""

    def __init__(self, dim: int = 128):
        self.dim = dim

    def embed(self, text: str) -> List[float]:
        h = hashlib.sha256(text.lower().encode()).digest()
        vec = []
        for i in range(self.dim):
            byte_idx = i % len(h)
            val = (h[byte_idx] + i) / 255.0 - 0.5
            vec.append(val)
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


def _cosine_sim(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# Semantic index
# ---------------------------------------------------------------------------

class SemanticIndex:
    """Brute-force vector index for semantic search."""

    def __init__(self, embedding_dim: int = 128):
        self._model = SimpleEmbeddingModel(embedding_dim)
        self._vectors: Dict[str, List[float]] = {}

    def add_document(self, doc_id: str, text: str) -> None:
        self._vectors[doc_id] = self._model.embed(text)

    def remove_document(self, doc_id: str) -> None:
        self._vectors.pop(doc_id, None)

    def search(self, query: str, top_k: int = 20) -> List[Tuple[str, float]]:
        qvec = self._model.embed(query)
        scores = []
        for doc_id, dvec in self._vectors.items():
            sim = _cosine_sim(qvec, dvec)
            scores.append((doc_id, sim))
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]


# ---------------------------------------------------------------------------
# Snippet generator
# ---------------------------------------------------------------------------

class SnippetGenerator:
    """Generates highlighted text snippets for search results."""

    def __init__(self, max_length: int = 200):
        self.max_length = max_length
        self._tokenizer = SimpleTokenizer()

    def generate(self, text: str, query: str) -> Tuple[str, List[str]]:
        query_tokens = set(self._tokenizer.tokenize(query))
        sentences = re.split(r"[.!?]+", text)
        scored: List[Tuple[float, str]] = []
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            sent_tokens = set(self._tokenizer.tokenize(sent))
            overlap = len(query_tokens & sent_tokens)
            score = overlap / len(query_tokens) if query_tokens else 0
            scored.append((score, sent))
        scored.sort(key=lambda x: -x[0])
        snippet_parts = []
        highlights = []
        total_len = 0
        for score, sent in scored:
            if total_len + len(sent) > self.max_length:
                break
            snippet_parts.append(sent)
            total_len += len(sent)
            for qt in query_tokens:
                pattern = re.compile(re.escape(qt), re.IGNORECASE)
                for m in pattern.finditer(sent):
                    start = max(0, m.start() - 20)
                    end = min(len(sent), m.end() + 20)
                    highlights.append(sent[start:end])
        snippet = ". ".join(snippet_parts)
        if len(snippet) > self.max_length:
            snippet = snippet[: self.max_length] + "..."
        return snippet, highlights[:5]


# ---------------------------------------------------------------------------
# Search analytics
# ---------------------------------------------------------------------------

class SearchAnalytics:
    """Tracks search queries and click-through for analytics."""

    def __init__(self, zone_id: str = ""):
        self.zone_id = zone_id
        self._queries: List[Dict[str, Any]] = []
        self._clicks: List[Dict[str, Any]] = []
        self._query_counts: Counter = Counter()
        self._zero_results: int = 0
        self._total_searches: int = 0

    def record_search(self, query: str, num_results: int, took_ms: float) -> None:
        self._total_searches += 1
        self._query_counts[query.lower()] += 1
        if num_results == 0:
            self._zero_results += 1
        self._queries.append({
            "query": query, "results": num_results,
            "took_ms": took_ms, "timestamp": time.time(),
        })
        if len(self._queries) > 50000:
            self._queries = self._queries[-25000:]

    def record_click(self, query: str, doc_id: str, position: int) -> None:
        self._clicks.append({
            "query": query, "doc_id": doc_id,
            "position": position, "timestamp": time.time(),
        })
        if len(self._clicks) > 50000:
            self._clicks = self._clicks[-25000:]

    def get_popular_queries(self, limit: int = 20) -> List[Tuple[str, int]]:
        return self._query_counts.most_common(limit)

    def get_click_through_rate(self) -> float:
        if self._total_searches == 0:
            return 0.0
        return len(self._clicks) / self._total_searches

    def get_zero_result_rate(self) -> float:
        if self._total_searches == 0:
            return 0.0
        return self._zero_results / self._total_searches

    def get_avg_latency_ms(self) -> float:
        if not self._queries:
            return 0.0
        return sum(q["took_ms"] for q in self._queries) / len(self._queries)

    def get_dashboard(self) -> Dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "total_searches": self._total_searches,
            "unique_queries": len(self._query_counts),
            "zero_result_rate": round(self.get_zero_result_rate(), 4),
            "click_through_rate": round(self.get_click_through_rate(), 4),
            "avg_latency_ms": round(self.get_avg_latency_ms(), 2),
            "popular_queries": self.get_popular_queries(10),
        }


# ---------------------------------------------------------------------------
# Sovereign search engine
# ---------------------------------------------------------------------------

class SovereignSearchEngine:
    """
    Complete sovereign search engine combining BM25 and semantic search.
    All data stays within the configured sovereign zone.
    """

    def __init__(self, config: Optional[SearchConfig] = None):
        self.config = config or SearchConfig()
        self.zone_id = self.config.zone_id
        self._documents: Dict[str, Document] = {}
        self._bm25 = BM25Index(self.config.bm25_k1, self.config.bm25_b)
        self._semantic = SemanticIndex(self.config.embedding_dim)
        self._snippet_gen = SnippetGenerator(self.config.snippet_length)
        self._analytics = SearchAnalytics(self.zone_id)
        self._status = IndexStatus.READY

    def ingest(self, doc: Document) -> str:
        doc.zone_id = self.zone_id
        self._documents[doc.doc_id] = doc
        combined = f"{doc.title} {doc.body}"
        self._bm25.add_document(doc.doc_id, combined)
        self._semantic.add_document(doc.doc_id, combined)
        return doc.doc_id

    def ingest_batch(self, docs: List[Document]) -> List[str]:
        self._status = IndexStatus.UPDATING
        ids = [self.ingest(d) for d in docs]
        self._status = IndexStatus.READY
        return ids

    def delete(self, doc_id: str) -> bool:
        if doc_id not in self._documents:
            return False
        self._documents.pop(doc_id)
        self._bm25.remove_document(doc_id)
        self._semantic.remove_document(doc_id)
        return True

    def search(self, query: str, mode: Optional[SearchMode] = None,
               max_results: Optional[int] = None) -> SearchResponse:
        t0 = time.time()
        mode = mode or SearchMode.HYBRID
        top_k = max_results or self.config.max_results

        bm25_results: Dict[str, float] = {}
        semantic_results: Dict[str, float] = {}

        if mode in (SearchMode.BM25, SearchMode.HYBRID):
            for did, score in self._bm25.search(query, top_k * 2):
                bm25_results[did] = score

        if mode in (SearchMode.SEMANTIC, SearchMode.HYBRID):
            for did, score in self._semantic.search(query, top_k * 2):
                semantic_results[did] = score

        # normalize
        bm25_max = max(bm25_results.values()) if bm25_results else 1.0
        sem_max = max(semantic_results.values()) if semantic_results else 1.0
        if bm25_max > 0:
            bm25_results = {k: v / bm25_max for k, v in bm25_results.items()}
        if sem_max > 0:
            semantic_results = {k: v / sem_max for k, v in semantic_results.items()}

        # combine
        all_ids = set(bm25_results) | set(semantic_results)
        w = self.config.semantic_weight
        combined: List[Tuple[str, float, float, float]] = []
        for did in all_ids:
            bm = bm25_results.get(did, 0.0)
            se = semantic_results.get(did, 0.0)
            score = (1 - w) * bm + w * se
            if score >= self.config.min_score:
                combined.append((did, score, bm, se))
        combined.sort(key=lambda x: -x[1])
        combined = combined[:top_k]

        results = []
        for did, score, bm_score, sem_score in combined:
            doc = self._documents.get(did)
            if not doc:
                continue
            snippet, highlights = self._snippet_gen.generate(doc.body, query)
            results.append(SearchResult(
                doc_id=did, title=doc.title, snippet=snippet,
                score=round(score, 4), url=doc.url,
                bm25_score=round(bm_score, 4),
                semantic_score=round(sem_score, 4),
                metadata=doc.metadata, highlights=highlights,
            ))

        took = (time.time() - t0) * 1000
        if self.config.enable_analytics:
            self._analytics.record_search(query, len(results), took)

        return SearchResponse(
            query=query, results=results, total_hits=len(results),
            took_ms=round(took, 2), mode=mode, zone_id=self.zone_id,
        )

    def record_click(self, query: str, doc_id: str, position: int) -> None:
        self._analytics.record_click(query, doc_id, position)

    def get_analytics(self) -> Dict[str, Any]:
        return self._analytics.get_dashboard()

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": self._status.value,
            "zone_id": self.zone_id,
            "total_documents": len(self._documents),
            "analytics": self._analytics.get_dashboard(),
        }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def run_demo() -> None:
    engine = SovereignSearchEngine(SearchConfig(zone_id="eu-west-sovereign"))
    sample_docs = [
        Document(title="Sovereign AI Computing",
                 body="Zhilicon provides sovereign AI infrastructure ensuring data "
                      "never leaves the configured jurisdiction. Hardware-rooted "
                      "trust with Zhipu chips enables true data sovereignty."),
        Document(title="Federated Learning Guide",
                 body="Federated learning allows training models across multiple "
                      "organizations without sharing raw data. Each participant "
                      "trains locally and only shares encrypted gradients."),
        Document(title="Privacy-Preserving ML",
                 body="Differential privacy adds calibrated noise to query results "
                      "protecting individual records while maintaining aggregate "
                      "accuracy. Epsilon tracking ensures budget compliance."),
        Document(title="Zhipu Chip Architecture",
                 body="The Zhipu accelerator features a 7nm process node with "
                      "hardware TEE, on-chip encryption, and memory isolation. "
                      "Designed for sovereign AI workloads in regulated industries."),
        Document(title="Healthcare AI Applications",
                 body="AI in healthcare enables faster diagnosis, drug discovery "
                      "and personalized treatment plans. Sovereign deployment "
                      "ensures patient data compliance with HIPAA and GDPR."),
    ]
    engine.ingest_batch(sample_docs)
    queries = ["sovereign data", "federated learning privacy",
               "chip architecture", "healthcare AI"]
    for q in queries:
        resp = engine.search(q)
        logger.info("Query '%s': %d results in %.1f ms",
                    q, resp.total_hits, resp.took_ms)
        for r in resp.results[:3]:
            logger.info("  [%.3f] %s", r.score, r.title)
    logger.info("Analytics: %s", json.dumps(engine.get_analytics(), indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_demo()
