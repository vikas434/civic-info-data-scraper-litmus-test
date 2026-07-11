# US Civic Representative Validator

A benchmarking system that queries multiple LLMs to discover current US government representatives for a given ZIP code, then compares results against pre-filled ground truth.

## Language

**ZIP Group**:
All rows in the input workbook that share the same ZIP code, representing every role to be looked up for that jurisdiction.
_Avoid_: ZIP block, ZIP batch, ZIP set

**Role**:
A single government position to be looked up (e.g. Governor, US Senator, City Council Member). Defined per ZIP Group by whatever rows exist in the workbook — the workbook is the source of truth.
_Avoid_: Office, position, seat

**Ground Truth**:
The pre-filled MyCivX name and website columns in the workbook. These are never overwritten by the system.
_Avoid_: Reference data, source data, baseline

**LLM Run**:
A single execution of the benchmark for one model against one or more ZIP Groups. Results accumulate in the workbook across multiple runs.
_Avoid_: Benchmark run, model run, inference pass

**Match**:
A per-model, per-role verdict — true when the LLM's name and website fuzzy-match the Ground Truth after normalization. One match column per model.
_Avoid_: Accuracy, correctness, result

**Structural Anomaly**:
A ZIP Group whose role list is unexpected or inconsistent with similar ZIP Groups. Logged for human review; never auto-corrected.
_Avoid_: Malformed ZIP, bad data, schema mismatch

**Scorecard**:
The high-level summary report (summary.md) showing per-model accuracy %, average latency, and average estimated cost.
_Avoid_: Dashboard, report, leaderboard

**Web Search Capability**:
Whether a model has live web search access during inference. Flagged in benchmark reports; models without it still run but their results are marked accordingly.
_Avoid_: Grounding, search access, tool calling
