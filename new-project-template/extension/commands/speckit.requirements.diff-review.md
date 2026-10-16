---
description: "Independent diff review: commission a fresh-context reviewer with only the goal, the applicable checklists, and the implementation diff, fix every finding, and re-run until a clean pass; fires as the after_implement hook."
---

# Independent diff review

Before reporting an implementation complete, the diff is reviewed by a
context that did not write it. The author's reasoning is not part of the
review input: the reviewer receives the goal, the checklists, and the
diff as text, exactly the way an external reviewer does. The author's
belief that the change is correct is not evidence.

1. **Collect the diff and the goal.** Produce the implementation diff
   (the working tree against its base, or the change set named by the
   task batch) and the goal artifacts a reviewer needs: the feature
   spec or acceptance criteria, and the applicable checklists (for
   example the tasks checklist). Do not include chat history, plan
   rationale, or any explanation of what the change is "supposed" to do
   beyond those artifacts.
2. **Commission the review in a fresh context.** Delegate to a subagent
   or a new session whose prompt contains only the goal, the
   checklists, and the diff. Instruct the reviewer to treat every
   changed surface as an untrusted claim and to derive its own
   falsification probes from the goal and the checklist rules: failure
   and partial-failure paths, boundary conditions, both directions of
   every constraint the change introduces (no undeclared or extra
   entries and no missing ones, nothing invalid accepted and nothing
   valid rejected), per-entity behaviour when an operation spans many
   entities, and tests exercised on the real invocation path. Findings
   cite the probe that shows them.
3. **Fix and re-run until clean.** Correct each finding, then re-run
   the review on the updated diff with a fresh reviewer context. Do not
   rationalize a finding away; a disputed finding is re-derived, not
   overruled.
4. **Report.** Report PASS only when a reviewer pass over the final
   diff found no violations; otherwise report the open findings and do
   not mark the task done. Record which probes fired, not only the
   verdict: a pass with no probes is not a pass.

The reviewer must never be handed the author's conclusions. When no
fresh context is available (a solo session with no delegation), the
author runs the same probe pass in-context and records it as a
self-review with its blind-spot caveat, not as an independent pass.
