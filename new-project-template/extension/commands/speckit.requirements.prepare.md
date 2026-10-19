---
description: "Assemble a deterministic, self-contained requirements-context brief for a single roadmap ID and emit a ready-to-run core /speckit-specify command for human review."
scripts:
  sh: scripts/bash/assemble-brief.sh {ARGS}
---

# Prepare requirements context for a roadmap feature

Assemble a **self-contained feature brief** for one roadmap entry by reading the
project's authoritative, human-maintained `ROADMAP.md` and `REQUIREMENTS.md`,
then print a ready-to-run core `/speckit-specify` command.

This command is **read-only and deterministic**. It does **not** create a
feature directory, branch, `spec.md`, checklist, or any other file, and it
does not alter the product mapping. The `ROADMAP.md` Completes/Advances mapping
remains manual and authoritative; this command resolves that mapping into a
reviewable brief.

## User Input

```text
$ARGUMENTS
```

The input **MUST** be exactly one roadmap ID of the form `R` followed by a
positive integer (for example `R1`, `R2`). Anything else - an empty value,
extra tokens, surrounding words, or a malformed ID - is rejected.

## Execution

1. Run the Bash 4+ assembler from the repository root and pass the roadmap ID
   exactly as given: `extensions/requirements/scripts/bash/assemble-brief.sh $ARGUMENTS`.
2. The script exits non-zero with an actionable message on any error (malformed
   ID, missing roadmap row, a dependency that is not yet `done`, a
   Completes/Advances mapping that overlaps or cites an unknown requirement,
   duplicate IDs, or schema drift). On success it exits zero.
3. **Print the script's stdout verbatim** to the human. Do not summarise,
   re-order, or "resolve" it further. Do not run any core Spec Kit command
   during this command's execution; the human authorizes the next step after
   review.

## Output contract

On success the script prints a brief containing: the roadmap ID and sub-feature,
roadmap status and dependency evidence, the Intent and Scope boundary, the
Completes/Advances requirement IDs, the **exact full requirement text** grouped
by classification, a Requirements Coverage seed (with a SHA-256 digest per
Completes ID, over the requirement's normalized text) that matches the
project's spec template, a suggested spec `Input` line, and a ready-to-run
`/speckit-specify ...` command.

## Human review gate

After presenting the brief, remind the human that:

- they must **review** the assembled brief against `ROADMAP.md` and
  `REQUIREMENTS.md`, and
- they (not this command) run the emitted core `/speckit-specify` command,
  unless they explicitly authorize you to run it after review because their
  environment cannot copy the command. An example authorization is: "I
  reviewed the brief; run the emitted core command."

Core `/speckit-specify` does not resolve roadmap or requirement IDs. This
project extension resolves the existing manual roadmap mapping into the brief;
the human still reviews it before starting core Specify.
