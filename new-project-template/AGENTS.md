# AGENTS.md

Guidance for AI agents working in this repository. This file carries
project invariants and the enforcement map; universal discipline lives in
the per-user global instruction file and on-demand skills, not here.

## Project

@FILL-IN@ One or two paragraphs: what this project is, its layout (the
main source directories), and where the product scope and delivery plan
live.

## Style rules (enforced by tests)

- **No em dashes (U+2014) in project-produced artifacts.** Use a hyphen
  instead. Upstream Spec Kit content (stock scripts and base templates, the
  bundled workflow, the vendored skill tree, dot-form command scaffolds) may
  contain them. `tests/test_style.py` scans everything the project produces -
  including `specs/`, the `requirements` extension, the constitution, the
  hooks and gates, and the template overrides - and excludes only the
  upstream surfaces and runtime output (`artifacts/`). This applies to code,
  comments, docstrings, docs, YAML, and shell scripts, and to the output of
  project tooling that seeds artifacts (for example the requirements brief).
  This rule is a house convention: remove it and the matching exclusion
  logic in `tests/test_style.py` if your project does not want it.

## Verification

@FILL-IN@ The commands that define done (for example make targets), the
canonical environment they must run in, and any tooling gotchas. State
which invocation is the single definition of done.

## Commitments

- Requirement IDs in `REQUIREMENTS.md` are never renumbered or reused; the
  requirement-to-feature mapping lives only in `ROADMAP.md`.
- Recorded artifacts and run records must never contain credentials or
  sensitive values. @FILL-IN@ name your project's protected data classes.

## Where enforcement fires

- `make test` (and CI running the same): the traceability verifier over
  every committed spec, the extension bash suite, the style gate, the
  enforcement-chain mirror tests (hook registrations with their full firing
  shape, checklist rules surviving into every mirror, the manifest
  descriptions' firing surfaces matching the hook registrations, domain
  neutrality of the seedable checklists, the project checklist instances
  below), and the workshop-action sync test
  (the `.workshop/` definition's actions name real Makefile targets;
  every public Makefile target is exposed as an action or allowlisted
  with a reason).
- Skills mode: the hooks registered in `.specify/extensions.yml` inject
  the checklists before plan, tasks, implement, and converge, run the
  traceability verifier before analyze and converge, commission an
  independent fresh-context diff review after implement, and enforce the
  analysis remediation loop after analyze.
- Workflow mode (`specify workflow run speckit`): the coverage,
  plan-checklist, tasks, implement-checklist, diff-review, and final-tree
  checks fire as review gates in the workflow overlay. The bundled workflow has no analyze or converge step,
  so the `before_analyze`, `after_analyze`, and `before_converge` hooks have
  no gate counterpart and fire in skills mode only.
- Acceptance: a human confirms every `Completes` claim (a roadmap row's
  assertion that the feature fully delivers a requirement) has
  realizing implementation before the roadmap status flips to `done`.

## Agent workflow discipline

1. **Prefer upstream extension points over forking.** Extend speckit via the
   installed extension (`extensions/requirements/`), hooks in
   `.specify/extensions.yml`, and workflow overlays under
   `.specify/workflows/overlays/`. Inspect what exists before editing
   vendored skills in `.github/skills/`; the requirements skills are
   generated from the extension commands - regenerate them with the
   extension's `generate-skills.sh` instead of hand-editing.
2. **Verify implementation completeness before claiming delivery.** A
   `Completes` claim implies both spec content and a real code path;
   confirm the code path exists before transcribing or reviewing so a
   roadmap is never marked `done` while over-claiming unbuilt work.
3. **Agentic requirement phrases generation.** When setting up or modifying
   requirements in `REQUIREMENTS.md`, the phrases table
   (`extensions/requirements/data/phrases.txt`) must be updated. Generate
   verbatim candidates with
   `extensions/requirements/scripts/bash/extract-phrases.sh REQUIREMENTS.md -o extensions/requirements/data/phrases.txt`
   then review and tighten them before committing: the script guarantees
   verbatim wording, not distinctiveness, and it overwrites the target file.
   Prefer wording unique to each requirement (a generic phrase lets a spec
   satisfy a claim without transcribing the requirement). Always run
   `bash extensions/requirements/scripts/bash/verify-traceability.sh` (or `make test`)
   to verify that every phrase is an exact verbatim match of the requirement text.


## Project checklist instances

The checklists in the requirements extension name universal
rules; these are this project's recorded instances (the checklists point
here). Fill them in; the no-unfilled-markers test enforces it.

- Command surfaces: @FILL-IN@ your project's command entry points (for
  example a CLI's subcommands), tested on their real invocation path - the
  default or primary route - not only a flagged or synthetic variant.
- Coverage-critical artifact kinds: @FILL-IN@ the artifact kinds new code
  must cover with tests (for example functions, configurable behaviour,
  validators, and query or report surfaces).
