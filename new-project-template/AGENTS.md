# AGENTS.md

Guidance for AI agents working in this repository.

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
- Follow the existing style of the file you are editing; make minimal
  changes.

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
  enforcement-chain mirror tests (hook registrations, checklist rules surviving
  into every mirror, domain neutrality of the seedable checklists, the
  project checklist instances below), and the workshop-action sync test
  (the `.workshop/` definition's actions name real Makefile targets;
  every public Makefile target is exposed as an action or allowlisted
  with a reason).
- Skills mode: the hooks registered in `.specify/extensions.yml` inject
  the checklists before plan and tasks, run the traceability
  verifier before analyze and converge, and enforce the analysis
  remediation loop after analyze.
- Workflow mode (`specify workflow run speckit`): the same checks fire as
  the review gates in the workflow overlay.
- Acceptance: a human confirms every `Completes` claim (a roadmap row's
  assertion that the feature fully delivers a requirement) has
  realizing implementation before the roadmap status flips to `done`.

## Agent workflow discipline

1. **Inspect the working tree before planning or reviewing.** Run `git
   status`, `git diff`, and `git log --oneline -5`, and read files from
   disk (not from memory or earlier turns) before proposing or critiquing
   changes: sessions often contain uncommitted or newly-committed work.
   Every factual claim in a handoff plan carries a `file:line` or commit
   citation, or is marked unverified.
2. **Never infer exit codes through a pipeline.** A pipe such as
   `cmd | tail` masks the real exit status; use `set -euo pipefail` or
   capture the return code explicitly (for example `${PIPESTATUS[0]}`).
3. **Prefer upstream extension points over forking.** Extend speckit via the
   installed extension (`extensions/requirements/`), hooks in
   `.specify/extensions.yml`, and workflow overlays under
   `.specify/workflows/overlays/`. Inspect what exists before editing
   vendored skills in `.github/skills/`; the requirements skills are
   generated from the extension commands - regenerate them with the
   extension's `generate-skills.sh` instead of hand-editing.
4. **Verify implementation completeness before claiming delivery.** A
   `Completes` claim implies both spec content and a real code path;
   confirm the code path exists before transcribing or reviewing so a
   roadmap is never marked `done` while over-claiming unbuilt work.
5. **Make enforcement as strong as it claims.** If a gate or check is meant
   to prevent something, wire it into `make test` or a mandatory hook -
   not only an advisory prompt.
6. **Author tests and fixtures as if written with the original suite.** Use
   generic, property-based names and state the invariant the test verifies,
   not the regression that motivated it.
7. **Know your harness's subagent semantics.** If your tool's subagents
   return only summaries (their tool output is not surfaced to the caller),
   run read-only deterministic commands directly in the parent session so
   the verbatim output returns; reserve subagents for work where a summary
   is acceptable.
8. **Verify owned state after a mutating tool runs, and commit standing-claim
   checks as tests.** After an installer, upgrader, or generator mutates
   project state, diff the files it owns before the step is done; a
   standing claim belongs in `make test`, not as a one-off session check.

When a defect escapes, add or strengthen the rule at the layer that fires -
a test first, then a mandatory hook, then a workflow gate - not as further
prose in this file.

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
