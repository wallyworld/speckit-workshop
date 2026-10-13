# 05 - Reference: Commands, Artifacts, Glossary, Errors

The cheat sheet for working with Spec Kit after the workshop. This is the
page to bookmark.

## Commands

All commands are slash commands run in your agent. They operate on the
current feature directory (`.specify/feature.json` records which feature
is active).

| Command | What it does | When to run |
|---|---|---|
| `/speckit.specify <description>` | Creates `specs/NNN-feature/spec.md` from a natural-language description | New feature |
| `/speckit.clarify` | Asks up to 5 targeted questions about underspecified areas; folds answers back into the spec | Any time the spec is thin |
| `/speckit.plan` | Creates `plan.md` (technical design, files, data model) from the spec | After the spec is solid |
| `/speckit.tasks` | Breaks the plan into ordered, testable tasks (`tasks.md`) | After the plan |
| `/speckit.analyze` | Cross-checks spec, plan, and tasks for consistency; findings feed a remediation loop | After task generation, or after corrections |
| `/speckit.implement` | Executes tasks, writes code, runs tests | After tasks |
| `/speckit.converge` | Re-reads spec/plan/tasks, diffs code against them, appends missing work | At the end of every implement iteration |
| `/speckit.taskstoissues` | Converts tasks into GitHub issues | If you track work externally |
| `/speckit.checklist` | Generates a custom checklist for the feature | During planning/review |
| `/speckit.constitution` | Creates/updates the project constitution (principles) | Project setup, or when rules change |

Related CLI commands:

```bash
specify init --here --non-interactive --integration opencode --force   # new project
specify --version                                                      # check CLI
specify preset resolve spec-template                                   # see active template
```

## Running the app

```bash
uv run uvicorn petstore_app:app --reload
```

- The API is live at <http://127.0.0.1:8000>.
- FastAPI auto-serves an interactive, clickable UI at
  <http://127.0.0.1:8000/docs> (Swagger) and <http://127.0.0.1:8000/redoc>
  (ReDoc) - no frontend code needed to use the pet store from a browser.
- `--reload` restarts the server as you edit; stop it with Ctrl-C.

## Artifacts

| Artifact | Path | Contents | Written by |
|---|---|---|---|
| Spec | `specs/NNN-feature/spec.md` | User stories, functional requirements (testable), success criteria, assumptions, edge cases | `/speckit.specify`, refined by clarify |
| Plan | `specs/NNN-feature/plan.md` | Technical approach, files, data model, interface design | `/speckit.plan` |
| Tasks | `specs/NNN-feature/tasks.md` | Ordered, checked-off task list, each naming a file | `/speckit.tasks`, appended by converge |
| Constitution | `.specify/memory/constitution.md` | Project principles and governance the agent must honor | `/speckit.constitution` |
| Feature pointer | `.specify/feature.json` | Which feature is active | `/speckit.specify` |

## The closed loop

```
specify -> clarify -> plan -> tasks -> implement -> converge
  ^                                                       |
  +-------------------------------------------------------+
```

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
| `.opencode/commands/speckit.*.md` | The installed command definitions OpenCode loads |
| Feature directory | `specs/NNN-name/`; the folder holding spec.md, plan.md, tasks.md |
| Converge | The step that compares code to spec/plan/tasks and restarts the loop if they disagree |
| Testable requirement | A functional requirement that can be verified by a test (as opposed to a sentiment) |
| Landmine | A requirement stated in the spec that a naive implementation violates while still passing happy-path tests |
| Closed loop | The property that the loop will not declare "done" while code and spec disagree |
| Extension | An optional pack that adds behaviors to Spec Kit (see [06](06-whats-next.md)) |
| Preset | A packaged selection of command/template/script overrides, selectable at `specify init --preset` |
| Bundle | A versioned stack of extensions, presets, and workflows, installed with `specify bundle install` |
| Requirement phrase | A distinctive phrase copied verbatim from a requirement's own wording, used to verify a spec materially contains that requirement (see [new-project-template/README.md](new-project-template/README.md)) |
| Requirement digest | A SHA-256 digest over a requirement's normalized text, recorded in a spec when it claims the requirement; a digest that no longer matches the requirement's current wording marks the claim stale (see [new-project-template/README.md](new-project-template/README.md)) |

## Common errors and fixes

| Error | Fix |
|---|---|
| `/speckit.specify` says no feature description | You passed an empty description. Re-run with the text inline. |
| Command says "no feature directory" | Run `/speckit.specify` first; it sets `.specify/feature.json`. |
| `specify --version` command not found | `uv tool install specify-cli` was not run, or the tool binary is not on PATH. Re-run the install. |
| Agent plans against the wrong feature | Check `.specify/feature.json`; if it points at a prior feature, the agent is resolving the wrong directory. |
| Test suite passes but converge complains | Converge compares against the *spec*, not just the tests. The spec likely states a requirement the tests do not assert (see the hands-on landmine). |
| `ModuleNotFoundError: petstore_app` when starting the server | The plan args pinned the module name `petstore_app.py`; if your agent chose a different name, run uvicorn against the module it created (`uv run uvicorn <that-module>:app --reload`). |
| Agent reports `pytest: command not found` | The venv is not activated in the agent's shell. Run tests with `uv run pytest` (see [01](01-setup.md) §1.4). |
| `uv pip install` fails for the venv | Run from the project root, after `uv venv` has created `.venv`. |
| Question about whether something is in scope | Ask `/speckit.clarify`, or edit the spec directly. Scope is a spec property, not an implementation detail. |
| Multiple features in one session | Spec Kit is one-feature-per-loop. Start a fresh session for a new feature. |

Next: [what's next](06-whats-next.md).