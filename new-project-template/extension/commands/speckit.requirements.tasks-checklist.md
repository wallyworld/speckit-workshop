---
description: "Tasks checklist: enum-extending tasks grounded in source and existing checkers, sequential IDs, tests-first with known-good and known-bad fixtures, boundary tests (raise to catcher, command-surface tests on their real invocation path), positive-path fixtures for fail-closed behaviors, and malformed inputs in validator matrices."
---

# Tasks checklist

Apply this checklist before and while generating tasks.md, and whenever
appending convergence work to it. It fires as a mandatory `before_tasks`
and `before_converge` hook in skills mode and as the `review-tasks` gate
in workflow mode.

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
   and every new checker ships a known-good fixture that must pass and
   a known-bad fixture that must fail.
4. **Boundary tests are first-class tasks.** Every task that adds a raise
   names the handler that catches it and carries a task driving the
   exception through that handler; every new command surface carries a
   test on its real invocation path (the default or primary route), not
   only a flagged or synthetic variant.
5. **Fail-closed behaviors carry positive-path tests.** Every fail-closed
   parse or probe carries a fixture test with a realistic response for
   the success it must produce, alongside its failure-path tests; a
   parser of an external service's response blocks on live validation
   when the wire format cannot be verified offline.
6. **Validator matrices include malformed inputs.** Every new validator's
   test matrix includes schema-valid-but-malformed inputs (wrong types,
   non-numeric strings, empty, duplicates), not only the happy and
   rejected shapes.

The command surfaces and coverage-critical artifact kinds specific to
this project are recorded in `AGENTS.md`.

Report PASS, or one line per violation naming the task ID it concerns.
