# FixOps AI — Final Evaluation Report

## Verified result

- Configuration uses per-instance environment defaults; API keys are excluded from dataclass representations.
- SOCKS dependency issue resolved; real all-MiniLM-L6-v2 model downloaded and evaluated.
- Full Pytest suite: **47 passed**, including the real semantic model test.
- Offline suite: **46 passed, 1 skipped** (semantic integration intentionally disabled).
- Streamlit launched on localhost; root page and health endpoint returned HTTP 200.
- Optional LLM path tested using mocked responses; no paid provider call was made.

## Retrieval measurements

| Engine | Recall@3 | Supported accepted | Unsupported rejected | Mean latency | p50 | p95 | Initialization |
|---|---:|---:|---:|---:|---:|---:|---:|
| tfidf | 100% (22/22) | 100% | 100% (6/6) | 0.35 ms | 0.35 ms | 0.42 ms | 47.96 ms |
| semantic | 100% (22/22) | 100% | 100% (6/6) | 10.55 ms | 8.81 ms | 21.12 ms | 38355.66 ms |

## Interpretation and limits

Macro Recall@3 over 22 supported questions; 6 unsupported excluded from recall. One warm timed request per question including query encoding, cosine ranking and scope check; no UI/LLM/network time. Startup measured separately. Authored smoke set, not an independent benchmark.

Initialization includes imports, model loading/download when needed, and corpus encoding. The semantic initialization in this run included first-use setup; it is not a steady-state request measurement. Exact per-question results, hashes and runtime metadata are in evaluation.json. Runtime clock timestamps are preserved as reported by the execution environment.

The evaluation contains 22 supported questions (one per runbook) and 6 unsupported questions. Every supported question has one expected source. Both methods achieved the same top-three recall on this small authored set; these results do not establish semantic superiority. The scope rules know some unsupported categories, so the rejection score is a regression check rather than an independent generalization estimate.

No retrieval result confirms a root cause or a successful fix. Similarity scores are not calibrated probabilities. Operational data, organization-specific procedures, independent paraphrases and broader unsupported questions are needed before deployment beyond a local demo.

## Reproduce

```bash
python -m pip install -r requirements.txt
python evaluate.py --backend both
```

Then enable `FIXOPS_TEST_SEMANTIC=1` in your shell and run `python -m pytest -q`. See the README for Windows syntax. The model must be downloaded once or supplied as a local directory.

## Evidence files

- `evaluation.json`: complete measured comparison and question-level results.
- `pytest-full.txt`: 47 passing tests with semantic integration enabled.
- `pytest-offline.txt`: offline-only test results.
- `launch-check.json`: real HTTP health and root-page checks.
- `streamlit-launch.log`: process launch and controlled shutdown.
- `environment.json`: exact package versions; `../requirements-tested.txt` provides corresponding pins.
