# Instructor Notes

Delivery guidance for instructors running this workshop. The student
materials are [index.md](index.md) through [05-whats-next.md](05-whats-next.md).

## Timing

The agent's plan and implement steps each take minutes of generating.
NB: I validated with `openrouter/z-ai/glm-4.6`, when I ran it, it took
~20 minutes of agent work end to end (specify 1 min, clarify with 3
questions, plan 2, tasks 1, implement 10, two converge cycles 3).

One failure mode to from my dry run: if the agent starts the dev server in
the foreground during implement, the turn hangs on it. Escape does not
always recover; the reliable recovery is to quit the TUI
(Ctrl-C), relaunch `opencode`, and continue - the speckit commands
re-read the artifacts from disk, so nothing is lost. Any message typed
while the turn is stuck queues and runs when the session continues.

## Setup (01-setup.md)

Have students run `./scripts/workshop.sh` before the session. The first
container build takes minutes. Subsequent are fast (the script only restarts the
container when a mount is stale). Note: `workshop info` prints the status.

Inside the container, the most common failure is a stale or partially-installed
CLI - the "Confirm it works" step at the end is a hard gate. NB: a student whose
shell says `command not found: specify` is in the host shell, not the container:
send them back in with `workshop shell`.

Note: copilot users need to run `copilot` then `/login` inside the container
first (gitHub device flow; their host credential store does not carry like they
do with opencode).

## Core concepts (02-core-concepts.md)

Target 10-15 minutes with questions.

## Demo (03-the-loop.md)

- Notes:
  - after Step 1: open `spec.md` together - the user stories (with
    priorities), the functional requirements, the
    success criteria, the assumptions. Point out that the agent derived
    the "stock-derived availability" rule from the description.
  - after Step 3: point out that the plan names the concrete files and
    the data model. Note the fact that the plan is written
    *before* any code, and that it is the agent's own work product.
  - after Step 4: walk through a few tasks. Point out that tasks are
    small and each names the file it touches.
  - during Step 5: this is where the agent's own
    verification loop (run tests, read failures, fix, re-run) becomes
    visible.
  - after Step 7: the API surface (hopefully)
    matches the spec's functional requirements.

## Refinement (04-the-refinement.md)

The two possible failure modes: (a) a student whose spec lost the requirement
(Checkpoint 1) and (b) a student whose tests pass but never assert the
requirement (Checkpoint 2).

## Why this project

I chose the pet store because it has a decent set of requirements
(catalog, inventory, orders), testable deliverables,
and a validation rule (the stock availability rule) that a naive
implementation will violate while still passing happy-path tests.
