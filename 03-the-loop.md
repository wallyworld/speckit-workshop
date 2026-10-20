# 03 - The Loop - Build a pet store

Start in the workshop container from [01](01-setup.md), with `/project/petstore`,
the agent open, and `/speckit` commands available.

> **Command form.** As in [02](02-core-concepts.md), the commands below use
> OpenCode's dot form; with agy or Copilot use the hyphenated form
> (`/speckit-specify` in place of `/speckit.specify`).

> **No container clipboard?** You never have to copy a command. Reply
> `run the next step` or `run the emitted command`; the agent acts on the
> artifacts on disk. Copy alternatives are in
> [06 - Reference](06-reference.md#clipboard-inside-the-container).

`.specify/memory/constitution.md` should already be ratified from
[01](01-setup.md#14-ratify-the-project-constitution). If it still has
template placeholders, go back: the plan's Constitution Check has nothing
to check.

## The feature description

This is the pet catalog slice. Order placement is deliberately **excluded**:
features are independent slices, and the spec records what is out of scope.
[04](04-the-refinement.md) is that slice.

## Step 1: `/speckit.specify <the feature description>`

```
/speckit.specify You are building a pet store. Users can list pets with an availability
status, add a new pet, view a pet by id, and delete a pet. Each pet has a
name, a stock count, and an availability status that is derived from
whether stock is above zero. Placing an order for a pet is out of scope
for this feature.
```

The agent creates `specs/001-<slug>/` and fills `spec.md` from the template.
The slug comes from your description, so it varies; one run produced
`specs/001-pet-crud/`. Open the spec and check that it lists user stories,
functional requirements, success criteria, edge cases, and assumptions; that
the stories have priorities; that the requirements are testable; and that the
"stock-derived availability" rule is stated. If the rule is missing, say so
before moving on. The run may also produce a requirements checklist beside
the spec; `research.md` arrives later with `/speckit.plan`.

Inline text is the vanilla starting point for a single slice. Production
projects usually assemble the prompt from `REQUIREMENTS.md` and a roadmap;
[05 - What's Next](05-whats-next.md) shows that bridge.

## Step 2: `/speckit.clarify` (optional but useful)

```
/speckit.clarify
```

Clarify asks up to 5 questions about underspecified areas, one at a time.
In my run it asked three. Answer them and keep going until it stops; the
answers are folded back into `spec.md`. Reopen the file afterward and check
the new lines. If a question changes the feature materially, that is the
mechanism working, not friction.

## Step 3: `/speckit.plan`

```
/speckit.plan The app is a FastAPI service using SQLite for storage and
pytest for tests. Tests are run with "uv run pytest" from the project
root. Name the API module petstore_app.py and expose the app object as
"app" (so the server runs as "uv run uvicorn petstore_app:app
--reload --host 0.0.0.0"). Keep it minimal - no auth, no pagination, no extra
application libraries beyond FastAPI, uvicorn, and pytest (a dev-only
HTTP client for TestClient is fine). Include pytest tests covering
every functional requirement.
```

`plan.md` lands in the feature directory with the technical approach, files,
data model, API endpoints, edge cases, and a **Constitution Check** against
`.specify/memory/constitution.md`. A conflict has to be justified in
Complexity Tracking or the design changes. The plan is written before any
code, and it is the agent's own work product. Open the Constitution Check
and read the tests-required and minimal-stack entries. If the check is
empty, stop and fix the constitution first.

## Step 4: `/speckit.tasks`

```
/speckit.tasks
```

`tasks.md` is dependency-ordered. Each task has a checkbox, an action, and a
file path. The checkboxes are the plan, not a progress tracker:
implementations do not always tick them, so read the list, not the marks.
Pick two tasks and confirm each names the file it touches.

## Step 5: `/speckit.analyze`

```
/speckit.analyze
```

Analyze cross-checks `spec.md`, `plan.md`, and `tasks.md` and reports
inconsistencies, ambiguities, and constitution conflicts. It is read-only.
Fix the artifacts before implementing; the command will not touch the code.
[05 - What's Next](05-whats-next.md) makes this same check mandatory through
extension hooks.

## Step 6: `/speckit.implement`

```
/speckit.implement
```

The agent works through the tasks: FastAPI app, SQLite storage, endpoints,
tests. It runs the suite and fixes failures until it passes, and it reads the
constitution as a governance constraint (tests required, minimal stack).
Its verify loop becomes visible here: run tests, read failures, fix, re-run.

If it starts the dev server in the foreground, the turn hangs. Escape does
not always recover; quit the TUI with Ctrl-C, relaunch `opencode`, and
continue. The speckit commands re-read the artifacts from disk, so nothing
is lost.

## Step 7: `/speckit.converge`

```
/speckit.converge
```

Converge re-reads `spec.md`, `plan.md`, and `tasks.md`, diffs the code
against them, and reports whether the implementation is complete. A
constitution MUST violation is CRITICAL. If the metrics line says the
constitution principles were skipped, the constitution is still unfilled;
go back to [01](01-setup.md#14-ratify-the-project-constitution) Section 1.4.

It may append missing work to `tasks.md`, for example a test for an edge case
you specified but the agent did not implement. Review what it appends before
re-running implement. Appended findings can name work the code already
contains; check the task against the code first. My run needed two converge
cycles. Re-run `/speckit.implement`, then `/speckit.converge`, until it
reports **converged**.

Converge is the closing check, and it compares against the spec, not only the
tests. If the plan said `status` is derived but the code stores it as a
column, converge flags the discrepancy and sends you back into the loop.

## Step 8: See it live

Start the server in a second byobu window with the launch command from the
feature's `plan.md` or `quickstart.md` (for example
`uv run uvicorn petstore_app:app --reload --host 0.0.0.0`, or
`uv run uvicorn src.main:app --reload --host 0.0.0.0` if the agent used a
`src/` package).

Open the docs UI in a browser **on your host** at the address from
`workshop info` (run it from your clone directory and read the `hostname:`
line). For a clone named `speckit-workshop` that is
<http://speckit-ws.speckit-workshop.wp:8000/docs>. Swagger lists the pet
endpoints: POST `/api/v1/pets`, GET `/api/v1/pets`, GET
`/api/v1/pets/{id}`, DELETE `/api/v1/pets/{id}`. If your plan chose a
different prefix, use the paths Swagger shows.
Add a pet with a name and a stock count, list it, then delete it. The API
surface should match the functional requirements in `spec.md`. If uvicorn
reports `Could not import module "petstore_app"`, the agent chose a different
module name; run `uv run uvicorn <that-module>:app --reload --host 0.0.0.0`
(for example `uv run uvicorn src.main:app --reload --host 0.0.0.0`).

## On disk

The spec, plan, and tasks are files under `specs/001-<slug>/`.
Converge was the closing gate hence nothing counted as done
until it reported converged.

Next: [the-refinement](04-the-refinement.md) - add a non-trivial requirement.
