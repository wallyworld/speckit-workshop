---
description: "Plan checklist: escape hatches need requirement authority, qualitative thresholds are operationalized, every MUST the plan relies on has a task that builds it, and boundaries are specified (raise to catcher, fail-closed positive-path tests, wire-format fixtures, command-surface tests on their real invocation path, validator malformed-input cases)."
---

# Plan checklist

Apply this checklist before and while generating a feature plan (plan.md).
It fires as a mandatory `before_plan` hook in skills mode and as the
`review-plan-checklist` gate in workflow mode.

1. **Escape hatches need requirement authority.** Every design opt-out for
   a behaviour a requirement gates with MUST (a `skip` mode, an optional
   field, an operator override) must name who may use the opt-out and cite
   the requirement wording that authorizes it. An opt-out no requirement
   authorizes is fixed at the spec root before tasks are generated.
2. **Operationalize qualitative thresholds.** Every threshold-shaped term
   in a requirement the spec claims to complete ("sustained", "bounded",
   "configured") must carry an operational formula and default in
   research.md or data-model.md before tasks.md is generated; a task asked
   to implement an undefined criterion is written blind.
3. **Every MUST the plan relies on has a task that builds it.** Every
   capability a requirement gates with MUST that the plan depends on must
   have a task that builds it, and every task names exact file paths; a
   capability with no task will surface as a finding later.
4. **Boundaries are specified, not implied.** Every delta that adds a raise
   names the handler that catches it; every fail-closed behavior names
   its positive-path test; every parser delta over an external wire
   format names its fixture evidence and blocks on live validation when
   the format is offline-unverifiable; every new command surface names a
   test on its real invocation path (the default or primary route a
   user takes), not only a flagged or synthetic variant; every new
   validator names its schema-valid-but-malformed input cases.

The command surfaces and coverage-critical artifact kinds specific to
this project are recorded in `AGENTS.md`.

Report PASS, or one line per violation naming the file and the requirement
ID it concerns.
