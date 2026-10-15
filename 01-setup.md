# 01 - Setup

You'll get a workshop container and, inside it, a working Spec Kit project
with the pet store empty skeleton.

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
uv, OpenCode, Copilot, and gh. The script also mounts your existing agent
configuration (`~/.config/opencode`, `~/.copilot`) into the container, so
your logins carry over, and installs `yq` on your host via snap if it is
missing (that step asks for sudo). Re-running the script is safe: it
refreshes the container and only restarts it when a mount is stale.

Then connect:

```bash
workshop shell
```

You land in a byobu session, as user `workshop`, with this repository's
materials mounted at `/project`. Everything from here on happens inside this
container. Your build work goes in your home directory (`~`), not `/project`,
which is the shared workshop material, not the petstore this workshop is
building.

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

**Important**: this workshop starts from scratch. Do not copy any existing
files into the project - you will generate everything during the workshop.

Create it in your home directory, not under `/project`:

```bash
mkdir ~/petstore && cd ~/petstore
git init
specify init --here --non-interactive --integration opencode --force
```

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
  shared by every attendee; your project is yours, in `~`.

**Using Copilot instead of OpenCode**: run the init with
`--integration copilot`; the same commands install as skills under
`.github/skills/` (`speckit-specify`, `speckit-plan`, ...) and you run
them inside Copilot. Copilot authenticates against GitHub - its host
credential store does not carry into the container - so on first use
run `copilot`, then `/login`, and complete the GitHub device flow.

## 1.3 Confirm it works

Run this and confirm you see the Spec Kit command list:

```bash
ls .opencode/commands/
```

You should see 10 files: `speckit.specify.md`, `speckit.plan.md`,
`speckit.tasks.md`, `speckit.implement.md`, `speckit.converge.md`, and
others. These are the slash commands your agent will run. (The OpenCode
integration creates only `.opencode/commands/`;
there is no plugin install step. specify's output suggests adding
`.opencode/` to your `.gitignore` for credential hygiene - optional
here, the project is throwaway and the credential comes from elsewhere.)

Open the project in OpenCode and confirm the `/speckit` command surface is
available: from `~/petstore`, run `opencode`, then in the TUI type `/` and
confirm the `speckit.*` commands appear. While you are there, confirm
your model: the input line shows the active model and provider (the
build indicator, e.g. `Build · <model> OpenRouter`). If it shows a
model you cannot use - or a provider you have not authenticated - pick
one that works for you before continuing.

Also confirm there are **no** `REQUIREMENTS.md` or `ROADMAP.md` files at
the project root. There should not be. Spec Kit's core is
one-feature-at-a-time; the "phased delivery" concept (a requirements
source, a roadmap mapping many features) is a layer some larger projects
add *on top of* this core - the workshop will show you the core first, and
the [What's next](05-whats-next.md) page mentions the phased delivery layer.

## 1.4 (For the hands-on) Set up the pet store app dependencies

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
| `ls .opencode/commands/` | 10 `speckit.*.md` command files |
| OpenCode | `/speckit` commands resolvable |
| No `REQUIREMENTS.md`/`ROADMAP.md` | Confirms you are on the vanilla core |
| `.venv` with fastapi/uvicorn/pytest + HTTP test client | Ready for the build phase |

Next: [Core concepts](02-core-concepts.md).