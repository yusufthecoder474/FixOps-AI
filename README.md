# FixOps AI — Intelligent IT Incident Troubleshooting Assistant

A runnable 12-hour-scope Python/Streamlit MVP for finding relevant IT investigation procedures. It retrieves three runbooks using **all-MiniLM-L6-v2 embeddings + normalized-vector cosine ranking**, compares retrieval with **TF-IDF**, and optionally uses a chat-completions LLM to select a concise, cited sequence of existing steps.

## Reproducible performance evaluation (2026-10-26)

This update adds a frozen, paired benchmark of the original and optimized retrieval implementations. See [PERFORMANCE_EVALUATION.md](docs/PERFORMANCE_EVALUATION.md) for current measured results, [EVIDENCE.md](docs/EVIDENCE.md) for executed checks, and [the human-study protocol](docs/HUMAN_STUDY.md) for the **unexecuted** volunteer study. Raw measurements and profiles are in `reports/final/`.

Both retrieval engines, unsupported-query rejection, private history, optional cited LLM extraction and the Streamlit interface are preserved. The scoring optimization uses dot products of already-normalized vectors, which compute cosine similarity without repeatedly normalizing the corpus. No answer/result caching or label/threshold tuning was introduced.

The supplied older `reports/FINAL_EVALUATION.md`, `reports/evaluation.json`, launch checks and original test reports are **historical evidence from the input ZIP**, not new measurements. Small authored-set recall is not production accuracy. Retrieval milliseconds are not human troubleshooting time.

## Quick start (Windows PowerShell)

Use Python 3.11 or 3.12. Extract the ZIP, open its `fixops-ai` folder in VS Code and open a terminal there.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Open http://localhost:8501. No API key is required. Choose **semantic**, then enter: `Our checkout returns HTTP 500 after a deployment.` The first semantic request downloads the public model from Hugging Face; later requests use its local cache. Allow a few minutes and several hundred MB of dependencies/model storage. If downloads are unavailable, explicitly select **tfidf** in the sidebar: it works offline immediately after dependency installation. A semantic error never silently changes the retrieval engine.

Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

For the remaining commands, use the virtual environment's Python or activate it first. `requirements.txt` specifies compatible ranges; `requirements-tested.txt` pins the direct and major ML dependencies used in verification; `reports/environment.json` records the concrete versions tested here. This is not a fully hashed cross-platform lockfile.

## What is included

| File | Responsibility |
|---|---|
| `app.py` | Streamlit form, source panels, timings and local history |
| `fixops/config.py` | Environment-based configuration |
| `fixops/knowledge.py` | Runbook loading and document text |
| `fixops/retrieval.py` | Semantic and TF-IDF ranking, top 3 and abstention |
| `fixops/answer.py` | Local answer and validated LLM step selection |
| `fixops/privacy.py` | Fixed-vocabulary history projection and best-effort input redaction |
| `fixops/history.py` | SQLite history with 100-row retention |
| `data/runbooks.json` | 22 authored troubleshooting scenarios with stable IDs |
| `data/evaluation.json` | 22 supported and 6 unsupported questions with expected IDs |
| `RUNBOOKS.md` | Human-readable version of the same dataset |
| `evaluate.py` | Recall@3, acceptance/rejection and latency comparison |
| `tests/test_fixops.py` | Retrieval, privacy, citations, errors and optional real-model tests |
| `tests/test_app.py` | Streamlit supported/unsupported user flows |
| `reports/` | Actual measurements and verification notes |
| `.env.example` | Configuration example; copy to `.env` if needed |

## Request flow

1. A user submits a natural-language incident description (maximum 3,000 characters).
2. Best-effort redaction removes obvious credentials before local retrieval. Do not paste secrets; redaction does not recognize every possible secret format.
3. The cached engine encodes the question and ranks all runbooks with cosine similarity. Runbook embeddings are built once per engine configuration per Streamlit process.
4. The system retrieves exactly three entries. A score threshold plus conservative domain/scope rules decide whether it can offer an answer. Scores are **not probabilities**; this is not a root-cause detector.
5. With insufficient information, it explicitly abstains. Nearest matches remain visible but are labelled insufficient evidence.
6. Otherwise, local mode returns the first runbook's three cited investigation steps. All three candidates remain available for human inspection.
7. Optional LLM mode selects and orders at most five existing steps from the retrieved documents. The application validates each ID and step index and copies the original text. It never displays arbitrary generated prose or new commands.
8. Local history stores timestamp, a **lossy category-only summary of the query**, engine, source IDs and acceptance status. Raw text is never persisted by application code.

The LLM is intentionally an **extractive planner**, not an unrestricted chatbot. This keeps every displayed recommendation traceable. It may select a less relevant existing step, so human judgment remains necessary.

## Optional LLM

Copy `.env.example` to `.env`, then set:

```dotenv
FIXOPS_LLM_API_KEY=your-provider-key
FIXOPS_LLM_URL=https://your-provider.example/v1/chat/completions
FIXOPS_LLM_MODEL=your-provider-model-id
```

Use an actual OpenAI-compatible chat-completions provider endpoint and supported model ID. The default URL in `.env.example` is the OpenAI chat-completions endpoint; set the model explicitly. Restart Streamlit after changing environment configuration. The API key stays server-side. Requests use HTTPS, disable redirects, have a 20-second timeout and limit response size. No tools or function calling are enabled. Network failures, malformed JSON or invalid citations fall back to local procedures.

Only recognized incident categories and the three retrieved authored runbooks go to the provider, **not raw user text**. This deliberately sacrifices some context. API usage may incur provider charges. No live provider call is required for the demo or tests.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `FIXOPS_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Model ID or local saved model directory |
| `FIXOPS_SEMANTIC_THRESHOLD` | `0.38` | Minimum top semantic cosine score |
| `FIXOPS_TFIDF_THRESHOLD` | `0.12` | Minimum top TF-IDF cosine score |
| `FIXOPS_HISTORY_PATH` | `<project>/var/history.sqlite3` | Local history location |
| `FIXOPS_LLM_API_KEY` | empty | Enables optional provider mode |
| `FIXOPS_LLM_URL` | OpenAI chat-completions HTTPS URL | Compatible endpoint |
| `FIXOPS_LLM_MODEL` | empty | Explicit provider model ID |

Thresholds are MVP heuristics, **not calibrated confidence cutoffs**. Scope checks deliberately reject obvious off-topic requests and unsupported password-reset/backup-restore requests. They may reject useful paraphrases and may miss other unsupported requests. Evaluate independently before expanding the domain; do not treat the included acceptance scores as proof of universal reliability.

## Tests and evaluation

```bash
python -m pytest -q
python evaluate.py --backend both
```

Run the actual semantic integration test after the model is available:

```powershell
$env:FIXOPS_TEST_SEMANTIC="1"
python -m pytest -q
```

Linux/macOS: `FIXOPS_TEST_SEMANTIC=1 python -m pytest -q`.

The ordinary test suite avoids model downloads and uses real TF-IDF retrieval. The semantic-marked test loads the real model; it does not substitute fake vectors. LLM tests mock network responses to verify validation and privacy. `evaluate.py` runs the actual selected engines, writes `reports/evaluation.json`, and exits with status 2 if either selected engine is unavailable. A failed engine has no invented score. For offline-only measurement use `--backend tfidf --output reports/tfidf.json`.

**Recall@3** is the mean, over supported questions, of `number of expected source IDs retrieved / number of expected source IDs`. The current dataset has one expected source per supported question. Unsupported examples have empty expected sets and are excluded from Recall@3; their rejection rate is reported separately. Supported acceptance rate detects cases where retrieval ranks the right source but abstains.

The legacy `evaluate.py` records one warm retrieval measurement per question, including query embedding/vectorization, cosine comparison, ranking and scope checks. Initialization/model loading is separate. The UI also reports total request time including initialization and optional LLM calls. These timings are environment-specific; they are not an SLA. The authored questions are close to the runbooks and share scope assumptions with the rules. They are a **smoke evaluation**, not an independent holdout or a claim that semantic retrieval is superior.

## Knowledge-base provenance

The 22 procedures are original educational examples, not customer incident records, tested fixes or vendor-certified instructions. Each has a stable ID, symptoms, three read-only investigation steps, evidence to gather, escalation guidance and a real background reference. References supply domain background and do not imply that the entire authored procedure is quoted from that page. No incident outcomes, customer metrics or historical resolution claims are invented.

Covered topics: HTTP 500, CPU, SQL timeout, memory/OOM, DNS, API latency, 503, 502, 504, disk space, TLS, 401, 403, 429, crash loops, image pulls, readiness, connection pools, database locks, refused connections, packet loss and storage mounts.

## Operational boundaries

- Read-only with respect to infrastructure: no SSH, command execution, credential collection, probes, deployments, process termination or automated remediation. Local history/model-cache files are expected local writes.
- The application does not connect to the user's infrastructure. Runbook steps describe observations for an authorized engineer to perform using existing tools.
- A known-vocabulary projection is used instead of attempting to safely preserve arbitrary raw queries. There is no raw-query hash, log or export. Unknown text is discarded from persistent history.
- Run locally as a single user. The SQLite history is shared by all sessions of one process; this MVP has no authentication or per-user isolation. Bind to localhost as shown. Public hosting requires separate authentication, isolation and operational review.
- Disable the history checkbox to stop adding entries. To erase prior local history, stop the app and delete `var/history.sqlite3` (or the configured file).
- Keep `.env` out of version control. The included archive contains no API keys, model binaries or user history.

## Troubleshooting setup

- Model download blocked: use TF-IDF, or download the specified model on an approved network and set `FIXOPS_MODEL` to its local directory.
- SOCKS proxy support is included in requirements. If using an older environment with an import error, install `python -m pip install 'httpx[socks]'` in your environment. This is needed only for environments using a SOCKS proxy.
- Dependency trouble: use a fresh Python 3.11/3.12 virtual environment. Avoid mixing global PyTorch/Transformers installations.
- Missing optional LLM answer: verify the key, HTTPS URL and model; local cited steps remain available even when the provider fails.

## Suggested 12-hour implementation/demo budget

| Hours | Work |
|---|---|
| 0–2 | Runbooks, expected-source evaluation questions and source review |
| 2–4 | Semantic retrieval, TF-IDF baseline and scope handling |
| 4–6 | Streamlit source panels, scores, timing and history |
| 6–8 | Optional extractive LLM path and validation |
| 8–10 | Retrieval/privacy/UI tests and measurement |
| 10–12 | README, demo rehearsal and interview explanation |

This package implements that scope. Useful next steps are independent paraphrase evaluation, better abstention calibration and organization-approved runbooks—not autonomous remediation.

## Benchmark commands (project root, PowerShell)

```powershell
.\.venv\Scripts\python.exe -m benchmarks.run --backend both --warmups 3 --repeats 30 --output reports/my-benchmark
.\.venv\Scripts\python.exe -m benchmarks.run --backend tfidf --warmups 3 --repeats 30 --output reports/my-tfidf
$env:FIXOPS_TEST_SEMANTIC = "1"
.\.venv\Scripts\python.exe -m pytest -q
```

The first semantic use downloads MiniLM; no paid API or token is required. Use `requirements-tested.txt` for the direct dependency versions measured in this update; it is not a complete lockfile. Model weights are not bundled. `summary.json` records the actual model snapshot revision and artifact hashes, runtime versions, hardware limits and thresholds. Preserve the snapshot to reproduce the exact weights; a different upstream snapshot requires disclosure. Once cached, set `$env:HF_HUB_OFFLINE = "1"` to remove model network access during evaluation.

`benchmarks/freeze.json` verifies hashes of the original retrieval module, corpus, questions and task answer keys. Changes to those inputs stop the runner. Treat future tasks/corpus changes as a separately versioned benchmark, not an improvement on this frozen set. `raw.csv` contains one row per engine, variant, query and repeat, including ranking, scores, acceptance and external/internal latency. Startup is recorded separately. Exit 2 means an unavailable engine or benchmark failure; exit 3 means a ranking/acceptance difference requiring review. Do not interpret partial results as success.

The baseline module is an exact archived copy of the uploaded retrieval implementation. Both variants share the same fitted encoder and corpus matrix to hold those factors constant; paired calls randomize variant order and query order, without caching outputs. Three full warm-up passes precede 30 timed passes. Profiles run separately after measurements. Request latency excludes startup, Streamlit, optional LLM, history and human activity. Repeated queries increase timing precision, not evaluation sample size.

Mode B uses `python -m benchmarks.human plan`, `record` and `summarize`; follow the protocol before recruitment. The header-only assessment template and status file in `reports/human/` are intentionally **not study results**. The original `evaluate.py` remains available as a simpler smoke evaluation; use the new runner for before/after claims.

Audit saved data without downloading/loading the model: `python -m benchmarks.audit reports/final`.
