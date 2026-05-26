# Keyword And Hybrid Retrieval Implementation Plan

## Context

The current library RAG system uses semantic search implemented as vector search:

```text
User query
 -> retrieve_with_gate_retry()
 -> VectorStore.search()
 -> LlamaIndex retriever
 -> LanceDB vector retrieval
 -> retrieval gate / retry
 -> optional reranker
 -> final contexts
 -> LLM answer
```

Current implementation details:

- Documents are chunked by `library/pdf_processor.py`.
- Chunks are embedded with `bge-m3` through Ollama.
- Vectors are stored in LanceDB through LlamaIndex.
- `library/vector_store.py::VectorStore.search()` returns semantic/vector candidates.
- `evals/auto_retrieve.py::retrieve_with_gate_retry()` retries retrieval by increasing `top_k`.
- The reranker runs once after retry retrieval finishes, not on every retry attempt.

The missing capability is lexical keyword retrieval. Vector search is good at semantic meaning, but it can miss or mis-rank exact terms such as:

- acronyms: `BM25`, `RRF`, `LoRA`, `RAGAS`
- model names: `bge-reranker-v2-m3`
- function/class names
- filenames and book titles
- version numbers
- short ambiguous terms: `rank`, `index`, `cache`
- exact error messages or exact phrases

Keyword search should complement vector search, not replace it.

## Objective

Add optional local keyword search and hybrid retrieval while preserving current vector-only behavior by default.

Target flow:

```text
User query
 -> vector candidates
 -> keyword candidates
 -> merge/dedupe with RRF
 -> retrieval-time noise downrank/filter
 -> retrieval gate / retry
 -> optional reranker
 -> final contexts
 -> LLM answer
```

This milestone should not require re-chunking, re-embedding, or re-indexing the whole library.

## Non-Goals

Out of scope for this milestone:

- Re-chunking the existing PDF library.
- Re-embedding all documents.
- Replacing LanceDB.
- Replacing `library/data/metadata.json`.
- Migrating metadata to SQL.
- Implementing pgvector, Qdrant, Elasticsearch, or OpenSearch.
- Implementing persistent SQLite FTS5 as the first step.
- Changing existing retrieval thresholds.
- Fine-tuning embeddings or rerankers.
- Calling hosted search APIs.

## Threshold Policy

Keep existing retrieval gate thresholds unchanged for this implementation.

Current config values should remain as-is:

```yaml
rag:
  min_similarity: 0.72
  min_top_similarity: 0.72
  min_avg_similarity: 0.60
```

Important: hybrid scores and keyword scores must not be treated as vector similarity scores. Do not compare `hybrid_score`, `keyword_score`, or `rerank_score` directly against `min_top_similarity`.

## Current Storage

Current library data:

```text
library/data/metadata.json
library/data/documents/
library/data/vectors_v2/
```

Current vector result fields:

```text
chunk_id
doc_id
text
chapter
chunk_index
title
filename
file_path
score
```

Keyword and hybrid retrieval should preserve this shape and add non-breaking metadata fields.

## Recommended Milestones

### Milestone 1: Retrieval-Time Noise Filter

Add a lightweight retrieval-time quality filter/downrank step before final candidate selection and before reranking.

This does not require re-chunking or re-indexing.

Purpose:

- Reduce noisy front/back matter from winning retrieval.
- Avoid hard deleting existing chunks.
- Keep the current corpus intact.

Downrank candidates whose text/title/chapter looks like:

```text
Cover
Table of Contents
Contents
Praise for
Copyright
Index
References
Bibliography
About the Author
```

Start with downranking, not hard filtering. Some contents/index chunks may still be useful for locating chapter names, but they should not usually outrank body content.

Suggested config:

```yaml
rag:
  content_quality:
    enabled: true
    mode: downrank
    penalty: 0.2
    patterns:
      - "^\\s*table of contents\\b"
      - "^\\s*contents\\b"
      - "^\\s*praise for\\b"
      - "^\\s*copyright\\b"
      - "^\\s*index\\b"
      - "^\\s*references\\b"
      - "^\\s*bibliography\\b"
      - "^\\s*about the author\\b"
```

Implementation note:

- Add `noise_score` or `content_quality_penalty` metadata.
- Keep original `score` available.
- If applying a penalty to ranking, preserve original values such as `vector_score` and `keyword_score`.

### Milestone 2: In-Memory Keyword Search Prototype

Add local keyword search over existing chunks.

Purpose:

- Validate exact-term retrieval quickly.
- Avoid metadata migration.
- Avoid reprocessing PDFs.
- Keep changes reversible.

Preferred first input source:

```text
Read existing chunks from LanceDB table document_chunks_v2.
```

If direct LanceDB extraction is unreliable, add a small helper on `VectorStore` to export existing chunk records.

Suggested file:

```text
library/keyword_search.py
```

Suggested interface:

```python
class KeywordSearch:
    def build(self) -> None:
        ...

    def search(self, query: str, top_k: int = 20) -> list[dict]:
        ...
```

Returned fields should include:

```text
chunk_id
doc_id
text
chapter
chunk_index
title
filename
file_path
score
keyword_score
rank_source = "keyword"
keyword_rank
```

The `score` field must remain compatible with existing RAG code, but keyword-specific values should also be exposed as `keyword_score`.

### Milestone 3: Hybrid Retriever With RRF

Add a hybrid retriever that calls both vector search and keyword search, then merges candidates with Reciprocal Rank Fusion.

Suggested file:

```text
library/hybrid_retriever.py
```

Suggested interface:

```python
class HybridRetriever:
    def search(self, query: str, top_k: int) -> list[dict]:
        ...
```

Target flow:

```text
VectorStore.search(query, vector_top_k)
KeywordSearch.search(query, keyword_top_k)
merge by chunk_id / doc_id+chunk_index / text fingerprint
rank by RRF
apply content-quality downrank
return final top_k candidates
```

Use RRF first:

```text
rrf_score += weight / (rrf_k + rank)
```

Why RRF:

- Vector scores and BM25 scores are not on the same scale.
- RRF merges ranks, not raw score magnitudes.
- It is simple and inspectable.

Hybrid result fields:

```text
chunk_id
doc_id
text
title
chapter
chunk_index
filename
file_path
score
score_type
vector_score
keyword_score
hybrid_score
vector_rank
keyword_rank
hybrid_rank
rank_sources
content_quality_penalty
```

### Milestone 4: Runtime Feature Flag Integration

Keep current behavior unchanged unless hybrid is enabled.

Suggested config:

```yaml
rag:
  keyword_search:
    enabled: false
    provider: in_memory_bm25
    input_source: lancedb
    top_k: 20
    min_score:
    rebuild_on_startup: false
    cache_path: library/data/keyword_index
    max_chunks_for_in_memory: 50000
    fields:
      text_weight: 1.0
      title_weight: 2.0
      chapter_weight: 1.5

  hybrid_search:
    enabled: false
    vector_top_k: 20
    keyword_top_k: 20
    final_top_k: 8
    merge_strategy: rrf
    rrf_k: 60
    vector_weight: 1.0
    keyword_weight: 1.0
```

Preferred low-risk integration:

```text
Build a HybridRetriever with a .search(query, top_k) method and pass it where vector_store is currently expected.
```

This keeps `retrieve_with_gate_retry()` mostly unchanged.

## Retry Retrieve Semantics

Hybrid retrieval must respect `top_k` from retry retrieval.

Currently retry retrieval increases `top_k`, then calls:

```text
retriever.search(query, top_k=retry_top_k)
```

For `HybridRetriever.search(query, top_k)`, define:

```text
top_k = final candidate count returned after merge
vector_top_k = max(config.vector_top_k, top_k * 2)
keyword_top_k = max(config.keyword_top_k, top_k * 2)
```

This makes retry meaningful in hybrid mode.

Example:

```text
retry top_k = 14
vector_top_k = max(20, 28)
keyword_top_k = max(20, 28)
merged final output = 14
```

## Score Semantics

Do not collapse all scoring into one ambiguous `score`.

Recommended meanings:

```text
score
  Backward-compatible ranking score used by old UI/RAG code.

score_type
  "vector_similarity", "keyword_bm25", or "hybrid_rrf".

vector_score
  Original semantic/vector similarity from LanceDB/LlamaIndex.

keyword_score
  Keyword/BM25 lexical score.

hybrid_score
  RRF score after merging vector and keyword ranks.

rerank_score
  Cross-encoder score from the reranker, if reranker is enabled.
```

Retrieval gate currently expects vector similarity. Therefore:

- Do not compare `hybrid_score` to `min_top_similarity`.
- Do not compare `keyword_score` to `min_top_similarity`.
- Do not compare `rerank_score` to `min_top_similarity`.
- Preserve vector scores wherever available.
- Add trace metadata that states which score type is being displayed.

## Tokenization

First tokenizer:

- lowercase English terms
- split on punctuation and word boundaries
- preserve acronyms by lowercasing them consistently
- preserve numbers and version strings where practical
- add exact substring/phrase boost

Exact term boost examples:

```text
BM25
RRF
query rewrite
bge-reranker-v2-m3
llama_index
```

Thai tokenization should not block the first milestone. The initial version will still help Thai/English mixed queries when the technical terms are English acronyms or model names.

Future options:

- PyThaiNLP
- ICU tokenizer
- SQLite FTS5 unicode61
- Tantivy tokenizer

## Memory And Performance Guardrails

In-memory keyword search can be expensive for a large corpus.

Add guardrails:

```yaml
rag:
  keyword_search:
    max_chunks_for_in_memory: 50000
```

Expected behavior:

- Lazy-build the keyword index on first keyword/hybrid search.
- Keep feature flags disabled by default.
- Warn clearly if the chunk count exceeds the configured in-memory limit.
- Include build latency and search latency in debug/trace metadata.

If the prototype is useful but memory-heavy, move to persistent SQLite FTS5 in a later milestone.

## Trace And Debugging

Add trace metadata:

```text
retriever = "vector" | "hybrid"
keyword_enabled
hybrid_enabled
merge_strategy
vector_top_k
keyword_top_k
merged_result_count
vector_result_count
keyword_result_count
content_quality_enabled
content_quality_mode
keyword_build_latency_ms
keyword_search_latency_ms
hybrid_merge_latency_ms
```

For each final context:

```text
vector_rank
keyword_rank
hybrid_rank
vector_score
keyword_score
hybrid_score
score_type
rank_sources
content_quality_penalty
```

Current traces already persist full context text. This milestone should avoid adding extra duplicate full-text logs. A later cleanup can add:

```text
trace_text_mode: full | snippet | metadata_only
```

## Reranker Compatibility

Hybrid retrieval should produce candidates that can be sent into the existing reranker.

Ideal long-term flow:

```text
vector top 50
keyword top 50
RRF merge top 30-50
rerank top 30-50
final context top 5-8
```

For this milestone:

- Do not change the reranker model.
- Do not make reranker run on every retry attempt.
- Preserve fields such as `vector_score`, `keyword_score`, `hybrid_score`, and `rank_sources` after reranking.

## Tests

Add focused tests for:

- Disabled behavior remains vector-only.
- Keyword search returns chunks containing exact terms.
- Acronym/model-name queries work.
- Exact phrase boost affects ranking.
- RRF merge dedupes duplicate chunks.
- Hybrid result shape remains compatible with RAG answer generation.
- Retry retrieve still increases candidate count in hybrid mode.
- Hybrid scores are not treated as vector similarity scores.
- Content-quality downrank lowers noisy chunks such as `Index` and `Table of Contents`.

Suggested files:

```text
tests/test_keyword_search.py
tests/test_hybrid_retriever.py
tests/test_retry_retrieve.py
tests/test_content_quality_filter.py
```

## Acceptance Criteria

Functional:

- With keyword/hybrid disabled, current vector-only behavior is unchanged.
- Keyword search can return exact-term results from existing chunks.
- Hybrid search merges vector and keyword results without duplicate chunks.
- Hybrid retrieval respects retry `top_k`.
- Hybrid result shape remains compatible with current RAG answer generation.
- Optional reranker still works after hybrid retrieval.

Quality:

- Exact acronym/model/function queries improve compared with vector-only baseline.
- Semantic queries do not obviously regress when hybrid is enabled.
- Noisy `Index`, `Contents`, `Praise`, and `References` chunks are downranked.
- Thai/English mixed queries still work at least as well as before for English technical terms.

Safety:

- No external API calls are introduced.
- No metadata SQL migration is introduced.
- No full-library re-chunking or re-embedding is required.
- No full chunk text is logged beyond the existing trace behavior.

Performance:

- Keyword index build behavior is explicit.
- Search latency is measured.
- Memory risk is guarded by configuration.

## Suggested File Changes

Likely files:

```text
library/keyword_search.py
library/hybrid_retriever.py
library/retrieval_quality.py
library/vector_store.py
evals/auto_retrieve.py
evals/trace.py
pages_ui.py
config.example.yaml
tests/test_keyword_search.py
tests/test_hybrid_retriever.py
tests/test_retry_retrieve.py
tests/test_content_quality_filter.py
```

Keep the first implementation narrow:

1. Add retrieval-time content-quality downrank.
2. Add keyword search class.
3. Add hybrid retriever with RRF.
4. Add config sections, disabled by default.
5. Integrate hybrid behind `rag.hybrid_search.enabled`.
6. Add trace metadata.
7. Add tests.

## Implementation Prompt

Use this prompt when assigning the implementation to a new agent:

```text
You are working in the summary project. Read docs/keyword_search_implementation_plan.md first and implement the revised keyword and hybrid retrieval milestone.

Goal:
Add optional local keyword search, hybrid retrieval, and retrieval-time noisy-content downranking alongside the existing vector search. The system should improve exact-term retrieval for acronyms, model names, function names, filenames, error messages, and short technical queries while preserving current vector-only behavior when disabled.

Important constraints:
- Do not re-chunk the existing library.
- Do not re-embed the existing library.
- Do not replace LanceDB.
- Do not change the LanceDB vector index format.
- Do not replace library/data/metadata.json.
- Do not migrate metadata to SQL.
- Do not implement persistent SQLite FTS5 in this milestone.
- Do not add pgvector, Qdrant, Elasticsearch, OpenSearch, or hosted search providers.
- Do not change existing retrieval gate thresholds. Keep min_similarity, min_top_similarity, and min_avg_similarity as configured.
- Do not compare keyword_score, hybrid_score, or rerank_score directly against min_top_similarity.
- Preserve current vector-only behavior when keyword_search.enabled and hybrid_search.enabled are false.

Expected workflow:
User query
 -> vector candidates from VectorStore.search()
 -> keyword candidates from KeywordSearch.search()
 -> merge and dedupe with Reciprocal Rank Fusion
 -> apply retrieval-time content-quality downrank for noisy chunks such as Index, Contents, Praise, Copyright, References, Bibliography
 -> return final hybrid candidates
 -> existing retrieval gate / retry / reranker / RAG answer flow

Implementation details:
1. Add config sections under rag.keyword_search, rag.hybrid_search, and rag.content_quality in config.example.yaml. Keep keyword and hybrid disabled by default.
2. Add library/retrieval_quality.py or similar for retrieval-time downranking. Start with downranking, not hard filtering.
3. Add library/keyword_search.py with a KeywordSearch class. Implement an in-process BM25-style or lexical baseline suitable for exact-term retrieval.
4. Prefer reading existing chunk records from the current LanceDB/vector store data so no PDF reprocessing or metadata migration is required.
5. Add library/hybrid_retriever.py with a HybridRetriever.search(query, top_k) method.
6. HybridRetriever must respect retry top_k. Treat top_k as the final merged candidate count. Use vector_top_k = max(config.vector_top_k, top_k * 2) and keyword_top_k = max(config.keyword_top_k, top_k * 2).
7. Merge vector and keyword candidates using Reciprocal Rank Fusion.
8. Preserve existing context fields and add non-breaking fields: score_type, vector_score, keyword_score, hybrid_score, vector_rank, keyword_rank, hybrid_rank, rank_sources, content_quality_penalty.
9. Keep score semantics explicit. Existing vector similarity must remain available as vector_score.
10. Integrate hybrid retrieval behind rag.hybrid_search.enabled without changing current behavior when disabled.
11. Preserve reranker compatibility and preserve hybrid metadata after reranking where possible.
12. Add trace/debug metadata for retriever type, result counts, top_k values, merge strategy, content-quality behavior, and latency.
13. Add focused tests for disabled behavior, exact keyword retrieval, RRF merge/dedupe, retry top_k compatibility, content-quality downrank, score semantics, and RAG result-shape compatibility.

Acceptance criteria:
- Existing vector-only retrieval works unchanged when keyword/hybrid are disabled.
- Keyword search can find chunks containing exact terms that vector search may miss.
- Hybrid search returns deduped merged results.
- Retry Retrieve still increases candidate count meaningfully in hybrid mode.
- Noisy chunks such as Index, Contents, Praise, Copyright, References, and Bibliography are downranked.
- Hybrid scores are not treated as vector similarity scores.
- Optional reranker still works after hybrid retrieval.
- No full-library re-chunking, re-embedding, SQL migration, persistent SQLite FTS5, pgvector, Qdrant, Elasticsearch, OpenSearch, or external hosted search is introduced.
```
