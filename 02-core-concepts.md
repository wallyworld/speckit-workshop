# 02 - Core Concepts

How Spec Kit's moving parts work, from first principles.

## The mental model: an agentic loop around a written spec

You already know how to work with a coding agent: you describe a problem,
it reads your files, edits code, runs tests, and iterates. The problem
with that workflow is that "the agent's plan" lives in its context window
and is discarded when the session ends. Nothing preserves *what you asked
for* independently of what the agent decided to build.

Spec Kit's answer is to make the specification a **first-class artifact in
your repository**: a file (`spec.md`) that states what the feature must
do, in a form the agent re-reads at every phase. Each command in the loop
reads the artifacts written by the previous command, and writes its own.
The result is a chain: spec -> plan -> tasks -> code. When the chain is
complete, you have an audit trail from "what the user asked for" to "the
code that implements it."

## The loop

```
specify -> clarify -> plan -> tasks -> implement -> converge
  ^                                                       |
  +-------------------------------------------------------+
                (converge may add remaining tasks;
                 iterate implement/converge until clean)
```

| Step | Command | What it does | Produces |
|---|---|---|---|
| 1 | `/speckit.specify` | Turns a feature description into a specification | `specs/NNN-feature/spec.md` |
| 2 | `/speckit.clarify` (optional) | Asks up to 5 targeted questions when parts are underspecified | updates to `spec.md` |
| 3 | `/speckit.plan` | Designs the technical approach, files, and architecture | `specs/NNN-feature/plan.md` |
| 4 | `/speckit.tasks` | Breaks the plan into an ordered, actionable task list | `specs/NNN-feature/tasks.md` |
| 5 | `/speckit.implement` | Executes the tasks, writing code | code changes |
| 6 | `/speckit.converge` | Re-reads spec/plan/tasks, diffs the code against them, and adds any missing work as new tasks | updated `tasks.md` (and the loop repeats) |

## The artifacts: the chain of written intent

- **`spec.md`** - *what* and *why*. User stories, functional requirements,
  success criteria. This is the contract the whole loop is accountable to.
  Note: each requirement "must be testable" - a vague requirement cannot
  be verified at converge time.
- **`plan.md`** - *how*. Technical design: stack, files, data model,
  interfaces, edge cases.
- **`tasks.md`** - *who/what order*. The plan broken into small,
  independently-testable tasks, each with a checkbox and a file path.

The loop is "closed" because each artifact must be traceable to the one
before it: every task comes from a plan, every plan from a spec, and
converge checks the code against all of them.

## Where validation actually fires

This is the key concept to internalize.

| Check | Who does it | When |
|---|---|---|
| Testable requirements | Spec author (you and the agent) | spec time |
| Plan covers the spec | `/speckit.plan` reads spec.md | plan time |
| Tasks cover the plan | `/speckit.tasks` reads plan.md | tasks time |
| Code passes its tests | test runner in `/speckit.implement` | implement time |
| Code matches spec and tasks | `/speckit.converge` re-reads spec/plan/tasks and diffs | converge time |

Validation is **not** "a reviewer at the end." It is a series of
incremental gates that force the agent to read and reconcile the intent
it wrote down. If the code drifts from the spec, converge does not say
"done" - it appends the missing work and re-enters the loop.

### A non-trivial requirement (preview)

In the hands-on phase, the spec will include requirements along these
lines: *"Placing an order for a pet that is no longer listed as available
must fail"* and - a more complex one - *"An order may not bring a pet's stock
below zero."* There is a subtle way to violate both at once: an
implementation that checks availability in the wrong order, or not at
all, can still pass happy-path tests ("place an order when stock is 1,
expect success") while silently letting a sold-out pet be ordered and
stock go negative. The **loop** catches this strain, because the spec's
requirements drive tests that a naive implementation cannot pass. You
will experience this directly.

Why not just write the test? You do write the test - the spec drives the
test, the test drives the implementation, and converge confirms the test
exists and passes. The point of putting a spec in front is that the
*requirement* is stated independently of any one implementation, so a
later refactor or rewrite has to re-honor it.

## The agent side: context management

None of this works if the agent cannot hold the loop in its head. Two
things make it practical:

1. **Each command re-reads the artifacts.** By structuring the work as
   explicit files, Spec Kit makes the spec/plan/tasks available to the
   agent at every step without it having to remember earlier messages -
   it reads the file fresh each time.
2. **Run one feature per session when possible.** A session that spans
   multiple unrelated features fills the context with stale reasoning.
   Starting a new session for a new phase in the loop (plan, then a fresh
   one for implement) keeps the context clean and the agent's attention
   on the task at hand.

## What you now know

- The loop is: specify -> plan -> tasks -> implement -> converge.
- The artifacts form a chain of written intent: spec, plan, tasks.
- Validation is incremental gates, not an end-of-project review.
- The spec is the contract the whole loop is accountable to.

Next: [the loop, demoed](03-the-loop.md).