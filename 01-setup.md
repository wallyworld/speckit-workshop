# 01 - Setup

## 1.0 Launch your workshop environment

The workshop runs in a fresh Ubuntu 24.04 LXC container built by the
`workshop` CLI from `.workshop/speckit-ws.yaml`. Your host needs git,
snap, and the workshop CLI; the container gets everything else.

From a clone of this repository on your host:

```bash
./scripts/workshop.sh
```

The first build can take minutes. Later runs are fast.
The container comes with uv, OpenCode, Copilot, Antigravity (agy), and gh.
The script creates `<clone>/petstore` on your host. The whole clone is mounted
at `/project`, so the generated project lives at `/project/petstore` inside
the container and `<clone>/petstore` on the host. The container can be
rebuilt; the host directory persists.

Agent config and credentials are not mounted from your host. Each agent SDK
keeps its own config in a persistent workshop mount, so sign in inside the
container once and the credential survives later starts and refreshes. Your
host's `~/.config/opencode`, `~/.local/share/opencode`, `~/.copilot`, and
`~/.gemini` - including any skills you have installed there - stay out of
the container.

Re-run the script any time; it refreshes the container. Sections 1.2 and 1.3
cover first use of each agent.

Then connect:

```bash
workshop shell
```

You land in a byobu session as user `workshop`, with the workshop material
at `/project` and your project at `/project/petstore`. The petstore folder is
git-ignored by this repository; `git init` in 1.2 starts its own history.

## 1.1 Install the `specify` CLI

Install `specify` once, in the container. It doesn't live in your project.
uv is already here from 1.0.

```bash
uv tool install specify-cli
```

```bash
specify --version
```

A 1.x version is fine; 1.2.1 is what I ran. If the shell says
`command not found: specify`, you're usually in the host shell, not the
container: run `workshop shell`. If the install is partial or the version
is stale, re-run the install or pin a release:

```bash
# Retry with a specific release (replace X.Y.Z with the latest tag from
# https://github.com/github/spec-kit/releases)
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
```

## 1.2 Create an empty project

If `<clone>/petstore` already has files, clear the contents on
your host and keep the directory. Don't copy an existing project in; you'll
generate everything here.

```bash
cd /project/petstore
git init
specify init --here --non-interactive --integration opencode --force
```

If `cd /project/petstore` fails, re-run `./scripts/workshop.sh` on your host;
it creates the host directory.

`--here` initializes in the current directory; `--non-interactive` skips
the picker; `--force` is needed because `git init` already made the
directory non-empty, and it makes the command idempotent.
`--integration opencode` installs OpenCode's commands. For agy or Copilot,
swap the integration:

**OpenCode:** the default integration. On first use run `opencode auth login`
and choose a provider. The credential is stored in
`~/.local/share/opencode/auth.json`, which its SDK keeps in a persistent
workshop mount, so later runs and refreshes keep the login.

**agy:** `--integration agy` installs skills under
`.agents/skills/speckit-<command>/SKILL.md` (`/speckit-specify`,
`/speckit-plan`, ...). On first use, run `agy` and complete Google sign-in
inside the container. Its SDK keeps `~/.gemini` in a persistent workshop
mount, so later runs and refreshes keep the login. In this workshop, `agy`
runs with
`--mode accept-edits --dangerously-skip-permissions --model gemini-3.8-flash-high`;
`Shift+Tab` toggles read-only Plan Mode.

**Copilot:** `--integration copilot` installs skills under
`.github/skills/` (`speckit-specify`, `speckit-plan`, ...). On first use
run `copilot`, then `/login`, and finish the GitHub device flow. Its SDK
persists the credentials in the workshop, so later runs keep the login.

## 1.3 Confirm it works

```bash
# For OpenCode:
ls .opencode/commands/

# Or for Antigravity (agy):
ls .agents/skills/

# Or for Copilot:
ls .github/skills/
```

Ten commands, as files or skill folders, with `specify` 1.2.1, including
`speckit.constitution.md` (or the `speckit-constitution/` skill folder),
`speckit.specify.md`, `speckit.plan.md`, `speckit.tasks.md`,
`speckit.analyze.md`, `speckit.implement.md`, and `speckit.converge.md`.
The count can drift between 1.x releases; those are the ones to check.

From `/project/petstore`, run `opencode` (or `agy`, or `copilot`), type `/`, and
confirm the Speckit commands appear: `speckit.*` in OpenCode, `speckit-*`
in agy and Copilot. The input line also shows the active model and
provider. Your host's model and provider settings are not mounted, so pick
a model you can use and authenticate inside the container before starting
(`opencode auth login` for OpenCode; the login steps in 1.2 for agy and
Copilot); otherwise the first command can fail.

There shouldn't be `REQUIREMENTS.md` or `ROADMAP.md` at the project root.
If either exists, you're not on the vanilla core; the core is one feature
at a time. [05](05-whats-next.md) covers the phased-delivery layer.

## 1.4 Ratify the project constitution

`specify init` seeded `.specify/memory/constitution.md` from Spec Kit's
template. It's still a scaffold: `[PROJECT_NAME]`, `[PRINCIPLE_...]`
placeholders, no real governance. Plan, analyze, implement, and converge
read it; an unfilled template gives them nothing to apply, and converge
says so and skips the check.

Ratify it before the first feature. Run this in the agent (dot form):

```
/speckit.constitution Ratify version 1.0.0 of the project constitution today for "petstore". This is governance, not a feature request. Use hyphens instead of em dashes. Principles:
1. Tests gate completion: `uv run pytest` must pass before work is called done.
2. Every new behaviour, including failure paths and domain invariants, has an automated test.
3. The feature spec is the source of truth: code and tests trace back to it, and the implementation does not silently expand scope.
4. Keep the runtime stack minimal and supported: FastAPI, uvicorn, pytest, SQLite; no auth, pagination, or extra runtime application libraries. Test-only dependencies used by the acceptance test are allowed.
5. Surface exact errors and protect credentials and sensitive data.
Amendments are explicit, justified, versioned, and recorded through this command. Keep it concise.
```

With agy or Copilot, use `/speckit-constitution`.

Start it, open a second byobu window (F2, or your byobu prefix
then `c`; the status bar shows the prefix), and do Section 1.5
while it runs. When it finishes, read the principles and run the
placeholder check:

```bash
sed -e 's/<!--.*-->//g' -e '/<!--/,/-->/d' .specify/memory/constitution.md \
  | grep -nE '\[[A-Z][A-Z0-9_]*\]'
```

The check exits 1 when clean. The `sed` strips HTML comments, including
the temporary Sync Impact Report, whose "placeholders replaced"
lines can name the tokens without leaving them unfilled. If any
`TODO(...)` items remain, resolve them before continuing.

> **Don't copy `new-project-template/constitution.md` here.** That two-part
> constitution belongs to the requirements-first template and references
> `REQUIREMENTS.md`, `ROADMAP.md`, `AGENTS.md`, and
> `docs/implementation-mechanics.md`, which this project doesn't have.
> [05](05-whats-next.md) explains when to adopt the full template.

## 1.5 (For the hands-on) Set up the pet store app dependencies

The FastAPI app comes later. For now, from `/project/petstore`, create the venv and
install the web framework plus test runner:

```bash
uv venv
uv pip install fastapi "uvicorn[standard]" pytest httpx
```

`httpx` backs FastAPI's `TestClient`; the tests use it. The Phase 2 browser
is installed on demand in [05](05-whats-next.md); phases 01-04 don't need
it.

Check the venv:

```bash
uv run pytest --version
```

It prints pytest's version and exits 0. A missing module means the
install didn't work properly. `uv run` uses the project venv without
activation, which is why the rest of the workshop runs tests this way.

> If `uv venv` can't find an interpreter, install one explicitly first:
> `uv python install 3.14 && uv venv --python 3.14`

## Summary

| Item | Goal |
|---|---|
| `./scripts/workshop.sh` + `workshop shell` | Byobu session as user `workshop` |
| `specify --version` | A current 1.x CLI is present |
| `ls .opencode/commands/` (or `.agents/skills/`) | 10 commands or skills, including `speckit.constitution` / `speckit-constitution` |
| OpenCode / agy / Copilot | Type `/`; Speckit commands appear |
| Host agent config and skills | Not mounted; sign in inside the workshop |
| `.specify/memory/constitution.md` | Ratified v1.0.0; no unfilled template placeholders |
| `/project/petstore` (`<clone>/petstore` on host) | Host-visible working tree; open it in your IDE |
| No `REQUIREMENTS.md`/`ROADMAP.md` | Vanilla core, not the phased-delivery layer |
| `.venv` with fastapi/uvicorn/pytest + HTTP test client | `uv run pytest --version` exits 0 |

Next: [Core concepts](02-core-concepts.md).
