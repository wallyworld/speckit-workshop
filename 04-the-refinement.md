# 04 - Refinement: The Order Placement Logic

Order placement, in `/project/petstore` inside the workshop container
([01](01-setup.md)). Start a fresh session. A session carried over from the
catalog feature can resolve the wrong directory and pick up the previous spec;
[02](02-core-concepts.md) explains why. The requirement below has a new
business rule to add to the pet store.

> **Command form.** Commands use OpenCode's dot form; with agy or Copilot use
> the hyphenated form (`/speckit-specify` in place of `/speckit.specify`).

> **No container clipboard?** Reply `run the next step` or
> `run the emitted command`; the agent acts on the files on disk. Copy
> alternatives are in
> [06 - Reference](06-reference.md#clipboard-inside-the-container).

## The feature description you will run

> You are building a pet store. Users can place an order for a pet. Placing an
> order for a pet that is no longer listed as available must fail. A successful
> order reduces the pet's available stock by one. Canceling an order that is
> still open must restore the pet's stock by one. An order may not bring a pet's
> stock below zero.

The last sentence is the interesting one for this workshop. Does the loop turn
it into a check, or leave it as prose in `spec.md`?

## Implement the requirement

The block is the full loop. Run it one command at a time from `/project/petstore`;
the sections below mark the required interactions.

```
/speckit.specify You are building a pet store. Users can place an order for a pet. Placing
an order for a pet that is no longer listed as available must fail. A
successful order reduces the pet's available stock by one. Canceling an
order that is still open must restore the pet's stock by one. An order
may not bring a pet's stock below zero.
/speckit.clarify
/speckit.plan The app is a FastAPI service using SQLite for storage and
pytest for tests. Tests are run with "uv run pytest" from the project
root. Name the API module petstore_app.py and expose the app object as
"app". Keep it minimal - no auth, no pagination (a dev-only HTTP client
for TestClient is fine). Include pytest tests covering every functional
requirement. Reuse the
pet catalog schema and endpoints already present.
/speckit.tasks
/speckit.analyze
/speckit.implement
/speckit.converge
```

After clarify, check the spec. Functional Requirements must say an order for
an unavailable pet **must fail** and stock **must not** go below zero. If
clarify turned either into a vague phrase, put the precise sentence back. A
loose requirement can't be verified at converge time.

## Analyze the artifacts

Analyze is read-only and only checks the written artifacts, not the code. Fix
the spec, plan, or tasks until its report is clean.

## Check the tests and the API

`uv run pytest` passes, and you've got order placement plus a suite. Look for an
`orders` table and `POST /api/v1/orders`; a cancel route may be
`POST /api/v1/orders/{id}/cancel` or `DELETE /api/v1/orders/{id}`,
depending on the run. If your plan chose a different prefix, use the paths
Swagger shows.

Open the test file. Look for a case where an order for a zero-stock pet
**fails**, and one showing stock never drops below zero. If the suite only
covers an in-stock order succeeding, it passes without asserting the
requirement - this is the potential gap this phase is about investigating.

Start the server in a second byobu window with the launch command from the
feature's `plan.md` or `quickstart.md` (for example
`uv run uvicorn petstore_app:app --reload --host 0.0.0.0`, or
`uv run uvicorn src.main:app --reload --host 0.0.0.0` if the agent used a
`src/` package).

Open the docs UI from your host browser. Use the `hostname:` line from
`workshop info` (run it in your clone); for a clone named `speckit-workshop`
that's
<http://speckit-ws.speckit-workshop.wp:8000/docs>. Create a pet with stock 1,
order it, then order it again. The second call should fail, and stock should
stay at 0. A 200 means the implementation missed the requirement; stock at -1
would be the indication something went wrong.

## Converge

Converge re-reads the spec, plan, and tasks, then compares the code to them.
The block ends with converge. Run it again after the test check:

```
/speckit.converge
```

Converge reports **converged** when code and artifacts agree. Otherwise it
points at a missing test or a gap in the code. Mine needed two cycles. The
common gap: the code decrements stock without an availability check, so orders
drive it to -1 while a happy-path suite stays green. Converge appends the
missing task, for example "write a test asserting an order for a zero-stock pet
fails", and you run implement and converge again.

Either result is a successful exercise. The loop doesn't let "tests pass" stand
in for "requirement met".

## Summary

Specs and tests aren't the same thing. The spec states the requirement, tests
assert it, code implements it. Analyze checks that the written artifacts agree;
converge checks that the code agrees with them.

A naive "decrement stock, done" passes a happy-path suite and violates the
spec. The loop catches it because the requirement was written independently of
the code. If you'd told the agent only "write an order endpoint", it would've
produced the happy-path implementation, the tests would've passed, and nobody
would've noticed the issue until production.

The loop doesn't stop you writing a bad spec. It makes a bad or incomplete spec
visible: converge checks the code against it and refuses to call it done when
they disagree.

One more gap this exercise can expose: out of the box, Spec Kit treats test
tasks as optional, so a tasks list can omit them - the requirement is then
asserted only if the implementer writes tests on its own initiative. Your
constitution's principle 2 says every new behaviour, including failure paths,
has a test, so the omission is a constitution violation, not just a spec gap.
But in the vanilla project that principle is prose: the agent can still ignore
it. This project's
[`new-project-template/`](new-project-template/) closes that gap: its
constitution principle 8 makes test coverage mandatory, its tasks template
states tests are required, and a hook checks the test list before tasks and
converge. That's the difference between a principle and a gate.

## If you finish early

Add another requirement and run the loop again, for example: *"An order that
has not been canceled must not be modified after it is placed."* See what
converge says about it.

Or, explicitly **outside** the loop: in a fresh non-spec-kit session, ask for a
single `index.html` storefront served by FastAPI (`StaticFiles`), listing pets
and placing orders against the API. Because this would be written outside the
loop, it never enters the requirements chain.

Next: [what's next](05-whats-next.md) and [reference](06-reference.md).
