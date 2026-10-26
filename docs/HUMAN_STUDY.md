# Mode B: human task-completion protocol — UNEXECUTED

No volunteers were recruited and no participant data was collected in this implementation. `reports/human/assessed-template.csv` has a header only. Example IDs in commands are placeholders, not participants. Automated benchmark repetitions are not human observations.

## Question and scope

Does FixOps help people locate the correct authored runbook and identify its three expected investigation steps faster, with fewer errors, than manual search? This tests information lookup and comprehension, not successful resolution of a live incident. All 22 supported scenarios, expected source IDs and verbatim steps are frozen in `benchmarks/tasks.json`. These are educational runbooks, not production incident records. Unsupported queries are evaluated in Mode A and excluded from timed human tasks.

## Before recruitment and collection

1. Recruit consenting adult volunteers familiar with basic IT troubleshooting. Aim for complete blocks of four; record actual recruitment, experience band, withdrawals and exclusions separately, using anonymized IDs only. Participation is voluntary, with withdrawal allowed. Do not store names, credentials or private incident data.
2. Pre-register participant count, timeout (300 seconds/task), primary measure (participant-level difference of median successful completion times), quality measures and exclusions. Preserve a dated copy before opening data. Report small samples descriptively; do not claim statistical significance without a suitable participant-level analysis.
3. Use identical laptop/browser, corpus, display and environment. Manual condition: local `RUNBOOKS.md`, normal browser/editor Find and scrolling, with all runbooks accessible. No internet, AI assistant, shell search or source answer keys. Assisted condition: Streamlit, **TF-IDF**, optional LLM off, history off, initialized with a practice task. No manual document search. Freeze the backend, thresholds, app version and device for all sessions. A later semantic study is a separate study.
4. Practice both interfaces on the same facilitator-created practice scenario excluded from the 22 scored queries. Explain how to enter the selected source ID and describe the three investigation steps. Give no feedback on scored tasks. Permit breaks; log interruptions, device problems and deviations.

## Assignment and counterbalancing

From project root:

```powershell
python -m benchmarks.human plan --participants P01 P02 P03 P04
python -m streamlit run app.py
python -m benchmarks.human record --participant P01
```

Replace placeholder IDs with actual consenting volunteers. `assignments.json` is an allocation plan, not execution evidence. The fixed seeded task permutation assigns 11 manual and 11 assisted tasks per person, without repeating any task for that person. Adjacent participants receive complementary conditions; the next pair reverses task order. Over four participants, each task appears twice per condition, early and late, and each condition starts equally often. Partial blocks weaken balance and must be disclosed. Schedule tasks before collection; do not change assignment in response to performance. Shared vocabulary and transfer between related scenarios remain limitations.

## Timing and observations

The CLI reveals only the task query, starts `perf_counter`, and records a participant's Enter press when they locate their selected runbook. This is **self-reported location time**, even if the chosen source later proves wrong. Total elapsed time ends after they enter the selected ID and a description of all three steps. It includes reading, searching, thinking and answer-entry time. A facilitator should supervise the 300-second limit; the terminal cannot interrupt an input prompt automatically. Ask the participant to stop at timeout, enter their partial answer and continue. Actual overruns are retained, flagged and excluded from successful timing summaries, not hidden or silently capped.

Record disturbances separately; keep all raw rows. Resume skips previously recorded participant/task pairs. Back up `raw.csv` before any scoring. Do not access `tasks.json` or expected source labels while the participant performs a task. Do not execute runbook commands against real infrastructure.

## Blinded assessment

Copy raw observations to `assessed.csv`. Give an assessor the task, chosen source and submitted steps, but conceal condition, order, times and participant identity while scoring. Use the frozen key: correct expected source ID plus all three required steps, with faithful paraphrases accepted and no materially incorrect additional action. Record `success` as 1 only if all requirements are met and the task did not time out. Record `errors` as number of missing/incorrect required steps, plus one if the source is wrong, plus one per materially incorrect extra action. Record a pseudonymous assessor ID in `assessor`; document adjudication of ambiguous paraphrases before revealing condition. Machine timings alone cannot establish success. This CLI deliberately does not auto-grade text.

```powershell
python -m benchmarks.human summarize --assessed reports/human/assessed.csv
```

The summarizer rejects missing assessment, duplicate participant/task rows, non-finite or negative timings, invalid condition labels and successful timeouts. It produces success rates, errors, timeouts, successful-only location/completion medians, and participant paired medians. Include unsuccessful/withdrawn/excluded counts, actual participants, task counts, missingness and protocol deviations in any report. Validate assessed rows against the allocation plan before analysis. Do not substitute repeated task observations for independent participants. Withhold a resume task-time reduction bullet until genuine evidence supports it; always pair faster successful times with completion quality.
