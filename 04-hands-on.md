# 04 - Hands-On: The Order Placement You Implement

This is the hands-on phase: you run the same loop on order placement in
your own repo. The feature you will specify contains a verification
landmine. Checkpoints are inline and timed as minutes into the phase
(target: 28 minutes for the full loop).

If the instructor demoed the pet catalog with you, your `petstore`
project already has `specs/001-<slug>/` (the catalog feature you just
built - in this run it was `specs/001-pet-store-users/`) with a working
implementation. If you worked self-paced, complete [03](03-the-loop.md)
first, or start from your own pet catalog slice.

## The feature description you will run

> A pet store. Users can place an order for a pet. Placing an order for a
> pet that is no longer listed as available must fail. A successful order
> reduces the pet's available stock by one. Canceling an order that is
> still open must restore the pet's stock by one. An order may not bring a
> pet's stock below zero.

That final sentence is the landmine. Notice how the description states it
flatly: "An order may not bring a pet's stock below zero." The whole
hands-on phase is about whether the loop turns that sentence into a real
check - and whether a naive implementation survives it.

## Checkpoint 0 (0 min): you understand the task

Before running anything, answer this out loud or to a neighbor: which
sentences in the description are **requirements** that tests must prove,
and which are **behavior** you can implement freely? There is no wrong
answer; the exercise is to notice the distinction.

## Checkpoint 1 (5 min): the spec states the invariant

Run the full loop on the order-placement feature:

```
/speckit.specify A pet store. Users can place an order for a pet. Placing
an order for a pet that is no longer listed as available must fail. A
successful order reduces the pet's available stock by one. Canceling an
order that is still open must restore the pet's stock by one. An order
may not bring a pet's stock below zero.
/speckit.clarify
/speckit.plan The app is a FastAPI service using SQLite for storage and
pytest for tests. Tests are run with "uv run pytest" from the project
root. Name the API module petstore_app.py and expose the app object as
"app". Keep it minimal - no auth, no pagination (a dev-only HTTP client
for TestClient is fine). Reuse the
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

## Checkpoint 2 (18 min): the implementation and its tests exist

**Pass condition**: `pytest` passes in your project. You now have an
implementation of order placement and a test suite. If you are working
from the catalog-only project, the implementation will have added an
`orders` table and `POST /orders` (and possibly a cancel action, e.g.
`POST /orders/{id}/cancel`) to your FastAPI app.

**The hard question**: does the suite include a test that an order for a
zero-stock pet **fails**, and a test that placing an order never drives
stock below zero? Open the test file and look. If the tests only cover the
happy path (order for an in-stock pet succeeds), you have exactly the
landmine: the loop will have produced tests that pass, but the *requirement*
is not asserted.

**See it in the browser**: with the server running
(`uv run uvicorn petstore_app:app --reload`), open
<http://127.0.0.1:8000/docs> and try it like a real pet store: create a
pet with stock 1, place an order for it, then place a second order for
the same pet. Whether that second order **fails in the UI** - or is
silently accepted - is the landmine made visible. Write down what you
see; the debrief will compare notes.

## Checkpoint 3 (26 min): the landmine, or the loop closing

Now run the loop's hard check again - the converge step re-reads the
spec and compares the code to it:

```
/speckit.converge
```

Two outcomes:

- **The loop closes**: converge reports the implementation matches the
  spec. Your tests assert the invariant, the code enforces it, and
  converge finds no gap. The feature is done. *This is the ideal outcome
  and the payoff.*
- **The loop re-enters**: converge points at a missing test or gap in the
  code. A common one: the spec says "must not go below zero" but the
  implementation decrements stock without checking availability first -
  so a sequence of orders can drive stock to -1, and the test suite
  (written from the happy path) never noticed. Converge appends the
  missing task ("write a test asserting an order for zero-stock fails")
  and you re-run implement and converge.

**Either** outcome is a successful exercise. The point is the *loop's*
behavior: it does not let "the tests pass" stand in for "the requirement
is met."

## Debrief (28 min): what just happened

The demonstrable lesson of this phase is that **specs and tests are not
the same thing, and the loop keeps them honest with each other**:

- The spec is the *requirement* (stock must not go below zero).
- The tests are the *assertions* (the invariant is checked).
- The implementation is the *behavior*.
- Converge is the step that verifies all three agree.

A naive implementation - "place an order, decrement stock, done" - passes
tests that only check the happy path, but violates the spec. The loop
catches it exactly because the *requirement* was stated independently of
the code. If you had just told the agent "write an order endpoint," the
agent would have produced the happy-path implementation, the tests would
have passed, and nobody would have noticed the drain below zero until
production.

The loop does not prevent you from writing a bad spec - no process does.
But it makes a *bad or incomplete spec* visible, because the loop's last
step checks the code against the spec you wrote, and it refuses to call
it done when the two disagree.

## If you finish early

Add one more requirement to the order feature and run the loop again, for
example: *"An order that has not been canceled must not be modified after
it is placed."* Watch how the loop carries that requirement through to
converge. This is a positive exercise - it shows how a *complete* spec
produces *verified* code.

Or, for fun (explicitly **outside** the loop): ask the agent, in a fresh
non-spec-kit session, to add a single `index.html` storefront page served
by FastAPI (`StaticFiles`) that lists the pets and places orders against
the API. Hand-written for fun, it does not enter the requirements chain -
notice the contrast with everything you just did through the loop.

Next: [reference](05-reference.md) and [what's next](06-whats-next.md).