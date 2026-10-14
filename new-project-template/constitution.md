# Project Constitution

This constitution has two parts. Part 1 carries the delivery principles:
universal software-delivery governance that travels with the process
tooling. Part 2 carries the project principles: governance specific to what
this product is. Every feature plan runs its Constitution Check against
both parts. The binding implementation mechanics live in
`docs/implementation-mechanics.md`, incorporated by reference.

## Part 1: Delivery principles

### 1. Use supported interfaces

Every external system this project interacts with is driven through its
documented, supported mechanisms, and an unsupported capability is reported
rather than worked around with an undocumented API. Operational state is
determined by querying a system through its supported interfaces, not by
inferring it from incidental signals. The binding mechanics for this
project's systems live in `docs/implementation-mechanics.md`, which this
principle incorporates by reference.

### 2. Surface exact errors

Every external tool invocation MUST surface the exact error and exit code
from the tool process. A `try/except` that swallows a tool error and
produces an invented message is a violation. Operators must be able to
diagnose failures from the tool's own error, without running raw commands.

### 3. Protect operational data

Credentials, generated secret values, and raw sensitive output must not be
committed or stored in normal artifacts. The protected data classes
specific to this project are recorded with the project commitments in
`AGENTS.md` and the requirements they serve in `REQUIREMENTS.md`.

### 4. Build and verify incrementally

Each feature delivers an independently testable outcome. Plans identify
design, implementation, and runtime-readiness checks separately. The
process tooling's analyze and converge stages check feature consistency;
they do not replace product evidence gates.

### 5. Plan staged delivery

`REQUIREMENTS.md` is the human-facing product source of scope; its
requirements carry stable, section-scoped RQ (requirement) IDs, declared
in that file and never renumbered or reused. `ROADMAP.md` groups that scope into
dependency-ordered feature deliverables and, in one table, maps each RQ ID
to the single feature that **Completes** it plus any earlier features that
**Advance** it. There is no separate requirement-ID traceability register:
the mapping is embedded in the roadmap. Each feature specification defines
the scope and acceptance criteria for one roadmap entry. Do not begin
implementation until the feature specification is accepted.

### 6. Review final state

Acceptance reviews assess the complete working tree against this
constitution, `REQUIREMENTS.md`, and the affected feature acceptance
criteria. Findings must be corrected and the affected review rerun against
the new final tree before acceptance. Workflow or layout migrations must
preserve product scope, safety requirements, delivery outcomes, and the
traceability needed to identify unimplemented work. That traceability is
the roadmap Completes/Advances mapping together with each spec's
Requirements Coverage section; acceptance reviews verify that mapping,
confirm that every RQ ID a feature Completes has realizing implementation,
and confirm that no Advances-only RQ is claimed complete.

### 7. Tests must pass before coding is considered finished

All existing non-integration tests MUST pass before changes are presented
as complete. Breaking a passing test suite is a violation that MUST be
fixed before the changes are accepted. The CI pipeline is a safety net,
not a first-pass detector: passing tests are the project's cheapest
regression signal, and tolerating breakage destroys it.

### 8. New code must have test coverage

Every new function, class, CLI argument, or configurable behaviour MUST
have at least one corresponding test case before the implementing task is
marked done. Trivial changes (renames, comment-only, generated boilerplate)
MAY be skipped with the reason documented in the task. Coverage is verified
by running the full non-integration suite; a code change without test
coverage is incomplete.

### 9. Correct data outranks stale prose

Recorded correctness MUST outrank contract prose. When a specification,
contract, or roadmap statement contains a bug or contradiction, the best
fix MUST be determined and applied at the root (correcting the source
artifact) instead of being worked around in later artifacts. A `done`
roadmap entry is not a frozen contract: while its scope remains undelivered,
its prose MAY be corrected like any other bug. Every such correction MUST
preserve scope, safety requirements, and traceability, and MUST be
justified in the feature that makes it.

## Part 2: Project principles

This part carries the governance specific to what this product is. Add one
principle per domain concern through `/speckit-constitution`, which
versions and records the amendment in the constitution; the plan of the
feature that makes it carries the justification. One principle per
domain concern keeps each one checkable at review time.

## Governance

This constitution governs all feature plans and tasks. A feature may amend
it only when the amendment is explicit, justified in its plan, and
versioned and recorded in the constitution by the
`/speckit-constitution` workflow. Amendments may add or revise
principles in either part; Part 1 stays domain-neutral. Completed feature
specifications are historical records; later changes use a new numbered
feature.
