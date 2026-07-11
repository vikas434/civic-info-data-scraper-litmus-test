# Project Overview

## Project Name

US Civic Representative Validator

## Goal

Build a Python application that automatically discovers the current US government representatives for a given ZIP code using multiple LLMs.

The system should use each LLM's native web search capability and compare results across models.

The primary source of truth is Google AI Mode (Gemini with Google Search Grounding).

Initially the application will benchmark multiple models.

Later one model will be selected to process all ZIP codes.

---

## Business Goal

Given an Excel sheet like

ZIP
Government Level
Branch
Role

Automatically populate

Official Name
Official Website

for every role.

The application must work for

Federal

State

County

City

Municipality

District

---

## Example

Input

ZIP: 10019

Role:

President

Vice President

Governor

Mayor

US Senator

US Representative

State Senator

City Council Member

...

Output

Official Name

Official Website

Confidence

Sources

Latency

Cost

---

## Requirements

The solution must

- use Python
- use PydanticAI
- use OpenRouter
- allow changing models from config
- use native web search/tool calling whenever supported by the model
- validate structured responses using Pydantic
- process one ZIP code at a time
- process all requested roles for a ZIP in a single LLM call
- write results back into Excel
- support benchmarking multiple models
- collect latency
- collect token usage
- estimate API cost
- retry invalid responses
- produce deterministic results

---

## Models

Initially benchmark

google/gemini-2.5-pro

google/gemini-2.5-flash

openai/gpt-5

openai/gpt-5-mini

anthropic/claude-sonnet-4

anthropic/claude-haiku-4

Model selection must be configurable.

---

## Input Excel

Columns

ZIP

Government Level

Branch

Role

Official Name

Official Website

---

The first version should preserve all formatting.

---

## Output

Fill

Official Name

Official Website

Confidence

Sources

Model Used

Latency

Estimated Cost

---

## Architecture

Excel Reader

↓

Group by ZIP

↓

PydanticAI Agent

↓

OpenRouter

↓

Native Web Search

↓

Structured Response

↓

Validation

↓

Excel Writer

↓

Benchmark Report

---

## Design Principles

Simple

Strong typing

Configurable

Minimal abstraction

Easy to debug

Easy to add models

No hardcoded prompts

No hardcoded API keys

No hardcoded model names

Everything configurable.

---

Future Goals

Parallel execution

Resume failed ZIP codes

Caching

Cost dashboard

Accuracy dashboard

HTML report


# Coding Instructions

Always prefer simplicity.

Never over-engineer.

---

## Package Manager

Use uv.

Do not use Poetry.

---

## Python Version

3.12+

---

## Code Style

PEP8

Type hints everywhere

No Any unless absolutely necessary

Use dataclasses only when appropriate.

Prefer Pydantic models.

---

## Architecture

Small modules.

Maximum file size around 300 lines.

Avoid giant files.

---

## Logging

Use structlog.

Every major action should be logged.

---

## Configuration

Everything configurable.

Never hardcode

models

prompts

paths

API keys

timeouts

retries

---

## Error Handling

Never crash.

Retry transient failures.

Log failures.

Continue processing remaining ZIP codes.

---

## PydanticAI

Always return structured models.

Never parse JSON manually.

---

## Excel

Use openpyxl.

Preserve formatting.

Do not recreate sheets.

Update cells only.

---

## Performance

Group rows by ZIP.

Never send one request per role.

Send one request per ZIP.

Return all roles together.

---

## Concurrency

Use asyncio.

Concurrency configurable.

Default = 5 workers.

---

## Benchmarking

Capture

Model

Latency

Input Tokens

Output Tokens

Estimated Cost

Validation Errors

Retry Count

---

## Testing

Every module should have tests.

Use pytest.

---

## Folder Structure

app/

config/

tests/

input/

output/

reports/

---

## Documentation

Every public function

Google style docstring.

---

## Prompt Files

Prompts should live inside

config/prompts/

Never embed long prompts in Python.

---

## Secrets

Read

OPENROUTER_API_KEY

from .env

Never hardcode.
