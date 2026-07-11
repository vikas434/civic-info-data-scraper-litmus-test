# CLAUDE.md

You are the lead software engineer for this project.

Your goal is to build a production-quality application.

Do NOT generate placeholder implementations.

Do NOT generate TODO comments.

Do NOT stub functionality.

Every feature should be fully implemented.

---

Project Goal

Build a configurable benchmarking system for evaluating LLMs on US civic representative discovery.

The application should:

- Read Excel
- Group rows by ZIP code
- Ask one LLM call per ZIP
- Return structured results
- Validate responses
- Fill Excel
- Measure latency
- Measure cost
- Compare models

---

Technology Stack

Python 3.12

uv

PydanticAI

OpenRouter

OpenPyXL

Pandas

Typer

Rich

Structlog

Pytest

Pydantic v2

---

Agent

Use one PydanticAI agent.

The model should come from configuration.

The prompt should come from a markdown file.

---

Model Switching

Changing

google/gemini-2.5-pro

to

anthropic/claude-sonnet-4

should require changing only one config value.

No code changes.

---

Structured Output

Never return dictionaries.

Always return Pydantic models.

---

Excel

The workbook is the source of truth.

Update cells only.

Do not destroy formatting.

---

Performance

Minimize API calls.

One ZIP = One LLM call.

Never one role per request.

---

Prompt

The prompt should instruct the LLM to

- always use web search
- never answer from memory
- prefer official government websites
- return confidence
- return sources
- return official website

---

Reliability

Automatically retry malformed responses.

Retry validation failures.

Retry rate limits.

Retry network errors.

---

Cost

Record

Prompt tokens

Completion tokens

Estimated cost

Latency

for every request.

---

Reports

Produce

benchmark.csv

benchmark.xlsx

summary.md

after execution.

---

Coding Philosophy

Readable code over clever code.

Explicit over implicit.

Simple over complex.

Strong typing everywhere.

No premature optimization.

Avoid unnecessary abstractions.

Follow SOLID where practical.

---

When implementing, complete one module at a time.

After each module:

- ensure it runs
- ensure it is tested
- then move to the next module.

Do not skip modules.

Do not assume unfinished work is acceptable.
