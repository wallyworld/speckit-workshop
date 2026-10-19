# Pet Store Phased Delivery Example

This directory is the reference implementation for the phased-delivery
walkthrough in [05 - What's Next](../../05-whats-next.md). It holds the
product artifacts and the retrofit script; 05 is the step-by-step lab.

## How this maps to the workshop

- **Phase 1 (Backend API)**:
  - **R1** ([`CAT-1` through `CAT-4`](REQUIREMENTS.md)): completed in
    [03 - The Loop](../../03-the-loop.md).
  - **R2** ([`ORD-1` through `ORD-4`](REQUIREMENTS.md)): completed in
    [04 - The Refinement](../../04-the-refinement.md).
- **Phase 2 (Web UI)**:
  - **R3** ([`UI-1` through `UI-5`](REQUIREMENTS.md)): the follow-up
    feature slice you build after the workshop.

## The artifacts

### `REQUIREMENTS.md`

The product source. Each requirement has a stable ID, scoped to its
section, and is stated independently of any feature. Phase 1 covers the
catalog and order backend; Phase 2 covers the browser UI. Requirement IDs
are never renumbered or reused.

### `ROADMAP.md`

The delivery map. One row per feature, nine columns:

| ID | Sub-feature | Intent | Scope boundary | Depends on | Status | Completes (RQ) | Advances (RQ) | Sub-spec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

`R1` and `R2` are `done`; `R3` is `planned`. The `Completes` column is the
sole requirement-to-feature mapping: each requirement is completed by
exactly one feature. A feature that only lays groundwork records the
requirement under `Advances` and never marks it done.

The `Sub-spec` link names the actual spec directory. Slugs are generated
from the agent's prompt and vary between runs; the retrofit script
reconciles the link with the directory that exists.

### `requirement-phrases.txt`

Curated, distinctive phrases copied verbatim from each requirement. The
verifier requires at least one phrase per Completes claim to appear in the
spec body. The file is a **project artifact** beside `REQUIREMENTS.md`,
not part of the extension source tree, so editing it needs no extension
reinstall.

The verifier hard-fails on a phrase that is not verbatim wording of its
requirement. To generate candidates:

```bash
bash extensions/requirements/scripts/bash/extract-phrases.sh REQUIREMENTS.md -o requirement-phrases.txt
```

Generated candidates are guaranteed verbatim but not guaranteed
distinctive. Review them and prefer wording unique to each requirement.

### `retrofit-petstore.py`

The retrofit helper used by 05. It is state-driven and idempotent:

```bash
python3 /project/examples/petstore/retrofit-petstore.py ~/petstore
```

It auto-installs the extension and mirror-test dependencies when needed,
fills every `@FILL-IN@` marker, appends the sample's domain terms to
`domain-terms.txt`, patches pre-bootstrap specs with Requirements Coverage
and canonical requirement wording, reconciles roadmap links, adds a
`test-app` target, replaces em dashes in project-produced files, and runs
the verifier and `make test`.
It reports every change; review the FR-to-RQ coverage tables it produces.
A `REVIEW` line marks a zero-score provisional mapping.

## Retrofit in brief

[05 - What's Next](../../05-whats-next.md) is the full walkthrough. The sequence is:

```bash
cd ~/petstore
cp /project/examples/petstore/REQUIREMENTS.md .
cp /project/examples/petstore/ROADMAP.md .
cp /project/examples/petstore/requirement-phrases.txt .

/project/new-project-template/bootstrap.sh ~/petstore
python3 /project/examples/petstore/retrofit-petstore.py ~/petstore
make test
```

The bootstrap installs the requirements extension and its hooks. The
script patches the Phase 1 specs, which predate the extension and therefore
have no Requirements Coverage section. `make test` runs the mirror suite
and the application tests.

If the bootstrap could not run `specify`, register the extension yourself:

```bash
cd ~/petstore
specify extension add --dev --force extensions/requirements
```

The hook registrations in `.specify/extensions.yml` are what make the
extension commands fire automatically. The file is written from the
extension manifest at install time.

## Building Phase 2: slice `R3` (Web UI)

Start a new agent session. The loop is unchanged; the extension adds
context and enforcement at each stage.

Command forms:

- Core commands use OpenCode's dot form: `/speckit.specify`.
- Extension commands are skills, hyphenated: `/speckit-requirements-prepare`.
- With agy or Copilot, core commands are hyphenated too: `/speckit-specify`.

### 1. Prepare

```text
/speckit-requirements-prepare R3
```

The command emits a read-only brief with the roadmap intent, scope
boundary, canonical text for `UI-1..UI-5`, per-requirement digests, and a
ready-to-run specify command. Review it before running it.

### 2. Specify

Run the emitted command, for example:

```text
/speckit.specify Implement slice R3 from ROADMAP.md: an interactive
browser frontend served by FastAPI that renders the catalog, creates pets,
places orders, and cancels orders.
```

The extension-provided spec template requires a Requirements Coverage
section. The agent drafts `specs/003-<slug>/spec.md` with `UI-1..UI-5`.

### 3. Clarify (optional)

```text
/speckit.clarify
```

Address design questions such as styling or component layout.

### 4. Plan

```text
/speckit.plan
```

The `before_plan` hook injects the plan checklist. The architecture
constraints are already in `REQUIREMENTS.md` (`UI-5`: served by FastAPI,
no external frontend build pipeline or node runtime) and the existing
backend is in `petstore_app.py`; the agent reads both.

### 5. Tasks

```text
/speckit.tasks
```

The `before_tasks` hook injects the tasks checklist, and the tasks
template makes tests required.

### 6. Analyze

```text
/speckit.analyze
```

`before_analyze` runs the requirement verifier; `after_analyze` runs the
remediation loop if findings exist.

### 7. Implement

```text
/speckit.implement
```

`before_implement` applies the tasks checklist to the code and tests being
written. `after_implement` commissions an independent, fresh-context
review of the diff; fix findings and re-run until clean.

### 8. Converge

```text
/speckit.converge
```

`before_converge` runs the requirement verifier and tasks checklist.
Converge refuses to report the feature converged while a claimed
requirement is missing, stale, or unimplemented.

If converge appends tasks, review them, re-run implement, then converge
again.

### 9. Close the roadmap

Update `ROADMAP.md` row `R3`:

- change `Status` from `planned` to `done`;
- set `Sub-spec` to your generated `specs/003-...` directory.

Then verify and run the gate:

```bash
bash extensions/requirements/scripts/bash/verify-traceability.sh specs/003-*/spec.md
make test
```

Only mark the row done when the spec content, fresh digest, and code all
support the claim.

## Testing the Web UI

Start the FastAPI application:

```bash
uv run uvicorn petstore_app:app --reload --host 0.0.0.0
```

From your host browser, open the workshop address from `workshop info`
(for example `http://speckit-ws.speckit-workshop.wp:8000/`).

You can:

- view the catalog with availability badges (`UI-1`);
- add pets and see the list refresh (`UI-2`);
- place orders and watch stock decrement, with order buttons disabled at
  zero (`UI-3`);
- view open orders and cancel them to restore inventory (`UI-4`).

## If something fails

- `No module named pytest` or `yaml`: run `make install`.
- `test_hook_registrations_present` fails: run
  `specify extension add --dev --force extensions/requirements`.
- No `| FR-### | RQ... | Completes |` rows: the spec predates the
  extension; run the retrofit script.
- `phrases file not found`: ensure `requirement-phrases.txt` is at the
  project root, or run the retrofit script.
- `DRIFTED` or `STALE`: update the spec content and digests through the
  prepare brief, or regenerate and review the phrases.
- Em dash style failure: use a hyphen. The retrofit script replaces em
  dashes in project-produced files only. If an em dash was in
  `REQUIREMENTS.md`, review or regenerate `requirement-phrases.txt` and
  re-run the verifier.

The full per-command explanation and the comparison with a vanilla Spec
Kit project are in the
[template README](../../new-project-template/README.md#the-requirements-extension-piece-by-piece).
