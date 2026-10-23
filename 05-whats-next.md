# 05 - What's Next: Phased Delivery

You've run the core loop twice: the pet catalog in
[03](03-the-loop.md) and order placement in [04](04-the-refinement.md).
This page adds the **phased delivery** layer: a product-level requirements
source, a roadmap, per-feature completion claims, and tooling that checks
those claims instead of trusting them.

You'll do this against the petstore you built in `/project/petstore`: copy the
artifacts, bootstrap the extension, retrofit the Phase 1 specs, then build
`R3` and try it in a browser.

> **Starting a new project?** This page retrofits the finished petstore.
> For a blank multi-phase project, use
> [the new-project guide](new-project-template/docs/start-a-project.md)
> (seeded as `docs/start-a-project.md`) and the starter files in `docs/`.
> Note: step 1 below copies samples written for the pet store project
> rather than a template that has to be filled in.

- **OpenCode slash commands** use the dot form for both core and extension
  commands: `/speckit.specify`, `/speckit.requirements.prepare`. The
  extension's hyphenated names are generated skills; OpenCode loads them
  through its skill tool, not its `/` menu.
- **With agy or Copilot**, use the hyphenated skill form for both:
  `/speckit-specify`, `/speckit-requirements-prepare`.

## The four-part model

1. **A requirements source.** `REQUIREMENTS.md` states every product
   requirement once, with a stable ID (`CAT-1`, `ORD-3`, `UI-5`),
   independently of any feature.
2. **A delivery roadmap.** `ROADMAP.md` maps every requirement to the one
   feature that **Completes** it (or an earlier feature that **Advances**
   it), with a status per row.
3. **Per-feature claims.** Each feature spec declares which requirements
   it completes and which it only advances.
4. **A verification step.** A requirement is `done` only when its wording
   is in the spec, its recorded digest matches, and the code realizes it.

The loop is unchanged. Analyze stays a core step; `before_analyze` and
`after_analyze` make the extension's checks mandatory.

## What the requirements extension adds

The template ships **one** extension package, `requirements`: seven
commands, two template overrides, eight mandatory hooks. The per-command
explanation is in [The requirements extension](new-project-template/README.md#the-requirements-extension).

| Loop stage | What fires |
| --- | --- |
| before specify | `/speckit.requirements.prepare R#` builds a reviewed brief with canonical requirement text and digests |
| plan | `before_plan`: plan checklist |
| tasks | `before_tasks`: tasks checklist, tests required |
| after tasks | `/speckit.requirements.acceptance-test` (manual): derive the executable acceptance test |
| analyze | `before_analyze`: requirement verifier; `after_analyze`: remediation loop |
| implement | `before_implement`: tasks checklist applied to code being written; `after_implement`: independent diff review |
| converge | `before_converge`: requirement verifier and tasks checklist |

Without it, `REQUIREMENTS.md` and `ROADMAP.md` are prose: a spec can
claim an ID without its content, tests can be omitted, and no independent
review runs.

## Step 1: Copy the product artifacts

Inside the workshop container:

```bash
cd /project/petstore
cp /project/examples/petstore/REQUIREMENTS.md .
cp /project/examples/petstore/ROADMAP.md .
cp /project/examples/petstore/requirement-phrases.txt .
```

Note: for you own project, use [the new-project guide](new-project-template/docs/start-a-project.md)
and the starter files; don't copy these samples.

`REQUIREMENTS.md` groups Phase 1 (catalog `CAT-1..CAT-4`, orders
`ORD-1..ORD-4`) and Phase 2 (web UI `UI-1..UI-6`). `ROADMAP.md` maps those
to `R1` (catalog), `R2` (orders), and `R3` (web UI): `R1` and `R2` are
`done`, `R3` is `planned`. `requirement-phrases.txt` holds verbatim
phrases from each requirement. It's a **project artifact** beside
`REQUIREMENTS.md`, not part of the extension.

Read both files; the `R3` row is the work.

## Step 2: Bootstrap the tooling

```bash
/project/new-project-template/bootstrap.sh /project/petstore
```

The bootstrap generates the extension's agent-facing skills inside
`/project/petstore`: `.github/skills/` for OpenCode and Copilot, and
`.agents/skills/` for agy (it writes there when the agy integration
created that root). Because `/project` is the host-backed clone mount, the
same files are visible at `<clone>/petstore` on the host.

Leave the manual `make install` and `@FILL-IN@` markers to Step 3's
retrofit: it runs `make install` if the venv or mirror-test dependencies
are missing, and fills every marker.

The bootstrap installs the extension, hooks, templates, review gates,
constitution skeleton, mirror tests, `AGENTS.md`, `CONTRIBUTING.md`, and
`Makefile`. It then runs
`specify extension add --dev --force extensions/requirements`, which
writes the registrations into `.specify/extensions.yml`.

Check that the CLI sees the registration, not only the file:

```bash
specify extension info requirements
```

On success it prints the extension, its commands, and `✓ Installed`; a
local install also prints `Not found in catalog (custom/local extension)`.
If the extension is not installed, it exits non-zero with `not found`. The
raw hook registrations are in `.specify/extensions.yml` if you want to inspect them:

```bash
grep -n "requirements" .specify/extensions.yml
```

If the bootstrap couldn't run `specify` (`command not found: specify`), it
still copies the extension source. Register it yourself:

```bash
cd /project/petstore
specify extension add --dev --force extensions/requirements
```

**Constitution caveat.** Your `/project/petstore` has the workshop constitution
you ratified in [01](01-setup.md#14-ratify-the-project-constitution).
`bootstrap.sh` never overwrites a customized constitution, so it keeps
yours. The template's two-part constitution is therefore not installed.
That is fine for this exercise. If you want the two-part version, move
`.specify/memory/constitution.md` aside before the bootstrap and re-run;
if you want to combine them, merge only the workshop principles not
already covered by the template's Part 1 into its Part 2.

## Step 3: Retrofit the pre-bootstrap specs

Your `001-*` and `002-*` specs predate the extension: no Requirements
Coverage, no curated phrases, so the verifier fails closed. The retrofit
fills the markers:

```bash
python3 /project/examples/petstore/retrofit-petstore.py /project/petstore
```

The script is idempotent. It registers the extension, seeds
`requirement-phrases.txt`, runs `make install` if needed, fills every
`@FILL-IN@` marker, appends `petstore` and `pet-catalog` to
`domain-terms.txt`, and reconciles `ROADMAP.md` links with `specs/`. It
adds Requirements Coverage to each spec: the roadmap entry,
Completes/Advances IDs, and digests from the extension's
`assemble-brief.sh`, plus the canonical wording in the matching FR. It
also adds a `test-app` target and includes it in `make test`, replaces em
dashes in project files, and runs the verifier and `make test`.

Review the report and coverage tables. FR-to-RQ rows come from keyword
overlap, so confirm the mapping. A `REVIEW` line marks a zero-score
provisional assignment; the verifier is the gate, the mapping is a review
aid.

To perform the verification:

```bash
make test
```

A clean run passes the style gate, traceability verifier, extension Bash
suite, enforcement-chain mirrors, workshop-action sync, and application
tests. (The bootstrap-manifest mirror runs only in the template tree,
where `bootstrap.sh` exists; seeded projects have no such test.)

## Step 4: Inspect the retrofit

Open `specs/001-<slug>/spec.md` and `specs/002-<slug>/spec.md`. Each has a
**Requirements Coverage** section with the roadmap entry (`R1` or `R2`),
the Completes/Advances IDs, the requirement digests, and the FR-to-RQ
mapping table.

The verifier:

```bash
bash extensions/requirements/scripts/bash/verify-traceability.sh
```

The last line should read
`OK - every claimed-complete requirement has distinctive content in its spec.`

The eight hooks are registered with `optional: false` in
`.specify/extensions.yml`. Without those registrations the commands exist
but don't fire.

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
| API prefix | the prefix chosen in the R1/R2 plan (empty for root routes); the reference run uses `/api/v1` |
| Active orders | `GET {prefix}/orders?status=open`; cancel via the R1/R2 route (`DELETE {prefix}/orders/{id}` or `POST {prefix}/orders/{id}/cancel`) |
| Implementation | static HTML/CSS/JS served by FastAPI; no node runtime or build |
| API calls | same-origin relative paths under `{prefix}`; no hardcoded host or port |
| Placeholders | none; the orders page must use the real API |
| Acceptance | the generated acceptance test is the gate; the manual host-browser pass verifies the visible outcomes |

`{prefix}` is the API prefix your R1/R2 plan chose; read it from the R1/R2
quickstart or `/docs`. The reference run uses `/api/v1`. Substitute your own
prefix everywhere below.

## Step 5: Build Phase 2 (`R3`) through the phased loop

The Web UI slice is `R3` in `ROADMAP.md`. Start a new agent session so
the Phase 1 context doesn't crowd the new feature.

### 5.1 Prepare the brief

```text
/speckit.requirements.prepare R3
```

The command validates that `R3` exists, its predecessors are `done`, and
its Completes/Advances IDs exist in `REQUIREMENTS.md`. It prints a
read-only brief: roadmap intent, scope boundary, canonical requirement text
for `UI-1..UI-6`, digests, and a ready-to-run specify command. Review the
brief now, but do not run its command yet: step 5.2 runs it once.

### 5.2 Specify (once)

Before running anything, check `specs/` for an existing R3 spec. If one
exists, do not run specify again; keep the first R3 spec (normally
`003-*`) and continue with clarify, plan, and tasks on it. If you have
both `003-*` and `004-*`, the troubleshooting entry below covers removing
the duplicate.

If no R3 spec exists, run the exact command the brief emitted. For this
sample's `R3` row it will be something like:

```text
/speckit.specify Interactive browser frontend connecting catalog and orders. Scope boundary: Client frontend served by FastAPI; uses existing R1/R2 API via same-origin relative paths; no hardcoded host or port; no external frontend build tools.
```

Run it **exactly once**. Do not also run a second specify from this page,
from the brief, or from anywhere else: each invocation creates a new
numbered directory, so `R3` would end up with both `003-*` and `004-*`.

**If your container can't copy text:** reply `run the emitted core
command`. The agent has the brief in the same session. That reply is your
approval; the review still happens first.

On a fresh run, the agent reads `ROADMAP.md` and `REQUIREMENTS.md` and
drafts `specs/003-<slug>/spec.md`. The spec template requires Requirements
Coverage; the spec must contain `UI-1..UI-6` and map its FRs to them. It
passes when it states `UI-1..UI-6`, contains a curated phrase from each
claimed-complete requirement, records a matching digest for each, and
claims `R3` with the correct Completes set.

### 5.3 Clarify, plan, tasks

```text
/speckit.clarify
/speckit.plan
/speckit.tasks
```

> **Note.** Clarify resolves ambiguity; it should not authorize new
> scope. If it asks about a capability absent from `REQUIREMENTS.md` and
> `ROADMAP.md` (eg authentication, roles), stop. Remove the capability from
> the spec or add it as a product requirement first. The answer to "who can
> create pets?" is "any user; authentication is out of scope."
> I found that the above happened when I was doing a dry run so am flagging
> it here.

At `plan`, `before_plan` injects the plan checklist: FR-to-requirement
traceability, real entry point and acceptance test for user-facing
requirements, opt-out citations, operational thresholds, a task for every
MUST, explicit boundaries, and no example value becoming an implementation
constant (a same-origin UI uses relative API paths). At `tasks`,
`before_tasks` injects the tasks checklist: tests first, an acceptance test
through the real entry point that starts the runtime and uses a non-example
origin for a same-origin UI, sequential IDs, failure paths. The tasks
template makes tests required.

The plan must reuse the Phase 1 FastAPI app module, use the R1/R2 API
prefix (or root-relative paths if the plan chose none), and record its real
launch command in `plan.md` and `quickstart.md`. Do not let it create a
second application module. If the plan does not name the launch command or
how it reaches the R1/R2 API, ask the agent to add that before tasks.

**Pass condition**: `plan.md` and `tasks.md` exist, the plan's Constitution
Check ran, the plan names the real entry point (`/`), runtime launch
command, and relative API paths matching the R1/R2 prefix (root-relative if
none) for a same-origin UI with no hardcoded host or port, and the tasks
include an acceptance-test task.

### 5.4 Install the browser and write the acceptance test (manual skill)

The acceptance test needs a real browser. The base container has no Chrome;
phases 01-04 don't need it. Install it once from a host terminal in your
clone (not inside the container):

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

The Python driver goes in the project venv:

```bash
cd /project/petstore
uv pip install pytest-playwright
```

Don't run `playwright install`: the generated test uses the container's
Chrome with `channel="chrome"` (or `--browser-channel=chrome`) and the
launch flags `--no-sandbox --disable-dev-shm-usage`.

With `tasks.md` in place and no implementation yet, invoke:

```text
/speckit.requirements.acceptance-test R3
```

The command reads the spec, plan, quickstart, and build/test entry points,
then writes the test first. It's a manual step, not a hook run automatically.
It adds isolated state and a known-bad fixture, then wires the test into `make test`.

The test is written before implementation, so: the acceptance test is derived
from the spec/plan/quickstart while no code exists, run red, and then made
green by the implement step. The gate (Step 6) runs after implement to confirm
the feature passes.

Check the generated test:

- it starts the real runtime itself (or the project gate starts it), loads
  `/`, `#/catalog`, `#/create-pet`, and `#/orders` in a real browser, and
  fails on console or page errors; a test that assumes a server is already
  running at a hardcoded URL is a finding;
- for this same-origin UI, it starts the app on an ephemeral port and loads
  the page from `127.0.0.1:<port>`, not the example `localhost:8000`, so a
  hardcoded API base URL fails;
- it asserts every `UI-1..UI-6` outcome, not only HTTP status or static
  text;
- it uses temporary state, cleans up, has a known-bad fixture, and can be
  made to fail;
- it includes fast contract checks (no auth/session surface, no hardcoded
  API host or port, no placeholders, a real order listing at the R1/R2
  prefix (the reference run uses `GET /api/v1/orders`), stock restore on
  cancel) and runs under `make test`.

Run it now; it should fail because the feature isn't implemented. Module
imports, status checks, and static text aren't an acceptance test.

### 5.5 Analyze

```text
/speckit.analyze
```

`before_analyze` runs the requirement verifier, so drift or a stale digest
shows up in the analysis report. Analyze itself stays read-only. If it
reports findings, `after_analyze` runs the remediation loop: correct every
instance of the same claim or defect class, then re-verify on a fresh
pass.

### 5.6 Implement

```text
/speckit.implement
```

`before_implement` applies the tasks checklist to the code and tests being
written, not only the task text. The agent writes the HTML/JS/CSS, wires
the FastAPI static route or index handler, and runs the tests.

`after_implement` commissions an independent, fresh-context review of the
diff. The reviewer gets only the goal, checklists, and diff. For this web
feature it must also run the real entry point or acceptance test; a review
that only reads the diff is incomplete. Fix every finding and re-run until
clean.

In my dry run, an agent that started uvicorn in the foreground hung the
turn. Escape didn't always recover; quit with Ctrl-C, relaunch `opencode`,
and continue. The speckit commands re-read the artifacts from disk, so
nothing is lost.

### 5.7 Converge

```text
/speckit.converge
```

`before_converge` runs the requirement verifier and the tasks checklist
again. Converge re-reads the spec and compares the code to it. It refuses
to call the feature converged while a claimed requirement is missing from
the spec, stale, or unimplemented.

If converge appends missing work to `tasks.md`, review the task, re-run
implement, then converge again.

A converged API isn't a converged web page. Step 6's acceptance test and
manual page checks still have to pass.

## Step 6: Run the acceptance gate and see the Web UI live

Run the acceptance test through the project gate from `/project/petstore`:

```bash
cd /project/petstore
make test
```

Start the app in a second byobu window (F2, or the tmux prefix Ctrl-b c)
or another container terminal. Use the launch command recorded in the R3
`plan.md` or `quickstart.md`; do not guess the module:

```bash
cd /project/petstore
rg -n 'uvicorn .*:app' specs/003-*/plan.md specs/003-*/quickstart.md
```

If you kept a differently numbered R3 directory, substitute its path.
Run the command it prints. The two common layouts are:

```bash
uv run uvicorn petstore_app:app --reload --host 0.0.0.0   # if the plan named petstore_app.py
uv run uvicorn src.main:app --reload --host 0.0.0.0       # if the agent used a src/ package
```

Leave it running while you try the UI. Stop it with Ctrl-C.

Open a browser **on your host**. Your host can't reach the container's
`127.0.0.1`; run `workshop info` from your clone and use the `hostname:`
line. For a clone named `speckit-workshop`:

```
http://speckit-ws.speckit-workshop.wp:8000/
```

The R3 contract for this sample is the root path (`/`), so open that.
If the implementation leaves `/docs` routed, it remains available for the
JSON API.

Try each requirement:

- **Catalog (`UI-1`)**: each pet shows name, stock count, and a distinct
  availability badge that changes with availability.
- **Create (`UI-2`)**: invalid input is blocked client-side; a successful
  submit updates the catalog immediately. No login.
- **Order (`UI-3`)**: zero stock disables the order action; ordering an
  in-stock pet decrements stock by one.
- **Orders (`UI-4`)**: the active order appears; cancel it and both the
  list and catalog stock update in place.
- **Serving (`UI-5`)**: a static single-page app served by FastAPI, no node
  runtime or frontend build, no full-page reload for in-app actions.
- **Same-origin (`UI-6`)**: the page works from the workshop hostname (not
  `localhost:8000`), and network calls go to relative paths under the
  R1/R2 API prefix (the reference run uses `/api/v1/pets`), not an
  absolute URL. The automated acceptance test also serves the app on an
  ephemeral port to catch a hardcoded port.

If the page doesn't load, check that uvicorn is bound to `0.0.0.0`, that
you used the `workshop info` hostname, and that `/` is served. The DevTools
Console on `/`, `#/catalog`, `#/create-pet`, and `#/orders` should be free
of red errors. If `/docs` is still routed, it confirms the API side
independently.

**Why API-only tests miss this.** A test suite can pass while the browser is
broken: uncaught JavaScript errors, a shared state object that is not
exposed, an API path prefix that does not match the backend, a hardcoded API
base URL that only works from `localhost:8000`, or placeholder code that
returns an empty list etc.

## Step 7: Verify and close the loop

Confirm Step 6's test passed normally and failed under mutation, and the
manual pass succeeded. If either failed, don't mark the row done.

Verify the `R3` spec:

```bash
bash extensions/requirements/scripts/bash/verify-traceability.sh /project/petstore/specs/003-*/spec.md
```

If you kept a differently numbered R3 directory, substitute its path.

Then update `ROADMAP.md` row `R3`:

- change `Status` from `planned` to `done`;
- confirm or update the `Sub-spec` link to your kept R3 directory (normally
  `specs/003-...`).

From `/project/petstore`, the full gate and working tree:

```bash
make test
git status
git diff
```

The roadmap row is a claim. Mark it `done` only when the spec content, the
fresh digest, and the code all support it.

## Troubleshooting

- **`Could not import module "petstore_app"`**: the R3 plan named a
  different app module. Read the launch command from
  `specs/003-*/quickstart.md` or `plan.md` and run that module instead,
  for example `uv run uvicorn src.main:app --reload --host 0.0.0.0`.
- **`NetworkError when attempting to fetch resource` or "Failed to fetch"**:
  the client hardcoded `http://localhost:8000` or another absolute API base
  URL. Use same-origin relative paths under the R1/R2 prefix (the
  reference run uses `/api/v1/pets`); keep absolute URLs only in
  curl/quickstart examples. Load the page from the workshop hostname; the
  acceptance test covers the ephemeral-port case.
- **Two specs for one roadmap row (`003-*` and `004-*`)**: specify ran
  twice. Keep the first R3 spec (`003-*`), delete the later `004-*`
  directory, set `.specify/feature.json` to the kept directory, and update
  the R3 `Sub-spec` link to it. Continue with clarify, plan, and tasks; do
  not run specify again.
- **`make test` says `No module named pytest` or `yaml`**: run
  `make install`. It installs the requirements even with an existing venv.
- **`No module named playwright`**: `uv pip install pytest-playwright`.
- **`test_hook_registrations_present` fails**: `.specify/extensions.yml`
  is missing or wiped. Run
  `specify extension add --dev --force extensions/requirements`.
- **`no '| FR-### | RQ... | Completes |' rows found`**: the spec predates
  the extension. Run the retrofit script.
- **`phrases file not found`**: copy `requirement-phrases.txt` to the
  project root, or run the retrofit script.
- **`stale phrase` or `DRIFTED`**: the wording changed after the phrase or
  digest was recorded. Regenerate with
  `scripts/extract-phrases.sh REQUIREMENTS.md -o requirement-phrases.txt`,
  review, and update the spec text and digests through the brief.
- **Em dash style failure**: use a hyphen. Retrofit replaces em dashes in
  project files only. If `REQUIREMENTS.md` had one, the curated phrase may
  be stale; regenerate `requirement-phrases.txt` and re-run the verifier.
- **Constitution looks different after bootstrap**: bootstrap keeps a
  customized constitution. Move the file aside before re-running to get
  the template's two-part version.
- **`window.appState` is undefined or the catalog says "Failed to load"**:
  modules share state through `window.appState`. Fix it there; don't add
  per-module fallbacks.
- **Login page or `/auth` 404s**: auth is out of scope. Remove the login
  route, auth module, session middleware, and credentials.
- **Orders page says the feature would need an endpoint**: UI-4 isn't
  implemented. Add the order-listing endpoint at the R1/R2 prefix
  (reference: `GET /api/v1/orders?status=open`); wire the real list and
  cancel actions.
- **Repeated 500s after the first request**: the SQLite connection must
  work across FastAPI's worker threads. Use `check_same_thread=False` or a
  per-request connection.
- **A request to `/api/...` returns 404**: the client used a prefix or path
  the backend does not serve. Match the prefix and routes your R1/R2 plan
  chose; the reference run uses `/api/v1/...`. Do not assume every backend
  is root-relative.
- **Acceptance-test skill not available**: rerun `bootstrap.sh` or
  `generate-skills.sh`, reinstall the extension. The skill comes from
  `extensions/requirements/commands/speckit.requirements.acceptance-test.md`.
- **`google-chrome: command not found`**: install it from a host terminal
  in your clone: `workshop run --uid 0 -- install-browser`.
- **`Executable doesn't exist` or Playwright tries to download a browser**:
  use container Chrome, not a bundled one. Launch with `channel="chrome"`
  (or `--browser-channel=chrome`); don't run `playwright install`.
- **`Running as root without --no-sandbox is not supported`** or Chrome
  crashes on small `/dev/shm`: add
  `--no-sandbox --disable-dev-shm-usage`.
- **Generated test passes but page is broken**: the test is too weak.
  Require real runtime, real entry point, each UI requirement, and a
  failing mutation.
- **Generated test missing from `make test`**: wire it into the project
  gate, not a separate script.

## Extensions, presets, and bundles

- **Extensions** add commands, templates, and hooks; install with
  `specify extension add`; register in `.specify/extensions.yml`.
- **Presets** are packaged file overrides selected at `specify init`; no
  commands or hooks.
- **Bundles** are versioned stacks of extensions, presets, and workflows,
  installed with `specify bundle install`.

## Reading list

- The [spec-kit README](https://github.com/github/spec-kit) for install,
  preset/bundle reference, and the extension API.
- The template README's
  [requirements extension section](new-project-template/README.md#the-requirements-extension)
  and the [template conventions](new-project-template/README.md#conventions-the-tooling-expects).
- The core `/speckit.constitution` command and the
  [`new-project-template/constitution.md`](new-project-template/constitution.md)
  two-part model.
- The [community extension catalog](https://github.github.io/spec-kit/community/extensions.html).
