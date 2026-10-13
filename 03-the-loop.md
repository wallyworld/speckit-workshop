# 03 - The Loop, Demoed: Pet Catalog

Run each command and let the agent work - watch what happens at each
step. This walkthrough assumes you are in the `petstore` project created
in [01](01-setup.md), with the agent open and `/speckit` commands
available.

## The feature description

We ask the agent to build the *pet catalog* slice of the pet store:

> A pet store. Users can list pets with an availability status, add a new
> pet, view a pet by id, and delete a pet. Each pet has a name, a stock
> count, and an availability status that is derived from whether stock is
> above zero. Placing an order for a pet is out of scope for this feature.

Notice that order placement is deliberately **excluded**: features are
independent slices, and the spec records what is out of scope. The
hands-on phase ([04](04-hands-on.md)) is the order-placement slice.

## Step 1: `/speckit.specify <the feature description>`

Run:

```
/speckit.specify A pet store. Users can list pets with an availability
status, add a new pet, view a pet by id, and delete a pet. Each pet has a
name, a stock count, and an availability status that is derived from
whether stock is above zero. Placing an order for a pet is out of scope
for this feature.
```

What you should see happen (narrate as you go):

- The agent generates a feature directory: `specs/001-<slug>/` (the slug
  is derived from your description - in this run: `specs/001-pet-store-users/`).
- Inside it, `spec.md` is created from the spec template.
- The spec is filled in with: user stories, functional requirements,
  success criteria, edge cases, assumptions.

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
answers get folded back into the spec.

Clarify exists to prevent the "informed guess that turns out wrong"
failure mode. If the agent asks a question whose answer materially
changes the feature, that is the mechanism working.

## Step 3: `/speckit.plan`

```
/speckit.plan The app is a FastAPI service using SQLite for storage and
pytest for tests. Tests are run with "uv run pytest" from the project
root. Name the API module petstore_app.py and expose the app object as
"app" (so the server runs as "uv run uvicorn petstore_app:app
--reload"). Keep it minimal - no auth, no pagination, no extra
application libraries beyond FastAPI, uvicorn, and pytest (a dev-only
HTTP client for TestClient is fine).
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
  list. Each task has a checkbox, a clear action, and a file path.

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
  edge case you specified but the agent did not implement).
- The loop repeats: re-run `/speckit.implement`, then `/speckit.converge`
  again, until it reports **converged**.

This is the closed-loop proof: converge is the step that checks the code
against the stated intent. If the agent planned a `status` field but
implemented it as a column when the plan said "derived," converge flags
the discrepancy and re-enters the loop.

## Step 7: See it live

```
uv run uvicorn petstore_app:app --reload
```

Run it in the foreground in a separate terminal (or use your editor's
terminal split) and leave it running for the demo, so the request log
and the reload output stay visible as you click through the UI. Stop
the server with Ctrl-C when done.

Open <http://127.0.0.1:8000/docs> in a browser. FastAPI auto-serves an
interactive UI (Swagger) here - every endpoint is now clickable. Try it
like a real pet store:

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

Next: [hands-on](04-hands-on.md) - your turn, with a landmine.