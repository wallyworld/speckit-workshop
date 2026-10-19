# 01 - Setup

You'll get a workshop container and, inside it, a host-mounted petstore
working tree that you will initialize as a Spec Kit project, ratify its
constitution, and build.

## 1.0 Launch your workshop environment

This workshop runs inside a LXC container. This is a fresh Ubuntu 24.04
environment the `workshop` CLI builds from this repository's definition
(`.workshop/speckit-ws.yaml`). Your host needs git, snap, and the
workshop CLI; everything else is provisioned inside the container.

From a clone of this repository on your host:

```bash
./scripts/workshop.sh
```

The first run builds the container (a few minutes) and installs the sdks:
uv, OpenCode, Copilot, Antigravity (agy), and gh. The script also mounts
your existing agent configuration (`~/.config/opencode`, `~/.copilot`,
`~/.gemini`) into the container, so your logins carry over. It creates
`<clone>/petstore` on your host and mounts it at `~/petstore` inside the
container, so you can open that folder in your IDE while the workshop runs.
It installs `yq` on your host via snap if it is missing (that step asks for
sudo). Re-running the script is safe: it refreshes the container and only
restarts it when a mount is stale.

Then connect:

```bash
workshop shell
```

You land in a byobu session, as user `workshop`, with this repository's
materials mounted at `/project`. Everything from here on happens inside this
container. Your build work goes in `~/petstore`, which is mounted from
`<clone>/petstore` on your host; that is the folder to open in your IDE.
`/project` is the shared workshop material, not the petstore this workshop
is building. The same folder also appears at `/project/petstore` because
the whole clone is mounted there; always work through `~/petstore`.

## 1.1 Install the `specify` CLI

Spec Kit's CONTROL PLANE is the `specify` CLI. You install it once, per
environment. It does not enter your project. (uv is already in the
container, as one of the sdks from 1.0.)

```bash
uv tool install specify-cli
```

Confirm it installed:

```bash
specify --version
```

You should see a `1.x` version (1.0 or later). If you see anything
else, or the command is not found:

```bash
# Retry with a specific release (replace X.Y.Z with the latest tag from
# https://github.com/github/spec-kit/releases)
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
```

## 1.2 Create an empty project

**Important**: this workshop starts from scratch. If `<clone>/petstore`
already contains files from an earlier run, delete them on your host first.
Do not copy existing project files into it - you will generate everything
during the workshop.

Create it in your home directory. The workshop script has already mounted
`<clone>/petstore` on your host at `~/petstore`, so your IDE can see the
files:

```bash
cd ~/petstore
mountpoint -q ~/petstore && echo "petstore is host-mounted"
git init
specify init --here --non-interactive --integration opencode --force
```

If `cd ~/petstore` fails or the mountpoint check says nothing, re-run
`./scripts/workshop.sh` on your host. Do not create the directory inside
the container; that would give you a container-only directory the host
cannot see.

Notes:

- `--here` initializes in the current directory.
- `--non-interactive` and `--force` let it run unattended (ie no picker or
  confirmation prompt). Because `git init` has already created `.git`, the
  directory is not empty, so `--force` is required here (it makes the
  command idempotent).
- `--integration opencode` installs the agent integration for OpenCode.
  Spec Kit works with many agents (Claude, Copilot, Gemini, ...); we use
  OpenCode for this workshop.
- Home rather than `/project`: `/project` is the workshop material,
  shared by every attendee; your project is yours, in `~`. The host copy
  `<clone>/petstore` is git-ignored by this repository and has its own git
  history. The same folder is visible at `/project/petstore`; work through
  `~/petstore`.

**Using Antigravity (agy) instead of OpenCode**: run the init with
`--integration agy`; the same commands install as skills under
`.agents/skills/speckit-<command>/SKILL.md` (`/speckit-specify`,
`/speckit-plan`, ...) and you run them inside `agy`. Because `~/.gemini`
is mounted from your host, your Google authentication and configuration
carry directly into the container. `agy` in this workshop is pre-configured
to run with Gemini 3.8 Flash (`gemini-3.8-flash-high`) in autonomous build mode,
auto-applying diffs and commands without prompt fatigue. You can press
`Shift+Tab` inside `agy` at any time to toggle into read-only Plan Mode.

**Using Copilot instead of OpenCode**: run the init with
`--integration copilot`; the same commands install as skills under
`.github/skills/` (`speckit-specify`, `speckit-plan`, ...) and you run
them inside Copilot. Copilot authenticates against GitHub - its host
credential store does not carry into the container - so on first use
run `copilot`, then `/login`, and complete the GitHub device flow.

## 1.3 Confirm it works

Run this and confirm you see the Spec Kit command list:

```bash
# For OpenCode:
ls .opencode/commands/

# Or for Antigravity (agy):
ls .agents/skills/

# Or for Copilot:
ls .github/skills/
```

You should see 10 files (or skill folders), including
`speckit.constitution.md` (or the `speckit-constitution/` skill folder),
`speckit.specify.md`, `speckit.plan.md`, `speckit.tasks.md`,
`speckit.implement.md`, and `speckit.converge.md`. These are the slash
commands your agent will run. (The OpenCode integration creates
`.opencode/commands/`, agy creates `.agents/skills/`, and Copilot creates
`.github/skills/`.)

Open the project in your agent and confirm the `/speckit` command surface is
available: from `~/petstore`, run `opencode` (or `agy` if using Antigravity,
or `copilot` if using Copilot), then in the TUI type `/` and
confirm the `speckit.*` commands appear. While you are there, confirm
your model: the input line shows the active model and provider. If it shows a
model you cannot use - or a provider you have not authenticated - pick
one that works for you before continuing.

Also confirm there are **no** `REQUIREMENTS.md` or `ROADMAP.md` files at
the project root. There should not be. Spec Kit's core is
one-feature-at-a-time; the "phased delivery" concept (a requirements
source, a roadmap mapping many features) is a layer some larger projects
add *on top of* this core - the workshop will show you the core first, and
the [What's next](05-whats-next.md) page mentions the phased delivery layer.

## 1.4 Ratify the project constitution

`specify init` seeded `.specify/memory/constitution.md` from Spec Kit's
template. That file is a scaffold: it still contains `[PROJECT_NAME]` and
`[PRINCIPLE_...]` placeholders. Spec Kit's plan, analyze, implement, and
converge steps read the constitution; an unfilled template gives them no
governance to apply (converge says so explicitly and skips it).

Ratify it now, before the first feature. In the agent, run (dot form):

```
/speckit.constitution Ratify version 1.0.0 of the project constitution today for "petstore". This is governance, not a feature request. Use hyphens instead of em dashes. Principles:
1. Tests gate completion: `uv run pytest` must pass before work is called done.
2. Every new behaviour, including failure paths and domain invariants, has an automated test.
3. The feature spec is the source of truth: code and tests trace back to it, and the implementation does not silently expand scope.
4. Keep the stack minimal and supported: FastAPI, uvicorn, pytest, SQLite; no auth, pagination, or extra application libraries.
5. Surface exact errors and protect credentials and sensitive data.
Amendments are explicit, justified, versioned, and recorded through this command. Keep it concise.
```

With agy or Copilot use `/speckit-constitution`.

The command takes a few minutes. Start it, then open a second byobu
window (F2, or the tmux prefix Ctrl-b c) and do Section 1.5 while it works. When
it finishes, open `.specify/memory/constitution.md` and read the
principles. Check that it is ratified:

```bash
sed -e 's/<!--.*-->//g' -e '/<!--/,/-->/d' .specify/memory/constitution.md \
  | grep -nE '\[[A-Z][A-Z0-9_]*\]'
```

No output means the placeholders are gone (the check exits 1 when clean;
that is expected). The `sed` removes HTML comments, including the
temporary Sync Impact Report, whose "placeholders replaced" lines can name
the tokens without leaving them unfilled. If the command left any
`TODO(...)` items, resolve them before continuing.

> **Do not copy `new-project-template/constitution.md` here.** That
> two-part constitution belongs to the requirements-first template and
> references `REQUIREMENTS.md`, `ROADMAP.md`, `AGENTS.md`, and
> `docs/implementation-mechanics.md`, which this project does not have.
> [05](05-whats-next.md) explains when to adopt the full template.

## 1.5 (For the hands-on) Set up the pet store app dependencies

Later you will build a FastAPI app. Now, in the same `petstore` directory,
create a virtual environment and install the web framework plus a test
runner:

```bash
uv venv
uv pip install fastapi "uvicorn[standard]" pytest httpx
```

(`httpx` is the HTTP client library used by FastAPI's `TestClient` - you
will use it in the tests.)

Confirm the venv works before moving on:

```bash
uv run pytest --version
```

`uv run` runs a command inside the project's `.venv` and is used to
run the tests throughout the workshop because it works
without activating the venv itself.

> If `uv venv` complains that no Python interpreter was found, install
> one explicitly first:
> `uv python install 3.14 && uv venv --python 3.14`

## Summary

| Item | Goal |
|---|---|
| `./scripts/workshop.sh` + `workshop shell` | In-container byobu session as user `workshop` |
| `specify --version` | A current 1.x CLI (1.0 or later) is present |
| `ls .opencode/commands/` (or `.agents/skills/`) | 10 commands or skills, including `speckit.constitution` / `speckit-constitution` |
| OpenCode / agy / Copilot | `/speckit` commands resolvable |
| `.specify/memory/constitution.md` | Ratified v1.0.0; no unfilled template placeholders |
| `~/petstore` -> `<clone>/petstore` | Host-visible working tree; open it in your IDE |
| No `REQUIREMENTS.md`/`ROADMAP.md` | Confirms you are on the vanilla core |
| `.venv` with fastapi/uvicorn/pytest + HTTP test client | Ready for the build phase |

Next: [Core concepts](02-core-concepts.md).