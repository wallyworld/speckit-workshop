#!/usr/bin/env bash
# Focused, portable tests for the Bash requirements-context assembler.
# No external test framework: plain assertions with a summary and non-zero exit
# on any failure. Runs entirely against in-repo fixtures.

set -u

TESTS_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
FIX="$TESTS_DIR/fixtures"
ASSEMBLE="$TESTS_DIR/../scripts/bash/assemble-brief.sh"
REQ_OK="$FIX/requirements-ok.md"

pass=0
fail=0

ok() { printf '  ok   - %s\n' "$1"; pass=$((pass + 1)); }
bad() { printf '  FAIL - %s\n' "$1"; fail=$((fail + 1)); }

# run ROADMAP_FIXTURE ID -> sets OUT (stdout+stderr) and RC
run() {
  local roadmap=$1 id=$2
  OUT=$(SPECKIT_ROADMAP_FILE="$FIX/$roadmap" SPECKIT_REQUIREMENTS_FILE="$REQ_OK" \
    bash "$ASSEMBLE" $id 2>&1)
  RC=$?
}

assert_success() {
  local name=$1
  if [ "$RC" -eq 0 ]; then ok "$name (exit 0)"; else bad "$name (expected exit 0, got $RC): $OUT"; fi
}

assert_failure() {
  local name=$1
  if [ "$RC" -ne 0 ]; then ok "$name (non-zero exit $RC)"; else bad "$name (expected non-zero exit)"; fi
}

assert_contains() {
  local name=$1 needle=$2
  case "$OUT" in
    *"$needle"*) ok "$name" ;;
    *) bad "$name (missing: $needle)" ;;
  esac
}

echo "Bash assembler tests"
echo "===================="

# 1. Normal R2 assembly, exact golden output.
run roadmap-ok.md R2
assert_success "normal R2 assembly"
if diff -u "$FIX/expected-r2.txt" <(printf '%s\n' "$OUT") >/dev/null 2>&1; then
  ok "normal R2 assembly matches golden output exactly"
else
  bad "normal R2 assembly golden mismatch"
  diff -u "$FIX/expected-r2.txt" <(printf '%s\n' "$OUT") || true
fi
assert_contains "brief cites roadmap ID"        "brief - R2"
assert_contains "brief has Completes text"       "- **AAA-2**: Second requirement on a single line."
assert_contains "brief has Advances text"        "- **BBB-1**: Third requirement, foundational"
assert_contains "brief has coverage seed"        "Roadmap entry: \`ROADMAP.md\` -> **R2**"
assert_contains "brief has ready core command"   "/speckit-specify Deliver the second slice"
assert_contains "brief states human review"      "A human must REVIEW"
assert_contains "brief identifies manual mapping" "mapping remains manual and"

# 2. Malformed IDs.
for badid in R0 RX 2 R2x r2; do
  run roadmap-ok.md "$badid"
  assert_failure "malformed ID '$badid' rejected"
done
# Missing argument.
OUT=$(SPECKIT_ROADMAP_FILE="$FIX/roadmap-ok.md" SPECKIT_REQUIREMENTS_FILE="$REQ_OK" bash "$ASSEMBLE" 2>&1); RC=$?
assert_failure "missing argument rejected"
# Extra whitespace-surrounded values.
run roadmap-ok.md "R2 R3"
assert_failure "extra values rejected"
assert_contains "extra values message actionable" "exactly one roadmap ID"

# 3. Missing row.
run roadmap-ok.md R9
assert_failure "missing roadmap row rejected"
assert_contains "missing row message actionable" "no ROADMAP row found for ID 'R9'"

# 4. Blocked dependency.
run roadmap-blocked.md R2
assert_failure "blocked dependency rejected"
assert_contains "blocked dependency message actionable" "must be 'done'"

# 5. Mapping overlap.
run roadmap-overlap.md R2
assert_failure "Completes/Advances overlap rejected"
assert_contains "overlap message actionable" "both Completes and Advances"

# 6. Missing requirement.
run roadmap-missingreq.md R2
assert_failure "unknown mapped requirement rejected"
assert_contains "missing requirement message actionable" "absent from REQUIREMENTS.md"

# 7. Schema drift.
run roadmap-drift.md R2
assert_failure "roadmap schema drift rejected"
assert_contains "schema drift message actionable" "schema drift"

# 7a. Letter-suffixed requirement IDs in Completes (project grammar, e.g.
# TEL-2a, SCEN-5a, PLATFORM-9a) must be accepted, not silently truncated.
run roadmap-lettersuffix.md R2
assert_success "letter-suffixed completes ID accepted"
assert_contains "letter-suffixed ID included in brief" "Completes: AAA-1a"

echo
echo "Verify tests"
echo "============"
VERIFY="$TESTS_DIR/../scripts/bash/verify-traceability.sh"
REQ_TRACE="$FIX/requirements-trace.md"

# run_verify SPEC [EXPECTED_RC] -> sets OUT and RC. Fully hermetic: the
# requirements file, the phrase table, and the specs root all point at the
# fixtures, so these tests never depend on the containing project's state
# (a fresh seed before its first feature has no specs/ tree at all).
run_verify() {
  local spec=$1
  OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
    SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
    SPECKIT_SPECS_ROOT="$FIX" \
    bash "$VERIFY" "$FIX/$spec" 2>&1)
  RC=$?
}

# 8. Fully traceable spec passes.
run_verify spec-traceable.md
assert_success "traceable spec verifies clean"
assert_contains "traceable confirms OK" "OK"
for id in ART-1 ART-6 PLATFORM-5 TEL-1; do
  assert_contains "traceable covers $id" "$id"
done

# 9. Drifted spec (ART-6 claimed but content absent) fails and names ART-6.
run_verify spec-drifted.md
assert_failure "drifted spec fails (non-zero exit $RC)"
assert_contains "drift names ART-6" "ART-6"
assert_contains "drift reason actionable" "DRIFT"

# 10. No Completes rows fails closed rather than passing vacuously.
run_verify spec-no-completes.md
assert_failure "spec with no Completes rows fails closed"
assert_contains "no-completes message actionable" "cannot confirm traceability"

# 11. Missing spec file is an actionable error.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  bash "$VERIFY" "$FIX/does-not-exist.md" 2>&1); RC=$?
assert_failure "missing spec file rejected"
assert_contains "missing spec message actionable" "spec file not found"

# 12. Missing requirements file is an actionable error.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$FIX/does-not-exist.md" bash "$VERIFY" "$FIX/spec-traceable.md" 2>&1); RC=$?
assert_failure "missing requirements file rejected"
assert_contains "missing requirements message actionable" "requirements file not found"

# 13. A claim is satisfied only by its own requirement's wording, not another
# requirement's (QUAL-3 must not pass because ART-3's wording is present).
run_verify spec-drifted-phrases.md
assert_failure "phrase-distinct spec fails (non-zero exit $RC)"
assert_contains "QUAL-3 not cross-satisfied by ART-3 wording" "QUAL-3"
assert_contains "SCEN-6 not satisfied by generic accounting wording" "SCEN-6"

# 14. A spec claiming multiple Completes RQs, including letter-suffixed ones,
# verifies clean when each has a phrase hit.
run_verify spec-traceable-multi.md
assert_success "multi-RQ traceable spec verifies clean"
assert_contains "multi-RQ traceable confirms OK" "OK"
for id in SCEN-1 TEL-2a TEL-4 QUAL-6; do
  assert_contains "multi-RQ traceable covers $id" "$id"
done

# 15. A drifted spec with multiple Completes RQs fails closed and names each
# drifted RQ, including letter-suffixed IDs.
run_verify spec-drifted-multi.md
assert_failure "multi-RQ drifted spec fails (non-zero exit $RC)"
assert_contains "multi-RQ drift names TEL-2a" "TEL-2a"
assert_contains "multi-RQ drift names QUAL-6" "QUAL-6"
assert_contains "multi-RQ drift reason actionable" "DRIFT"

# 15a. Phrase validation is case-insensitive: a phrase differing from the
# requirement wording only in letter case validates at load time and
# satisfies the spec-side match (which is case-insensitive anyway).
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-case.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-traceable.md" 2>&1); RC=$?
assert_success "case-variant requirement phrases validate and verify clean"
assert_contains "case-variant run confirms OK" "OK"

# 15b. A malformed requirement ID inside a Completes cell fails closed
# instead of being silently ignored: an unparseable claim is a defect,
# not an absence.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-malformed-ids.md" 2>&1); RC=$?
assert_failure "malformed Completes ID rejected"
assert_contains "malformed ID message actionable" "malformed requirement ID"

# 15c. A Completes claim whose recorded requirement digest no longer
# matches the requirement's current wording fails as STALE: the spec
# was written against wording that has since changed.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-stale-digest.md" 2>&1); RC=$?
assert_failure "stale digest rejected"
assert_contains "stale verdict named" "STALE"
assert_contains "stale names the requirement" "PLATFORM-5"

# 15d. A Completes claim with no recorded requirement digest fails as
# UNDIGESTED: a claim that cannot be freshness-checked never passes.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-undigested.md" 2>&1); RC=$?
assert_failure "missing digest rejected"
assert_contains "undigested verdict named" "UNDIGESTED"

# 15e. A recorded digest that is not exactly 64 hex characters - a
# correct 64-hex prefix with trailing alphanumerics included - fails as
# MALFORMED: freshness must never validate on a shared prefix.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-digest-garbage.md" 2>&1); RC=$?
assert_failure "malformed digest rejected"
assert_contains "malformed verdict named" "MALFORMED"

# 15f. A Completes claim for a well-formed ID the requirements source
# does not define fails as UNKNOWN - never an unbound-variable crash -
# when a digest is recorded for it.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-unknown-id.md" 2>&1); RC=$?
assert_failure "unknown requirement rejected"
assert_contains "unknown verdict named" "UNKNOWN"

# 15g. A digest recorded more than once in the requirement-digests
# field is MALFORMED: duplicates are never first-match-wins.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-digest-duplicate.md" 2>&1); RC=$?
assert_failure "duplicate digest rejected"
assert_contains "duplicate verdict named" "more than once"

# 15h. A digest outside the requirement-digests field - prose, a
# comment, an earlier sentence - never satisfies freshness for a
# stale field entry.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-digest-outfield.md" 2>&1); RC=$?
assert_failure "out-of-field digest rejected"
assert_contains "out-of-field still stale" "STALE"

# 15i. A digest token of non-hex characters is MALFORMED, never a
# STALE comparison against the real wording.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-digest-nonhex.md" 2>&1); RC=$?
assert_failure "non-hex digest rejected"
assert_contains "non-hex verdict named" "MALFORMED"

# 15j. A 64-hex digest with a punctuation suffix is MALFORMED, never
# fresh on the shared prefix.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-digest-punct.md" 2>&1); RC=$?
assert_failure "punctuation-suffixed digest rejected"
assert_contains "punctuation-suffix verdict named" "MALFORMED"

# 15k. A second requirement-digests field - a stale or conflicting
# record riding a valid first field - fails the whole spec closed,
# never first-field-wins.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-digest-dupfield.md" 2>&1); RC=$?
assert_failure "duplicate digests field rejected"
assert_contains "duplicate-field error named" "requirement-digests fields"

# 15l. Stray text inside the requirement-digests field is unparsed
# content, never silently ignored.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-digest-stray.md" 2>&1); RC=$?
assert_failure "stray in-field content rejected"
assert_contains "unparsed-content error named" "unparsed content"

# 15m. A phrase entry with a leading, adjacent, or trailing separator is
# an empty phrase field: read drops trailing empties, so the separator
# shape is rejected before the split, never slipped past the field loop.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-separator.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-traceable.md" 2>&1); RC=$?
assert_failure "separator-broken phrase table rejected"
assert_contains "separator table error named" "empty phrase field"

# 15n. A heading at any level following the digests field bounds the
# field - a valid digest list is never rejected because a level-three
# heading leaked into the field as unparsed content.
OUT=$(SPECKIT_REQUIREMENTS_FILE="$REQ_TRACE" \
  SPECKIT_PHRASES_FILE="$FIX/phrases-fixture.txt" \
  SPECKIT_SPECS_ROOT="$FIX" \
  bash "$VERIFY" "$FIX/spec-digest-heading.md" 2>&1); RC=$?
assert_success "heading after digests field bounds the field"
assert_contains "heading fixture confirms OK" "OK"

# 16. The project's phrases table validates against the real
# REQUIREMENTS.md, and every committed spec verifies clean: the verifier
# with no arguments checks every spec.md under specs/ and validates every
# requirement phrase at load time. Skipped on a freshly seeded repository
# before phrases or specs exist; test 17 enforces phrases coverage as soon
# as REQUIREMENTS.md declares IDs.
ROOT_REQUIREMENTS="$TESTS_DIR/../../../REQUIREMENTS.md"
PROJECT_PHRASES="$TESTS_DIR/../data/phrases.txt"
if [ -n "$(grep -vE '^#|^$' "$PROJECT_PHRASES" 2>/dev/null || true)" ] \
   && compgen -G "$TESTS_DIR/../../../specs/*/spec.md" > /dev/null; then
  OUT=$(SPECKIT_REQUIREMENTS_FILE="$ROOT_REQUIREMENTS" bash "$VERIFY" 2>&1); RC=$?
  assert_success "phrases table and every committed spec validate against real REQUIREMENTS.md"
  assert_contains "real-requirements run confirms OK" "OK"
else
  ok "no phrases or no committed specs yet (fresh seed); nothing to validate"
fi

# 17. Phrase coverage is complete: every requirement ID in REQUIREMENTS.md
# has a curated phrases entry, and no entry cites an ID that does not exist
# (a claim with no curated phrase fails closed as a maintainer action).
# Absent sources are a stated skip, never a vacuous pass: an error here
# must never read as "coverage ok".
PHRASES_FILE="$TESTS_DIR/../data/phrases.txt"
if [ ! -f "$ROOT_REQUIREMENTS" ]; then
  ok "no REQUIREMENTS.md yet (fresh seed); coverage activates with it"
elif [ ! -f "$PHRASES_FILE" ]; then
  bad "phrases table not found ($PHRASES_FILE); every REQUIREMENTS ID needs an entry"
elif [ -z "$(grep -vE '^#|^$' "$PHRASES_FILE")" ]; then
  # An all-comments table is a fresh seed only while REQUIREMENTS.md
  # declares no IDs; once it does, an empty table is a vacuous pass,
  # not a fresh seed.
  if grep -qE '^\- \*\*[A-Z]+-[0-9]+[a-z]?\*\*' "$ROOT_REQUIREMENTS"; then
    bad "phrases table is empty but REQUIREMENTS.md declares IDs; every ID needs an entry"
  else
    ok "phrases table still all comments (fresh seed); no IDs declared yet"
  fi
else
  _missing=$(comm -23 \
    <(grep -oE '^\- \*\*[A-Z]+-[0-9]+[a-z]?\*\*' "$ROOT_REQUIREMENTS" | grep -oE '[A-Z]+-[0-9]+[a-z]?' | sort -u) \
    <(grep -vE '^#|^$' "$PHRASES_FILE" | cut -d'|' -f1 | tr -d ' ' | sort -u))
  if [ -z "$_missing" ]; then
    ok "phrases table covers every requirement ID in REQUIREMENTS.md"
  else
    bad "phrases table is missing requirement ID(s): $_missing"
  fi
  # Two-way coverage: an entry citing an ID REQUIREMENTS.md does not
  # define survives one-way checking and lets a deleted requirement's
  # phrases linger as dead weight (and a false coverage signal).
  _extra=$(comm -13 \
    <(grep -oE '^\- \*\*[A-Z]+-[0-9]+[a-z]?\*\*' "$ROOT_REQUIREMENTS" | grep -oE '[A-Z]+-[0-9]+[a-z]?' | sort -u) \
    <(grep -vE '^#|^$' "$PHRASES_FILE" | cut -d'|' -f1 | tr -d ' ' | sort -u))
  if [ -n "$_extra" ]; then
    bad "phrases table cites requirement ID(s) absent from REQUIREMENTS.md: $_extra"
  else
    ok "phrases table cites no IDs absent from REQUIREMENTS.md"
  fi
fi

echo
printf 'Summary: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
