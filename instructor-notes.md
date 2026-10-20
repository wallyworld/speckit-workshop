# Instructor Notes

Delivery guidance for instructors running this workshop. The student
materials are [index.md](index.md) through [06-reference.md](06-reference.md).

## Timing

The agent's plan and implement steps each take minutes of generating.
NB: I validated with `openrouter/z-ai/glm-4.6`, when I ran it, it took
~21 minutes of agent work end to end (specify 1 min, clarify with 3
questions, plan 2, tasks 1, analyze 1, implement 10, two converge cycles
3).

One failure mode from my dry run: if the agent starts the dev server in
the foreground during implement, the turn hangs on it. Escape does not
always recover; the reliable recovery is to quit the TUI
(Ctrl-C), relaunch `opencode`, and continue - the speckit commands
re-read the artifacts from disk, so nothing is lost. Any message typed
while the turn is stuck queues and runs when the session continues.

## Setup (01-setup.md)

Have students run `./scripts/workshop.sh` before the session. The first
container build takes minutes. Subsequent runs are fast. Note: `workshop info`
prints the status.

Inside the container, the most common failure is a stale or partially-installed
CLI - the "Confirm it works" step at the end is a hard gate. NB: a student whose
shell says `command not found: specify` is in the host shell, not the container:
send them back in with `workshop shell`.

Note: the workshop does not mount host agent config. Students sign in
inside the container on first use - OpenCode and agy use their normal
login flow, and Copilot users run `copilot` then `/login` (GitHub device
flow). Each agent SDK persists its config and credentials in a workshop
mount, so a refresh or restart does not require signing in again.

Clipboard note: the container does not share the host clipboard, and
OpenCode's copy action can report success while the text never reaches
the terminal. Tell students they can reply `run the emitted command`
instead of pasting, or use the byobu/tmux copy buffer. The workarounds
are in [06 - Reference](06-reference.md#clipboard-inside-the-container).

The whole clone is mounted at `/project`, so `<clone>/petstore` on the host
is `/project/petstore` in the container; students can open it in their IDE.
To reset a student's project, delete the contents of `<clone>/petstore` on
the host and re-run `./scripts/workshop.sh`; keep the directory itself.

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
  - after Step 5: point out that analyze is a read-only cross-check of
    the three artifacts before code exists, and that 05 makes the same
    step mandatory through the extension hooks.
  - during Step 6: this is where the agent's own
    verification loop (run tests, read failures, fix, re-run) becomes
    visible.
  - after Step 8: the API surface (hopefully)
    matches the spec's functional requirements.

## Refinement (04-the-refinement.md)

The two possible failure modes: (a) a student whose spec lost the requirement
(Checkpoint 1) and (b) a student whose tests pass but never assert the
requirement (Checkpoint 2). After analyze, point out that it only checks
the written artifacts. After converge, ask whether it cited the
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
`/project/petstore` project, bootstraps the requirements extension, runs the
retrofit script for the Phase 1 specs, and drives slice `R3` through the
loop with the hooks firing. `examples/petstore/README.md` is the reference
companion with the file formats and troubleshooting. Those interested in
the enforcement details can read the template README's per-command
section. Do not copy the template constitution by itself: run the full
bootstrap, and note that it keeps the constitution the student already
generated.

The base container deliberately has no browser. At Step 5.4, students
install Chrome on demand from a host terminal:
`workshop run --uid 0 -- install-browser` (script:
`scripts/install-browser.sh`). Do not move this into the dev-tools SDK
`setup-base` hook: that makes every student pay the image cost for an
optional phase. The Python driver goes in the project venv with
`uv pip install pytest-playwright`; the test uses the container Chrome with
`channel="chrome"` and `--no-sandbox --disable-dev-shm-usage`.

There is no supplied acceptance checker. The generated acceptance test is
the only automated gate, plus the manual host-browser pass. If a student's
test is API-only or never fails under the mutation, send them back to the
acceptance-test skill's review list.

