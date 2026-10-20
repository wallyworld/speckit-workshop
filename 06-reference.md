# 06 - Reference: Commands, Artifacts, Glossary, Errors

The cheat sheet for working with Spec Kit after the workshop.

## Commands

All commands are slash commands run in your agent. The loop commands
operate on the current feature directory (`.specify/feature.json` records
which feature is active); `/speckit.constitution` operates on the project.

| Command | What it does | When to run |
|---|---|---|
| `/speckit.specify <description>` | Creates `specs/NNN-feature/spec.md` from a natural-language description | New feature |
| `/speckit.clarify` | Asks up to 5 targeted questions about underspecified areas; folds answers back into the spec | Any time the spec is thin |
| `/speckit.plan` | Creates `plan.md` (technical design, files, data model) from the spec | After the spec is solid |
| `/speckit.tasks` | Breaks the plan into ordered, testable tasks (`tasks.md`) | After the plan |
| `/speckit.analyze` | Cross-checks spec, plan, and tasks for consistency before implementation; findings feed a remediation pass | After task generation, before implementation |
| `/speckit.implement` | Executes tasks, writes code, runs tests | After tasks |
| `/speckit.converge` | Re-reads spec/plan/tasks, diffs code against them, appends missing work | At the end of every implement iteration |
| `/speckit.taskstoissues` | Deprecated: converts tasks into GitHub issues (the bundled `github` extension provides the namespaced replacement) | Only if you track work externally and have not installed the `github` extension |
| `/speckit.checklist` | Generates a custom checklist for the feature | During planning/review |
| `/speckit.constitution` | Creates/updates the project constitution (principles) | Before the first feature; again only when principles change (not a per-feature loop step) |

Commands are shown in OpenCode's dot form; with agy or Copilot they are
hyphenated (`/speckit-specify`, `/speckit-plan`, ...).

Related CLI commands:

```bash
specify init --here --non-interactive --integration opencode --force   # new project
specify --version                                                      # check CLI
specify preset resolve spec-template                                   # see active template
```

## Clipboard inside the container

The container does not share the host clipboard. opencode may report that
it copied text, but the clipboard sequence can be swallowed by byobu,
tmux, or the terminal. You do not need to copy commands to make progress.

- **Let the agent run the next step.** After a command emits a brief or a
  handoff, reply `run the emitted command` or `continue to the next
  step`. The agent re-reads the artifacts from disk, so a fresh session
  can also continue.
- **Use the tmux buffer.** In byobu, press `Ctrl-b [` to enter copy mode,
  move to the start, press Space, move to the end, press Enter, then
  `Ctrl-b ]` to paste. Byobu's prefix may be `Ctrl-a` in some
  configurations; use the prefix shown in the status bar. This stays
  inside the container.
- **Use the terminal selection.** In Konsole, hold Shift while dragging
  to select text, then `Ctrl+Shift+C`; paste with `Ctrl+Shift+V`. Holding
  Shift bypasses the application's mouse handling.
- **Check the terminal's OSC 52 support.** Some terminals and tmux
  configurations drop OSC 52 clipboard writes. The selection and tmux
  buffer methods above do not depend on it.

If a command still refuses to run without the pasted text, tell the agent
explicitly: "I reviewed the brief; run the emitted core command." That is
the same human approval as pasting it.

## Project location

`/project/petstore` inside the container is `<clone>/petstore` on your host,
because the whole clone is mounted at `/project`. Open that folder in your
IDE; it is git-ignored by the workshop repository and has its own git history.

If `/project/petstore` is missing, re-run `./scripts/workshop.sh` on your
host; it creates the host directory.

## Running the app

Use the launch command recorded in the project's `plan.md` or
`quickstart.md`; the module name varies by run. The two common layouts are:

```bash
uv run uvicorn petstore_app:app --reload --host 0.0.0.0   # plan named petstore_app.py
uv run uvicorn src.main:app --reload --host 0.0.0.0       # src/ package layout
```

- The API is live at <http://127.0.0.1:8000> inside the container; from
  your host browser, use the `hostname:` line from `workshop info` (run
  from your clone; `<workshop-name>.<clone-name>.wp` -
  <http://speckit-ws.speckit-workshop.wp:8000> for a clone named
  `speckit-workshop`), because a host browser cannot reach the
  container's 127.0.0.1.
- For the Phase 1 API, FastAPI auto-serves an interactive, clickable UI at
  `/docs` (Swagger) and `/redoc` (ReDoc). The Phase 2 UI is served at `/`;
  if `/docs` remains routed, it stays available for the JSON API.
- `--reload` restarts the server as you edit; stop it with Ctrl-C.

## Browser tooling for Phase 2

The base container does not include a browser: phases 01-04 do not need
one. Install Chrome on demand from a host terminal in your clone:

```bash
workshop run --uid 0 -- install-browser
```

Then, in the container, install the Python driver in the project:

```bash
cd /project/petstore
uv pip install pytest-playwright
```

Do not run `playwright install`; launch the container Chrome with
`channel="chrome"` (or `--browser-channel=chrome`) and
`--no-sandbox --disable-dev-shm-usage`.

## Artifacts

| Artifact | Path | Contents | Written by |
|---|---|---|---|
| Spec | `specs/NNN-feature/spec.md` | User scenarios, functional requirements (testable), success criteria, assumptions, edge cases | `/speckit.specify`, refined by clarify |
| Plan | `specs/NNN-feature/plan.md` | Technical approach, files, data model, interface design | `/speckit.plan` |
| Tasks | `specs/NNN-feature/tasks.md` | Ordered task list, each naming a file (the checkboxes are the plan, not a progress tracker) | `/speckit.tasks`, appended by converge |
| Constitution | `.specify/memory/constitution.md` | Project principles and governance the agent must honor | `specify init` seeds a placeholder; `/speckit.constitution` ratifies or updates it |
| Feature pointer | `.specify/feature.json` | Which feature is active | `/speckit.specify` |

## The closed loop

The constitution is project-level and sits above this loop; plan, analyze,
implement, and converge read it.

```
specify -> clarify -> plan -> tasks -> analyze -> implement -> converge
  ^                                                                  |
  +------------------------------------------------------------------+
```

- Analyze cross-checks the written artifacts before implementation; it
  does not inspect code, so converge remains the closing gate.
- The naive version of this is "agent writes code until the tests pass."
  The loop's distinction is that converge re-reads the *spec*, not just
  the tests, and appends missing work rather than declaring done.
- Iterate `implement` + `converge` until converge reports the spec and
  code agree.

## Glossary

| Term | Meaning |
|---|---|
| Spec Kit | A spec-driven development (SDD) process toolkit for agentic coding |
| `specify` | The CLI that installs the agent integration and commands |
| Constitution | Project-level principles in `.specify/memory/constitution.md`, created or updated by `/speckit.constitution` and read by plan, analyze, implement, and converge |
| Constitution Check | The gate in `plan.md` that evaluates the design against the constitution; a MUST conflict is CRITICAL in analyze and converge |
| Analyze | The read-only check that spec, plan, and tasks agree before implementation |
| `.opencode/commands/` / `.agents/skills/` / `.github/skills/` | The installed command definitions and skills OpenCode, agy, and Copilot load |
| Feature directory | `specs/NNN-name/`; the folder holding spec.md, plan.md, tasks.md |
| Converge | The step that compares code to spec/plan/tasks and restarts the loop if they disagree |
| Testable requirement | A functional requirement that can be verified by a test (as opposed to a sentiment) |
| Potential flaw | A requirement stated in the spec that a naive implementation violates while still passing happy-path tests |
| Closed loop | The property that the loop will not declare "done" while code and spec disagree |
| Extension | An optional pack that adds behaviors to Spec Kit (see [05-whats-next](05-whats-next.md)) |
| Preset | A packaged selection of command/template/script overrides, selectable at `specify init --preset` |
| Bundle | A versioned stack of extensions, presets, and workflows, installed with `specify bundle install` |
| Requirement phrase | A distinctive phrase copied verbatim from a requirement's own wording, used to verify a spec materially contains that requirement (see [new-project-template/README.md](new-project-template/README.md)) |
| Requirement digest | A SHA-256 digest over a requirement's normalized text, recorded in a spec when it claims the requirement; a digest that no longer matches the requirement's current wording marks the claim stale (see [new-project-template/README.md](new-project-template/README.md)) |

## Common errors and fixes

| Error | Fix |
|---|---|
| `/speckit.specify` reports "No feature description provided" | You passed an empty description. Re-run with the text inline. |
| "Feature directory not found" | Run `/speckit.specify` first; it sets `.specify/feature.json`. |
| `specify --version` command not found | `uv tool install specify-cli` was not run, or the tool binary is not on PATH. Re-run the install. |
| `command not found: specify` (or `uv`) in your shell | You are in the host shell, not the workshop container - the sdks live inside it. Re-enter with `workshop shell`. |
| Agent plans against the wrong feature | Check `.specify/feature.json`; if it points at a prior feature, the agent is resolving the wrong directory. |
| Test suite passes but converge complains | Converge compares against the *spec*, not just the tests. The spec likely states a requirement the tests do not assert (see the non-trivial requirement phase). |
| opencode says it copied text, but paste does nothing | The container does not share the host clipboard. See [Clipboard inside the container](#clipboard-inside-the-container); reply `run the emitted command` instead of copying. |
| Plan's Constitution Check is empty or still says "Gates determined based on constitution file", or converge's metrics line reports the constitution principles were skipped | The constitution is still the unfilled seed. Run `/speckit.constitution` and confirm the check in [01](01-setup.md#14-ratify-the-project-constitution) returns nothing. |
| `/speckit.constitution` left `TODO(...)` placeholders | Supply the missing date or version, or rerun with the ratification date and version explicit. |
| uvicorn reports `Could not import module "petstore_app"` when starting the server | The plan named a different app module. Use the launch command from the feature's `plan.md` or `quickstart.md` (`uv run uvicorn src.main:app --reload --host 0.0.0.0`, or the module your plan named). |
| Agent reports `pytest: command not found` | The venv is not activated in the agent's shell. Run tests with `uv run pytest` (see [01](01-setup.md) Section 1.5). |
| `uv pip install` fails for the venv | Run from the project root, after `uv venv` has created `.venv`. |
| Question about whether something is in scope | Ask `/speckit.clarify`, or edit the spec directly. Scope is a spec property, not an implementation detail. |
| Multiple features in one session | Spec Kit is one-feature-per-loop. Start a fresh session for a new feature. |
| `google-chrome: command not found` during Phase 2 | Install it on demand: `workshop run --uid 0 -- install-browser` from a host terminal in your clone. |
| Playwright reports `Executable doesn't exist` or tries to download a browser | Use the container Chrome: `channel="chrome"` (or `--browser-channel=chrome`), and do not run `playwright install`. |
