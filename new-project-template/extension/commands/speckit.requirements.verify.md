---
description: "Verify that every requirement a feature spec claims to complete is materially present in that spec (requirement-phrase traceability from REQUIREMENTS.md) and recorded against the requirement's current wording (SHA-256 digest freshness)."
scripts:
  sh: scripts/bash/verify-traceability.sh {ARGS}
---

# Verify requirement-content traceability in a feature spec

Check that each requirement a feature spec claims to *complete* (its
`| FR-### | RQ... | Completes |` mapping rows) is materially represented in
the spec body, not just cited as an ID in the trace table. The check is
**content-based**: each completed requirement has curated requirement phrases
(distinctive wording from `REQUIREMENTS.md`); at least one must appear in
the spec. This catches transcription drift: a requirement claimed as
`Completes` whose distinctive content never appears in the spec body.

The check is also **freshness-based**: every Completes claim must record
`<ID> sha256:<digest>` in the spec, where the digest is the SHA-256 over
the requirement's normalized text. A recorded digest that no longer
matches the requirement's current wording is STALE, and a claim with no
recorded digest is UNDIGESTED; both fail. This catches staleness: a
claim written against requirement wording that has since changed.

This command is **read-only and deterministic**. It never creates or edits a
branch, spec, plan, tasks, or any other file.

## User Input

```text
$ARGUMENTS
```

Optional: zero or more `spec.md` file paths to scope the check to a feature.
With no arguments, every `spec.md` under the project `specs/` directory is
checked. A roadmap ID or any other value is not expected.

## Execution

1. Run the Bash 4+ verifier from the repository root with any provided
   arguments: `extensions/requirements/scripts/bash/verify-traceability.sh $ARGUMENTS`.
2. The script reads `REQUIREMENTS.md` (override `SPECKIT_REQUIREMENTS_FILE`)
   and the chosen `spec.md` files (override `SPECKIT_SPECS_ROOT`), prints one
   line per claimed-complete requirement, and exits non-zero with an
   actionable list of drifted requirement IDs when any claimed requirement
   has no requirement phrase in its spec.
3. **Print the script's stdout verbatim**. Do not summarise, re-order, or
   "resolve" it further, and do not run any core Spec Kit command yourself.

## Output contract

On success (exit 0): `OK - every claimed-complete requirement has distinctive
content in its spec.` On drift (exit 1): `DRIFT` plus the list of requirement
IDs whose content is missing, with the requirement phrases that were not found.
On staleness (exit 1): `STALE` for claimed requirements whose recorded
digest no longer matches their current wording, and `UNDIGESTED` for claims
with no recorded digest. The command never fails closed silently on an
incorrectly parsed spec: a spec with no `Completes` rows is an error, not a
pass.

## Advisory guidance

This is an **advisory** check that surfaces drift for the human to resolve
(by transcribing the required content via core specify - `/speckit.specify`
in OpenCode, `/speckit-specify` on agy or Copilot - or a manual edit). It
does not rewrite the spec.

Before approving a `review-coverage` gate, and before relying on the
converge command reporting "converged", run this command. If any
`Completes` requirement is flagged, stop: the spec claims completion but does
not actually specify the requirement, so convergence cannot be trusted.
