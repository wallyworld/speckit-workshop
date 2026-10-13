# Agent instructions

- Read `AGENTS.md` and `CONTRIBUTING.md` before making changes.
- Never use em dashes (U+2014) in project-produced artifacts. Use a hyphen
  instead; `tests/test_style.py` is the enforcer and defines the exact
  exclusions (AGENTS.md states the rule). This is a house convention:
  remove it and the test if your project does not want it.
- @FILL-IN@ The commands that define done for your project, and the
  canonical environment they must run in (for example a make target that
  runs the full suite in one invocation).

Repository skills

- This repository publishes agent skills under `.github/skills` (one skill
  per directory, each containing a `SKILL.md` with frontmatter `name` and
  `description`). Many coding agents auto-discover skills from
  `.github/skills`; `.github/copilot-instructions.md` and
  `.opencode/opencode.json` wire the tools that need an explicit pointer.
- The checklist and remediation skills generated from the extension's
  commands carry the phase checklists for any work you author or
  implement in this repository:
  their boundary rules (raise-to-catch, positive-path fixtures,
  malformed-input matrices) apply to every feature you build.
