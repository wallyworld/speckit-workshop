# Contributing

This guide is for engineers and implementation agents. The project uses
GitHub Spec Kit to deliver its product one feature at a time.

## Start here

Read these files before changing a feature:

| Purpose                                | Path |
|----------------------------------------| --- |
| Product scope and delivery roadmap     | [`REQUIREMENTS.md`](REQUIREMENTS.md) |
| Staged deliverables and status         | [`ROADMAP.md`](ROADMAP.md) |
| Governance and traceability rules      | [`.specify/memory/constitution.md`](.specify/memory/constitution.md) |
| Feature design and implementation work | The matching feature directory under [`specs/`](specs/) |

Requirement IDs live in [`REQUIREMENTS.md`](REQUIREMENTS.md); the
requirement-to-feature mapping lives in [`ROADMAP.md`](ROADMAP.md) as the
**Completes** and **Advances** columns. Spec Kit's core `/speckit-specify`
command does not resolve RQ (requirement) IDs - the requirements extension
assembles the mapping into a reviewable brief.

Coding agents read [`agent-instructions.md`](agent-instructions.md), which
points here and to [`AGENTS.md`](AGENTS.md). Most harnesses now read
`AGENTS.md` directly; the tool-specific wiring is done once by the seed:
[`.github/copilot-instructions.md`](.github/copilot-instructions.md) for
Copilot, and `.opencode/opencode.json` pointing OpenCode at the repository
skills. If you add a `CLAUDE.md`, import the shared guidance with
`@AGENTS.md` rather than restating it in prose.

## Preparing context for a feature

```text
/speckit-requirements-prepare R2
```

The command validates that `R2` exists, that each predecessor is `done`,
and that its Completes/Advances mapping refers to existing requirements.
It then prints a self-contained brief with the roadmap intent, scope
boundary, exact canonical requirement text, and a coverage seed with
per-requirement digests. Review
the brief against [`ROADMAP.md`](ROADMAP.md) and
[`REQUIREMENTS.md`](REQUIREMENTS.md), then run the emitted core
`/speckit-specify` command. The extension is read-only: it never creates
a branch, feature directory, or spec, and it never changes roadmap
status.

If the extension is unavailable, assemble the same brief manually by
reading the roadmap row, the full text of its Completes/Advances IDs, the
[constitution](.specify/memory/constitution.md), and predecessor specs.

## Local setup

The project's standard development environment is a
[Workshop](https://ubuntu.com/workshop) sandbox: `scripts/workshop.sh`
launches or refreshes it and mounts the host's agent configuration so
agents inside share your credentials. See the README's Workshop
section for the actions it provides. The named actions mirror the
Makefile's public entry points: when you add a target that defines
done, add a matching action (the generic `make` passthrough covers
ad-hoc targets), and `tests/test_workshop_actions.py` fails on drift
in either direction.

@FILL-IN@ Dependency installation and the test-gate commands with the
canonical environment they must run in.

Then install the `specify` CLI and your harness integration
(`<your-harness-integration>` is your coding agent's key from
`specify integration list`, for example `opencode`, `claude`,
`copilot`, `gemini`, `cursor-agent`):

```bash
specify check
specify integration install <your-harness-integration>
specify extension add --dev --force extensions/requirements
```

One integration is active at a time. A second harness integration can
be installed alongside (`specify integration install <key>`), and
`specify integration use <key>` makes it active and re-registers the
extension's commands for it.

GitHub Copilot needs no integration install: the Copilot CLI
auto-discovers the `speckit-*` skills from the git-tracked
`.github/skills/` directory. Restart your agent client and run
`/skills` to confirm the skills are available. The agent adapter and
installed extension are local and ignored by Git; the extension source
is versioned in [`extensions/requirements/`](extensions/requirements/).

The `/speckit-requirements-verify` command checks that every
requirement a feature spec claims to *complete* is materially present in
that spec, and that each claim's recorded digest matches the
requirement's current wording. It fires as a mandatory
`before_analyze` / `before_converge` hook, and the underlying verifier
script runs under your test gate via
`tests/test_requirement_traceability.py` regardless.

## Command invocation forms

The command form depends on the surface: markdown command integrations
such as OpenCode scaffold dotted command files (`/speckit.specify`,
`/speckit.requirements.verify`), while the generated skills carry the
hyphenated names (`/speckit-requirements-verify`) and are the form the
hooks and workflow gates (described under Reviews below) name. OpenCode
discovers the skills
through the `skills.paths` entry in `.opencode/opencode.json`; GitHub
Copilot discovers them natively from `.github/skills/`. This guide shows
the hyphenated skill form.

## Feature workflow

For a new feature:

```text
/speckit-requirements-prepare R#
/speckit-specify <reviewed brief emitted by the preparation command>
/speckit-clarify
/speckit-plan
/speckit-checklist
/speckit-tasks
/speckit-analyze
/speckit-implement
/speckit-converge
```

`/speckit-clarify` and `/speckit-checklist` are used when their extra
clarification or focused checklist is useful; the other stages are the
normal delivery path.

For an existing feature, read its `spec.md` and `tasks.md`, then start
from the stage that has not yet been completed. Confirm that each
feature-local FR (the spec's functional-requirement ID) maps to the
correct `Completes` or `Advances` RQ; an
Advances RQ must never be recorded as done in that feature. Update the
roadmap's Sub-spec link after core Specify creates the feature directory.

## Reviews

Feature specifications must align with their roadmap entry and state their
scope boundary. Use `/speckit-analyze` after task generation to check
consistency across the feature artifacts. Analysis findings are remediated
through `/speckit-requirements-remediation-loop`, which fires automatically
as the mandatory `after_analyze` hook: every hook is declared in the
extension manifest (`extensions/requirements/extension.yml`) and registered
into `.specify/extensions.yml` at install time, so a reinstall can never
drop the enforcement checks; `make test` asserts the registrations.

The enforcement hooks are carried by the extension's checklist commands:

- `/speckit-requirements-plan-checklist` (mandatory `before_plan` hook):
  design opt-outs cite the requirement wording that authorizes them,
  qualitative thresholds carry operational definitions, every MUST the
  plan relies on has a task that builds it, and boundaries are specified:
  every raise names the handler that catches it, every fail-closed
  behavior its positive-path test, every parser delta its wire-format
  fixture evidence, every new command surface a test on its real
  invocation path, and every validator its malformed-input cases.
- `/speckit-requirements-tasks-checklist` (mandatory `before_tasks`,
  `before_implement`, and `before_converge` hooks): tasks that extend an
  enum or register are grounded in current source values and existing
  checkers, task IDs are sequential in execution order (renumber freely
  before implementation; append-only after), and tests are written first
  with known-bad fixtures; the boundary rules apply to every task: a raise
  names the handler that catches it with a test driving the exception
  through, every new command surface carries a test on its real invocation
  path, fail-closed behaviors carry positive-path fixture tests, and
  validator matrices include malformed inputs. At `before_implement` the
  rules are applied to the changes and tests being written, not only the
  task text.
- `/speckit-requirements-diff-review` (mandatory `after_implement` hook):
  commissions an independent fresh-context review of the implementation
  diff before the work is reported done.
- `/speckit-requirements-remediation-loop` (mandatory `after_analyze`
  hook): the analysis remediation loop.
- `/speckit-requirements-verify` (mandatory `before_analyze` and
  `before_converge` hooks): requirement-phrase traceability of Completes
  claims.

The checklists name universal rules; this project's command
surfaces and coverage-critical artifact kinds (the checklists' project
instances) are recorded in [`AGENTS.md`](AGENTS.md) ("Project checklist
instances"; fill them in, the unfilled-marker test enforces it).

Style rules enforced by the test suite:

- **No em dashes (U+2014) in project-produced artifacts.** Use a hyphen
  instead. `tests/test_style.py` scans everything the project produces
  (including `specs/` and the extension) and excludes only upstream Spec Kit
  content and runtime output.

Review generated tasks before implementation. After implementation, review the
complete working tree against the product requirements and the feature
acceptance criteria. If you make corrections, review the corrected tree again.

The project overlays review gates onto the native workflow
(`.specify/workflows/overlays/speckit/review-gates.yml`), mirroring the
extension commands above:

- `review-coverage` (after `specify`) mirrors
  `/speckit-requirements-verify` before human sign-off.
- `review-plan-checklist` (after `plan`) mirrors
  `/speckit-requirements-plan-checklist`.
- `review-tasks` (after `tasks`) mirrors
  `/speckit-requirements-tasks-checklist`.
- `review-implement-checklist` (after `tasks`, applied to the changes being
  written) mirrors `/speckit-requirements-tasks-checklist`.
- `review-diff` (after `implement`) commissions an independent
  fresh-context review of the implementation diff via
  `/speckit-requirements-diff-review` before the work is reported done.
- `review-final-tree` (after `implement`) confirms each Completed RQ ID
  has realizing implementation, that baseline-completed invariants still
  hold, and that no Advances-only RQ is claimed complete; if findings are
  fixed, rerun the gate against the corrected tree.

The gates apply when you run the native workflow command:

```bash
specify workflow run speckit -i "spec=<feature outcome>"
```

Working skill by skill, the same rules arrive through the mandatory
hooks: every `speckit-*` skill reads `.specify/extensions.yml` and executes
its registered hooks at the matching lifecycle points.

## Running tests

@FILL-IN@ Test locations, how to run unit and integration suites, and
any build steps the tests require.

## Updating Spec Kit

Commit or stash work first, then:

```bash
specify self check
specify self upgrade
specify integration upgrade <your-harness-integration>
specify workflow resolve speckit
specify preset resolve spec-template
```

Then reinstall the requirements extension so the installed copy matches
the tracked source:

```bash
specify extension add --dev --force extensions/requirements
```

The hook registrations in `.specify/extensions.yml` are written by the
installer from the extension manifest - never hand-edit them; a
manifest that loses its hooks section silently wipes the registrations
on reinstall.

**Regenerating the agent skills**: the skills under `.github/skills/`
are generated copies of the extension command docs under
`extensions/requirements/commands/` - the commands are the source of
truth. After any change to a command, regenerate its skill copy:

```bash
extensions/requirements/scripts/bash/generate-skills.sh .
```

The mirror test fails while a command and its skill have drifted
apart, so never hand-edit a generated skill.

Review the Git diff before committing: the enforcement-chain mirror tests in
`tests/test_enforcement_chain.py` fail if the upgrade wiped the hook
registrations, dropped the hook sections from the vendored skills, broke
extension-template resolution, stopped the overlay gates from composing,
or let a project-domain term back into a seedable checklist surface.
Commit provider-neutral `.specify/`, `specs/`, requirements, and
roadmap files; keep generated agent adapters and local caches ignored.

**Maintaining the extension-provided templates**: each provided file
must stay a complete copy of the core template plus the project
section (the resolver returns it in its entirety). After an upgrade,
diff the refreshed core template against `extensions/requirements/templates/`
and port upstream changes by hand, keeping the project section intact,
then reinstall the extension. The core templates remain unmodified.
