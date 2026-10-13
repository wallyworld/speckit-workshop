# 01 - Setup

Get from "OpenCode installed" to a working Spec Kit project with the pet
store empty skeleton.

## 1.1 Install the `specify` CLI

Spec Kit's CONTROL PLANE is the `specify` CLI. You install it once, per
machine. It does not enter your project.

```bash
# Requires uv (https://docs.astral.sh/uv/#installation)
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

```bash
mkdir petstore && cd petstore
git init
specify init --here --non-interactive --integration opencode --force
```

Notes:

- `--here` initializes in the current directory.
- `--non-interactive` and `--force` let it run unattended (no picker, no
  confirmation prompt). Because `git init` has already created `.git`, the
  directory is not empty, so `--force` is required here (it makes the
  command idempotent).
- `--integration opencode` installs the agent integration for OpenCode.
  Spec Kit works with many agents (Claude, Copilot, Gemini, ...); we use
  OpenCode for this workshop because it is your environment.

## 1.3 Confirm it works

Run this and confirm you see the Spec Kit command list:

```bash
ls .opencode/commands/
```

You should see 10 files: `speckit.specify.md`, `speckit.plan.md`,
`speckit.tasks.md`, `speckit.implement.md`, `speckit.converge.md`, and
others. These are the slash commands your agent will run.

Open the project in OpenCode and confirm the `/speckit` command surface is
available. The exact way you invoke commands depends on your OpenCode
version; the canonical invocation is `/speckit.<command>` (for example
`/speckit.specify`).

Also confirm there are **no** `REQUIREMENTS.md` or `ROADMAP.md` files at
the project root. There should not be. Spec Kit's core is
one-feature-at-a-time; the "phased delivery" concept (a requirements
source, a roadmap mapping many features) is a layer some larger projects
add *on top of* this core - the workshop will show you the core first, and
the [What's next](06-whats-next.md) page mentions the phased layer.

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

`uv run` runs a command inside the project's `.venv` - it is the one
canonical way to run the tests throughout the workshop, because it works
without activating the venv (the agent's shell is not activated).

> If `uv venv` complains that no Python interpreter was found, install
> one explicitly first:
> `uv python install 3.12 && uv venv --python 3.12`

## Summary

| Item | Goal |
|---|---|
| `specify --version` | A current 1.x CLI (1.0 or later) is present |
| `ls .opencode/commands/` | 10 `speckit.*.md` command files |
| OpenCode | `/speckit` commands resolvable |
| No `REQUIREMENTS.md`/`ROADMAP.md` | Confirms you are on the vanilla core |
| `.venv` with fastapi/uvicorn/pytest + HTTP test client | Ready for the build phase |

Next: [Core concepts](02-core-concepts.md).