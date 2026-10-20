#!/usr/bin/env bash
# Generate the agent-facing skills from the extension commands.
#
# Usage: generate-skills.sh /path/to/project [author]
#
# The skills under .github/skills/ are generated copies of the extension
# command docs under extensions/requirements/commands/ - the commands are
# the source of truth, the skills are the agent-facing distribution
# copies. Agent harnesses use different project skill roots, so the
# generator also writes the same copies into .agents/skills/ (agy and other
# agent-compatible harnesses) or .claude/skills/ (Claude Code) when the
# project's integration has already created that root. After any change to
# a command, regenerate its skill copy: drift between the two fails the
# mirror test (test_extension_skills_match_source_commands). Idempotent:
# re-running overwrites the generated skills with the current command
# bodies, quotes the frontmatter description (a value carrying a
# colon-and-space must never break the YAML), and prunes generator-owned
# skill directories whose command no longer exists. Only the
# generator-owned speckit-requirements-* namespace is pruned; vendored core
# skills are never touched.
set -euo pipefail

HERE=$(cd -- "$(dirname -- "$0")" && pwd)
TARGET=${1:?usage: generate-skills.sh /path/to/project [author]}
COMMANDS_DIR="$HERE/../../commands"

# The skill metadata author: the positional argument if given, else the
# manifest's (extension.yml) author field, else the target's basename.
# `generate-skills.sh .` alone must never rewrite the author to the
# literal "." - the manifest author is the project's own record.
MANIFEST="$HERE/../../extension.yml"
if [ -n "${2:-}" ]; then
  AUTHOR=$2
else
  AUTHOR=$(sed -n 's/^  author:[[:space:]]*"\{0,1\}\([^"]*\)"\{0,1\}[[:space:]]*$/\1/p' "$MANIFEST" | head -n1)
  [ -n "$AUTHOR" ] || AUTHOR=$(basename "$TARGET")
fi

[ -d "$COMMANDS_DIR" ] || {
  echo "error: extension commands not found at $COMMANDS_DIR" >&2
  exit 1
}

python3 - "$TARGET" "$AUTHOR" "$COMMANDS_DIR" <<'PY'
import json
import re
import shutil
import sys
from pathlib import Path

target = Path(sys.argv[1])
author = sys.argv[2]
commands = sorted(Path(sys.argv[3]).glob("*.md"))
assert commands, "no extension commands found"

# .github/skills is the common distribution copy (Copilot, and the
# template's OpenCode config). The other roots belong to harnesses that
# install their own core skills there; generate into one only when the
# integration already created it, so a project gets no tree for a harness
# it does not use.
skill_roots = [Path(".github/skills")]
for candidate in (Path(".agents/skills"), Path(".claude/skills")):
    if (target / candidate).is_dir():
        skill_roots.append(candidate)

for cmd in commands:
    lines = cmd.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", f"{cmd}: missing frontmatter"
    close = lines.index("---", 1)
    frontmatter = "\n".join(lines[1:close])
    desc = re.search(r'^description:\s*"?(.+?)"?\s*$', frontmatter, re.M).group(1)
    body = "\n".join(lines[close + 1:]).strip()
    hyphen = cmd.stem.replace(".", "-")
    content = (
        "---\n"
        f"name: {json.dumps(hyphen)}\n"
        f"description: {json.dumps(desc)}\n"
        "compatibility: Requires spec-kit project structure with .specify/ directory\n"
        "metadata:\n"
        f"  author: {json.dumps(author)}\n"
        "  source: extension:requirements\n"
        "---\n\n"
        f"{body}\n"
    )
    for root in skill_roots:
        skill_dir = target / root / hyphen
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        print(f"  + {root}/{hyphen}/SKILL.md")

# Prune stale generated skills: a renamed or removed command must not
# leave its old skill discoverable. Only generator-owned
# speckit-requirements-* directories are candidates - the vendored
# core skills are never touched.
generated = {cmd.stem.replace(".", "-") for cmd in commands}
for root in skill_roots:
    skills = target / root
    if skills.is_dir():
        for stale in sorted(skills.glob("speckit-requirements-*")):
            if stale.name not in generated:
                shutil.rmtree(stale)
                print(f"  - {root}/{stale.name} (removed: no matching command)")
PY
