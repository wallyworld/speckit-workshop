# 05 - What's Next: Phased Delivery, Step by Step

You have run the core loop twice: the pet catalog in
[03](03-the-loop.md) and order placement in [04](04-the-refinement.md).
That is the right way to learn Spec Kit. This page adds the **phased
delivery** layer on top of the same loop: a product-level requirements
source, a roadmap, per-feature completion claims, and tooling that checks
those claims instead of trusting them.

You will do this against the petstore you built in `~/petstore`:

1. copy the product artifacts into your project;
2. install the phased-delivery tooling;
3. retrofit the two specs you authored before the tooling existed;
4. inspect the retrofit;
5. build the Phase 2 Web UI (`R3`) through the loop, with the extension
   commands and hooks firing at each stage;
6. run the Web UI and try it in your browser;
7. verify the completion claims and close the roadmap.

> **Starting a new project?** This page retrofits the finished petstore
> sample. For a blank multi-phase project, use
> [the new-project guide](new-project-template/docs/start-a-project.md)
> (copied into a seeded project as `docs/start-a-project.md`) and the
> starter files in `docs/`. Step 1 below copies worked sample artifacts,
> not a template for your own product.

Command forms used below:

- **Core commands** use OpenCode's dot form: `/speckit.specify`.
- **Extension commands** are skills, so they use the hyphenated form:
  `/speckit-requirements-prepare`. The dot form
  (`/speckit.requirements.prepare`) is also installed by the extension.
- With agy or Copilot, use the hyphenated form for core commands too:
  `/speckit-specify`.

## The four-part model

1. **A requirements source.** `REQUIREMENTS.md` states every product
   requirement once, with a stable ID (`CAT-1`, `ORD-3`, `UI-5`),
   independently of any feature.
2. **A delivery roadmap.** `ROADMAP.md` maps every requirement to the one
   feature that **Completes** it (or an earlier feature that **Advances**
   it), with a status per row.
3. **Per-feature claims.** Each feature spec declares which requirements
   it completes and which it only advances.
4. **A verification step.** A requirement is only `done` when its wording
   is present in the spec, its recorded digest still matches the current
   wording, and the code realizes it.

The core loop is unchanged. Analyze is a core Spec Kit step, as in the
earlier hands-on loops; the extension makes its checks mandatory through
the `before_analyze` and `after_analyze` hooks. The extension puts an
accounting layer in front of the loop.

## What the requirements extension adds

The phased delivery template ships **one** extension package, `requirements`. It contains
seven commands, two template overrides, and eight mandatory hooks. The full
per-command explanation, including what each command prevents versus a
vanilla Spec Kit project, is in the template README section
[The requirements extension, piece by piece](new-project-template/README.md#the-requirements-extension-piece-by-piece).

| Loop stage | What fires |
| --- | --- |
| before specify | `/speckit-requirements-prepare R#` builds a reviewed brief with canonical requirement text and digests |
| plan | `before_plan`: plan checklist |
| tasks | `before_tasks`: tasks checklist, tests required |
| after tasks | `/speckit-requirements-acceptance-test` (manual): derive the executable acceptance test |
| analyze | `before_analyze`: requirement verifier; `after_analyze`: remediation loop |
| implement | `before_implement`: tasks checklist applied to code being written; `after_implement`: independent diff review |
| converge | `before_converge`: requirement verifier and tasks checklist |

The extension is optional for Spec Kit itself. It is necessary for the
guarantees we are describing: without it, `REQUIREMENTS.md` and `ROADMAP.md` are
prose, a spec can claim an ID without containing its content, tests can be
omitted, and no independent review runs.

## Step 1: Copy the product artifacts

Inside the workshop container:

```bash
cd ~/petstore
cp /project/examples/petstore/REQUIREMENTS.md .
cp /project/examples/petstore/ROADMAP.md .
cp /project/examples/petstore/requirement-phrases.txt .
```

These are the completed petstore artifacts. For your own project, use
[the new-project guide](new-project-template/docs/start-a-project.md) and
the starter files; do not copy these sample files as your product.

What you copied:

- `REQUIREMENTS.md` groups Phase 1 (catalog `CAT-1..CAT-4`, orders
  `ORD-1..ORD-4`) and Phase 2 (web UI `UI-1..UI-5`).
- `ROADMAP.md` maps those requirements to `R1` (catalog), `R2` (orders),
  and `R3` (web UI). `R1` and `R2` are `done`; `R3` is `planned`.
- `requirement-phrases.txt` holds distinctive, verbatim phrases from each
  requirement. It is a **project artifact** beside `REQUIREMENTS.md`, not
  part of the extension.

Read the two Markdown files before continuing. The roadmap row for `R3`
is the work you will do.

## Step 2: Bootstrap the tooling

```bash
/project/new-project-template/bootstrap.sh ~/petstore
```

**About the closing checklist.** The message is generic for any fresh
project. In this workshop path you do not run `make install` or fill in
the `@FILL-IN@` markers yourself: Step 3's retrofit script runs
`make install` when the project virtual environment or the mirror-test
dependencies are missing, and fills every marker.

The bootstrap installs the requirements extension and its hooks, the spec
and tasks templates, the workflow review gates, the constitution skeleton,
the mirror tests, the `AGENTS.md` and `CONTRIBUTING.md` skeletons, and the
`Makefile`. It then runs `specify extension add --dev --force
extensions/requirements`, which writes the hook registrations into
`.specify/extensions.yml`.

Confirm the CLI sees the registered extension (a file existing is not
enough):

```bash
specify extension info requirements
```

On success it prints the extension, its commands, and its hooks; if the
install did not run, it exits non-zero with `not found`. The raw hook
registrations are in `.specify/extensions.yml` if you want to inspect them:

```bash
grep -n "requirements" .specify/extensions.yml
```

If the bootstrap could not run `specify` (CLI not found), it still copies
the extension source. Register it yourself:

```bash
cd ~/petstore
specify extension add --dev --force extensions/requirements
```

**Constitution caveat.** Your `~/petstore` has the workshop constitution
you ratified in [01](01-setup.md#14-ratify-the-project-constitution).
`bootstrap.sh` never overwrites a customized constitution, so it keeps
yours. The template's two-part constitution is therefore not installed.
That is fine for this exercise. If you want the two-part version, move
`.specify/memory/constitution.md` aside before the bootstrap and re-run;
if you want to combine them, merge only the workshop principles not
already covered by the template's Part 1 into its Part 2.

## Step 3: Retrofit the pre-bootstrap specs

Your `001-*` and `002-*` specs were authored before the extension existed.
They have no Requirements Coverage section and do not contain the curated
requirement phrases, so the traceability verifier would fail closed. The
retrofit script fixes that and fills the skeleton markers:

```bash
python3 /project/examples/petstore/retrofit-petstore.py ~/petstore
```

The script is idempotent and reports every change. In order, it:

- registers the extension if `.specify/extensions.yml` is missing;
- seeds or migrates `requirement-phrases.txt`;
- runs `make install`, which creates the project virtual environment and
  installs the mirror-test dependencies, if `pytest` or `yaml` is missing;
- fills every `@FILL-IN@` marker with petstore values;
- appends `petstore` and `pet-catalog` to `domain-terms.txt` while keeping
  the shipped placeholder;
- reconciles the `ROADMAP.md` Sub-spec links with the real `specs/`
  directories;
- adds Requirements Coverage to every spec that needs it, using the
  extension's `assemble-brief.sh` for the roadmap entry, Completes/Advances
  IDs, and requirement digests, and transcribes the canonical requirement
  wording into the matching FR;
- adds a `test-app` target so `make test` runs the application tests as
  well as the mirror suite;
- replaces em dashes in project-produced files;
- runs the traceability verifier and `make test`, and reports the result.

Review the report and the coverage tables. Every FR-to-RQ row is chosen by
keyword overlap, so confirm the mapping; a `REVIEW` line marks a zero-score
provisional assignment. The verifier is the gate; the mapping is a
human-review aid.

Then run the gate yourself:

```bash
make test
```

A clean run means the style gate, traceability verifier, extension Bash
suite, enforcement-chain mirrors, workshop-action sync, and application
tests all pass.

## Step 4: Inspect the retrofit

Open `specs/001-<slug>/spec.md` and `specs/002-<slug>/spec.md`. Each now has
a **Requirements Coverage** section with:

- the roadmap entry (`R1` or `R2`);
- the Completes/Advances IDs from the roadmap row;
- the requirement digests;
- the FR-to-RQ mapping table.

Run the verifier directly to see the per-requirement verdicts:

```bash
bash extensions/requirements/scripts/bash/verify-traceability.sh
```

You should see `OK - every claimed-complete requirement has distinctive
content in its spec.`

Open `.specify/extensions.yml`: the eight mandatory hooks are registered
with `optional: false`. The commands exist without these registrations,
but they do not fire automatically. This file is what makes the hooks run.

### R3 delivery contract for this sample

The workshop's petstore is a web product, so its real entry point is a web
page. A different project might expose a CLI, API, device, or generated file;
the generic rule is the same: acceptance is exercised through the real entry
point, not only through internal functions.

| Item | Required for this sample |
| --- | --- |
| Entry route | `/` |
| Hash routes | `#/catalog`, `#/orders`, `#/create-pet` |
| Authentication | none: no login, roles, passwords, sessions, or credentials |
| Active orders | `GET /orders?status=open`; cancel with `DELETE /orders/{id}` |
| Implementation | static HTML/CSS/JS served by FastAPI; no node runtime or build |
| Placeholders | none; the orders page must use the real API |
| Acceptance | the generated acceptance test is the gate; the manual host-browser pass verifies the visible outcomes |

## Step 5: Build Phase 2 (`R3`) through the phased loop

The Web UI slice is `R3` in `ROADMAP.md`. Start a new agent session so the
Phase 1 context does not crowd the new feature.

### 5.1 Prepare the brief

```text
/speckit-requirements-prepare R3
```

The command validates that `R3` exists, that its predecessors are `done`,
and that its Completes/Advances IDs exist in `REQUIREMENTS.md`. It prints
a read-only brief with the roadmap intent, scope boundary, canonical
requirement text for `UI-1..UI-5`, per-requirement digests, and a
ready-to-run core specify command. Review it before running it.

**If your container cannot copy text:** you do not need to copy the
emitted command. After reviewing the brief, reply `run the emitted core
command` (or `run the emitted /speckit-specify command`). The agent has
the brief in the same session and can run it for you. That reply is your
approval; the review still happens before it runs.

### 5.2 Specify

Run the emitted command, for example:

```text
/speckit.specify Implement slice R3 from ROADMAP.md: an interactive
browser frontend served by FastAPI that renders the catalog, creates pets,
places orders, and cancels orders. Serve it at `/`. Do not add
authentication, login, roles, sessions, or any capability not listed in
REQUIREMENTS.md. Implement active orders against a real GET /orders
endpoint, not placeholder data. Include tests that exercise the real page.
```

The agent reads `ROADMAP.md` and `REQUIREMENTS.md` and drafts
`specs/003-<slug>/spec.md`. The extension-provided spec template requires
a Requirements Coverage section; the spec must contain `UI-1..UI-5` and
map its FRs to them.

**Pass condition**: the spec states the `UI-1..UI-5` requirements, and its
coverage table claims `R3` with the correct Completes set.

### 5.3 Clarify, plan, tasks

```text
/speckit.clarify
/speckit.plan
/speckit.tasks
```

> **Scope check.** Clarify resolves ambiguity in the spec; it does not
> authorize new scope. If it asks about a capability absent from
> `REQUIREMENTS.md` and `ROADMAP.md` (for example authentication or roles),
> stop. Either remove the capability from the spec or add it as a product
> requirement first. The answer to "who can create pets?" is "any user;
> authentication is out of scope."

At `plan`, the `before_plan` hook injects the plan checklist: every FR
traces to a product requirement, every user-facing requirement names its
real entry point and acceptance test, design opt-outs must cite requirement
wording, thresholds need operational definitions, every MUST needs a task,
and boundaries must be specified. At `tasks`, the `before_tasks` hook
injects the tasks checklist: tests come first, every user-facing
requirement has an acceptance test through the real entry point, IDs are
sequential, and failure paths are covered. The tasks template makes tests
required.

**Pass condition**: `plan.md` and `tasks.md` exist, the plan's Constitution
Check ran, the plan names the real entry point (`/`), and the tasks include
an acceptance-test task.

### 5.4 Install the browser and write the acceptance test (manual skill)

The acceptance test drives the real browser. The base container does not
include Chrome because the earlier phases do not need it. Install it once
now, from a host terminal in your clone (not inside the container):

```bash
workshop run --uid 0 -- install-browser
```

The action installs Chrome and checks that it launches headless as the
`workshop` user. It takes a few minutes and adds roughly 700 MB to the
container, which is why the base image leaves it out. Back in the container,
confirm it:

```bash
google-chrome --version
```

Install the browser driver in the project environment:

```bash
cd ~/petstore
uv pip install pytest-playwright
```

Do not run `playwright install`: the generated test uses the container's
Chrome with `channel="chrome"` (or `--browser-channel=chrome`) and the
launch flags `--no-sandbox --disable-dev-shm-usage`.

After `tasks.md` exists and before implementation, invoke:

```text
/speckit-requirements-acceptance-test R3
```

The skill reads the spec, plan, quickstart, and build/test entry points,
then derives the executable acceptance test through the real entry point. It
is a manual step, not a hook. It writes the test test-first, adds isolated
state and a known-bad fixture, and wires it into `make test`.

Review the generated test before accepting it:

- it starts the real runtime and drives the real entry point;
- it loads `/`, `#/catalog`, `#/create-pet`, and `#/orders` in the real
  browser and fails on console or page errors;
- it asserts every `UI-1..UI-5` outcome, not just HTTP status or static text;
- it uses a temporary database/state and cleans up;
- it includes fast contract checks: no auth/session surface, no placeholder
  implementation, a real `GET /orders`, and stock restore on cancel;
- it has a known-bad fixture and can be made to fail;
- it runs under `make test`.

Run it now: it should fail because the feature is not implemented yet. A
test that only imports modules, checks a status, or asserts static text is
not an acceptance test.

The test you generate is the single automated acceptance gate for R3. In a
new project the same skill derives the equivalent test from that project's
real entry point.

### 5.5 Analyze

```text
/speckit.analyze
```

This is the same core analyze step you ran in the earlier loops; the
extension makes it a gate. `before_analyze` runs the requirement verifier,
so any drift or stale digest appears in the analysis report. If analysis
reports findings, `after_analyze` runs the remediation loop: correct every
instance of the same claim or defect class, then re-verify on a fresh pass.

### 5.6 Implement

```text
/speckit.implement
```

`before_implement` applies the tasks checklist to the code and tests being
written, not only the task text. The agent writes the HTML/JS/CSS, wires
the FastAPI static route or index handler, and runs the tests.

`after_implement` commissions an independent, fresh-context review of the
implementation diff. The reviewer gets only the goal, the applicable
checklists, and the diff. For this web feature, the review must also run the
real entry point or acceptance test; a review that only reads the diff is
incomplete. Fix every finding and re-run until clean before reporting the
work done.

### 5.7 Converge

```text
/speckit.converge
```

`before_converge` runs the requirement verifier and the tasks checklist
again. Converge re-reads the spec and compares the code to it. It refuses
to call the feature converged while a claimed requirement is missing from
the spec, stale, or unimplemented.

If converge appends missing work to `tasks.md`, review the appended task,
re-run implement, then converge again.

A converged API is not a converged web page. Before proceeding, the
acceptance gate in Step 6 must pass: the generated acceptance test and the
manual page checks.

## Step 6: Run the acceptance gate and see the Web UI live

From `~/petstore`, first run the generated acceptance test through the
project gate:

```bash
cd ~/petstore
make test
```

Then prove it can fail: break one UI requirement (for example remove the
shared state binding, return a placeholder order list, or change the API
path), run `make test`, confirm the generated acceptance test fails, and
restore the code.

That failure is the automated gate. The manual pass below is the human
check of the same outcomes in a real host browser; it does not replace the
generated test.

Then start the app from `~/petstore` in a second byobu
window (F2, or the tmux prefix Ctrl-b c) or a separate terminal inside
the container:

```bash
cd ~/petstore
uv run uvicorn petstore_app:app --reload --host 0.0.0.0
```

Leave it running while you try the UI. Stop it with Ctrl-C when done.

Open a browser **on your host**. Your host cannot reach the container's
`127.0.0.1`; run `workshop info` from your clone directory and use the
`hostname:` line. For a clone named `speckit-workshop` that is:

```
http://speckit-ws.speckit-workshop.wp:8000/
```

The R3 contract for this sample is the root path (`/`), so open that.
If the implementation leaves `/docs` routed, it remains available for the
JSON API.

Try each requirement:

- **Catalog (`UI-1`)**: the page lists each pet's name, current stock count,
  and a distinct availability badge; the badge changes with availability.
- **Create (`UI-2`)**: submit the form with invalid input and confirm
  client-side validation blocks the request; on success the catalog updates
  immediately. No login is required.
- **Order (`UI-3`)**: a pet at zero stock has a visually disabled order
  action. Place an order for an in-stock pet and watch stock decrement by
  one.
- **Orders (`UI-4`)**: the active orders list shows the order; cancel it
  and watch both the order list and the catalog stock update in place.
- **Serving (`UI-5`)**: the UI is a static single-page application served
  directly by FastAPI, with no node runtime or external frontend build and
  no full-page reload for in-app actions.

If the page does not load, check that the server bound to `0.0.0.0`, that
you used the `workshop info` hostname rather than `127.0.0.1`, and that the
implementation serves `/`. Open DevTools Console and confirm it is free of
red errors on `/`, `#/catalog`, `#/create-pet`, and `#/orders`. If `/docs`
is still routed, it confirms the API side independently.

**Why API-only tests miss this.** A test suite can pass while the browser is
broken: uncaught JavaScript errors, a shared state object that is not
exposed, an API path prefix that does not match the backend, or placeholder
code that returns an empty list. For a UI feature, the generated acceptance
test must load each route in a real browser, fail on console errors, and
exercise every UI requirement; keep fast contract tests (API paths, no
placeholder markers, real `GET /orders`) as an additional gate. This R3
pass is the cautionary example: the original auth/login scope was added
without a product requirement, the `window.appState` binding and `/api`
prefix broke the page, and UI-4 was a placeholder while the API tests
stayed green.

## Step 7: Verify and close the loop

Confirm the generated acceptance test passed and was shown to fail under a
mutation in Step 6. Confirm the manual browser pass in Step 6 succeeded. If
either fails, do not mark the roadmap row done.

Confirm the `R3` spec verifies clean:

```bash
bash extensions/requirements/scripts/bash/verify-traceability.sh ~/petstore/specs/003-*/spec.md
```

Then update `ROADMAP.md` row `R3`:

- change `Status` from `planned` to `done`;
- set the `Sub-spec` link to your generated `specs/003-...` directory.

Finally run the full gate and review the working tree from `~/petstore`:

```bash
make test
git diff
```

The roadmap row is a claim. Only mark it `done` when the spec content, the
fresh digest, and the code all support it.

## Troubleshooting

- **`make test` says `No module named pytest` or `yaml`**: run
  `make install`. The fixed install target always installs the
  requirements, even if a venv already exists.
- **`No module named playwright`**: install the browser driver in the
  project venv: `uv pip install pytest-playwright`.
- **`test_hook_registrations_present` fails**: `.specify/extensions.yml`
  is missing or was wiped. Run
  `specify extension add --dev --force extensions/requirements`.
- **`no '| FR-### | RQ... | Completes |' rows found`**: the spec predates
  the extension. Run the retrofit script.
- **`phrases file not found`**: copy `requirement-phrases.txt` to the
  project root, or run the retrofit script to seed it.
- **`stale phrase` or `DRIFTED`**: the requirement wording changed after
  the phrase or digest was recorded. Regenerate candidates with
  `extensions/requirements/scripts/bash/extract-phrases.sh REQUIREMENTS.md -o requirement-phrases.txt`,
  review them, and update the spec text and digests through the brief.
- **Em dash style failure**: use a hyphen. The retrofit script replaces em
  dashes in project-produced files, but not in upstream or runtime
  surfaces. If an em dash was in `REQUIREMENTS.md`, the curated phrase may
  no longer be verbatim; review or regenerate `requirement-phrases.txt`
  and re-run the verifier.
- **Constitution looks different after bootstrap**: the bootstrap keeps a
  customized constitution. If you want the template's two-part version,
  move the file aside and re-run.
- **`window.appState` is undefined or the catalog says "Failed to load"**:
  the page modules share state through `window.appState`; fix the shared
  state rather than adding a fallback in each module.
- **Login page or `/auth` 404s**: authentication is out of scope. Remove the
  login route, auth module, session middleware, and credentials; do not try
  to guess a username and password.
- **Orders page says the feature would need an endpoint**: UI-4 is not
  implemented. Add `GET /orders?status=open` and wire the real list and
  cancel actions; placeholder text is a failure.
- **Repeated 500s after the first request**: the SQLite connection must be
  usable across FastAPI's worker threads; use `check_same_thread=False` or a
  per-request connection.
- **`/api` returns 404**: the backend routes are root-relative. Remove the
  `/api` prefix from the frontend client.
- **The acceptance-test skill is not available**: rerun
  `bootstrap.sh` or `generate-skills.sh` and reinstall the extension; the
  skill is generated from
  `extensions/requirements/commands/speckit.requirements.acceptance-test.md`.
- **`google-chrome: command not found`**: install it on demand from a host
  terminal in your clone:
  `workshop run --uid 0 -- install-browser`.
- **`Executable doesn't exist` or Playwright tries to download a browser**:
  use the container Chrome, not a bundled browser. Launch with
  `channel="chrome"` (or `--browser-channel=chrome`) and do not run
  `playwright install`.
- **`Running as root without --no-sandbox is not supported`** or Chrome
  crashes on a small `/dev/shm`: add `--no-sandbox` and
  `--disable-dev-shm-usage` to the launch args.
- **The generated test passes but the page is broken**: the test is too
  weak. Require it to start the real runtime, drive the real entry point,
  assert each UI requirement, and fail under a deliberate mutation.
- **The generated test is missing from `make test`**: wire it into the
  project test gate, not a separate manual script.

## Extensions, presets, and bundles

- **Extensions** add commands, templates, and hooks; they are installed
  with `specify extension add` and registered in `.specify/extensions.yml`.
  Upstream ships opt-in extensions (`bug`, `assess`), and a community
  catalog exists. The requirements extension is this template's reference
  example.
- **Presets** are packaged file overrides selected at `specify init`; they
  add no commands or hooks.
- **Bundles** are versioned stacks of extensions, presets, and workflows,
  installed with `specify bundle install`.

The vanilla project from the workshop is the bare default. This page added
one extension and its enforcement layer; it did not change the loop.

## Reading list

- The [spec-kit README](https://github.com/github/spec-kit) (install
  instructions, preset/bundle reference, extension API).
- The template README's
  [requirements extension section](new-project-template/README.md#the-requirements-extension-piece-by-piece)
  and the [template conventions](new-project-template/README.md#conventions-the-tooling-expects).
- The core `/speckit.constitution` command and the
  [`new-project-template/constitution.md`](new-project-template/constitution.md)
  two-part model.
- The [community extension catalog](https://github.github.io/spec-kit/community/extensions.html).
