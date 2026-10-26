# FixOps AI performance evaluation — 2026-10-26

## Outcome and limits

TF-IDF median warm retrieval latency decreased **37.8%**, from **0.383 ms** to **0.238 ms**. Both engines maintained Recall@1 and Recall@3 of 22/22 and unsupported-query rejection of 6/6 on the **same small authored set**. No top-three source ordering or supported/unsupported decisions changed across the paired measurements. This does not establish production accuracy or faster human troubleshooting.

MiniLM median improved 3.1% (14.717 → 14.268 ms), but **p95 regressed 1.9%** (37.250 → 37.972 ms). The small semantic median difference and variable tail are descriptive measurements, not evidence of a reliable general semantic speedup. Query encoding remains its dominant cost. No retrieval-quality regression was observed on this set.

**Human study: unexecuted; 0 volunteers, 0 measured human tasks.** No end-to-end human time reduction is claimed.

## Mode A results

| Engine | Implementation | Mean ms | Median ms | p95 ms | Recall@1 | Recall@3 | Unsupported rejection |
|---|---|---:|---:|---:|---:|---:|---:|
| tfidf | baseline | 0.422 | 0.383 | 0.620 | 100% | 100% | 100% |
| tfidf | optimized | 0.269 | 0.238 | 0.407 | 100% | 100% | 100% |
| semantic | baseline | 18.703 | 14.717 | 37.250 | 100% | 100% | 100% |
| semantic | optimized | 17.753 | 14.268 | 37.972 | 100% | 100% | 100% |

Supported-query acceptance is 22/22 for all four combinations. Recall is macro-averaged over the 22 supported queries only; the six unsupported queries are excluded from recall. With one expected runbook per query, recall equals hit rate. Latencies pool all 28 supported/unsupported queries with equal repetition. Each implementation/engine has 840 observations: 28 unique queries × 30 repetitions. There are **28 distinct evaluation queries, not 840 independent tasks**.

## Frozen input and baseline

The source is the uploaded `FixOps_AI.zip`; no project recreation. `benchmarks/baseline_retrieval.py` is a byte-for-byte copy of its original `fixops/retrieval.py`. `benchmarks/freeze.json` stores hashes of this module, original corpus, original queries and enriched task key, all frozen before the optimization. The runner fails on a hash mismatch.

`benchmarks/tasks.json` includes all existing supported scenarios, their expected runbook IDs, and verbatim expected procedures, plus the six unsupported scenarios. Coverage spans HTTP errors, CPU, SQL timeouts, OOM, DNS, latency, disk, TLS/auth, Kubernetes, database pools/locks and network/storage failures. Human success requires identifying the correct source and its three investigation steps. These are investigator-authored educational scenarios, not real incident resolution outcomes or a held-out test set. No query, label, threshold or scope rule was tuned during this work.

## Measurement method

Command from project root:

```bash
HF_HUB_OFFLINE=1 python -m benchmarks.run --backend both --repeats 30 --warmups 3 --output reports/final
```

Each engine is constructed once. The baseline and candidate share the same fitted encoder and corpus matrix; scoring/search code differs. Both variants receive three full warm-up passes. A fixed random seed (20261026) shuffles task order per repetition and variant order within each pair. There is no result cache and no batch query acceleration. All queries are encoded on every call. The reported latency uses external `perf_counter` around `search`, including input validation, redaction, vectorization/embedding, similarity, stable top-three ranking and scope checks. Internal latency is also retained in CSV. cProfile runs after timing and does not contaminate the timed sample. Model download and initialization are excluded; initialization is recorded separately.

This compares warm lookup implementations under paired conditions in one process. It excludes Streamlit rendering, optional LLM, history, model download and all human activity. p95 uses NumPy's linear percentile interpolation. No inference, confidence interval or population significance is claimed. Shared host load, thermal effects, nine Torch threads under an eight-CPU quota, and pooling query difficulties limit precision and portability. Independent fresh-process replicates are needed before claiming a durable latency target. Earlier exploratory runs are retained but are not pooled into these final results.

## Environment

- Python 3.12.14; Linux-6.18.55-x86_64-with-glibc2.39.
- CPU: AMD EPYC 9V74 80-Core Processor; runtime exposes 9 logical CPUs; cgroup quota `800000 100000` (8 CPU equivalents).
- Memory limit: 8 GiB. Corpus: 22 runbooks. MiniLM ran on CPU with 9 Torch threads.
- Model: `sentence-transformers/all-MiniLM-L6-v2`; snapshot `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Actual model/config/tokenizer hashes are recorded in `summary.json`.
- Thresholds: TF-IDF 0.12; semantic 0.38. Original scope rules unchanged.
- Versions: numpy 2.3.5, scipy 1.17.0, scikit-learn 1.8.0, sentence-transformers 5.7.0, torch 2.14.1, transformers 5.20.2, streamlit 1.66.1.

## Profile and optimization

Before changing source, cProfile measured 560 TF-IDF lookups: 0.582 s cumulative search, including 0.261 s cosine similarity (~45%). See `reports/benchmark/prechange-tfidf-profile.txt`. Calls are nested, so cumulative percentages must not be summed as disjoint time components. That profile identified a substantial avoidable scoring cost: `cosine_similarity` validates, copies and normalizes vectors on every request, including the unchanged corpus. TF-IDF's default L2 normalization and MiniLM's `normalize_embeddings=True` already supply unit vectors. Their dot product equals cosine similarity; zero TF-IDF vectors remain zero. The candidate uses `safe_sparse_dot(vector, matrix.T, dense_output=True)`, retaining the stable full-sort top-three behavior, thresholds and scope gate. No batching, caching or task-specific shortcut was added.

Final before/after `.prof` files and readable cumulative profiles are in `reports/final/`. TF-IDF vectorization is the remaining major cost; MiniLM encoding dominates semantic requests. The patch also turns non-string incident descriptions into a clear ValueError. It does not alter the Streamlit workflow.

## Mode B and resume wording

See `docs/HUMAN_STUDY.md`. The tools generate a four-sequence counterbalanced allocation, collect genuine per-task times and answers, and summarize assessor-scored observations. Each volunteer sees every scored task once, under only one condition. Opposite participants receive complementary conditions; subsequent pairs reverse task order. The manual baseline is local runbook browsing/Find. The assisted condition fixes TF-IDF with the optional LLM disabled. A missing or blank study stays unexecuted. The header-only CSV template is not data.

Supported resume bullet:

> Reduced median TF-IDF retrieval latency from 0.383 ms to 0.238 ms (37.8%) while maintaining 100% Recall@3 on 22 authored evaluation queries across 22 runbooks, using a paired warm-lookup benchmark.

Do not use a human troubleshooting-time reduction bullet. Do not describe the authored-set recall as production accuracy.

## Evidence files

- `reports/final/raw.csv`: 3,360 actual timed lookup observations, with source IDs, similarity scores, decisions and pair order.
- `reports/final/summary.json`: metrics, input/source hashes, model identity and environment.
- `reports/final-command-output.txt`: actual runner output; exit 0.
- `reports/raw-audit.txt`: exact independent recomputation of summary values from raw CSV.
- `reports/pytest-current.txt`: current full test output, including real MiniLM and Streamlit interaction tests.
- `docs/EVIDENCE.md`: commands, outcomes and limitations.
