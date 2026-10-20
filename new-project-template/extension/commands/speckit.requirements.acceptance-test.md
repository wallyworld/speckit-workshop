---
description: "Derive and add an executable acceptance test for every user-facing requirement through the real delivery entry point (HTTP route, CLI command, UI route, device action, or produced file), on the real runtime, with isolated state, a known-bad fixture, a self-starting or gate-started runtime, run-time-supplied values rather than hardcoded examples, and wiring into the project test gate; invoked manually after tasks and before implementation."
---

# Acceptance test

## User Input

```text
$ARGUMENTS
```

Optional: a roadmap ID (for example `R3`) or a feature directory. When
empty, use the active feature.

Use this procedure after `tasks.md` exists and before implementation. It
turns each user-facing requirement into an executable acceptance test that
drives the real delivery entry point. It does not assume a particular
runtime, language, framework, or test runner: the entry point is whatever
the product actually exposes.

An acceptance test derived here is the primary evidence for a user-facing
requirement. Unit tests of internal functions, static text assertions, and
injected doubles do not replace it.

1. **Read the sources.** If an argument names a roadmap or feature ID, use
   that feature's `spec.md` and `plan.md`; otherwise use the active feature.
   Read `quickstart.md`, the project build/test entry points, and the
   existing test conventions. If `plan.md` does not name the real entry point or the
   runtime launch command for a user-facing requirement, stop and fix the
   plan first; do not invent a test-only entry point.
2. **Map requirements to entry points.** For every user-facing requirement,
   record the requirement ID, the real delivery entry point (an HTTP route,
   CLI command, UI route or screen, device action, produced file, and so
   on), the observable outcome, and the known failure mode. Keep this map;
   it is the review artifact.
3. **Identify the runtime and isolation.** Name the launch command from
   `plan.md` or `quickstart.md`, the test framework already in use, the
   isolated state (temporary database, directory, port, device harness, or
   fixture), and the teardown. The test must start that runtime itself, or
   the project test gate must start it explicitly. A test that assumes an
   already-running instance at a hardcoded example value is not
   self-contained and is a finding. Any value the test needs that appears
   in an example - an address, port, credential, token, path, or
   identifier - must be supplied at run time, and a test or implementation
   that hardcodes the example value must fail. Add a fast check that
   implementation code does not hardcode example values. Do not point a
   test at production data or a developer's live database. Use the runtime
   and tools the environment provides; do not download a new one unless
   none is available. Record any launch flags. Tool errors are failures,
   not noise.
4. **Write the test in stages, tests first.** Start with one user-facing
   requirement: start the real runtime in the test fixture (or let the
   project gate start it), drive the real entry point, and assert the
   user-visible outcome. Run it before the implementation exists and confirm
   it fails for the expected reason. Then extend the same test to the
   remaining requirements, one at a time.
5. **Add a known-bad fixture.** Create a fixture or mutation that proves the
   test can fail on the failure mode the user would see. Run it, confirm
   the failure, and restore the good state.
6. **Wire it into the project test gate.** Put the test in the project's
   existing test location, run it through the project's normal invocation
   (for example the make target or CI command), and make a failing
   acceptance test fail that gate. Do not leave it as a manual-only script
   unless no executable entry point exists.
7. **Review the result.** Reject the test if it:
   - only imports modules, calls internal helpers, or asserts static text;
   - checks a status code or file existence without the user-visible
     outcome;
   - does not start the real runtime itself and has no project gate that
     starts it;
   - assumes an already-running instance at a hardcoded example value, or
     uses a launch command different from the one in
     `plan.md`/`quickstart.md`;
   - hardcodes an example value that the requirement expects to be supplied
     at run time;
   - does not exercise the real entry point, or ignores the runtime's
     errors;
   - shares production state or leaves state behind;
   - has no known-bad fixture or cannot be made to fail;
   - skips a user-facing requirement in the spec;
   - is not wired into the project test gate.
8. **Report.** Report the requirement-to-entry-point-to-test mapping, the
   runtime start path (test fixture or project gate), the files changed, the
   red/green/mutation results, and any requirement whose entry point cannot
   be automated. For a manual fallback, name the manual check and record the
   acceptance evidence.

The project's test gate, not this procedure, is the gate. A generated test
that has never failed is not evidence.
