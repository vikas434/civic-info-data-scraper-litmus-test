# US Civic Representative Validator

> An LLM-powered benchmarking tool to automatically discover and validate US civic representatives across all government levels by ZIP code.

## Overview

The **US Civic Representative Validator** takes an input spreadsheet containing US ZIP codes and targeted civic roles (e.g., President, Governor, Mayor, City Council Member). It uses a PydanticAI-based agent with OpenRouter to query state-of-the-art LLMs (like Google Gemini and Anthropic Claude), prompting them to use native web search to discover the current officeholder's official name and website.

The primary goal of this repository is to **benchmark different LLMs** on their accuracy, latency, and cost for discovering civic data, and to ultimately serve as the automated data population engine for civic directories.

## Features

- **Automated Data Discovery:** Finds representatives from the Federal level down to local Municipalities and Districts using web-grounded LLM searches.
- **Configurable LLM Benchmarking:** Easily swap between models (Gemini 2.5, GPT-4o, Claude 3.5 Sonnet, etc.) via OpenRouter to compare performance.
- **Structured Validation:** Uses Pydantic to ensure the LLM output is strictly typed, handling missing data gracefully and standardizing names and URLs.
- **Excel Native:** Reads from and writes directly to `.xlsx` files while preserving original formatting, making it seamless for non-technical users.
- **Robust Analytics:** Captures latency, prompt/completion token usage, estimated costs, and confidence metrics for every single query.

## Project Structure

```
├── app/                  # Core application logic (agent, matcher, runner, validator)
├── config/               # System configurations and LLM prompts
├── docs/                 # Architecture Decision Records (ADRs) and domain terminology
├── input/                # Source Excel workbooks with ZIPs and roles
├── output/               # Processed Excel workbooks with populated data
├── reports/              # Analytics and benchmarking reports (CSV/HTML)
└── tests/                # Pytest suite
```

## Getting Started

This project uses `uv` for fast dependency management.

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure environment:**
   Copy `.env.example` to `.env` and add your OpenRouter API key.
   ```bash
   cp .env.example .env
   ```

3. **Run the pipeline:**
   *(Execution instructions to be documented based on CLI entrypoint)*

## Built With
- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- [PydanticAI](https://pydantic.dev)
- [OpenRouter](https://openrouter.ai)
- [OpenPyXL](https://openpyxl.readthedocs.io/en/stable/)
