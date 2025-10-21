<!--
Sync Impact Report
- Version change: N/A → 1.0.0
- Modified principles: Initial adoption
- Added sections: Core Principles (1–5); Additional Constraints & Standards; Development Workflow & Quality Gates; Governance
- Removed sections: None
- Templates requiring updates:
  - .specify/templates/plan-template.md ✅ updated
  - .specify/templates/spec-template.md ✅ updated
  - .specify/templates/tasks-template.md ✅ updated
  - .specify/templates/commands/* ⚠ pending (directory not present in repo)
- Follow-up TODOs:
  - TODO(RATIFICATION_DATE): Original adoption date unknown; set by maintainers.
-->

# CommonForms Constitution

## Core Principles

### I. CLI-First, Text I/O, Deterministic Exit Codes
All core functionality MUST be accessible via the `commonforms` CLI. Inputs are
provided via flags/args and file paths; normal results go to `stdout` (or the
designated output file path), and errors go to `stderr`.

- Exit code 0 indicates success; non‑zero indicates failure with a clear error.
- Human‑readable output MUST be provided; JSON output MAY be provided when
  needed for automation.
- CLI help (`-h/--help`) MUST describe arguments, defaults, and examples.

Rationale: A CLI‑first contract makes automation, scripting, and debugging
straightforward across environments and CI.

### II. Reproducible Inference and Model Versioning
Inference MUST be reproducible to the extent supported by dependencies.

- Default model weights and versions MUST be explicit and documented. The
  `--model` flag selects the model (e.g., `FFDNet-L`, `FFDNet-S`, or a path).
- Sources of non‑determinism (hardware kernels, parallelism) MUST be documented
  and, where feasible, controllable (e.g., seeds or deterministic modes).
- Any change that alters output schema, field naming, or form structure IS a
  breaking change for downstream consumers and MUST be versioned accordingly.

Rationale: Pinning models and documenting variance preserves result integrity
and enables fair A/B and regression testing.

### III. Core Invariants Are Tested (Non‑Negotiable)
The following invariants MUST have automated tests and pass in CI:

- Producing a fillable PDF from a valid input creates one or more widgets.
- `--fast` mode still produces valid, fillable outputs.
- Encrypted PDFs fail with the defined exception unless a supported password
  mechanism is provided.

Golden tests for representative PDFs SHOULD be maintained when stability is
expected; update only with an explicit rationale.

Rationale: Invariants guard against silent regressions in form creation.

### IV. Simplicity and Performance Budgets
Default experience MUST be simple and useful on CPU‑only environments; GPU use
is optional.

- Each feature/spec MUST declare measurable performance goals (e.g., runtime,
  memory) and a basic validation plan.
- Unnecessary dependencies MUST NOT be added. Prefer lean solutions first.
- Performance optimizations MUST NOT break output correctness.

Rationale: Predictable, simple defaults maximize utility and maintainability.

### V. Privacy, Data Handling, and Minimal Logging
User documents are sensitive. The system MUST protect confidentiality.

- No telemetry or external transmission of PDF contents.
- Temporary files MUST be ephemeral and cleaned up.
- If a model download is needed, the CLI MUST clearly indicate the download and
  cache locally; an offline path MUST be supported.
- Logs MUST avoid PDF content; include only minimal, non‑sensitive metadata.

Rationale: Respect for user data is essential for trust and compliance.

## Additional Constraints & Standards

- Language/Tooling: Python ≥ 3.10; `ruff` for lint/format via pre‑commit.
- Dependency Policy: Prefer compatible ranges; pin when determinism or security
  requires it; review `pyproject.toml` on changes.
- Security: Follow guidance in `rules/` and `codeguard-*` docs where relevant.
- Artifacts: Test resources reside under `tests/resources/`; golden outputs (if
  used) are versioned and explained in PRs.
- Observability: Structured, minimal logs; errors include actionable context; no
  sensitive content logged.

## Development Workflow & Quality Gates

- Every PR includes a Constitution Check summary covering: CLI contract,
  reproducibility notes, required tests, performance goals, and privacy/logging.
- CI MUST run invariant tests and lints. Failing checks block merges.
- Feature specs MUST declare measurable success criteria tied to user value.
- Breaking changes to outputs or contracts MUST be called out with migration
  notes and version impacts.

## Governance

- Authority: This Constitution supersedes other practice docs when in conflict.
- Amendments: Propose via PR updating this file with a Sync Impact Report,
  version bump, and migration notes. Approval by maintainers required.
- Versioning: Semantic Versioning for this document (MAJOR.MINOR.PATCH) separate
  from application/package versions.
  - MAJOR: Backward‑incompatible governance or principle redefinitions.
  - MINOR: New principle/section or materially expanded guidance.
  - PATCH: Clarifications and non‑semantic refinements.
- Compliance: Review in PRs and at release cut. Non‑compliance requires either
  remediation or an explicit, time‑boxed exception documented in the PR.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): original adoption date unknown | **Last Amended**: 2025-10-20
