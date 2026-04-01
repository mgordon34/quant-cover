# AGENTS.md

This file defines repository-wide expectations for agents and contributors working in this codebase.

## Priority Order

When making decisions, optimize in this order:

1. readability
2. maintainability
3. correctness
4. simplicity
5. speed of implementation

If there is tension between cleverness and clarity, choose clarity.

## Code Style

- Write clean, explicit Python.
- Prefer straightforward control flow over dense abstractions.
- Keep functions and modules easy to scan.
- Use descriptive names.
- Avoid unnecessary indirection.
- Avoid premature generalization.
- Prefer standard library solutions when they are sufficient.

## Comments

- Do not add comments unless they provide necessary context that the code itself cannot express clearly.
- Do not add comments that restate obvious behavior.
- If a block is complex enough to need repeated explanation, prefer refactoring it into clearer code.

## Refactoring Preference

- Prefer refactoring existing code over writing parallel new code when possible.
- Before adding a new abstraction, check whether the current structure can be improved instead.
- Remove duplication when it improves clarity.
- Do not preserve awkward patterns just because they already exist.

## Project Structure Expectations

As the repository grows, keep concerns separated:

- `api` for transport-layer concerns
- `domain` for core business concepts
- `services` for orchestration and use-case logic
- `scraping` for source ingestion code
- `db` for persistence concerns

Do not mix scraping logic into route handlers.
Do not put business logic directly in framework entrypoints.
Do not couple API response models tightly to database internals unless there is a clear reason.

## Python Standards

- Use type hints where they improve clarity.
- Prefer small, cohesive modules.
- Keep side effects near the edges of the application.
- Make dependencies explicit.
- Raise clear errors.
- Avoid hidden global state.

## Editing Guidance

- Make the smallest correct change.
- Read surrounding code before editing.
- Preserve consistency with existing naming and structure unless refactoring is part of the task.
- When touching confusing code, favor simplifying it rather than layering onto it.

## Early-Stage Repository Guidance

- This repository is in an early scaffold phase.
- Do not overengineer worker systems, billing, or infrastructure before they are needed.
- Build foundations that are easy to extend later.
- Prefer stable seams over speculative architecture.

## Session Start Checklist

At the start of a session:

1. read `README.md`
2. read `plan.md`
3. inspect the current repository structure
4. confirm the requested work matches the current phase of the project

## When In Doubt

- choose the more readable implementation
- choose the simpler interface
- choose the design that is easier to maintain six months from now
- refactor instead of adding complexity
