# 02 - Core Concepts

## The mental model: an agentic loop around a requirements spec

Spec Kit puts the specification in your repository, where it survives the
session. `spec.md` states what the feature must do, and the agent re-reads it
at every phase. Each command in the loop reads the artifacts written before
it; most write a new one, and analyze only reports. The chain is
`spec -> plan -> tasks -> code`, with an audit trail from the request to the
code.

## The constitution: the layer above the loop

Before the first feature, the project records its constitution: principles
every feature must honor. It lives in
`.specify/memory/constitution.md`. `specify init` seeds a placeholder;
`/speckit.constitution` ratifies or updates it (workshop:
[01](01-setup.md#14-ratify-the-project-constitution)). It isn't a loop step.

Two sections of `plan.md` are relevant here. The **Constitution Check** tests the
design against each principle. A conflict either changes the design or goes in
**Complexity Tracking**: an entry naming the principle, why the deviation is
necessary, and what simpler option was rejected. Example: the constitution
says "minimal runtime stack"; the design wants a background job library. Drop
the library, or record why it needs the dependency.

Analyze treats a MUST conflict as CRITICAL. Implement reads the constitution
as a governance constraint. Converge treats a MUST violation as CRITICAL and
appends remediation.

An unfilled template gives plan and analyze nothing to check, and converge
skips it. If the Constitution Check still says "Gates determined based on
constitution file", or converge's metrics line reports the principles were
skipped, the file is still a placeholder. Run `/speckit.constitution` first.

## The loop

The loop is per feature; the constitution applies to every feature.
In my run with `openrouter/z-ai/glm-4.6`, it took about 21 minutes of agent
work: specify 1 minute, plan 2, tasks 1, analyze 1, implement 10, and 3 across
two converge cycles. Clarify asked three questions.

```
specify -> clarify -> plan -> tasks -> analyze -> implement -> converge
  ^                                                                  |
  +------------------------------------------------------------------+
                (converge may add remaining tasks;
                 iterate implement/converge until clean)
```

| Step | Command | What it does | Produces |
|---|---|---|---|
| 1 | `/speckit.specify` | Turns a feature description into a specification | `specs/NNN-feature/spec.md` |
| 2 | `/speckit.clarify` (optional) | Asks up to 5 targeted questions when parts are underspecified | updates to `spec.md` |
| 3 | `/speckit.plan` | Designs the technical approach, files, and architecture | `specs/NNN-feature/plan.md` |
| 4 | `/speckit.tasks` | Breaks the plan into an ordered, actionable task list | `specs/NNN-feature/tasks.md` |
| 5 | `/speckit.analyze` | Cross-checks spec, plan, and tasks for inconsistencies before implementation (read-only) | analysis report |
| 6 | `/speckit.implement` | Executes the tasks, writing code | code changes |
| 7 | `/speckit.converge` | Re-reads spec/plan/tasks, diffs the code against them, and adds any missing work as new tasks | updated `tasks.md` (and the loop repeats) |

Commands above use OpenCode's dot form. With agy or Copilot they're
hyphenated: `/speckit-constitution`, `/speckit-specify`, `/speckit-clarify`,
`/speckit-plan`, `/speckit-tasks`, `/speckit-analyze`, `/speckit-implement`,
`/speckit-converge`.

## The artifacts

- **`constitution.md`** - project rules, versioned and amended explicitly.
  Read at every step; not a feature artifact.
- **`spec.md`** - what and why: user stories with priorities, functional
  requirements, success criteria. This is the contract. State observable
  behaviour, not a meta-rule such as "each requirement must be testable"; a
  vague requirement can't be verified at converge time.
- **`plan.md`** - how: stack, files, data model, interfaces, edge cases.
- **`tasks.md`** - the plan broken into small, independently testable tasks,
  each with a checkbox and a file path. The checkboxes are the plan, not a
  progress tracker.

Each artifact traces to the one before it; converge checks the code against
all of them.

## Where validation occurs

Validation isn't a reviewer at the end. It's a series of gates:

| Check | Who does it | When |
|---|---|---|
| Constitution is honored | plan's Constitution Check; deviations recorded in Complexity Tracking; analyze and converge treat MUST conflicts as CRITICAL | plan/analyze/converge time |
| Testable requirements | Spec author (you and the agent) | spec time |
| Plan covers the spec | `/speckit.plan` reads spec.md | plan time |
| Tasks cover the plan | `/speckit.tasks` reads plan.md | tasks time |
| Spec, plan, and tasks agree | `/speckit.analyze` cross-checks the three artifacts | analyze time |
| Code passes its tests | test runner in `/speckit.implement` | implement time |
| Code matches spec and tasks | `/speckit.converge` re-reads spec/plan/tasks and diffs | converge time |

Analyze is read-only and never inspects code; converge is the closing gate.
If code drifts, converge doesn't say done. It appends the missing work and
re-enters the loop.

### A non-trivial requirement (preview)

The order feature in 04 has two flat requirements: *"Placing an order for a
pet that is no longer listed as available must fail"* and *"An order may not
bring a pet's stock below zero."* A naive implementation can pass the happy
path (order when stock is 1, expect success) and still let a sold-out pet be
ordered or drive stock to -1. If the tests only assert the happy path,
converge appends a test for the missing rule; it re-reads the spec, not just
the tests. A passing suite isn't the same as a verified requirement.

The spec drives the test, the test drives the implementation, and converge
confirms the test exists and passes. The point of putting a spec in front
is that the *requirement* is stated independently of any one implementation,
so a later refactor or rewrite has to still honor it.

## The agent side: context management

Each command re-reads the artifacts from disk, so the agent doesn't have to
remember earlier messages. Keep one feature per session. A session that spans
features can resolve the wrong directory; if the plan looks like it belongs
to a previous feature, check `.specify/feature.json`.

Governance above the loop, artifacts between the commands, a gate at every
handoff.

Next: [the implementation loop](03-the-loop.md).
