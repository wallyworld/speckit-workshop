---
description: "Tasks checklist: enum-extending tasks grounded in source and existing checkers, sequential IDs, tests-first with known-good and known-bad fixtures, an acceptance test through the real entry point for every user-facing requirement (not implementation-only, not a placeholder; the test starts the runtime itself or the project gate starts it, never an assumed already-running instance at a hardcoded example value), boundary tests (raise to catcher, command-surface tests on their real invocation path), positive-path fixtures for fail-closed behaviors, malformed inputs in validator matrices, one-to-N refactors carrying per-entity and partial-failure tests, semantic checks enumerating every violation class, and failure boundaries enumerating their wrapped calls' failure classes."
---

# Tasks checklist

Apply this checklist before and while generating tasks.md, whenever
appending convergence work to it, and before implementing a batch of
tasks: at implementation time every rule is checked against the changes
and tests being written, not only against the task text. It fires as a
mandatory `before_tasks`, `before_implement`, and `before_converge` hook
in skills mode and as the `review-tasks` gate in workflow mode.

1. **Ground enum-extending tasks in source and existing checkers.** Before
   writing a task that extends an enum, register, or valid-values set
   (type enums, status registers, configuration keys), list the current
   values from the source and grep the test suite for checkers that
   enumerate that set; the task must also update every artifact an existing
   checker tracks, so a new value cannot turn a green fixture-pair test red.
2. **Task IDs are sequential in execution order.** Before implementation
   begins, tasks.md may be regenerated and renumbered freely: fix defects
   at the root rather than letter-suffixing. Once tasks are implemented,
   convergence appends new work at the bottom under a new phase and never
   renumbers; letter suffixes are sanctioned only there. Never retitle,
   reorder, or insert into existing phases.
3. **Tests-first ordering, with known-bad fixtures.** Every new
   function, configurable behaviour, validator, and query or report
   surface has a test, written before the implementation it covers,
   and every new or re-scoped checker or probe ships a known-good
   fixture that must pass and a known-bad fixture that must fail. A
   checker's known-bad fixture exercises the claim it actually makes -
   its marker and docstring semantics - not only a neighbouring failure.
4. **Boundary tests are first-class tasks.** Every task that adds a raise
   names the handler that catches it and carries a task driving the
   exception through that handler; every new command surface carries a
   test on its real invocation path (the default or primary route), not
   only a flagged or synthetic variant, and a change to an existing probe
   or validator carries the same real-entry-point test, not only one on an
   internal helper.
5. **Fail-closed behaviors carry positive-path tests.** Every fail-closed
   parse or probe carries a fixture test with a realistic response for
   the success it must produce, alongside its failure-path tests; a
   parser of an external service's response blocks on live validation
   when the wire format cannot be verified offline.
6. **Validator matrices include malformed inputs.** Every new validator's
   test matrix includes schema-valid-but-malformed inputs (wrong types,
   non-numeric strings, empty, duplicates), not only the happy and
   rejected shapes. A semantic or cross-field validator that runs on
   documents the schema may already have rejected carries a no-raise
   matrix: malformed container shapes (a scalar where a list or mapping
   belongs) must surface as validation errors, never as exceptions. A
   pattern rule implemented on more than one surface (a schema pattern
   and a runtime guard) carries a cross-surface matrix that injects every
   character outside the rule's allowed class at the start, middle, and
   end and asserts every surface rejects it, so anchoring and
   line-terminator edge semantics are tested, not assumed.
7. **One-to-N refactors carry per-entity and partial-failure tests.** When a
   change moves an operation from a single entity to many (one candidate to
   a list, one target to a set, one step to a sequence), the task carries a
   per-entity test, a partial-failure test (entity N fails and entities
   1..N-1 are shown rolled back, refused, or otherwise left in the correct
   state), and an end-to-end test on the real invocation path, not only
   per-entity unit behaviour.
8. **Semantic checks enumerate every violation class.** A cross-field or
   cross-collection check states its invariant as a closed relation before
   implementation - no undeclared or extra entries and no missing ones,
   nothing invalid accepted and nothing valid rejected - and derives the
   classes from everything the invariant protects and every consumer that
   depends on it (identity, ownership, evidence), not only the fields the
   change names. A field the schema leaves optional because some states do
   not carry it is still required by the check for every state that does,
   and external-response classification matches the raw response at its
   boundary rather than searching formatted or wrapped text, where one
   response can embed another. One known-bad fixture per violation class;
   a single negative fixture proves one direction of a relation, never the
   check.
9. **Failure boundaries enumerate their wrapped calls' failure classes.** A
   boundary that catches, rolls back, or retries (a try/except around a
   sequence of calls, a cleanup handler, a rollback) lists every failure
   class the wrapped calls can raise, derived from the callees and their
   callees, not from the failure that was observed: a class left out is a
   silent fail-open. Each handled class carries a known-bad fixture that
   drives the boundary and asserts its effect.

10. **Acceptance tests use the real entry point.** Every user-facing
    requirement carries an executable acceptance test through the delivery
    interface on the real runtime (the HTTP route, CLI command, UI screen,
    device action, or produced file the user actually uses), not only unit
    tests of internal functions, static text assertions, or injected
    doubles. The test asserts the user-visible outcome and the known failure
    mode, carries a known-bad fixture, and runs in the project's test gate.
    The test starts the runtime itself or the project gate starts it
    explicitly; a test that assumes an already-running instance at a
    hardcoded example value fails this rule. Any value the test needs that
    appears in an example is supplied at run time.
    A placeholder, empty/default implementation, or implementation-only
    assertion fails this rule. After tasks.md exists, invoke
    `/speckit.requirements.acceptance-test` (the hyphenated skill form
    `/speckit-requirements-acceptance-test` on agy or Copilot) to derive the
    test; this is a manual step after tasks, not a hook.

The command surfaces and coverage-critical artifact kinds specific to
this project are recorded in `AGENTS.md`.

Report PASS, or one line per violation naming the task ID it concerns.
