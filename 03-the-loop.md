# 03 - The Loop, Demoed: Pet Catalog

Run each command and let the agent work - watch what happens at each
step. This walkthrough assumes you are inside your workshop container
([01](01-setup.md)), in the `~/petstore` project you created there, with
the agent open and `/speckit` commands available.

> **Command form.** As in [02](02-core-concepts.md), the commands below use
> OpenCode's dot form; with agy or Copilot use the hyphenated form
> (`/speckit-specify` in place of `/speckit.specify`).

## The feature description

We ask the agent to build the *pet catalog* slice of the pet store:

> You are building a pet store. Users can list pets with an availability status,
> add a new pet, view a pet by id, and delete a pet. Each pet has a name, a
> stock count, and an availability status that is derived from whether stock is
> above zero. Placing an order for a pet is out of scope for this feature.

Notice that order placement is deliberately **excluded**: features are
independent slices, and the spec records what is out of scope. The
next phase ([04](04-the-refinement.md)) is the order-placement slice.

## Step 1: `/speckit.specify <the feature description>`

Run:

```
/speckit.specify You are building a pet store. Users can list pets with an availability
status, add a new pet, view a pet by id, and delete a pet. Each pet has a
name, a stock count, and an availability status that is derived from
whether stock is above zero. Placing an order for a pet is out of scope
for this feature.
```

> **Why inline text here?**
> Spec Kit's core command accepts a description prompt directly
> (`/speckit.specify <text>`). In this workshop, we pass the description
> inline so you can see the agent turn raw intent into the first repository
> artifact (`spec.md`) without extra file-management friction. In production
> or multi-feature projects, this input is typically assembled from a
> requirements document (`REQUIREMENTS.md`) and a roadmap - an architecture
> we explore in [05 - What's Next](05-whats-next.md).

What you should see happen (narrate as you go):

- The agent generates a feature directory: `specs/001-<slug>/` - the slug
  is derived from your description, so yours will differ (in one run it
  was `specs/001-pet-crud/`).
- Inside it, `spec.md` is created from the spec template.
- The spec is filled in with: user stories, functional requirements,
  success criteria, edge cases, assumptions. (The run may also produce a
  requirements checklist alongside the spec; `research.md` comes later,
  from `/speckit.plan`.)

Open `spec.md` and read it: the user stories have priorities, the
functional requirements are each testable, the agent derived the
"stock-derived availability" rule from your description and stated it
as a requirement.

## Step 2: `/speckit.clarify` (optional but useful)

```
/speckit.clarify
```

The clarify command asks up to 5 targeted questions about underspecified
areas - typical ones are scope ("is X in this feature?"), validation,
and data-shape choices. Accept its questions and answer them - the
answers get folded back into the spec. It is interactive: the questions
arrive one at a time, so keep answering until it is done.

Clarify exists to prevent the "informed guess that turns out wrong"
failure mode. If the agent asks a question whose answer materially
changes the feature, that is the mechanism working.

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

What you should see:

- `specs/001-<slug>/plan.md` is created: the technical approach, the
  files to create, the data model, the API endpoints, the edge cases.

## Step 4: `/speckit.tasks`

```
/speckit.tasks
```

What you should see:

- `specs/001-<slug>/tasks.md` is created: a dependency-ordered task
  list. Each task has a checkbox, a clear action, and a file path. The
  checkboxes are the plan, not a progress tracker - implementations do
  not always tick them off, so read the list, not the marks.

## Step 5: `/speckit.implement`

```
/speckit.implement
```

What you should see:

- The agent executes the tasks in order: creates the FastAPI app, the
  SQLite storage layer, the endpoints, and the tests.
- It runs the test suite and fixes failures until it passes.

## Step 6: `/speckit.converge`

```
/speckit.converge
```

What you should see:

- The agent re-reads `spec.md`, `plan.md`, and `tasks.md`, diffs the
  current code against them, and reports whether the implementation is
  complete.
- It may append missing work to `tasks.md` (for example: a test for an
  edge case you specified but the agent did not implement). Review what
  it appends before re-running implement - appended findings can name
  work the code already contains.
- The loop repeats: re-run `/speckit.implement`, then `/speckit.converge`
  again, until it reports **converged**.

This is how the loop is closed: converge is the step that checks the code
against the stated intent. If the agent planned a `status` field but
implemented it as a column when the plan said "derived," converge flags
the discrepancy and re-enters the loop.

## Step 7: See it live

```
uv run uvicorn petstore_app:app --reload --host 0.0.0.0
```

Run it in the foreground in a second byobu window (F2, or the tmux prefix
Ctrl-b c) or a separate terminal inside the container, and
leave it running for the demo, so the request log and the reload output
stay visible as you click through the UI. 
About `--host 0.0.0.0`: without it uvicorn binds to the container's
loopback only, which your host browser cannot reach.
Stop the server with Ctrl-C when done.

Open the served docs UI in a browser **on your host**. Your host
browser cannot reach the container's 127.0.0.1 - that address is the
container's own loopback. The workshop tool instead registers a DNS
name for your container that your host *can* reach: run `workshop info`
from your clone directory and read the `hostname:` line. The name
follows the pattern `<workshop-name>.<clone-name>.wp` - for a clone
named `speckit-workshop`, that is `speckit-ws.speckit-workshop.wp`, so
the served UI lives at
<http://speckit-ws.speckit-workshop.wp:8000/docs>.
FastAPI auto-serves an interactive UI (Swagger) there - every endpoint
is now clickable. Try it like a real pet store:

- **POST** `/pets` - add a pet with a name and a stock count.
- **GET** `/pets` - list the pets and their availability.
- **GET** `/pets/{id}` - view one pet.
- **DELETE** `/pets/{id}` - remove a pet.

## What just happened

- You wrote a feature description, and the agent turned it into a written
  artifact chain: spec, plan, tasks.
- The agent implemented the tasks and ran its own tests as it went.
- Converge checked the final code against the spec/plan/tasks and
  reconciled any gaps.
- Nothing was "done" until converge said so.
- You then pointed a browser at it: the feature is live at `/docs`, a
  clickable pet store rendered by FastAPI itself.

Next: [the-refinement](04-the-refinement.md) - add a non-trivial requirement.