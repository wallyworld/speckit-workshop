# 04 - Refinement: The Order Placement Logic

This is the refinement phase: you run the same loop on order placement in
your own project, inside your workshop container ([01](01-setup.md)).
The feature you will specify contains a verification deliverable for a
non-trivial requirement.

To avoid loading up the context from the initial pet catalog feature, start 
a new session in your coding harness prior to running the next loop.

> **Command form.** Commands use OpenCode's dot form; with agy or Copilot use
> the hyphenated form (`/speckit-specify` in place of `/speckit.specify`).

## The feature description you will run

> You are building a pet store. Users can place an order for a pet. Placing an
> order for a pet that is no longer listed as available must fail. A successful
> order reduces the pet's available stock by one. Canceling an order that is
> still open must restore the pet's stock by one. An order may not bring a pet's
> stock below zero.

That final sentence is the non-trivial requirement. The whole refinement phase
is about whether the loop turns that sentence into a real check - and whether a
naive implementation survives it.

## Implement the requirement

Run the full loop on the order-placement feature:

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
/speckit.implement
/speckit.converge
```

**Pass condition**: your `spec.md` states, in the Functional Requirements,
that an order for an unavailable pet **must fail** and that stock **must
not** go below zero. If the agent's clarify step collapsed that into a
vague phrase, feed the precise sentence back into the spec before
continuing.

If the spec does not state the "must not go below zero" requirement
explicitly, that is the spec being loose - a loose requirement cannot be
verified at converge time.

## Implementation and its tests exist

**Pass condition**: `pytest` passes in your project. You now have an
implementation of order placement and a test suite. The implementation will have
added an `orders` table and `POST /orders` (and possibly a cancel action, e.g.
`POST /orders/{id}/cancel`) to your FastAPI app.

**Check**: does the suite include a test that an order for a
zero-stock pet **fails**, and a test that placing an order never drives
stock below zero? Open the test file and look. If the tests only cover
the happy path (order for an in-stock pet succeeds), you have discovered
the potential flaw: the loop will have produced tests that pass, but
the *requirement* is not asserted.

**See it in the browser**: with the server running
(`uv run uvicorn petstore_app:app --reload --host 0.0.0.0`), open the
served docs UI in a browser on your host: the `hostname:` line of
`workshop info` (run from your clone) gives the address
(`<workshop-name>.<clone-name>.wp`), so a clone named `speckit-workshop`
uses <http://speckit-ws.speckit-workshop.wp:8000/docs>. Then try it like
a real pet store: create a pet with stock 1, place an order for it,
then place a second order for the same pet. Whether that second order
**fails in the UI** - or is silently accepted - is the $64,000,000 question.

## Converge

Now run the loop's converge check again - the converge step re-reads the
spec and compares the code to it:

```
/speckit.converge
```

Two outcomes:

- **The loop closes**: converge reports the implementation matches the
  spec. Your tests assert the invariant, the code enforces it, and
  converge finds no gap. The feature is (hopefully) done.
- **The loop re-enters**: converge points at a missing test or gap in the
  code. A common one: the spec says "must not go below zero" but the
  implementation decrements stock without checking availability first -
  so a sequence of orders can drive stock to -1, and the test suite
  (written from the happy path) never noticed. Converge appends the
  missing task ("write a test asserting an order for zero-stock fails")
  and you re-run implement and converge.

**Either** outcome is a successful exercise. The loop does not let "the tests
pass" stand in for "the requirement is met."

## Summary

The demonstrable lesson of this phase is that **specs and tests are not
the same thing, and the loop keeps them consistent with each other**:

- The spec is the *requirement* (stock must not go below zero).
- The tests are the *assertions* (the invariant is checked).
- The implementation is the *behavior*.
- Converge is the step that verifies all three agree.

A naive implementation - "place an order, decrement stock, done" - passes
tests that only check the happy path, but violates the spec. The loop
catches it because the *requirement* was stated independently of
the code. If you had just told the agent "write an order endpoint," the
agent would have produced the happy-path implementation, the tests would
have passed, and nobody would have noticed the drain below zero until
production.

The loop does not prevent you from writing a bad spec.
But it makes a *bad or incomplete spec* visible, because the loop's last
step checks the code against the spec you wrote, and it refuses to call
it done when the two disagree.

One more gap this exercise can expose: out of the box, Spec Kit treats test
tasks as optional, so a tasks list can omit them - the requirement is then
asserted only if the implementer writes tests on its own initiative. Your
constitution's principle 2 says every new behaviour, including failure
paths, has a test, so the omission is a constitution violation, not just a
spec gap. But in the vanilla project that principle is prose: the agent can
still ignore it. This project's
[`new-project-template/`](new-project-template/) closes that gap: its
constitution principle 8 makes test coverage mandatory, its tasks template
states tests are required, and a hook checks the test list before tasks and
converge. That is the difference between a principle and a gate.

## If you finish early

Add one more requirement to the order feature and run the loop again, for
example: *"An order that has not been canceled must not be modified after
it is placed."* Watch how the loop carries that requirement through to
converge. It shows how a *complete* spec  produces *verified* code.

Or, for fun (explicitly **outside** the loop): ask the agent, in a fresh
non-spec-kit session, to add a single `index.html` storefront page served by
FastAPI (`StaticFiles`) that lists the pets and places orders against the API.
Because it's hand-written for "fun", it does not enter the requirements chain -
notice the contrast with everything you just did through the loop.

Next: [what's next](05-whats-next.md) and [reference](06-reference.md).