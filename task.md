# Build Order

## Phase 1
- Initialize uv project
- Create folder structure
- Configure linting and testing
- Verify project runs

## Phase 2
- Create Pydantic models
- Create configuration loader
- Add .env support

## Phase 3
- Build Excel reader/writer
- Preserve workbook formatting
- Group rows by ZIP

## Phase 4
- Build PydanticAI agent
- Integrate OpenRouter
- Add configurable model selection
- Load prompts from markdown

## Phase 5
- Implement structured output validation
- Retry on validation failures
- Add logging

## Phase 6
- Add benchmark metrics
- Measure latency
- Record token usage
- Estimate request cost

## Phase 7
- Add concurrent ZIP processing
- Resume failed ZIPs
- Export benchmark reports

Definition of Done:
- Running `uv run app` processes an input workbook end-to-end, fills representative data, preserves formatting, and generates benchmark reports without manual intervention.
