# Pet Store Phased Delivery Example

This directory is the reference implementation for the phased-delivery
walkthrough in [05 - What's Next](../../05-whats-next.md). It holds the
product artifacts and the retrofit script; 05 is the step-by-step lab.

For a new multi-phase project, start with the template's
[new-project guide](../../new-project-template/docs/start-a-project.md).
This directory is the finished reference, not a starter.

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

The `Sub-spec` link names the actual spec directory for a delivered row.
Planned rows use `-` until the spec exists. Slugs are generated from the
agent's prompt and vary between runs; the retrofit script reconciles a link
with the directory that exists.

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
python3 /project/examples/petstore/retrofit-petstore.py /project/petstore
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
cd /project/petstore
cp /project/examples/petstore/REQUIREMENTS.md .
cp /project/examples/petstore/ROADMAP.md .
cp /project/examples/petstore/requirement-phrases.txt .

/project/new-project-template/bootstrap.sh /project/petstore
python3 /project/examples/petstore/retrofit-petstore.py /project/petstore
make test
```

The bootstrap installs the requirements extension and its hooks. The
script patches the Phase 1 specs, which predate the extension and therefore
have no Requirements Coverage section. `make test` runs the mirror suite
and the application tests.

If the bootstrap could not run `specify`, register the extension yourself:

```bash
cd /project/petstore
specify extension add --dev --force extensions/requirements
```

The hook registrations in `.specify/extensions.yml` are what make the
extension commands fire automatically. The file is written from the
extension manifest at install time.

## Building Phase 2: slice `R3` (Web UI)

### R3 delivery contract for this project

| Item | Required for this project |
| --- | --- |
| Entry route | `/` |
| Hash routes | `#/catalog`, `#/orders`, `#/create-pet` |
| Authentication | none: no login, roles, passwords, sessions, or credentials |
| Active orders | `GET /orders?status=open`; cancel with `DELETE /orders/{id}` |
| Implementation | static HTML/CSS/JS served by FastAPI; no node runtime or build |
| Placeholders | none; the orders page must use the real API |
| Acceptance | the generated acceptance test is the gate; the manual host-browser pass verifies the visible outcomes |

Note: a different product may expose a CLI, API, device, or generated file.

Start a new agent session. The loop is unchanged; the extension adds
context and enforcement at each stage.

Command forms:

- OpenCode slash commands use the dot form for core and extension commands:
  `/speckit.specify`, `/speckit.requirements.prepare`.
- With agy or Copilot, use the hyphenated skill form for both:
  `/speckit-specify`, `/speckit-requirements-prepare`.

### 1. Prepare

```text
/speckit.requirements.prepare R3
```

The command emits a read-only brief with the roadmap intent, scope
boundary, canonical text for `UI-1..UI-5`, per-requirement digests, and a
ready-to-run specify command. Review the brief now, but do not run its
command yet: step 2 runs it once.

### 2. Specify (once)

Before running anything, check `specs/` for an existing R3 spec. If one
exists, do not run specify again; keep the first R3 spec (normally
`003-*`) and continue with clarify, plan, and tasks on it. If you have
both `003-*` and `004-*`, the troubleshooting entry in 05 covers removing
the duplicate.

If no R3 spec exists, run the exact command the brief emitted. For this
sample's `R3` row it is:

```text
/speckit.specify Interactive browser frontend connecting catalog and orders. Scope boundary: Client frontend served by FastAPI; uses existing R1/R2 API; no external frontend build tools.
```

Run it **exactly once**. Do not also run a second specify from this page
or from the brief: each invocation creates a new numbered directory, so
`R3` would end up with both `003-*` and `004-*`.

Note: if the container clipboard does not work, you do not need to copy the
emitted command. Reply `run the emitted core command`; the agent has the
brief in context. See
[06 - Reference](../../06-reference.md#clipboard-inside-the-container)
for terminal copy alternatives.

The extension-provided spec template requires a Requirements Coverage
section. On a fresh run, the agent drafts `specs/003-<slug>/spec.md` with
`UI-1..UI-5`.

### 3. Clarify (optional)

```text
/speckit.clarify
```

Address design questions such as styling or component layout. If clarify
asks who may create pets or how users log in, do not add auth: UI-1..UI-5
do not require it. Answer "any user; authentication is out of scope," or
remove the question from the spec.

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
template makes tests required, including the acceptance-test task.

### 6. Install the browser and write the acceptance test

The acceptance test drives the real browser. The base container does not
include Chrome because the earlier phases do not need it. Install it once
from a host terminal in your clone:

```bash
workshop run --uid 0 -- install-browser
```

Back in the container, install the driver in the project environment:

```bash
cd /project/petstore
uv pip install pytest-playwright
```

Do not run `playwright install`: the test uses the container Chrome with
`channel="chrome"` (or `--browser-channel=chrome`) and the launch flags
`--no-sandbox --disable-dev-shm-usage`.

After tasks and before implementation, invoke the manual command:

```text
/speckit.requirements.acceptance-test R3
```

It derives the executable test from the spec, plan, and real entry point,
adds isolated state and a known-bad fixture, and wires it into `make test`.
Review the generated test: it must load `/`, `#/catalog`, `#/create-pet`,
and `#/orders` in the real browser, fail on console/page errors, assert every
`UI-1..UI-5` outcome, include the fast contract checks (no auth/session
surface, no placeholder implementation, real `GET /orders`, stock restore),
and run under `make test`. Run it before implementation and confirm it
fails for the expected reason. It is the automated acceptance gate.

### 7. Analyze

```text
/speckit.analyze
```

`before_analyze` runs the requirement verifier; `after_analyze` runs the
remediation loop if findings exist.

### 8. Implement

```text
/speckit.implement
```

`before_implement` applies the tasks checklist to the code and tests being
written. `after_implement` commissions an independent, fresh-context
review of the diff; fix findings and re-run until clean.

### 9. Converge

```text
/speckit.converge
```

`before_converge` runs the requirement verifier and tasks checklist.
Converge refuses to report the feature converged while a claimed
requirement is missing, stale, or unimplemented.

If converge appends tasks, review them, re-run implement, then converge
again.

### 10. Close the roadmap

Run the acceptance gate first:

```bash
bash extensions/requirements/scripts/bash/verify-traceability.sh specs/003-*/spec.md
make test
```

If you kept a differently numbered R3 directory, substitute its path in
the verifier command.

After the generated test and the manual
host-browser pass succeed, update `ROADMAP.md` row `R3`:

- change `Status` from `planned` to `done`;
- set `Sub-spec` to your kept R3 directory (normally `specs/003-...`).

Only mark the row done when the spec content, fresh digest, and code all
support the claim.

## Testing the Web UI

From `/project/petstore`, first run the generated acceptance test through the
project gate:

```bash
cd /project/petstore
make test
```

Prove it can fail by breaking one UI behavior, running `make test`, and
restoring the code. The browser install and `pytest-playwright` dependency
from [section 6](#6-install-the-browser-and-write-the-acceptance-test) are
prerequisites.

Then start the FastAPI application:

```bash
cd /project/petstore
uv run uvicorn petstore_app:app --reload --host 0.0.0.0
```

From your host browser, open the workshop address from `workshop info`
(for example `http://speckit-ws.speckit-workshop.wp:8000/`) at `/`, the R3
contract's entry route.

You can:

- view the catalog with pet names, stock counts, and availability badges
  that change with availability (`UI-1`);
- add pets through the form, see client-side validation block invalid
  input, and watch the catalog refresh immediately (`UI-2`);
- place orders and watch stock decrement, with order buttons visually
  disabled at zero (`UI-3`);
- view open orders and cancel them to restore inventory in place (`UI-4`);
- confirm the UI is a static single-page app served by FastAPI, with no
  node runtime or external build (`UI-5`).

Open DevTools Console and confirm it is free of red errors on `/`,
`#/catalog`, `#/create-pet`, and `#/orders`.

## If something fails

- `No module named pytest` or `yaml`: run `make install`.
- `No module named playwright`: install the driver in the project venv:
  `uv pip install pytest-playwright`.
- `google-chrome: command not found`: run
  `workshop run --uid 0 -- install-browser` from a host terminal in your
  clone.
- Playwright `Executable doesn't exist` or tries to download a browser:
  use the container Chrome with `channel="chrome"` (or
  `--browser-channel=chrome`); do not run `playwright install`.
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
[template README](../../new-project-template/README.md#the-requirements-extension).
