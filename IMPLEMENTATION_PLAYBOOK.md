# Implementation Playbook

This file is the working instruction for how we continue building this product.
Use it as the default execution guide for every next task.

## Product Mission

Build a production-style B2B AI Knowledge Platform that:

1. Ingests internal documents
2. Indexes chunks + vectors
3. Answers questions with grounded evidence
4. Tracks quality with internal evaluation and metrics

## Current Baseline (Already Implemented)

- Document upload, parsing, chunking
- Vector indexing into Qdrant
- Retrieval + reranking (`POST /search`)
- Grounded single-turn ask with citations (`POST /ask`)
- Evaluation layer:
  - ask run persistence
  - feedback capture
  - QA metrics
  - filters + triage presets in UI

## Non-Negotiable Rules

1. Keep architecture modular (services, not route-level business logic).
2. Preserve strict grounding:
   - answer only from retrieved context
   - no invented facts
   - explicit insufficient-evidence behavior
3. No scope creep without explicit decision.
4. Keep UX internal-tool focused: debug visibility over cosmetic complexity.
5. Every substantial change must be verifiable (lint/tests/manual checks).

## Scope Guardrails

Do not start these unless explicitly approved for the current step:

- Agent workflows
- Hybrid retrieval
- Queue/worker overhaul
- Auth overhaul
- Major infra re-architecture

## Delivery Workflow (Follow For Every Task)

1. Clarify target outcome in one sentence.
2. Implement smallest complete vertical slice.
3. Add/extend debug fields when behavior changes.
4. Run checks:
   - backend compile/lint
   - frontend lint
   - focused manual smoke path
5. Summarize:
   - what changed
   - why
   - how validated
   - suggested commit title + file list

## Definition of Done (Per Feature)

A feature is done only if all are true:

- API contract is explicit and stable
- UI reflects backend behavior correctly
- Failure paths are handled and observable
- No new lint/type errors
- README/API docs updated if contract changed

## Priority Order For Next Iterations

1. Evaluation UX polish and fast triage
2. Better failure diagnostics (clear reason taxonomy)
3. Retrieval quality controls and threshold tuning
4. Lightweight internal QA workflows (without leaving current architecture)
5. Performance and reliability hardening

## Error Reason Taxonomy (Working Convention)

Keep reasons normalized and reusable across backend, metrics, and UI:

- no_results
- not_enough_results
- low_top_vector_score
- low_top_rerank_score
- llm_error
- provider_error
- timeout
- exception

If adding a new reason:

1. Add consistently at generation point
2. Include in metrics aggregation/breakdown
3. Make visible in ask-runs UI filters/badges

## Commit Hygiene

- Prefer small focused commits per vertical change.
- Commit only related files.
- Use message pattern:
  - `add ...` for new capability
  - `improve ...` for enhancement
  - `fix ...` for bug/behavior regression
  - `refactor ...` for structure-only changes

## Working Agreement

When we say "continue", default action is:

1. Pick the next highest-impact item from this playbook.
2. Implement it end-to-end.
3. Validate.
4. Return commit suggestion and exact file list.
