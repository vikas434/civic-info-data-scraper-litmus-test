# Each LLM Run targets one model and accumulates results into the workbook

Rather than running all models in a single execution, the CLI accepts a `--model` flag and fills only that model's columns. Results persist in the workbook across runs. This allows the operator to verify one ZIP manually after a single-model run before scaling to all ZIPs or adding more models. Sequential execution is the default; concurrency is opt-in via `--workers`.
