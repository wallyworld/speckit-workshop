# Spec Kit Process Template

Seeds a new project with a requirements-first Spec Kit process - the
product's requirements and a roadmap steer delivery across many
features - plus the tooling that enforces the process. One command
installs everything and a short fill-in pass then makes it project specific.

## Orientation

Spec Kit is a spec-driven development toolkit: an agent runs slash
commands that turn a feature description into a written spec, plan, and
task list, analyzes them for consistency, implements them, and converges
the code back against the spec. That command sequence is the loop:

```
specify -> clarify -> plan -> tasks -> analyze -> implement -> converge
  ^                                                                  |
  +------------------------------------------------------------------+
```

Spec Kit's model is one feature at a time: each feature goes through the
loop on its own, and the workflow keeps no picture of the product the
features add up to. A product delivered as multiple features needs an
accounting layer in front of the loop - **phased delivery**: the
product's requirements are stated once, each with a stable ID, in a
single source (`REQUIREMENTS.md`); a roadmap (`ROADMAP.md`) maps every
requirement to the one feature that completes it in delivery order.
Each requirement carries requirement phrases - distinctive wording
copied verbatim from its own text - so a spec claiming to complete the
requirement can be checked for actually containing its content.

Out of the box, using default upstream Spec Kit, each command is a
prompt: nothing verifies that the artifacts it produces cover what they
claim, and nothing connects a feature to the product plan. This project
template addresses that limitation. It adopts the phased-delivery model
above and adds an enforcement layer to check it, in four ways:

- **deterministic checkers** - Bash scripts over the artifacts, chiefly
  the requirement traceability verifier, run by the project's test
  suite;
- **moment-of-authoring hooks** - mandatory checklists injected around
  Spec Kit's own commands at the exact moment the artifact is written;
- **workflow gates** - the above checks composed into Spec Kit's bundled
  workflow (the command sequence `specify workflow run` executes) as
  approve/reject gates;
- **mirror tests** - plain pytest modules re-checking the same claims,
  so the repository's own suite fails on drift even in a bare checkout
  (a fresh clone, or CI) where the agent tooling is absent.

Each mirror test asserts one standing claim - a hook
registration, a rule's incorporation into every surface - so removing or
breaking it fails `make test`.

The principle behind the layering is that an agent obeys prose unreliably,
but it cannot skip a gate. A rule that can be a test must not stay
prose; a rule no test can verify belongs in a hook injected at the
moment of authoring; a process-bound check becomes a workflow gate.
Using prose is the last resort.

An **extension** is Spec Kit's packaging for all of this: a manifest
declaring commands, templates, and hooks, plus the scripts the commands
run. **Skills** are the agent-facing copies of the extension commands,
generated into `.github/skills/`, and into `.agents/skills/` or
`.claude/skills/` according to the harness that is being used.

## Where this fits in the Spec Kit ecosystem

Spec Kit's core is deliberately per-feature; for work too large for one
loop cycle it documents a manual roadmap convention - the "spec of
specs" ([concepts/spec-of-specs](https://github.github.io/spec-kit/concepts/spec-of-specs.html)):
a roadmap table with stable IDs, dependencies, and links, with no
tooling behind it and status maintained by hand. This template does
what that convention asks for, and add the parts it does not have: a
product-level requirements source above the roadmap, explicit
completion semantics per roadmap row (Completes/Advances against
requirement IDs), and deterministic verification of those claims. Each
Completes claim is checked two ways, because the two checks catch
different modes of failure:

- **requirement phrase** - distinctive wording copied verbatim from the
  requirement, anchored at load time (a phrase that is not verbatim
  source wording fails the build). It proves the requirement's content
  is present in the spec (since an ID in a table doesn't prove anything).
- **requirement digest** - a SHA-256 over the requirement's normalized
  text, recorded in the spec when the claim is written. It proves the
  claim is fresh: if the requirement's wording later changes, the
  recorded digest no longer matches and the spec is flagged stale.

So the above ensure presence and freshness: one catches a claim whose
content was never specified; the other, a claim written against wording
that has since changed.

## What lands in the seeded project

The seeded project runs on the phased-delivery convention:
`REQUIREMENTS.md` as the single requirements source, `ROADMAP.md` as the
requirement-to-feature map, and requirement phrases tying each completion
claim to requirement content (the Conventions section below has the
exact formats). On top of that convention, the seed installs:

- a **two-part constitution** (universal delivery principles + your domain
  principles),
- an **authoring guide** (`docs/start-a-project.md`) and starter
  `docs/REQUIREMENTS.md.example` and `docs/ROADMAP.md.example` files for a
  new multi-phase project,
- a **requirements extension** that turns a roadmap row into a
  self-contained brief and verifies every requirement a spec claims to
  complete is materially present in that spec and recorded against the
  requirement's current wording,
- a **phrase extractor** (`scripts/extract-phrases.sh`) that drafts
  verbatim requirement-phrase candidates for review,
- **enforcement hooks** that fire automatically around Spec Kit's
  own commands (plan, tasks, analyze, implement, converge),
- **review gates** mirroring the same checks as approve/reject steps in
  Spec Kit's bundled workflow,
- **extension-provided templates** (the spec template gains a
  Requirements Coverage section; the tasks template requires tests),
- **mirror tests** - plain pytest modules re-checking the same claims:
  style gate, traceability verifier, spec-to-roadmap alignment,
  enforcement-chain integrity,
- a **project domain-term list** (`domain-terms.txt`) seeded with the
  placeholder and read by the domain-neutrality scan,
- **a tool-agnostic wiring chain** so every coding agent reaches the
  same guidance (`agent-instructions.md`, `.github/copilot-instructions.md`,
  `.opencode/opencode.json`).

## The requirements extension

The seed installs **one** extension package, `requirements` (it is not a
collection of extensions). The package declares seven commands, two template
overrides, and eight mandatory hook registrations. The workflow gates and
mirror tests are separate enforcement layers around it.

**Terminology**

- **Extension**: an installable package declaring commands, templates, and
  hooks (`extensions/requirements/extension.yml`).
- **Command**: an agent-facing instruction file.
- **Skill**: the generated agent-facing copy of a command.
- **Hook**: a registration that fires a command at a lifecycle event,
  recorded in `.specify/extensions.yml`.
- **Gate**: an approve/reject step in workflow mode.
- **Mirror test**: a pytest check that re-verifies the same claim without
  needing the agent tooling to be installed.

**The seven commands**

| Command | Fires at | What it does | Why a vanilla Spec Kit project lacks it |
| --- | --- | --- | --- |
| `speckit.requirements.prepare` | Manually, before specify | Validates the roadmap row and its predecessors, then emits a read-only brief with the roadmap intent, scope boundary, canonical requirement text, per-requirement SHA-256 digests, and a ready-to-run core specify command. | Core specify accepts free-form text. There is no roadmap row concept and no guarantee the requirement wording reaches the spec. |
| `speckit.requirements.verify` | `before_analyze`, `before_converge`, and `make test` | For every Completes claim, requires at least one curated requirement phrase in the spec body and a recorded digest matching the requirement's current wording. Fails closed on drift, staleness, missing digests, and malformed claims. | Converge checks code against the spec. Nothing checks the spec against the product requirements; an ID in a table can claim content that was never written, and a claim can outlive the wording it was recorded against. |
| `speckit.requirements.plan-checklist` | `before_plan` | Injects the plan checklist: no requirement-less scope (every FR traces to a product requirement), design opt-outs must cite the requirement wording that authorizes them, every user-facing requirement names its real entry point and acceptance test, threshold-shaped terms need operational definitions, every in-scope MUST needs a task, boundaries must be specified (raise-to-catcher, fail-closed positive-path test, wire-format fixtures, real invocation-path tests, malformed-input cases), and example values are not constants (a sample address, port, credential, token, path, or identifier must not become a hardcoded implementation constant; any such value is supplied at run time). | The plan is free-form. It can invent a capability the product requirements do not authorize, silently design around a MUST, leave a qualitative threshold undefined, omit the task that builds a requirement, or leave a user-facing requirement with no executable acceptance path. |
| `speckit.requirements.tasks-checklist` | `before_tasks`, `before_implement`, `before_converge` | Injects the tasks checklist: tests-first with known-good and known-bad fixtures, an acceptance test through the real entry point for every user-facing requirement, the test starts the runtime itself or the project gate starts it, never an assumed already-running instance at a hardcoded example value, sequential IDs, enum grounding in current source, boundary rules applied to the code and tests being written, and append-only compliant convergence tasks. | Stock Spec Kit treats test tasks as optional. A tasks list can omit failure-path tests, ship a placeholder, test only internal functions while the delivered interface is broken, and a constitution principle alone is prose the agent can ignore. |
| `speckit.requirements.acceptance-test` | Manually, after tasks and before implementation | Derives and adds an executable acceptance test for every user-facing requirement through the real delivery entry point: runtime launch, isolated state, user-visible assertions, a known-bad fixture, a self-starting or gate-started runtime, run-time-supplied values rather than hardcoded examples, and wiring into the project test gate. It is a procedure skill, not a hook. | Vanilla Spec Kit has no step that derives an end-to-end test from the plan's entry point. Unit and static tests can stay green while the delivered interface is broken. |
| `speckit.requirements.diff-review` | `after_implement` | Commissions a fresh-context reviewer with the goal, the applicable checklists, the implementation diff, and the real entry-point or acceptance-test result; fix every finding and re-run until a clean pass before reporting done. | No independent review exists. The authoring agent reviews its own diff with its own context and reasoning, and a review that never runs the delivery interface can pass a broken product. |
| `speckit.requirements.remediation-loop` | `after_analyze` | Requires every analysis finding to be corrected, checks the other instances of the same defect class, and re-verifies on a fresh pass until clean. | Analyze reports findings but does not enforce remediation. One occurrence can be fixed while others remain. |

**The two templates**

- `spec-template`: adds the Requirements Coverage section (roadmap entry,
  Completes/Advances, FR-to-RQ table). Without it, a spec has no structured
  completion claim for the verifier to read.
- `tasks-template`: makes tests required per task and adds the
  acceptance-test shape for user-facing requirements (the real entry
  point, the user-visible outcome, a known-bad fixture, a self-starting or
  gate-started runtime, and run-time-supplied values rather than hardcoded
  examples).
  Without it, upstream treats test tasks as optional and leaves the
  delivered interface unexercised.

**The eight hook registrations**

`bootstrap.sh` installs the extension, and the installer writes these
registrations into `.specify/extensions.yml` from the manifest. The
commands do exist without the registrations, but they do not fire
automatically:

| Lifecycle event | Command |
| --- | --- |
| `before_plan` | `speckit.requirements.plan-checklist` |
| `before_tasks` | `speckit.requirements.tasks-checklist` |
| `before_implement` | `speckit.requirements.tasks-checklist` |
| `after_implement` | `speckit.requirements.diff-review` |
| `before_analyze` | `speckit.requirements.verify` |
| `after_analyze` | `speckit.requirements.remediation-loop` |
| `before_converge` | `speckit.requirements.verify` |
| `before_converge` | `speckit.requirements.tasks-checklist` |

All eight are registered with `optional: false`. A registration with
`enabled: false` or a non-empty condition is a silent no-fire, so
`make test` asserts these all fire as needed. The installer rebuilds
the hooks section from the manifest on reinstall; a manifest that loses its
hooks section silently wipes every registration. `make test` catches that
too.

**The six extension workflow gates**

When you run the bundled workflow (`specify workflow run speckit`) instead
of working skill by skill, the same checks appear as approve/reject gates:

| Gate | Runs after | Mirrors |
| --- | --- | --- |
| `review-coverage` | specify | `speckit.requirements.verify` before human sign-off |
| `review-plan-checklist` | plan | `speckit.requirements.plan-checklist` |
| `review-tasks` | tasks | `speckit.requirements.tasks-checklist` |
| `review-implement-checklist` | tasks, applied to implementation ahead | `speckit.requirements.tasks-checklist` |
| `review-diff` | implement | `speckit.requirements.diff-review` |
| `review-final-tree` | implement | Final tree against constitution, requirements, and acceptance criteria |

The bundled workflow has no analyze or converge step, so the
`before_analyze`, `after_analyze`, and `before_converge` hooks have no gate
counterpart and fire in skills mode only.

**What is not the extension**

- The **constitution** is installed by the bootstrap, not declared by the
  extension manifest.
- The **workflow gates** live in `.specify/workflows/overlays/speckit/`.
- The **mirror tests** are plain pytest files under `tests/`.
- The **core loop** is upstream Spec Kit. The extension adds context and
  enforcement around it; it does not replace specify, plan, tasks,
  implement, or converge.

## Why not a generic Spec Kit project?

The core loop works without this template. The extension is not required
for Spec Kit to function; it is required for the phased-delivery guarantees
this template promises.

| Generic Spec Kit | This template |
| --- | --- |
| Description prompts are the only feature input. | `REQUIREMENTS.md` is the product source above every feature. |
| Each feature is tracked alone. | `ROADMAP.md` maps every requirement to one Completes feature and any Advances. |
| The spec is the only truth. | Every Completes claim is checked for requirement content in the spec. |
| No claim freshness. | SHA-256 digests flag claims written against older requirement wording. |
| Test tasks are optional. | The tasks template and checklist require tests, including failure paths. |
| No independent implementation review. | A fresh-context diff review runs after implement. |
| Analyze findings are reported. | The remediation loop forces complete, class-wide corrections. |
| Enforcement is prose in agent instructions. | Hooks, workflow gates, and mirror tests enforce it. |

If you remove the extension, `/speckit.specify`, `/speckit.plan`,
`/speckit.tasks`, `/speckit.analyze`, `/speckit.implement`, and
`/speckit.converge` still run.
What disappears is the accounting layer: requirement IDs and a roadmap
remain prose, a spec can claim completion without transcribing the
requirement, stale claims stay green, test omissions survive, and nothing
commissions an independent review. The core loop is unchanged; the
guarantees are not free.

The verifier checks that claimed requirements are present; it does not
check that the spec contains only authorized scope. An FR with no product
requirement behind it is scope drift, not extra credit :-). The plan
checklist prompts the review to require authority for design opt-outs,
but the scope check itself is a human review step: confirm every FR
traces to a product requirement, and treat a capability absent from
`REQUIREMENTS.md` as a requirements change. An important point is that
clarify answers do not authorize new scope.

## User-facing requirements and the real entry point

A user-facing requirement is observed through the delivery interface the
product actually exposes. That interface may be an HTTP route, a CLI
command, a UI screen, a device action, a generated file, or something
else. The template does not assume a particular technology.

- The plan names the real entry point for every user-facing requirement.
- After tasks exist, invoke `/speckit.requirements.acceptance-test` (the
  hyphenated skill form `/speckit-requirements-acceptance-test` on agy or
  Copilot) to derive the executable acceptance tests. The command carries
  the procedure: real runtime, isolated state, user-visible assertions, a
  known-bad fixture, a self-starting or gate-started runtime,
  run-time-supplied values rather than hardcoded examples, and wiring into
  the test gate. It is a manual step, not a hook.
- The tasks include an executable acceptance test that drives that entry
  point on the real runtime and asserts the user-visible outcome and its
  known failure mode, with a known-bad fixture that proves the test fails.
- Unit tests of internal functions, static text assertions, and injected
  test doubles do not satisfy a user-facing requirement.
- A placeholder or empty/default implementation is a failure, even when
  the endpoint or command responds.
- If the entry point cannot be automated, the plan names the manual check
  and the acceptance record.

## Prerequisites

- the `specify` CLI (spec-kit 1.0.0 or later) and your coding agent
  installed,
- the uv Python package manager
  (`make install` creates the project virtual environment and installs
  the mirror-test dependencies),
- Bash 4+ for the extension scripts.

The Workshop sandbox is optional. If you use the Workshop development
environment described below, you also need LXD 6.8 or later and the
Workshop CLI (`sudo snap install --classic workshop`).

## Seed a project

```bash
mkdir myproject && cd myproject
git init
specify init --here --non-interactive --integration <your-harness-integration> --force
/path/to/this/template/bootstrap.sh "$(pwd)"
```

`<your-harness-integration>` is the integration key for your coding
agent: `specify integration list` shows every key (for example
`opencode`, `claude`, `copilot`, `gemini`, `cursor-agent`). One key is
installed at init; additional harness integrations can be added later
with `specify integration install`.

`bootstrap.sh` is this template's installer - it copies the extension,
gates, mirrors, and skeletons into the target. Skeleton files you have
customized are preserved; the extension tree, tests, Makefile,
requirements.txt, workflow overlay, helper scripts, opencode config, and
generated skills are machinery and are refreshed on every run. It calls
the extension's `generate-skills.sh`, which produces the agent-facing
skill copies of the extension's commands in `.github/skills/` and in
the integration's skill root when it uses `.agents/skills/` or
`.claude/skills/`.

After seeding, read `docs/start-a-project.md` for the authoring
walkthrough. It takes you from the product idea to the first roadmap row
and shows how to add later phases.

The bootstrap prints a fill-in checklist with the exact steps and
commands. In full:

1. `REQUIREMENTS.md` - your product scope. Start from
   `docs/REQUIREMENTS.md.example` and replace the placeholders.
2. `ROADMAP.md` - the feature table. Start from `docs/ROADMAP.md.example`;
   every requirement needs exactly one `Completes` owner.
3. `requirement-phrases.txt` - requirement phrases (verbatim wording from
   your REQUIREMENTS.md). It is a project artifact beside REQUIREMENTS.md,
   so editing it needs no extension reinstall.
4. The `@FILL-IN@` markers in `AGENTS.md` and `CONTRIBUTING.md`,
   including AGENTS.md's **Project checklist instances** (the
   project-specific instances the checklists point at).
5. `agent-instructions.md` - your definition-of-done commands.
6. `docs/implementation-mechanics.md` - the binding mechanics for your
   systems.
7. `.specify/memory/constitution.md` - Part 2 (your domain principles).
8. `extensions/requirements/extension.yml` - the repository URL.
9. `domain-terms.txt` - extend the deny list with your domain's terms.
   Keep the shipped `acme-storefront` placeholder and append your own,
   one per line. The file is a project artifact, so a bootstrap re-run
   keeps it; the scan guards your vocabulary once your terms are in.

### Author the first phase

After the bootstrap, read `docs/start-a-project.md`. In short:

1. copy `docs/REQUIREMENTS.md.example` to `REQUIREMENTS.md` and replace the
   placeholders with observable MUST requirements;
2. copy `docs/ROADMAP.md.example` to `ROADMAP.md`; give every requirement
   exactly one `Completes` owner and order the rows by dependency;
3. generate and review `requirement-phrases.txt`;
4. run `make test` and `/speckit.requirements.prepare R1` (hyphenated as
   `/speckit-requirements-prepare R1` on agy or Copilot).

The full sequence, including adding later phases, is in the guide.

`examples/` holds a minimal worked sample (requirements, roadmap, spec,
requirement phrases). Pass `--with-examples` to the bootstrap command to
install it.
The traceability tooling then verifies green immediately. The style and
enforcement gates stay red until you fill the skeletons and the AGENTS.md
checklist instances, which is the expected state of a freshly seeded
project.

## Workshop development environment

A new project gets a [Workshop](https://ubuntu.com/workshop) definition:
`.workshop/<name>.yaml`, named for the project by the bootstrap (the
tool keys its image cache by workshop name, so no two projects on one
machine share a name). It defines an `ubuntu@24.04` environment with the
`uv`, `opencode`, `copilot`, `agy`, `gh-cli`, and project `dev-tools` SDKs, the
`dev-tools` in-project SDK (its `setup-base` and `setup-project` hooks
install the system packages and mirror-test dependencies inside the workshop),
and `scripts/workshop.sh`, the host-side helper.

Start it from the project root:

```bash
scripts/workshop.sh
```

The script launches or refreshes the workshop. It does not mount host
agent configuration: each agent SDK persists its own config and
credentials in a workshop-owned mount, so sign in inside the workshop on
first use. That keeps host settings, skills, and credentials out of the
container. Inside the workshop
the project is mounted at `/project`, the setup hooks recreate the
project's `.venv` on every launch (a venv built inside one container must
not survive into the next), and the project's work runs sandboxed, isolated
from the host.
Project-specific system packages (a build tool the project needs, for
example) are added to the `setup-base` hook; re-running the bootstrap
preserves a customized `.workshop/` tree.

The definition also carries named actions (run them with
`workshop run -- <action>`; the tool infers the workshop from the
single definition):

```bash
workshop run -- test             # run the mirror-test suite (make test)
workshop run -- test-extension   # run the extension's Bash suite
workshop run -- install          # install the specify CLI, the project
                                  # venv, and the requirements extension
workshop run -- make <target>    # any Makefile target (generic passthrough)
workshop run -- opencode ...     # shell out to OpenCode
workshop run -- copilot ...      # shell out to Copilot
workshop run -- agy ...          # shell out to Antigravity
```

The named actions mirror the Makefile's public entry points: a new
target that defines done gains a matching action, and
`tests/test_workshop_actions.py` fails on drift in either direction
(an action naming a target that no longer exists; a public target with
no action). Targets deliberately left unnamed - sub-targets of an
aggregate, build artifacts - are recorded in the test's allowlist with
their reasons.

Inside the workshop the project is mounted at `/project`; `workshop shell`
opens an interactive shell in it, and the `uv` SDK's shared virtual
environment (which the setup hooks make the default `python3`) carries the
mirror-test dependencies.

## Conventions the tooling expects

These are the artifacts a new project expects. They are
domain-neutral: any product can be expressed in them. For a worked
authoring sequence, see `docs/start-a-project.md`.

**REQUIREMENTS.md** - bullet requirements, each with a stable,
section-scoped ID (`- **GREET-1**: ...`). IDs are never renumbered or
reused. Continuation lines are indented under the bullet.

**ROADMAP.md** - one row per feature, nine columns exactly:

| ID | Sub-feature | Intent | Scope boundary | Depends on | Status | Completes (RQ) | Advances (RQ) | Sub-spec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

*Completes* = the product fully satisfies these RQ (requirement) IDs
once this feature is `done`; each RQ is completed by exactly one feature.
*Advances* = foundational only; a later feature completes these - never
a completion claim. When a requirement is split, letter-suffixed
children are added beneath it (for example GREET-1, GREET-1a). This
table is the sole requirement-to-feature mapping.

**Specs** - each feature directory under `specs/NNN-name/` carries
spec.md, plan.md, tasks.md and friends. spec.md must include a
**Requirements Coverage** section with a `| FR | Realizes RQ | Relationship |`
mapping table (FR = the spec's functional-requirement ID); every
`Completes` row is verified by requirement-phrase content and a recorded
requirement digest.

**Requirement phrases** - one line per requirement ID in
`requirement-phrases.txt` at the project root: `ID|phrase|phrase|...`,
each phrase verbatim from that requirement's own REQUIREMENTS.md text.
It is a project artifact, deliberately outside the extension source tree,
so it survives extension reinstall and needs no reinstall after edits.
Because hand-curating phrases across dozens of requirements is tedious, you
can draft candidates and then tighten them:
- Run `bash scripts/extract-phrases.sh REQUIREMENTS.md -o requirement-phrases.txt`
  to emit one or two verbatim candidates per requirement ID from its MUST
  clause (it overwrites the target file).
- Or prompt your agent: *"Generate `requirement-phrases.txt` from
  `REQUIREMENTS.md`. For each bullet ID, extract 2-3 distinctive,
  verbatim phrases."*
Generated phrases are guaranteed verbatim (the script validates each one
before writing), but not guaranteed *distinctive*: a generic phrase such as
"list pets" verifies a claim without proving the requirement was transcribed.
Review the draft and prefer wording unique to each requirement. The verifier
hard-fails on any phrase that is not verbatim (so an agent cannot hallucinate
or mis-file phrases without failing the build), fails closed when a spec
claims an ID with no curated phrase, and the extension's Bash test suite
asserts every REQUIREMENTS ID has an entry.


**Requirement digests** - each spec's Requirements Coverage section
records `<ID> sha256:<digest>` for every requirement it completes,
where the digest is the SHA-256 over the requirement's normalized text
(trimmed, wrapped lines joined). The requirements brief emits the
current digests; a recorded digest that no longer matches the
requirement's wording fails the verifier as STALE, and a Completes
claim with no recorded digest fails as UNDIGESTED.

## Where enforcement fires

| Mode | What runs |
| --- | --- |
| `make test` (and CI) | Traceability verifier over every committed spec; the extension's Bash test suite; the style gate (the em-dash and marker rules); the installed extension matching the tracked source; the enforcement-chain mirror tests (hook registrations, checklist rules surviving into every mirror, domain neutrality of the seedable checklists, the AGENTS.md checklist-instances section - see below); the workshop-action sync test (the `.workshop/` definition's actions name real Makefile targets; every public target is exposed or allowlisted); the bootstrap-manifest coverage test (template tree only; it is not shipped to seeded projects, and checks that every shipped Python file under `tests/` has a copy line). The mirror tests gate on adoption: a project without the extension skips them; an adopting project missing an integral file fails. |
| Skills mode (generated `speckit-*` skills) | The hooks registered in `.specify/extensions.yml` inject the checklists before plan, tasks, implement, and converge; run the traceability verifier before analyze and converge; commission the independent diff review after implement; and enforce the analysis remediation loop after analyze. |
| Workflow mode (`specify workflow run speckit`) | The checks with gate counterparts fire as approve/reject gates in the bundled workflow; the analyze and converge hooks fire in skills mode only. |
| Acceptance | A human confirms every `Completes` claim (the roadmap's assertion that the feature fully delivers those requirements) has realizing implementation before the roadmap status flips to `done`. |

The project's `AGENTS.md` carries this map plus the
**Project checklist instances** section the checklists point at. Fill in
both records; the enforcement-chain test reads them directly and fails
while either record is empty. Only renaming the heading or the record
labels requires touching the test constants.

### The mirror tests (tests/)

Plain pytest modules that re-check the same claims the tooling makes,
so a bare checkout (fresh clone, CI) fails loudly without the agent
tooling installed. Each is adoption-gated: it skips with a stated
reason in a project that never adopted the extension, and fails in one
that adopted it with a broken chain.

- `tests/test_style.py` - the style gate: no em dashes in
  project-produced artifacts, and (once adopted) no unresolved
  `@FILL-IN@` markers.
- `tests/test_requirement_traceability.py` - drives the extension's
  Bash verifier under `make test`, checks every committed spec verifies
  clean, the installed extension matches the tracked source, the
  generated skills match their commands, and each spec's Completes set
  matches its roadmap row.
- `tests/test_enforcement_chain.py` - re-checks the enforcement chain
  itself: the hook registrations (with their enabled/optional shape),
  the skills surfacing them, template resolution, gate composition,
  checklist-rule incorporation into every mirror, domain neutrality of
  the seedable surfaces, and (in this template tree) that every manifest
  command, template, hook, and gate is documented in this README.
- `tests/test_workshop_actions.py` - re-checks the Workshop definition
  against the Makefile: every named action's make target exists, and
  every public Makefile target is exposed as an action or allowlisted
  with a reason.
- `tests/test_bootstrap_manifest.py` - checks the seed's own installer.
  Template-only: it is not copied into seeded projects. It verifies that
  every shipped Python file under `tests/` appears in `bootstrap.sh`'s
  copy manifest, and every manifested `tests/` path exists.

## Constitution parts

Part 1 (delivery principles) is universal and travels with the
tooling. Part 2 (project principles) is yours. Add one principle per
domain concern through the constitution command
(`/speckit.constitution` in OpenCode; `/speckit-constitution` on agy or
Copilot), which versions and records the amendment in the constitution.
After running it, check that
the two-part structure survived; the command resolves the stock
constitution template underneath. Part 1 stays domain-neutral (it names
no product, technology, or domain), so it travels unchanged; reviewing
your own artifacts against it keeps that boundary in practice.

This constitution is part of the seeded process, not a drop-in for a
vanilla `specify init` project: Part 1's principles reference the
requirements source, roadmap, and implementation mechanics, and the
enforcement comes from the extension and hooks the bootstrap installs.
For a vanilla project, use the core constitution command
(`/speckit.constitution` in OpenCode; `/speckit-constitution` on agy or
Copilot); for this template, run the bootstrap.

## What is optional

Two (opinionated) conventions ship wired in; both are removable:

- **The em-dash rule** (`tests/test_style.py`): no em dashes in
  project-produced artifacts. Remove the rule and the test if unwanted.
- **Tests-required tasks template**: the extension's tasks template
  requires tests (constitution principle 8, new code must have test
  coverage, makes it binding anyway); stock Spec Kit treats test tasks
  as optional.

## Maintaining this template

**Can-it-fail self-audit**: every check this template ships - test,
gate, or deny-list scan - must be able to fail. When you add or
strengthen one, verify it discriminates: temporarily break the surface
it guards (delete a hook registration, introduce a domain term, drop a
marker) and confirm `make test` fails with that check named, then
restore. A check that cannot be made to fail is a defect wearing a
guard's clothes; ship it with a known-bad fixture (test input that
must make the check fail) in the same change, or do not ship it.

Every file in this tree is authored and maintained here: the extension
(`extension/`, including its skill generator), the mirror tests
(`tests/`), the workflow gates (`review-gates.yml`), the constitution,
the skeletons, this README, `bootstrap.sh`, and `examples/`. When the
extension's commands or hooks change, keep the mirrors in sync in the
same change: the skills under `.github/skills/` and the harness-specific
`.agents/skills/` or `.claude/skills/` copies are generated copies of
the extension commands - the commands are the source of truth - so
regenerate them with the extension's `generate-skills.sh`, and the mirror
tests under `make test` fail on any drift between the commands, the
registrations, the gates, and the skills.

The seed's copy manifest in `bootstrap.sh` is mirrored the same way:
`tests/test_bootstrap_manifest.py` fails when a shipped Python file under
`tests/` is added without a matching copy line, or when a line names a
file that no longer exists. The mirror is template-only and is not shipped
to seeded projects. A new shipped mirror test needs its copy line, or the
gate goes red in this tree.
