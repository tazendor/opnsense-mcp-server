<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0 (initial authoring from template)

Modified principles: N/A (initial creation)

Added sections:
  - Core Principles (I–V)
  - Technology & Quality Standards
  - Development Workflow
  - Governance

Removed sections: N/A

Templates reviewed:
  ✅ .specify/templates/plan-template.md — Constitution Check section references
     principle gates; existing structure is compatible.
  ✅ .specify/templates/spec-template.md — Requirements format aligns;
     no mandatory sections added beyond existing template.
  ✅ .specify/templates/tasks-template.md — TDD principle (Principle V) makes
     test tasks MANDATORY, not optional. The template's "OPTIONAL" caveat is
     overridden by this constitution for all features in this project.

Follow-up TODOs:
  - None. All placeholders resolved.
-->

# OPNsense MCP Server Constitution

## Core Principles

### I. Simplicity First

Every design and implementation choice MUST favour the simplest solution that
satisfies the specification. Abstractions, indirection, and generality are
introduced only when the specification explicitly requires them.

- YAGNI: never implement speculative requirements.
- Three concrete duplications are preferred over a premature abstraction.
- No half-finished implementations; each merged piece MUST be fully working.
- Complexity MUST be justified in writing before it is introduced (see Governance).

### II. Idiomatic Python

All code MUST be written in idiomatic, modern Python (3.12+).

- Follow PEP 8 and PEP 257 style conventions, enforced by `ruff`.
- Prefer standard-library and MCP SDK primitives over third-party alternatives.
- Use dataclasses, `pathlib`, `contextlib`, and other stdlib idioms; avoid
  re-inventing them.
- No clever metaprogramming, dynamic attribute access, or monkey-patching unless
  the specification mandates it and no idiomatic alternative exists.

### III. Full Type Safety

Every module, function, method, and variable MUST carry complete type annotations.

- `mypy --strict` MUST pass with zero errors on every commit.
- `Any` is prohibited except at true external boundaries (raw JSON payloads,
  third-party libraries without stubs), and MUST be narrowed as soon as possible.
- Public API surfaces MUST use `Protocol` or `TypedDict` rather than opaque dicts.
- Type annotations serve as machine-checkable documentation; they are not optional.

### IV. Specification-Driven Development

No feature work begins without an approved specification. The specification is
the authoritative source of truth for scope, behaviour, and acceptance criteria.

- Implementation MUST match the specification; the specification is not updated
  retroactively to match a convenient implementation.
- Scope creep discovered during implementation is tracked as a new feature
  request, not silently added.
- Acceptance scenarios in the spec are the definitive definition of "done".

### V. Test-Driven Development (NON-NEGOTIABLE)

TDD is mandatory for all implementation work. The Red-Green-Refactor cycle is
strictly enforced.

- Tests are written first and MUST fail before any implementation code is added.
- User or reviewer approval of failing tests is required before implementation
  begins.
- All code is covered by tests at the unit, integration, and contract level as
  appropriate to the feature.
- No implementation task is complete until its corresponding tests pass and the
  test suite remains green.
- In the context of this project, the tasks-template "tests are OPTIONAL" caveat
  does NOT apply; tests are always included.

## Technology & Quality Standards

**Language**: Python 3.12+

**Protocol**: Model Context Protocol (MCP) via the official MCP Python SDK.

**Linting & formatting**: `ruff` (lint + format), configured in `pyproject.toml`.

**Type checking**: `mypy --strict`.

**Testing**: `pytest` with `pytest-asyncio` for async test support.
Test layout: `tests/unit/`, `tests/integration/`, `tests/contract/`.

**Dependency management**: `uv` (or `pip` + `pyproject.toml`); dependencies
pinned in `pyproject.toml` with a lock file.

**Quality gates** (MUST pass before any merge):
1. `ruff check` — zero lint errors.
2. `ruff format --check` — zero formatting violations.
3. `mypy --strict` — zero type errors.
4. `pytest` — full test suite green.

## Development Workflow

1. **Specify**: A feature spec (`spec.md`) is created and approved via
   `/speckit-specify` before any design or coding work begins.
2. **Plan**: A technical plan (`plan.md`) is produced via `/speckit-plan`.
   The Constitution Check gate in the plan MUST reference and satisfy
   Principles I–V before implementation starts.
3. **Tasks**: An ordered task list (`tasks.md`) is generated via
   `/speckit-tasks`. Test tasks appear before their implementation tasks.
4. **Red**: Tests are written and confirmed to fail (`pytest` shows FAILED).
5. **Green**: Implementation code is written until tests pass.
6. **Refactor**: Code is cleaned up while keeping tests green.
7. **Review**: All quality gates pass; implementation matches the spec.

## Governance

This constitution supersedes all other coding guidelines, README conventions,
and ad-hoc practices for the OPNsense MCP Server project. When a conflict
arises between this document and any other, this document wins.

**Amendments**:
- Any amendment MUST increment the version number following semantic versioning
  (MAJOR: principle removal or incompatible redefinition; MINOR: new principle
  or materially expanded guidance; PATCH: clarification or wording fix).
- All PRs and code reviews MUST verify compliance with the active principles.
- Complexity violations MUST be justified in a `## Complexity Tracking` section
  of the relevant `plan.md` before the work proceeds.
- Runtime development guidance is in `CLAUDE.md` (project root).

**Version**: 1.0.0 | **Ratified**: 2026-06-27 | **Last Amended**: 2026-06-27
