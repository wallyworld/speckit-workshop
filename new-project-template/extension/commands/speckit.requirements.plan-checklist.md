---
description: "Plan checklist: escape hatches need requirement authority, no requirement-less scope (every FR traces to a product requirement), the real entry point and its acceptance test named, qualitative thresholds are operationalized, every MUST the plan relies on has a task that builds it, boundaries are specified (raise to catcher, fail-closed positive-path tests, wire-format fixtures, command-surface tests on their real invocation path, validator malformed-input cases), and example values are not constants (a sample address, port, credential, token, path, or identifier must not become a hardcoded implementation constant; any such value is supplied at run time)."
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
4. **No requirement-less scope.** Every FR and user story must trace to a
   product requirement ID. A capability absent from the product
   requirements is a requirements change: remove it from the spec or add
   the requirement and roadmap entry before planning. A clarify answer does
   not authorize scope.
5. **Name the real entry point.** Every requirement observed through an
   external interface names that entry point (an HTTP route, CLI command,
   UI screen, device action, produced file, and so on) and the executable
   acceptance test that drives it. If it cannot be automated, name the
   manual check.
6. **Boundaries are specified, not implied.** Every delta that adds a raise
   names the handler that catches it; every fail-closed behavior names
   its positive-path test; every parser delta over an external wire
   format names its fixture evidence and blocks on live validation when
   the format is offline-unverifiable; every new command surface names a
   test on its real invocation path (the default or primary route a
   user takes), not only a flagged or synthetic variant; every new
   validator names its schema-valid-but-malformed input cases.
7. **Examples are not constants.** An address, port, credential, token,
   path, or identifier in a requirement, contract, or quickstart is
   illustrative unless the requirement makes it a constraint. The plan
   must state that such a value is supplied at run time (environment,
   configuration, or fixture) and must forbid a hardcoded example value;
   contracts must label example values as environment-specific examples
   only.

The command surfaces and coverage-critical artifact kinds specific to
this project are recorded in `AGENTS.md`.

Report PASS, or one line per violation naming the file and the requirement
ID it concerns.
