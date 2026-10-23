#!/usr/bin/env python3
"""Retrofit the workshop petstore for phased delivery.

Usage: retrofit-petstore.py [PROJECT_DIR]

PROJECT_DIR defaults to /project/petstore.

Run after:
  1. copying REQUIREMENTS.md, ROADMAP.md, and requirement-phrases.txt
     into the project, and
  2. running new-project-template/bootstrap.sh on the project.

The script is idempotent. It:
  - ensures the requirements extension is registered;
  - seeds or migrates requirement-phrases.txt (a project artifact);
  - fills every @FILL-IN@ skeleton marker with petstore values;
  - appends the sample's domain terms to the enforcement deny list;
  - reconciles ROADMAP.md sub-spec links with real spec directories;
  - adds Requirements Coverage and canonical requirement wording to
    specs authored before the extension was installed;
  - adds an application-test target to make test;
  - replaces em dashes in project-produced files;
  - runs the traceability verifier and make test, and reports the result.

It never overwrites a curated requirement-phrases.txt, never regenerates
phrases, and never touches upstream or runtime surfaces (including
node_modules).
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TEXT_SUFFIXES = {
    ".md", ".py", ".yaml", ".yml", ".sh", ".json", ".rst", ".tf", ".toml", ".txt",
}
EXCLUDED_DIRS = {
    ".git", ".venv", ".terraform", ".idea", "__pycache__", ".pytest_cache",
    "artifacts", "node_modules", "_build", "_dev",
}
EXCLUDED_FILES = {
    "LICENSE", "uv.lock", ".terraform.lock.hcl", ".workshop.lock",
}
EXCLUDED_PREFIXES = (
    ".specify/scripts/",
    ".specify/templates/",
    ".specify/workflows/speckit/",
    ".specify/workflows/workflow-registry.json",
    ".specify/integrations/",
    ".specify/extensions/",
    ".specify/feature.json",
    ".specify/init-options.json",
    ".specify/integration.json",
    ".agents/skills/",
    ".github/skills/",
    ".claude/skills/",
    ".opencode/commands/speckit.",
)
EXCLUDED_INSTALLER_FILES = {".specify/.gitignore"}
ALWAYS_SCAN = {
    ".gitignore",
    ".opencode/.gitignore",
    "Makefile",
    ".workshop/dev-tools/hooks/setup-base",
    ".workshop/dev-tools/hooks/setup-project",
    "gitignore",
    "requirement-phrases.txt.example",
}
EM_DASH = "\u2014"

REQUIREMENT_RE = re.compile(
    r"^- \*\*([A-Z][A-Z0-9]*-[0-9]+[a-z]?)\*\*:\s*(.*)$"
)
FR_RE = re.compile(r"^- \*\*(FR-[0-9]+[a-z]?)\*\*:\s*(.*)$")
COVERAGE_RE = re.compile(r"^##\s+Requirements Coverage", re.M)
ROADMAP_ENTRY_RE = re.compile(
    r"Roadmap entry:\s*`?ROADMAP\.md`?\s*->\s*\*\*(R[0-9]+)\*\*", re.I
)
ROADMAP_LINK_RE = re.compile(r"\[`?([^`\]]+)`?\]\(([^)]+)\)")

STOPWORDS = {
    "a", "an", "and", "any", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "if", "in", "into", "is", "it", "its", "must", "not",
    "of", "on", "or", "that", "the", "their", "then", "there", "these",
    "this", "to", "under", "with", "system", "service", "user", "users",
    "each", "all", "when", "which", "will", "may", "can", "should", "shall",
    "new", "same", "only", "also", "more", "than", "exactly", "any", "one",
}

SAMPLE_HINTS: dict[str, dict[str, int]] = {
    "CAT-1": {"add": 8, "adding": 8, "name": 3, "stock": 1, "initial": 3, "negative": 4},
    "CAT-2": {"list": 8, "derive": 8, "availability": 3, "status": 2, "greater": 4, "zero": 2},
    "CAT-3": {"view": 10, "retrieve": 10, "individual": 3, "identifier": 3, "404": 5, "found": 3},
    "CAT-4": {"delete": 10, "deleting": 10},
    "ORD-1": {"unavailable": 6, "zero": 3, "fail": 4, "error": 3, "prevent": 3, "validate": 4},
    "ORD-2": {"successful": 5, "decrease": 6, "reduce": 5, "exactly": 3, "one": 2},
    "ORD-3": {"below": 5, "zero": 3, "concurrent": 5, "atomic": 7, "prevent": 3},
    "ORD-4": {"cancel": 10, "canceling": 10, "restore": 6, "open": 2},
    "UI-1": {"catalog": 4, "render": 5, "badge": 6, "availability": 3},
    "UI-2": {"form": 5, "creation": 3, "validation": 4, "refresh": 5, "catalog": 2},
    "UI-3": {"order": 2, "action": 3, "disabled": 6, "zero": 3, "stock": 2},
    "UI-4": {"active": 4, "orders": 4, "display": 3, "cancel": 5, "update": 4},
    "UI-5": {"served": 5, "fastapi": 5, "static": 5, "pipeline": 5, "node": 3},
    "UI-6": {"same-origin": 6, "relative": 5, "hardcode": 6, "host or port": 5},
}
CHANGELOG: list[str] = []
PROBLEMS: list[str] = []
REVIEWS: list[str] = []
EM_DASH_FILES: list[str] = []


def log(message: str) -> None:
    CHANGELOG.append(message)
    print(f"  {message}")


def warn(message: str) -> None:
    PROBLEMS.append(message)
    print(f"  WARNING: {message}")


def review(message: str) -> None:
    REVIEWS.append(message)
    print(f"  REVIEW: {message}")


def norm(text: str) -> str:
    return " ".join(text.split()).strip()


def lower_norm(text: str) -> str:
    return norm(text).lower()


def tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= 3 and token not in STOPWORDS
    }


def stem(token: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def subprocess_run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, cwd=str(cwd), capture_output=True, text=True, check=False
    )


def replace_block(path: Path, old: str, new: str, label: str) -> bool:
    if not path.is_file():
        warn(f"{path.name} not found; cannot fill {label}")
        return False
    text = read(path)
    if old not in text:
        return False
    write(path, text.replace(old, new, 1))
    log(f"{path.relative_to(path.parent.parent)}: filled {label}")
    return True


def fill_markers(target: Path) -> None:
    agents = target / "AGENTS.md"
    replace_block(
        agents,
        "@FILL-IN@ One or two paragraphs: what this project is, its layout (the\n"
        "main source directories), and where the product scope and delivery plan\n"
        "live.",
        "This is a Pet Store application built with FastAPI and SQLite. The API "
        "module is `petstore_app.py`, tests live under `tests/`, and feature "
        "specs under `specs/`. Product scope and the delivery plan live in "
        "`REQUIREMENTS.md` and `ROADMAP.md`.",
        "Project description",
    )
    replace_block(
        agents,
        "@FILL-IN@ The commands that define done (for example make targets), the\n"
        "canonical environment they must run in, and any tooling gotchas. State\n"
        "which invocation is the single definition of done.",
        "A successful `make test` means the automated checks are good. The R3 "
        "browser acceptance test uses the container's Google Chrome through "
        "Playwright: launch with `channel=\"chrome\"` and args "
        "`[\"--no-sandbox\", \"--disable-dev-shm-usage\"]` (or pass "
        "`--browser-channel=chrome`), and do not run `playwright install`. "
        "For browser UI changes, the manual host-browser pass in 05 is also "
        "part of done.",
        "Verification",
    )
    replace_block(
        agents,
        "sensitive values. @FILL-IN@ name your project's protected data classes.",
        "sensitive values.",
        "Commitments",
    )
    replace_block(
        agents,
        "- Command surfaces: @FILL-IN@ your project's command entry points (for\n"
        "  example a CLI's subcommands), tested on their real invocation path - the\n"
        "  default or primary route - not only a flagged or synthetic variant.",
        "- Command surfaces: none for a sample web app.",
        "Command surfaces checklist instance",
    )
    replace_block(
        agents,
        "- Coverage-critical artifact kinds: @FILL-IN@ the artifact kinds new code\n"
        "  must cover with tests (for example functions, configurable behaviour,\n"
        "  validators, and query or report surfaces).",
        "- Coverage-critical artifact kinds: unit tests.",
        "Coverage-critical artifact kinds checklist instance",
    )

    contributing = target / "CONTRIBUTING.md"
    replace_block(
        contributing,
        "@FILL-IN@ Dependency installation and the test-gate commands with the\n"
        "canonical environment they must run in.",
        "Run `make install` to create the project virtual environment and install "
        "the mirror-test dependencies (`pytest`, `pyyaml`). The canonical test gate "
        "is `make test`.",
        "Local setup",
    )
    replace_block(
        contributing,
        "@FILL-IN@ Test locations, how to run unit and integration suites, and\n"
        "any build steps the tests require.",
        "Unit tests live under `tests/`. Run `make test` to execute the full "
        "mirror-test suite and the application tests. Individual suites: "
        "`make test-style`, `make test-traceability`, `make test-enforcement`, "
        "`make test-app`.",
        "Running tests",
    )

    agent_instructions = target / "agent-instructions.md"
    replace_block(
        agent_instructions,
        "- @FILL-IN@ The commands that define done for your project, and the\n"
        "  canonical environment they must run in (for example a make target that\n"
        "  runs the full suite in one invocation).",
        "- A clean run of `make test` defines done for automated checks; "
        "browser UI changes also need the manual host-browser pass in 05.",
        "definition of done",
    )

    mechanics = target / "docs" / "implementation-mechanics.md"
    replace_block(
        mechanics,
        "@FILL-IN@ The invocation rules for the external tools this project drives:\n"
        "flag ordering requirements, the exact-error obligation in practice, and the\n"
        "boundaries raw tool commands must stay behind.",
        "This project drives `uv` for environment management and `pytest` for "
        "testing. `uv run pytest` executes the test suite; `uv run uvicorn "
        "petstore_app:app` starts the server. No external CLI tools beyond `uv` "
        "and `specify` are required. Flag ordering is not sensitive for these "
        "tools; the exact-error obligation means never swallowing subprocess exit "
        "codes.",
        "Tool invocation mechanics",
    )
    replace_block(
        mechanics,
        "@FILL-IN@ How operational state is queried through supported interfaces\n"
        "rather than inferred from incidental signals (which query, which signal,\n"
        "and why the wrong signal is wrong).",
        "Operational state is queried through the FastAPI endpoints under the R1/R2 "
        "API prefix (the reference run uses `GET /api/v1/pets`, `GET /api/v1/orders`) "
        "and, for direct database inspection, through SQLite queries "
        "against `pets.db`. Inferring state from log messages or file timestamps is "
        "wrong: the database is the source of truth.",
        "State determination mechanics",
    )
    replace_block(
        mechanics,
        "@FILL-IN@ One section per Part 2 principle that needs binding mechanics:\n"
        "the norm the principle states, and the exact check or procedure that\n"
        "makes it real for this project's systems. Remove this section if no\n"
        "project principle needs one yet.",
        "### Minimal stack (constitution principle, Part 2)\n\n"
        "The application uses FastAPI, SQLite (via the stdlib sqlite3 module), and "
        "pytest only. No additional application libraries are introduced without a "
        "feature-spec justification. The check is manual at review time: a new "
        "import in `petstore_app.py` beyond `fastapi`, `sqlite3`, and `pydantic` "
        "requires justification in the plan.",
        "Project-principle mechanics",
    )

    if agents.is_file():
        text = read(agents)
        updated = text.replace(
            "extensions/requirements/data/phrases.txt", "requirement-phrases.txt"
        )
        if updated != text:
            write(agents, updated)
            log("AGENTS.md: updated requirement phrases path")

    for path in (agents, contributing, agent_instructions, mechanics):
        if path.is_file() and "@FILL-IN@" in read(path):
            warn(f"{path.relative_to(target)} still carries an @FILL-IN@ marker")


def ensure_extension_registered(target: Path) -> bool:
    if (target / ".specify" / "extensions.yml").is_file():
        print("  extension already registered (.specify/extensions.yml)")
        return True
    specify = shutil.which("specify")
    if not specify:
        warn(
            "specify CLI not found; run `specify extension add --dev --force "
            "extensions/requirements` before make test"
        )
        return False
    result = subprocess_run(
        [specify, "extension", "add", "--dev", "--force", "extensions/requirements"],
        target,
    )
    if result.returncode != 0:
        warn(
            "specify extension add failed: "
            + norm(result.stderr or result.stdout or "unknown error")
        )
        return False
    log("registered requirements extension (.specify/extensions.yml)")
    return True


def requirement_ids(target: Path) -> set[str]:
    ids: set[str] = set()
    lines = read(target / "REQUIREMENTS.md").splitlines()
    for line in lines:
        match = REQUIREMENT_RE.match(line)
        if match:
            ids.add(match.group(1))
    return ids


def ensure_phrases(target: Path, script_dir: Path) -> None:
    destination = target / "requirement-phrases.txt"
    curated = script_dir / "requirement-phrases.txt"
    legacy = target / "extensions" / "requirements" / "data" / "phrases.txt"
    ids = requirement_ids(target)

    def has_entries(path: Path) -> bool:
        if not path.is_file():
            return False
        for line in read(path).splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return True
        return False

    if not has_entries(destination):
        if has_entries(legacy):
            shutil.copyfile(legacy, destination)
            log("requirement-phrases.txt: migrated from the legacy extension path")
        elif has_entries(curated):
            shutil.copyfile(curated, destination)
            log("requirement-phrases.txt: seeded from the curated petstore example")
        elif ids:
            warn(
                "requirement-phrases.txt is missing or empty while REQUIREMENTS.md "
                "declares IDs; the verifier will fail closed"
            )
            return
    print(f"  requirement-phrases.txt: {destination}")

    if has_entries(destination):
        removed = []
        installed = (
            target / ".specify" / "extensions" / "requirements" / "data"
            / "phrases.txt"
        )
        for legacy_path in (legacy, installed):
            if legacy_path.is_file():
                legacy_path.unlink()
                removed.append(str(legacy_path.relative_to(target)))
                data_dir = legacy_path.parent
                try:
                    data_dir.rmdir()
                except OSError:
                    pass
        if removed:
            log("removed legacy extension phrases: " + ", ".join(removed))


def ensure_dependencies(target: Path) -> None:
    python = target / ".venv" / "bin" / "python"
    check = None
    if python.is_file():
        try:
            check = subprocess_run(
                [str(python), "-c", "import pytest, yaml"], target
            )
        except OSError:
            check = None
    if check is not None and check.returncode == 0:
        print("  mirror-test dependencies present")
        return
    makefile = target / "Makefile"
    if not makefile.is_file():
        warn("Makefile not found; run bootstrap.sh before this script")
        return
    result = subprocess_run(["make", "install"], target)
    if result.returncode != 0:
        warn("make install failed: " + norm(result.stderr or result.stdout))
    else:
        log("make install: installed the mirror-test dependencies")


def append_domain_terms(target: Path) -> None:
    path = target / "domain-terms.txt"
    existing: set[str] = set()
    if path.is_file():
        for line in read(path).splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                existing.add(stripped)
    additions = [
        term
        for term in ("acme-storefront", "petstore", "pet-catalog")
        if term not in existing
    ]
    if not additions:
        print("  domain terms already present")
        return
    if not path.is_file():
        write(
            path,
            "# Terms naming this project's product, system, or domain.\n"
            "# One per line; comments are ignored.\n",
        )
    text = read(path)
    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n".join(additions) + "\n"
    write(path, text)
    log("domain terms appended to domain-terms.txt: " + ", ".join(additions))


def update_repository_url(target: Path) -> None:
    path = target / "extensions" / "requirements" / "extension.yml"
    if not path.is_file():
        return
    text = read(path)
    if "TODO-your-repo-url" in text:
        write(
            path,
            text.replace(
                "TODO-your-repo-url",
                "https://github.com/wallyworld/speckit-workshop",
            ),
        )
        log("extension.yml: repository URL filled")


def sync_extension_install(target: Path) -> None:
    """Reinstall after editing the extension source (repository URL).

    The installed copy under .specify/extensions/ must stay byte-identical
    to the tracked source; the mirror test fails otherwise.
    """
    source = target / "extensions" / "requirements" / "extension.yml"
    installed = (
        target / ".specify" / "extensions" / "requirements" / "extension.yml"
    )
    if (
        source.is_file()
        and installed.is_file()
        and source.read_bytes() == installed.read_bytes()
    ):
        print("  installed extension already matches the source")
        return
    specify = shutil.which("specify")
    if not specify:
        warn(
            "specify CLI not found; reinstall the extension before make test: "
            "specify extension add --dev --force extensions/requirements"
        )
        return
    result = subprocess_run(
        [specify, "extension", "add", "--dev", "--force", "extensions/requirements"],
        target,
    )
    if result.returncode != 0:
        warn(
            "reinstalling the extension failed: "
            + norm(result.stderr or result.stdout or "unknown error")
        )
        return
    log("reinstalled the extension so the installed copy matches the source")


def spec_dirs(target: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    root = target / "specs"
    if not root.is_dir():
        return result
    for entry in sorted(root.iterdir()):
        if entry.is_dir() and (entry / "spec.md").is_file():
            result[entry.name] = entry
    return result


def roadmap_rows(target: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    path = target / "ROADMAP.md"
    if not path.is_file():
        return rows
    for line in read(path).splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 9 or not re.fullmatch(r"R[0-9]+", cells[0]):
            continue
        rows[cells[0]] = {
            "subfeature": cells[1],
            "intent": cells[2],
            "boundary": cells[3],
            "depends": cells[4],
            "status": cells[5],
            "completes": cells[6],
            "advances": cells[7],
            "subspec": cells[8],
        }
    return rows


def split_ids(value: str) -> list[str]:
    return [
        token.strip()
        for token in value.split(",")
        if token.strip() and token.strip() not in {"-", "(none)", "none"}
    ]


def reconcile_roadmap(target: Path) -> None:
    path = target / "ROADMAP.md"
    if not path.is_file():
        warn("ROADMAP.md not found")
        return
    rows = roadmap_rows(target)
    dirs = spec_dirs(target)
    used: set[str] = set()
    lines = read(path).splitlines()
    changed = False

    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 9 or cells[0] not in rows:
            continue
        row_id = cells[0]
        cell = cells[8]
        link = ROADMAP_LINK_RE.search(cell)
        current = link.group(1) if link else ""
        if current and (target / "specs" / current).is_dir():
            used.add(current)
            continue
        candidates: list[str] = []
        prefix = ""
        if current:
            prefix = current.split("-")[0]
        if not prefix and row_id.startswith("R"):
            prefix = f"{int(row_id[1:]):03d}"
        if prefix:
            candidates = [
                name for name in dirs if name.startswith(prefix + "-") and name not in used
            ]
        if not candidates:
            for name, directory in dirs.items():
                if name in used:
                    continue
                text = read(directory / "spec.md")
                if re.search(rf"\b{re.escape(row_id)}\b", text):
                    candidates.append(name)
        if len(candidates) != 1:
            if candidates:
                warn(
                    f"ROADMAP {row_id}: multiple candidate specs "
                    f"{candidates}; set the Sub-spec link manually"
                )
            continue
        actual = candidates[0]
        used.add(actual)
        replacement = f"[`{actual}`](specs/{actual}/)"
        if link:
            cells[8] = cell[: link.start()] + replacement + cell[link.end() :]
        else:
            cells[8] = replacement
        lines[index] = "| " + " | ".join(cells) + " |"
        changed = True
        log(f"ROADMAP {row_id}: sub-spec link -> {actual}")

    if changed:
        write(path, "\n".join(lines) + "\n")
    else:
        print("  roadmap sub-spec links already match")


def parse_requirement_text(brief: str) -> dict[str, str]:
    texts: dict[str, str] = {}
    in_section = False
    for line in brief.splitlines():
        if line.startswith("Requirement text - Completes"):
            in_section = True
            continue
        if in_section and line.startswith("Requirement text - Advances"):
            break
        if not in_section:
            continue
        match = REQUIREMENT_RE.match(line.rstrip())
        if match:
            texts[match.group(1)] = norm(match.group(2))
    return texts


def brief_for(target: Path, row_id: str) -> str | None:
    script = (
        target / "extensions" / "requirements" / "scripts" / "bash"
        / "assemble-brief.sh"
    )
    if not script.is_file():
        warn(f"assemble-brief.sh not found at {script}")
        return None
    result = subprocess_run(["bash", str(script), row_id], target)
    if result.returncode != 0:
        warn(
            f"assemble-brief.sh {row_id} failed: "
            + norm(result.stderr or result.stdout)
        )
        return None
    return result.stdout


def parse_seed(brief: str) -> dict[str, str] | None:
    seed: dict[str, str] = {}
    for line in brief.splitlines():
        stripped = line.strip()
        if stripped.startswith("Roadmap entry:"):
            seed["roadmap"] = stripped
        elif stripped.startswith("- **Completes**:"):
            seed["completes"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- **Advances**:"):
            seed["advances"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- **Requirement digests**:"):
            seed["digests"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Suggested spec Input line:"):
            break
    if not all(key in seed for key in ("roadmap", "completes", "advances", "digests")):
        return None
    return seed


def parse_fr_blocks(lines: list[str]) -> dict[str, tuple[int, int, str]]:
    blocks: dict[str, tuple[int, int, str]] = {}
    index = 0
    while index < len(lines):
        match = FR_RE.match(lines[index])
        if not match:
            index += 1
            continue
        end = index + 1
        while end < len(lines):
            candidate = lines[end]
            if not candidate.strip():
                break
            if candidate.startswith("- ") or candidate.startswith("#"):
                break
            end += 1
        text = " ".join(line.strip() for line in lines[index:end])
        text = re.sub(
            r"^- \*\*FR-[0-9]+[a-z]?\*\*:\s*", "", text, count=1
        )
        blocks[match.group(1)] = (index, end, norm(text))
        index = end
    return blocks


def score_rq(
    rq_id: str,
    requirement: str,
    fr_text: str,
    document_frequency: dict[str, int],
    document_count: int,
) -> float:
    req_tokens = {stem(token) for token in tokens(requirement)}
    fr_tokens = {stem(token) for token in tokens(fr_text)}
    score = 0.0
    for token in req_tokens & fr_tokens:
        frequency = document_frequency.get(token, 0)
        score += 0.5 * (math.log((document_count + 1) / (frequency + 1)) + 1)
    lowered = fr_text.lower()
    for hint, weight in SAMPLE_HINTS.get(rq_id, {}).items():
        if hint in lowered:
            score += weight
    return score


def map_requirements(
    frs: dict[str, tuple[int, int, str]],
    requirements: dict[str, str],
    completes: list[str],
    advances: list[str],
) -> tuple[dict[str, set[str]], set[str]]:
    document_frequency: dict[str, int] = {}
    for _, _, text in frs.values():
        for token in {stem(value) for value in tokens(text)}:
            document_frequency[token] = document_frequency.get(token, 0) + 1
    scores: dict[tuple[str, str], float] = {}
    for rq in completes + advances:
        for fr, (_, _, text) in frs.items():
            scores[(rq, fr)] = score_rq(
                rq, requirements.get(rq, ""), text, document_frequency, len(frs)
            )

    assignment: dict[str, set[str]] = {fr: set() for fr in frs}
    assigned_fr: dict[str, str] = {}
    provisional: set[str] = set()
    for rq in completes + advances:
        available = [fr for fr in frs if fr not in assigned_fr]
        pool = available or list(frs)
        best = max(pool, key=lambda fr: scores[(rq, fr)])
        if scores[(rq, best)] == 0:
            provisional.add(rq)
        assigned_fr[rq] = best
        assignment[best].add(rq)

    for fr in frs:
        if assignment[fr]:
            continue
        best = max(completes + advances, key=lambda rq: scores[(rq, fr)], default="")
        if best:
            assignment[fr].add(best)
    return assignment, provisional


def render_coverage(
    seed: dict[str, str],
    assignment: dict[str, set[str]],
    completes: set[str],
) -> list[str]:
    lines = [
        "## Requirements Coverage *(mandatory)*",
        "",
        seed["roadmap"],
        "",
        f"- **Completes**: {seed['completes']}",
        f"- **Advances**: {seed['advances']}",
        f"- **Requirement digests**: {seed['digests']}",
        "",
        "| FR | Realizes RQ | Relationship |",
        "| --- | --- | --- |",
    ]
    for fr in sorted(assignment, key=lambda value: int(re.sub(r"\D", "", value))):
        rqs = sorted(assignment[fr])
        if not rqs:
            continue
        completed = [rq for rq in rqs if rq in completes]
        advanced = [rq for rq in rqs if rq not in completes]
        if completed:
            lines.append(f"| {fr} | {', '.join(completed)} | Completes |")
        if advanced:
            lines.append(f"| {fr} | {', '.join(advanced)} | Advances |")
    lines.extend(
        [
            "",
            "Rules:",
            "",
            "- Every FR maps to at least one RQ ID.",
            "- A row's Relationship MUST equal this feature's roadmap classification for",
            "  that RQ (an Advances RQ can only appear as `Advances` here).",
            "- Do not restate RQ text; cite IDs only. No separate register is created.",
        ]
    )
    return lines


def remove_coverage(lines: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        if not re.match(r"^##\s+Requirements Coverage", line):
            continue
        end = index + 1
        while end < len(lines) and not lines[end].startswith("## "):
            end += 1
        return lines[:index] + lines[end:]
    return lines


def insert_coverage(lines: list[str], coverage: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        if re.match(r"^##\s+Success Criteria", line, re.I):
            return lines[:index] + coverage + [""] + lines[index:]
    for index, line in enumerate(lines):
        if re.match(r"^##\s+Assumptions", line, re.I):
            return lines[:index] + coverage + [""] + lines[index:]
    return lines + [""] + coverage


def parse_phrases(path: Path) -> dict[str, list[str]]:
    phrases: dict[str, list[str]] = {}
    if not path.is_file():
        return phrases
    for line in read(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "|" not in stripped:
            continue
        fields = [field.strip() for field in stripped.split("|")]
        if len(fields) > 1 and fields[0]:
            phrases[fields[0]] = [field for field in fields[1:] if field]
    return phrases


COVERAGE_ROW_RE = re.compile(
    r"^\|\s*(FR-[0-9]+[a-z]?)\s*\|\s*([^|]+?)\s*\|\s*(Completes|Advances)\s*\|"
)


def existing_coverage(
    lines: list[str], completes: set[str], advances: set[str]
) -> dict[str, object] | None:
    """Return a valid existing coverage section, or None.

    A human-edited table is preserved: only the roadmap entry, Completes,
    Advances, and digest lines are refreshed. If the table is missing,
    malformed, or its Completes set does not match the roadmap, the caller
    regenerates it.
    """
    start = next(
        (index for index, line in enumerate(lines)
         if re.match(r"^##\s+Requirements Coverage", line)),
        None,
    )
    if start is None:
        return None
    end = start + 1
    while end < len(lines) and not lines[end].startswith("## "):
        end += 1
    section = lines[start:end]
    mapping: dict[str, set[str]] = {}
    indices: dict[str, int] = {}
    valid = True
    for offset, line in enumerate(section):
        stripped = line.strip()
        if stripped.startswith("Roadmap entry:"):
            indices["roadmap"] = start + offset
        elif stripped.startswith("- **Completes**:"):
            indices["completes"] = start + offset
        elif stripped.startswith("- **Advances**:"):
            indices["advances"] = start + offset
        elif stripped.startswith("- **Requirement digests**:"):
            indices["digests"] = start + offset
        match = COVERAGE_ROW_RE.match(stripped)
        if not match:
            continue
        fr, tokens, relation = match.group(1), split_ids(match.group(2)), match.group(3)
        for rq in tokens:
            if rq not in completes and rq not in advances:
                valid = False
            if relation == "Completes" and rq not in completes:
                valid = False
            if relation == "Advances" and rq not in advances:
                valid = False
            mapping.setdefault(fr, set()).add(rq)
    if not valid or not mapping:
        return None
    if not set(completes) <= set().union(*mapping.values()):
        return None
    if not all(key in indices for key in ("roadmap", "completes", "advances", "digests")):
        return None
    return {"mapping": mapping, "indices": indices}


def refresh_coverage_header(
    lines: list[str], info: dict[str, object], seed: dict[str, str]
) -> list[str]:
    indices = info["indices"]  # type: ignore[assignment]
    lines[indices["roadmap"]] = seed["roadmap"]  # type: ignore[index]
    lines[indices["completes"]] = f"- **Completes**: {seed['completes']}"  # type: ignore[index]
    lines[indices["advances"]] = f"- **Advances**: {seed['advances']}"  # type: ignore[index]
    lines[indices["digests"]] = f"- **Requirement digests**: {seed['digests']}"  # type: ignore[index]
    return lines


def patch_spec(target: Path, directory: Path, row_id: str, seed: dict[str, str],
               requirements: dict[str, str], phrases: dict[str, list[str]]) -> None:
    path = directory / "spec.md"
    original = read(path)
    lines = original.splitlines()
    completes = split_ids(seed["completes"])
    advances = split_ids(seed["advances"])

    blocks = parse_fr_blocks(lines)
    if not blocks:
        warn(f"{directory.name}: no FR bullets found; coverage not added")
        return

    existing = existing_coverage(lines, set(completes), set(advances))
    if existing is not None:
        assignment = existing["mapping"]  # type: ignore[assignment]
        provisional: set[str] = set()
    else:
        assignment, provisional = map_requirements(
            blocks, requirements, completes, advances
        )
    normalized = lower_norm("\n".join(lines))

    appended: dict[str, list[str]] = {}
    for rq in completes + advances:
        curated = phrases.get(rq, [])
        if curated and any(lower_norm(phrase) in normalized for phrase in curated):
            continue
        sentence = requirements.get(rq)
        if not sentence:
            warn(f"{directory.name}: no canonical text for {rq}")
            continue
        fr = next(
            (fr for fr, rqs in assignment.items() if rq in rqs), None
        )
        if not fr:
            continue
        start, _, text = blocks[fr]
        if lower_norm(sentence) not in lower_norm(text):
            appended.setdefault(fr, []).append(sentence)

    if appended:
        for fr, sentences in appended.items():
            start, _, _ = blocks[fr]
            lines[start] = lines[start].rstrip() + " " + " ".join(sentences)

    if existing is not None:
        lines = refresh_coverage_header(lines, existing, seed)
    else:
        lines = remove_coverage(lines)
        coverage = render_coverage(seed, assignment, set(completes))
        lines = insert_coverage(lines, coverage)
    updated = "\n".join(lines).rstrip() + "\n"
    if updated == original:
        print(f"  {directory.name}: coverage already present and content unchanged")
        return
    write(path, updated)

    mapping = "; ".join(
        f"{fr} -> {', '.join(sorted(assignment[fr]))}"
        for fr in sorted(assignment, key=lambda value: int(re.sub(r"\D", "", value)))
        if assignment[fr]
    )
    if existing is not None:
        log(
            f"{directory.name}: refreshed the Requirements Coverage header for "
            f"{row_id}; preserved the existing FR table"
        )
    else:
        log(f"{directory.name}: Requirements Coverage for {row_id} ({mapping})")
    if appended:
        log(
            f"{directory.name}: transcribed canonical requirement text into "
            + ", ".join(sorted(appended, key=lambda value: int(re.sub(r"\D", "", value))))
        )
    if provisional:
        review(
            f"{directory.name}: provisional FR mapping for {', '.join(sorted(provisional))}; "
            "review the coverage table"
        )


def spec_row(target: Path, directory: Path, rows: dict[str, dict[str, str]]) -> str | None:
    path = directory / "spec.md"
    text = read(path)
    match = ROADMAP_ENTRY_RE.search(text)
    if match and match.group(1) in rows:
        return match.group(1)
    for line in text.splitlines():
        if line.startswith("**Input**"):
            ids = re.findall(r"\bR[0-9]+\b", line)
            for row_id in ids:
                if row_id in rows:
                    return row_id
    match = re.match(r"([0-9]{3})-", directory.name)
    if match:
        row_id = f"R{int(match.group(1))}"
        if row_id in rows:
            print(f"  {directory.name}: inferred roadmap row {row_id}")
            return row_id
    return None


def patch_specs(target: Path) -> None:
    rows = roadmap_rows(target)
    dirs = spec_dirs(target)
    if not dirs:
        print("  no feature specs found")
        return
    requirements_text: dict[str, str] = {}
    for line in read(target / "REQUIREMENTS.md").splitlines():
        match = REQUIREMENT_RE.match(line)
        if match:
            requirements_text[match.group(1)] = norm(match.group(2))
    phrases = parse_phrases(target / "requirement-phrases.txt")

    for name, directory in dirs.items():
        row_id = spec_row(target, directory, rows)
        if not row_id:
            warn(f"{name}: could not determine roadmap row; coverage not patched")
            continue
        verifier = (
            target / "extensions" / "requirements" / "scripts" / "bash"
            / "verify-traceability.sh"
        )
        if verifier.is_file():
            check = subprocess_run(["bash", str(verifier), str(directory / "spec.md")], target)
            if check.returncode == 0:
                print(f"  {name}: traceability already verifies clean")
                continue
        brief = brief_for(target, row_id)
        if brief is None:
            continue
        seed = parse_seed(brief)
        if seed is None:
            warn(f"{name}: could not parse the coverage seed for {row_id}")
            continue
        canonical = parse_requirement_text(brief)
        merged = {**requirements_text, **canonical}
        patch_spec(target, directory, row_id, seed, merged, phrases)


def add_app_test_gate(target: Path) -> None:
    if not (target / "tests" / "test_petstore.py").is_file():
        return
    makefile = target / "Makefile"
    if not makefile.is_file():
        return
    text = read(makefile)
    changed = False
    lines = text.splitlines()

    def block(lines: list[str], prefix: str) -> tuple[int, int]:
        start = next(
            (index for index, line in enumerate(lines) if line.startswith(prefix)),
            -1,
        )
        if start < 0:
            return (-1, -1)
        end = start
        while end < len(lines):
            end += 1
            if not lines[end - 1].rstrip().endswith("\\"):
                break
        return (start, end)

    phony_start, phony_end = block(lines, ".PHONY:")
    if phony_start >= 0:
        words = " ".join(lines[phony_start:phony_end]).replace("\\", "").split()
        unique = list(dict.fromkeys(words))
        if "test-app" not in unique or len(unique) != len(words):
            if "test-app" not in unique:
                unique.append("test-app")
            lines[phony_start:phony_end] = [" ".join(unique)]
            changed = True

    test_start, test_end = block(lines, "test:")
    if test_start >= 0:
        words = " ".join(lines[test_start:test_end]).replace("\\", "").split()
        unique = list(dict.fromkeys(words))
        if "test-app" not in unique or len(unique) != len(words):
            if "test-app" not in unique:
                unique.append("test-app")
            lines[test_start:test_end] = [" ".join(unique)]
            changed = True

    app_command = [
        "\tuv run pytest tests/ \\",
        "\t\t--ignore=tests/test_style.py \\",
        "\t\t--ignore=tests/test_requirement_traceability.py \\",
        "\t\t--ignore=tests/test_enforcement_chain.py \\",
        "\t\t--ignore=tests/test_workshop_actions.py \\",
        "\t\t--ignore=tests/test_bootstrap_manifest.py -v",
    ]
    app_start = next(
        (index for index, line in enumerate(lines) if line.startswith("test-app:")),
        None,
    )
    if app_start is None:
        insert_at = next(
            (index for index, line in enumerate(lines) if line.startswith("test-extension:")),
            len(lines),
        )
        lines[insert_at:insert_at] = ["test-app:", *app_command, ""]
        changed = True
    else:
        app_end = app_start + 1
        while app_end < len(lines) and lines[app_end].startswith("\t"):
            app_end += 1
        block = "\n".join(lines[app_start:app_end])
        if "--ignore=tests/test_style.py" not in block:
            lines[app_start + 1 : app_end] = app_command
            changed = True

    if changed:
        write(makefile, "\n".join(lines) + "\n")
        log("Makefile: test-app runs all application tests and is included in test")

    allow = target / "tests" / "test_workshop_actions.py"
    if allow.is_file():
        allow_text = read(allow)
        if '"test-app"' not in allow_text:
            allow_text = allow_text.replace(
                '    "test-bootstrap-manifest": "sub-target of test",',
                '    "test-bootstrap-manifest": "sub-target of test",\n'
                '    "test-app": "sub-target of test",',
            )
            write(allow, allow_text)
            log("test_workshop_actions.py: allowlisted test-app")

    pyproject = target / "pyproject.toml"
    if pyproject.is_file():
        py_text = read(pyproject)
        if "pyyaml" not in py_text:
            py_text = py_text.replace(
                'dev = [\n    "pytest",',
                'dev = [\n    "pytest",\n    "pyyaml",',
            )
            write(pyproject, py_text)
            log("pyproject.toml: added pyyaml to the dev dependency group")


def replace_em_dashes(target: Path) -> None:
    for root, dirs, files in os.walk(target, topdown=True):
        dirs[:] = sorted(
            directory
            for directory in dirs
            if directory not in EXCLUDED_DIRS and not directory.endswith(".egg-info")
        )
        for filename in sorted(files):
            path = Path(root) / filename
            try:
                rel = path.relative_to(target)
            except ValueError:
                continue
            if rel.name in EXCLUDED_FILES:
                continue
            if str(rel) in EXCLUDED_INSTALLER_FILES:
                continue
            if any(str(rel).startswith(prefix) for prefix in EXCLUDED_PREFIXES):
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES and str(rel) not in ALWAYS_SCAN:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if EM_DASH not in text:
                continue
            write(path, text.replace(EM_DASH, "-"))
            EM_DASH_FILES.append(str(rel))
    if EM_DASH_FILES:
        log("replaced em dashes in: " + ", ".join(EM_DASH_FILES))
    else:
        print("  no em dashes in project-produced files")


def run_verification(target: Path) -> None:
    verifier = (
        target / "extensions" / "requirements" / "scripts" / "bash"
        / "verify-traceability.sh"
    )
    if verifier.is_file():
        result = subprocess_run(["bash", str(verifier)], target)
        print("\nTraceability verifier:")
        output = (result.stdout or "") + (result.stderr or "")
        print(output.rstrip() or "  (no output)")
        if result.returncode != 0:
            warn("traceability verifier failed")
    if (target / "Makefile").is_file():
        result = subprocess_run(["make", "test"], target)
        print("\nmake test:")
        output = (result.stdout or "") + (result.stderr or "")
        print(output.rstrip() or "  (no output)")
        if result.returncode != 0:
            warn("make test failed")
        else:
            log("make test passed")


def main() -> int:
    target = (
        Path(sys.argv[1]).expanduser().resolve()
        if len(sys.argv) > 1
        else Path("/project/petstore").resolve()
    )
    script_dir = Path(__file__).resolve().parent
    if not target.is_dir():
        print(f"error: {target} is not a directory", file=sys.stderr)
        return 1
    for required in ("REQUIREMENTS.md", "ROADMAP.md", "AGENTS.md"):
        if not (target / required).is_file():
            print(
                f"error: {target / required} not found; run "
                "new-project-template/bootstrap.sh first",
                file=sys.stderr,
            )
            return 1

    print(f"Retrofitting {target} for the petstore example ...")
    ensure_extension_registered(target)
    ensure_phrases(target, script_dir)
    ensure_dependencies(target)
    fill_markers(target)
    append_domain_terms(target)
    update_repository_url(target)
    replace_em_dashes(target)
    if {"REQUIREMENTS.md", "requirement-phrases.txt"} & set(EM_DASH_FILES):
        review(
            "em dashes changed requirement wording or phrases; review "
            "requirement-phrases.txt and the recorded digests"
        )
    sync_extension_install(target)
    reconcile_roadmap(target)
    patch_specs(target)
    add_app_test_gate(target)
    run_verification(target)

    print("\n" + "=" * 72)
    print("Retrofit report")
    print("=" * 72)
    if CHANGELOG:
        for change in CHANGELOG:
            print(f"  - {change}")
    else:
        print("  no changes; the project was already retrofitted")
    if REVIEWS:
        print("\nReview items:")
        for item in REVIEWS:
            print(f"  - {item}")
    if PROBLEMS:
        print("\nOpen problems:")
        for problem in PROBLEMS:
            print(f"  - {problem}")
        return 1
    print("\nNext: review the coverage tables, then run the phased loop for R3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
