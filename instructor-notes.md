# Instructor Notes

Delivery guidance for running this workshop instructor-led. The student
materials ([index.md](index.md) through [06-whats-next.md](06-whats-next.md))
are self-contained; these notes cover room logistics, timing management,
and common in-room failure modes that do not belong in the student-facing
pages.

## Timing

The agent's plan and implement steps each take minutes of generating.
Validated with `openrouter/z-ai/glm-4.6`, the hands-on loop measured
~21 minutes of agent work end to end (specify 1 min, clarify with 3
questions, plan 2, tasks 1, implement 11, two converge cycles 3) -
inside its 28-minute slot. The demo loop's artifact steps are similar
(specify 2 min, plan 8, tasks 2), but plan and implement vary most
with the model. Two consequences: pre-run the feature beforehand and
demo it in playback, or narrate over the thinking time; and expect the
overrun to come from clarify and retried commands, not from the
artifact steps.

One failure mode to rehearse: if the agent starts the dev server in
the foreground during implement, the turn hangs on it. Escape does not
always recover the turn; the reliable recovery is to quit the TUI
(Ctrl-C), relaunch `opencode`, and continue - the speckit commands
re-read the artifacts from disk, so nothing is lost. Any message typed
while the turn is stuck queues and runs when the session continues.

The hands-on block targets 28 minutes for a full student loop: hold the
class to the checkpoint pacing in [04-hands-on.md](04-hands-on.md), and
if the room's containers or agents run slow, have students pair up or
start from your pre-run catalog repo (04 permits this; students clone
it into their container home) so the order-placement loop starts from a
warm base. Let the "if you finish early" work run into the debrief.

## Setup (01-setup.md)

Have students run `./scripts/workshop.sh` before the session or as they
walk in: the first container build takes minutes, and the 8-18 setup slot
cannot absorb it. Re-runs are fast (the script only restarts the
container when a mount is stale), so a pre-launch also flushes the
host-side failures - the workshop CLI, snap, the sudo prompt for `yq` -
before the clock starts. The most common in-room failure is a container
that never launches, not a broken project: walk the room at minute 0 and
re-launch anyone whose container is not ready (`workshop info`
prints the status).

Inside the container, the most common failure is a stale or
partially-installed CLI - the "Confirm it works" step at the end is a
hard gate; do not proceed past it until everyone passes it. A student
whose shell says `command not found: specify` is in the host shell,
not the container: send them back in with `workshop shell`.

1.3 also includes the model check: every attendee confirms their
agent's model indicator shows a usable model before the loop starts.
Walk the room there - a dead default or missing auth found at minute
15 is recoverable; the same failure mid-loop is the day's casualty.
Copilot users run `copilot` then `/login` inside the container first
(GitHub device flow; their host credential store does not carry).

This is a rare case where you may want to pre-pin a version for the
room so everyone is on the same CLI. If so, tell them the exact tag to
use. The docs and examples are written against 1.x.

## Core concepts (02-core-concepts.md)

This is the "why" section. Keep it tight - the hands-on phase
demonstrates the loop far better than slides. Target 10-15 minutes with
questions.

## Demo (03-the-loop.md)

Pre-run the loop in your own workshop container (the same launch path as
[01](01-setup.md)); the timing note above covers playback versus
narration.

- Pause after each step and walk through what was produced:
  - After Step 1: open `spec.md` together - the user stories (with
    priorities), the functional requirements (each testable), the
    success criteria, the assumptions. Point out that the agent derived
    the "stock-derived availability" rule from the description.
  - After Step 3: point out that the plan names the concrete files and
    the data model. Call attention to the fact that the plan is written
    *before* any code, and that it is the agent's own work product.
  - After Step 4: walk through a few tasks. Point out that tasks are
    small and each names the file it touches.
  - During Step 5: narrate the test run. This is where the agent's own
    verification loop (run tests, read failures, fix, re-run) becomes
    visible.
  - After Step 6: do not gloss over converge - it is the entire reason
    the session exists.
  - After Step 7: the payoff moment - point out that the API surface
    matches the spec's functional requirements one-to-one: the loop
    produced the interface, not the other way around.

## Hands-on (04-hands-on.md)

Walk around during the checkpoints. The two failure modes you are looking
for are (a) a student whose spec lost the invariant (Checkpoint 1) and
(b) a student whose tests pass but never assert the invariant (Checkpoint
2). Both are correct outcomes - they are the reason the workshop is
hands-on. Use the debrief to surface them with the room, without
singling anyone out.

Run the debrief as a group. Ask the room - anonymously on a shared doc,
or by show of hands - who hit each failure mode. Then use the framing in
the debrief section of 04.

## What's next (06-whats-next.md)

Do not go deep here in the main room. Name the two upstream bundled
extensions, say "the catalog exists," and move on. Drill into whichever
is interesting in Q&A.

If someone in the room works on a large product, the phased-delivery
section is the page to point them at after the workshop; it is not part
of the hands-on loop.

## Why this project

The pet store was chosen because it has a wide requirement surface
(catalog, inventory, orders), distinct independently-testable slices,
and a validation edge (the availability invariant) that a naive
implementation will violate while still passing happy-path tests. That
violation is the teachable moment.
