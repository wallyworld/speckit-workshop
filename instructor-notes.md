# Instructor Notes

Delivery guidance for instructors running this workshop. The student
materials are [index.md](index.md) through [06-reference.md](06-reference.md).

## Timing

The agent's plan and implement steps each take minutes of generating.
NB: I validated with `openrouter/z-ai/glm-4.6`, when I ran it, it took
~20 minutes of agent work end to end (specify 1 min, clarify with 3
questions, plan 2, tasks 1, implement 10, two converge cycles 3).

One failure mode from my dry run: if the agent starts the dev server in
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

Note: OpenCode and Antigravity (agy) mount credentials directly from
the host (`~/.config/opencode` and `~/.gemini`), while Copilot users
need to run `copilot` then `/login` inside the container first (GitHub
device flow; their host credential store does not carry).

The script mounts `<clone>/petstore` on the host at `~/petstore` in the
container, so students can open it in their IDE. To reset a student's
project, delete the contents of `<clone>/petstore` on the host and re-run
`./scripts/workshop.sh`; keep the directory itself. Do not delete the
mountpoint inside the container. Containers created before this mount
existed may already have a real `~/petstore` directory; the mount shadows
it, so move or copy that directory aside before re-running.

### Constitution (01 §1.4)

Start `/speckit.constitution` with the prompt in 01. While it runs, have
students open a second byobu window and do §1.5 (venv and dependencies).
It can take 2-4 minutes. The pass condition is that the placeholder check
in 01 returns nothing; if the agent leaves TODOs, resolve them. Do not skip
an unfilled constitution: plan and analyze have no concrete principles to
check, and converge skips it explicitly.

## Core concepts (02-core-concepts.md)

Target 10-15 minutes with questions.

## Demo (03-the-loop.md)

- Notes:
  - before/during Step 1: anticipated question: *"Is typing
    requirements inline into a slash command best practice?"* Explain that
    inline text is the vanilla starting point for single slices, allowing
    students to focus on the closed loop without upfront file boilerplate.
    Mention that in production projects, requirements live in a dedicated
    `REQUIREMENTS.md` file backed by a roadmap, and note that
    ([05-whats-next.md](05-whats-next.md)) will show exactly how to bridge
    from requirements files into Spec Kit.
  - after Step 1: open `spec.md` together - the user stories (with
    priorities), the functional requirements, the
    success criteria, the assumptions. Point out that the agent derived
    the "stock-derived availability" rule from the description.
  - after Step 3: point out that the plan names the concrete files and
    the data model. Note the fact that the plan is written
    *before* any code, and that it is the agent's own work product. Open
    the Constitution Check and ask whether the plan honors the
    tests-required and minimal-stack principles.
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
requirement (Checkpoint 2). After converge, ask whether it cited the
constitution. If it did not, use that to explain the difference between a
written principle and an enforced gate.

## Why this project

I chose the pet store because it has a decent set of requirements
(catalog, inventory, orders), testable deliverables,
and a validation rule (the stock availability rule) that a naive
implementation will violate while still passing happy-path tests.

## What's Next / Phase 2 (05-whats-next.md)

Those who finish early or want to explore multi-phase delivery after the
workshop can build **Phase 2 (Web UI)**. Point them to `05-whats-next.md`:
it is now the step-by-step walkthrough that copies `REQUIREMENTS.md`,
`ROADMAP.md`, and `requirement-phrases.txt` into their existing
`~/petstore` project, bootstraps the requirements extension, runs the
retrofit script for the Phase 1 specs, and drives slice `R3` through the
loop with the hooks firing. `examples/petstore/README.md` is the reference
companion with the file formats and troubleshooting. Those interested in
the enforcement details can read the template README's per-command
section. Do not copy the template constitution by itself: run the full
bootstrap, and note that it keeps the constitution the student already
generated.

