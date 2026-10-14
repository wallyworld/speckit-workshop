#!/usr/bin/env bash
# Generate the agent-facing skills from the extension commands.
#
# Usage: generate-skills.sh /path/to/project [author]
#
# The skills under .github/skills/ are generated copies of the extension
# command docs under extensions/requirements/commands/ - the commands are
# the source of truth, the skills are the agent-facing distribution
# copies. After any change to a command, regenerate its skill copy:
# drift between the two fails the mirror test
# (test_extension_skills_match_source_commands). Idempotent: re-running
# overwrites the generated skills with the current command bodies.
set -euo pipefail

HERE=$(cd -- "$(dirname -- "$0")" && pwd)
TARGET=${1:?usage: generate-skills.sh /path/to/project [author]}
AUTHOR=${2:-$(basename "$TARGET")}
COMMANDS_DIR="$HERE/../../commands"

[ -d "$COMMANDS_DIR" ] || {
  echo "error: extension commands not found at $COMMANDS_DIR" >&2
  exit 1
}

python3 - "$TARGET" "$AUTHOR" "$COMMANDS_DIR" <<'PY'
import re
import sys
from pathlib import Path

target = Path(sys.argv[1])
author = sys.argv[2]
commands = sorted(Path(sys.argv[3]).glob("*.md"))
assert commands, "no extension commands found"
for cmd in commands:
    lines = cmd.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", f"{cmd}: missing frontmatter"
    close = lines.index("---", 1)
    frontmatter = "\n".join(lines[1:close])
    desc = re.search(r'^description:\s*"?(.+?)"?\s*$', frontmatter, re.M).group(1)
    body = "\n".join(lines[close + 1:]).strip()
    hyphen = cmd.stem.replace(".", "-")
    skill_dir = target / ".github/skills" / hyphen
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {hyphen}\n"
        f"description: {desc}\n"
        "compatibility: Requires spec-kit project structure with .specify/ directory\n"
        "metadata:\n"
        f"  author: {author}\n"
        "  source: extension:requirements\n"
        "---\n\n"
        f"{body}\n",
        encoding="utf-8",
    )
    print(f"  + .github/skills/{hyphen}/SKILL.md")
PY
