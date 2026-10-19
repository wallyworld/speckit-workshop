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

The core loop is unchanged. The extension puts an accounting layer in
front of it.

## What the requirements extension adds

The phased delivery template ships **one** extension package, `requirements`. It contains
six commands, two template overrides, and eight mandatory hooks. The full
per-command explanation, including what each command prevents versus a
vanilla Spec Kit project, is in the template README section
[The requirements extension, piece by piece](new-project-template/README.md#the-requirements-extension-piece-by-piece).

| Loop stage | What fires |
| --- | --- |
| before specify | `/speckit-requirements-prepare R#` builds a reviewed brief with canonical requirement text and digests |
| plan | `before_plan`: plan checklist |
| tasks | `before_tasks`: tasks checklist, tests required |
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

The bootstrap installs the requirements extension and its hooks, the spec
and tasks templates, the workflow review gates, the constitution skeleton,
the mirror tests, the `AGENTS.md` and `CONTRIBUTING.md` skeletons, and the
`Makefile`. It then runs `specify extension add --dev --force
extensions/requirements`, which writes the hook registrations into
`.specify/extensions.yml`.

Two things to check:

```bash
ls .specify/extensions.yml
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
- installs the mirror-test dependencies if `pytest` or `yaml` is missing;
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

### 5.2 Specify

Run the emitted command, for example:

```text
/speckit.specify Implement slice R3 from ROADMAP.md: an interactive
browser frontend served by FastAPI that renders the catalog, creates pets,
places orders, and cancels orders.
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

At `plan`, the `before_plan` hook injects the plan checklist: design
opt-outs must cite requirement wording, thresholds need operational
definitions, every MUST needs a task, and boundaries must be specified.
At `tasks`, the `before_tasks` hook injects the tasks checklist: tests come
first, IDs are sequential, and failure paths are covered. The tasks
template makes tests required.

**Pass condition**: `plan.md` and `tasks.md` exist, the plan's Constitution
Check ran, and the tasks include tests for the UI behavior.

### 5.4 Analyze

```text
/speckit.analyze
```

`before_analyze` runs the requirement verifier, so any drift or stale
digest appears in the analysis report. If analysis reports findings,
`after_analyze` runs the remediation loop: correct every instance of the
same claim or defect class, then re-verify on a fresh pass.

### 5.5 Implement

```text
/speckit.implement
```

`before_implement` applies the tasks checklist to the code and tests being
written, not only the task text. The agent writes the HTML/JS/CSS, wires
the FastAPI static route or index handler, and runs the tests.

`after_implement` commissions an independent, fresh-context review of the
implementation diff. The reviewer gets only the goal, the applicable
checklists, and the diff. Fix every finding and re-run until clean before
reporting the work done.

### 5.6 Converge

```text
/speckit.converge
```

`before_converge` runs the requirement verifier and the tasks checklist
again. Converge re-reads the spec and compares the code to it. It refuses
to call the feature converged while a claimed requirement is missing from
the spec, stale, or unimplemented.

If converge appends missing work to `tasks.md`, review the appended task,
re-run implement, then converge again.

### Workflow mode (optional)

Instead of working skill by skill, you can run the bundled workflow and
see the same checks as approve/reject gates:

```bash
specify workflow run speckit -i "spec=an interactive pet store web UI served by FastAPI"
```

The extension adds six gates: `review-coverage` (after specify),
`review-plan-checklist` (after plan), `review-tasks` and
`review-implement-checklist` (after tasks), `review-diff` and
`review-final-tree` (after implement). The composed workflow also keeps
Spec Kit's stock gates. Each gate can approve or reject; rejection aborts
the workflow. The bundled workflow has no analyze or converge step, so
those hooks fire in skills mode only.

## Step 6: See the Web UI live

With the feature implemented (and converged, if you used the
skill-by-skill path), start the app from `~/petstore` in a second byobu
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

The R3 feature is the web UI itself, so open the route the implementation
serves. That is often the root path (`/`), but check `plan.md` and its
contracts, or `petstore_app.py`, for the route the agent chose (for
example `/ui`). If the implementation leaves `/docs` routed, it remains
available for the JSON API.

Try each requirement:

- **Catalog (`UI-1`)**: the page lists each pet's name, current stock count,
  and a distinct availability badge; the badge changes with availability.
- **Create (`UI-2`)**: submit the form with invalid input and confirm
  client-side validation blocks the request; on success the catalog updates
  immediately. If your clarify step introduced login or roles, use the
  appropriate account.
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
implementation serves the route named in its plan or contracts. If `/docs`
is still routed, it confirms the API side independently.

## Step 7: Verify and close the loop

Confirm the `R3` spec verifies clean:

```bash
bash extensions/requirements/scripts/bash/verify-traceability.sh ~/petstore/specs/003-*/spec.md
```

Then update `ROADMAP.md` row `R3`:

- change `Status` from `planned` to `done`;
- set the `Sub-spec` link to your generated `specs/003-...` directory.

Finally run the full gate and review the working tree:

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
