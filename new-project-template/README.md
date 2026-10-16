# Spec Kit Process Template

Seeds a new project with a requirements-first Spec Kit process - the
product's requirements and a roadmap steer delivery across many
features - plus the tooling that enforces the process. One command
installs everything; a short fill-in pass makes it project specific.

## Orientation

Spec Kit is a spec-driven development toolkit: an agent runs slash
commands that turn a feature description into a written spec, plan, and
task list, implements them, and converges the code back against the
spec. That command sequence is the loop:

```
specify -> clarify -> plan -> tasks -> implement -> converge
  ^                                                       |
  +-------------------------------------------------------+
```

Spec Kit's model is one feature at a time: each feature goes through the
loop on its own, and the workflow keeps no picture of the product the
features add up to. A product delivered as multiple features needs an
accounting layer in front of the loop - **phased delivery**: the
product's requirements are stated once, each with a stable ID, in a
single source (`REQUIREMENTS.md`); a roadmap (`ROADMAP.md`) maps every
requirement to the one feature that completes it, in delivery order;
and each requirement carries requirement phrases - distinctive wording
copied verbatim from its own text - so a spec claiming to complete the
requirement can be checked for actually containing its content.

Out of the box, using default upstream Spec Kit, each command is a
prompt: nothing verifies that the artifacts it produces cover what they
claim, and nothing connects a feature to the product plan. This project
template addresses that limitation; it adopts the phased-delivery model
above and adds an enforcement layer to check it, in four ways:

- **deterministic checkers** - Bash scripts over the artifacts, chiefly
  the requirement traceability verifier, run by the project's test
  suite;
- **moment-of-authoring hooks** - mandatory checklists injected around
  Spec Kit's own commands at the exact moment the artifact is written;
- **workflow gates** - the same checks composed into Spec Kit's bundled
  workflow (the command sequence `specify workflow run` executes) as
  approve/reject gates;
- **mirror tests** - plain pytest modules re-checking the same claims,
  so the repository's own suite fails on drift even in a bare checkout
  (a fresh clone, or CI) where the agent tooling is absent.

Each mirror test asserts one standing claim - a hook
registration, a rule's incorporation into every surface - so removing or
breaking it fails `make test`.

The principle behind the layering: an agent obeys prose unreliably,
but it cannot skip a gate. A rule that can be a test must not stay
prose; a rule no test can decide belongs in a hook injected at the
moment of authoring; a process-bound check becomes a workflow gate;
prose is the last resort.

An **extension** is Spec Kit's packaging for all of this: a manifest
declaring commands, templates, and hooks, plus the scripts the commands
run. **Skills** are the agent-facing copies of the extension commands,
generated into `.github/skills/`.

## Where this fits in the Spec Kit ecosystem

Spec Kit's core is deliberately per-feature; for work too large for one
loop cycle it documents a manual roadmap convention - the "spec of
specs" ([concepts/spec-of-specs](https://github.github.io/spec-kit/concepts/spec-of-specs.html)):
a roadmap table with stable IDs, dependencies, and links, with no
tooling behind it and status maintained by hand. This template does
what that convention asks for, plus the parts it does not have: a
product-level requirements source above the roadmap, explicit
completion semantics per roadmap row (Completes/Advances against
requirement IDs), and deterministic verification of those claims. Each
Completes claim is checked two ways, because the two checks catch
different escapes:

- **requirement phrase** - distinctive wording copied verbatim from the
  requirement, anchored at load time (a phrase that is not verbatim
  source wording fails the build). It proves the requirement's content
  is present in the spec; an ID in a table proves nothing.
- **requirement digest** - a SHA-256 over the requirement's normalized
  text, recorded in the spec when the claim is written. It proves the
  claim is fresh: if the requirement's wording later changes, the
  recorded digest no longer matches and the spec is flagged stale.

Presence and freshness: one catches a claim whose content was never
specified; the other, a claim written against wording that has since
changed.

## What lands in the seeded project

The seeded project runs on the phased-delivery convention:
`REQUIREMENTS.md` as the single requirements source, `ROADMAP.md` as the
requirement-to-feature map, and requirement phrases tying each completion
claim to requirement content (the Conventions section below has the
exact formats). On top of that convention, the seed installs:

- a **two-part constitution** (universal delivery principles + your domain
  principles),
- a **requirements extension** that turns a roadmap row into a
  self-contained brief and verifies every requirement a spec claims to
  complete is materially present in that spec and recorded against the
  requirement's current wording,
- **enforcement hooks** that fire automatically around Spec Kit's
  own commands (plan, tasks, analyze, converge),
- **review gates** mirroring the same checks as approve/reject steps in
  Spec Kit's bundled workflow,
- **extension-provided templates** (the spec template gains a
  Requirements Coverage section; the tasks template requires tests),
- **mirror tests** - plain pytest modules re-checking the same claims:
  style gate, traceability verifier, spec-to-roadmap alignment,
  enforcement-chain integrity,
- **a tool-agnostic wiring chain** so every coding agent reaches the
  same guidance (`agent-instructions.md`, `.github/copilot-instructions.md`,
  `.opencode/opencode.json`).

## Prerequisites

- the `specify` CLI (spec-kit 1.0.0 or later) and your coding agent
  installed,
- LXD 6.8 or later and the Workshop CLI
  (`sudo snap install --classic workshop`),
- the uv Python package manager
  (`make install` creates the project virtual environment and installs
  the mirror-test dependencies),
- Bash 4+ for the extension scripts.

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
gates, mirrors, and skeletons into the target, never overwriting
content you have customized - and it calls the extension's
`generate-skills.sh`, which produces the agent-facing skill copies of
the extension's commands.

The bootstrap prints a fill-in checklist with the exact steps and
commands. In full:

1. `REQUIREMENTS.md` - your product scope.
2. `ROADMAP.md` - the feature table.
3. `extensions/requirements/data/phrases.txt` - requirement phrases (verbatim
   wording from your REQUIREMENTS.md), then reinstall the extension.
4. The `@FILL-IN@` markers in `AGENTS.md` and `CONTRIBUTING.md`,
   including AGENTS.md's **Project checklist instances** (the
   project-specific instances the checklists point at).
5. `agent-instructions.md` - your definition-of-done commands.
6. `docs/implementation-mechanics.md` - the binding mechanics for your
   systems.
7. `.specify/memory/constitution.md` - Part 2 (your domain principles).
8. `extensions/requirements/extension.yml` - the repository URL.
9. Extend the domain-term deny list in `tests/test_enforcement_chain.py`
   with your domain's terms; the shipped entry is a demonstrative
   placeholder, and the scan guards your vocabulary once your terms are
   in.

`examples/` holds a minimal worked sample (requirements, roadmap, spec,
phrases). Pass `--with-examples` to the bootstrap command to install it.
The traceability tooling then verifies green immediately; the
no-unfilled-markers gate (a test that fails while any `@FILL-IN@` marker
remains) stays red until you fill the skeletons, which is the expected
state of a freshly seeded project.

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

The script launches or refreshes the workshop and mounts this
machine's agent configuration (`~/.copilot`, `~/.config/opencode`,
`~/.local/share/opencode`, `~/.gemini`) into it, so agents inside the workshop share
your credentials. Inside the workshop the project is mounted at
`/project`, the setup hooks recreate the project's `.venv` on every
launch (a venv built inside one container must not survive into the
next), and the project's work runs sandboxed, isolated from the host.
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
domain-neutral: any product can be expressed in them.

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
`extensions/requirements/data/phrases.txt`: `ID|phrase|phrase|...`,
each phrase verbatim from that requirement's own REQUIREMENTS.md text.
Because hand-curating phrases across dozens of requirements is tedious, you
can draft candidates and then tighten them:
- Run `bash extensions/requirements/scripts/bash/extract-phrases.sh REQUIREMENTS.md -o extensions/requirements/data/phrases.txt`
  to emit one or two verbatim candidates per requirement ID from its MUST
  clause (it overwrites the target file).
- Or prompt your agent: *"Generate `extensions/requirements/data/phrases.txt`
  from `REQUIREMENTS.md`. For each bullet ID, extract 2-3 distinctive,
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
| `make test` (and CI) | Traceability verifier over every committed spec; the extension's Bash test suite; the style gate (the em-dash and marker rules); the installed extension matching the tracked source; the enforcement-chain mirror tests (hook registrations, checklist rules surviving into every mirror, domain neutrality of the seedable checklists, the AGENTS.md checklist-instances section - see below); the workshop-action sync test (the `.workshop/` definition's actions name real Makefile targets; every public target is exposed or allowlisted); the bootstrap-manifest coverage test (every Python file under `tests/` ships in the seed's copy manifest). The mirror tests gate on adoption: a project without the extension skips them; an adopting project missing an integral file fails. The manifest test is tree-gated: it fires here and skips in a seeded project. |
| Skills mode (`/speckit-*` commands) | The hooks registered in `.specify/extensions.yml` inject the checklists before plan, tasks, and converge, run the traceability verifier before analyze and converge, and enforce the analysis remediation loop after analyze. |
| Workflow mode (`specify workflow run speckit`) | The same checks fire as approve/reject gates in the bundled workflow. |
| Acceptance | A human confirms every `Completes` claim (the roadmap's assertion that the feature fully delivers those requirements) has realizing implementation before the roadmap status flips to `done`. |

The project's `AGENTS.md` carries this map plus the
**Project checklist instances** section the checklists point at.
When you fill that section in, update the matching markers in
`tests/test_enforcement_chain.py` together with it - the test fails
until both the section and the checklists' pointers to it exist.

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
  checklist-rule incorporation into every mirror, and domain neutrality of
  the seedable surfaces.
- `tests/test_workshop_actions.py` - re-checks the Workshop definition
  against the Makefile: every named action's make target exists, and
  every public Makefile target is exposed as an action or allowlisted
  with a reason.
- `tests/test_bootstrap_manifest.py` - checks the seed's own installer:
  every Python file under `tests/` appears in `bootstrap.sh`'s copy
  manifest, and every manifested `tests/` path exists. Tree-gated: it
  fires in this template tree and skips in a seeded project (which
  carries no `bootstrap.sh`).

## Constitution parts

Part 1 (delivery principles) is universal and travels with the
tooling. Part 2 (project principles) is yours. Add one principle per
domain concern through `/speckit-constitution`, which versions and
records the amendment in the constitution. Part 1 stays
domain-neutral (it names no product, technology, or domain), so it
travels unchanged; reviewing your own artifacts against it keeps that
boundary in practice.

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
same change: the skills under `.github/skills/` are generated copies of
the extension commands - the commands are the source of truth - so
regenerate them with the extension's `generate-skills.sh`, and the mirror
tests under `make test` fail on any drift between the commands, the
registrations, the gates, and the skills.

The seed's copy manifest in `bootstrap.sh` is mirrored the same way:
`tests/test_bootstrap_manifest.py` fails when a Python file under
`tests/` is added without a matching copy line, or when a line names a
file that no longer exists. A new mirror test ships with its copy line
or the gate goes red in this tree.
