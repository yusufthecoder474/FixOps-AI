# Executed evidence — 2026-10-26

## Source inspection and preservation

Inspected all uploaded Python modules, Streamlit flow, configuration, privacy/history/answer logic, 22 authored runbooks, 28 evaluation questions, original tests and archived reports. Extracted the uploaded source; no repository was recreated. TF-IDF, MiniLM, the scope/score rejection policy, citations and Streamlit flow remain available. The original app, corpus, questions and existing test files are unchanged. Modified retrieval scoring and non-string validation; added benchmark/study tools, tests, documentation and new evidence. The original retrieval source is frozen byte-for-byte in `benchmarks/baseline_retrieval.py`.

## Commands and outcomes

Commands were executed from the extracted `fixops-ai` project except where noted. The final benchmark ran without concurrent tests/installations.

| Command/check | Actual outcome |
|---|---|
| `unzip -l upload/FixOps_AI.zip` | Input archive has 27 files; source and authored data present |
| Install pytest, dotenv, Streamlit, Sentence Transformers | Succeeded; initial unpinned install selected Sentence Transformers 6.2.0, outside the project range |
| `python -m pip install 'sentence-transformers==5.7.0' 'httpx[socks]>=0.27,<1'` | Succeeded; compatible ST version restored. Output in `reports/benchmark/dependency-install.txt` |
| First model import during dependency replacement | Failed with transient `ImportError: is_message_dict`; a fresh process after installation imported ST 5.7.0 and loaded real MiniLM successfully |
| Initial offline `python -m pytest -q` | 62 passed, 1 semantic integration skipped; output `reports/benchmark/pytest-initial.txt` |
| Pre-change cProfile over frozen TF-IDF search | 560 calls; cosine similarity ~45% of cumulative search time; `reports/benchmark/prechange-tfidf-profile.txt` |
| Preliminary TF-IDF paired benchmark, 30 repeats, 3 warmups | Succeeded; `reports/benchmark/raw.csv` and `summary.json`. This exploratory run is not pooled with final results |
| Initial full paired benchmark | Succeeded; `reports/paired-final/`. Exploratory only: model loading/tests overlapped parts of this session; final run replaces it for reported conclusions |
| `HF_HUB_OFFLINE=1 python -m benchmarks.run --backend both --repeats 30 --warmups 3 --output reports/final` | Exit 0; both real engines measured, 3,360 raw rows, no ranking or acceptance differences |
| `HF_HUB_OFFLINE=1 FIXOPS_TEST_SEMANTIC=1 python -m pytest -q` | Full output in `reports/pytest-current.txt`; all 65 tests passed, none skipped |
| `python -m compileall -q fixops benchmarks app.py evaluate.py` | Exit 0; output file `reports/compile-current.txt` is intentionally empty |
| `python -m benchmarks.audit reports/final` | Passed exact equality for every engine/variant metric; `reports/raw-audit.txt` |
| `python -m benchmarks.human summarize --assessed reports/human/assessed-template.csv` | Exit 0; status **unexecuted**, 0 participants, 0 observations |

A local edit command initially used the wrong relative path (`fixops-ai/benchmarks/human.py` while already inside that project). It raised FileNotFoundError, was corrected to `benchmarks/human.py`, and the corrected implementation was tested. No failed command was treated as evidence of success.

## Regression coverage

Original corpus/query retrieval, supported acceptance, unsupported rejection, empty/oversized input, citation validation, privacy/history, optional LLM error handling, configuration and Streamlit supported/unsupported interaction tests remain. New coverage verifies malformed non-string requests, normalized dot/cosine equivalence for sparse and dense paths, stable zero-vector ties, frozen expected step keys, counterbalanced assignments, rejection of unassessed/invalid human observations, failed-task accounting and correct metric denominators. The dense fixture is explicitly synthetic test data; real MiniLM is separately exercised by the original semantic integration test and the full final benchmark. Synthetic fixture timings are never written as human evidence.

## Interpretation and unexecuted work

- See `PERFORMANCE_EVALUATION.md` for final latency/recall/rejection values. MiniLM p95 increased in the final run; this regression is disclosed rather than discarded.
- 22 supported authored queries and six authored unsupported queries are not production validation. Scope rejection remains heuristic, including explicit phrase rules. New paraphrases, ambiguous incidents and adversarial unsupported queries require independent validation.
- No volunteers, live incidents, task-time observations or survey results were generated. Human allocation/capture/scoring tooling and protocol are delivered **unexecuted**. No real incident resolution effectiveness claim is supported.
- Current tests execute the Streamlit app via AppTest. Historical HTTP/health launch evidence stays historical; a new browser/health smoke run was not claimed.
- No live paid LLM/API call, production deployment or Windows/MSVC test was performed. Linux CPU measurements do not predict Windows performance. Model weights and environments are not bundled; the recorded snapshot and measured core versions support local reproduction.
