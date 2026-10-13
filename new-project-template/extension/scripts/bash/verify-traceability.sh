#!/usr/bin/env bash
# This extension uses associative arrays and mapfile, both introduced in Bash 4.
if (( BASH_VERSINFO[0] < 4 )); then
  printf '%s\n' \
    "verify-traceability.sh: error: Bash 4 or later is required; found Bash ${BASH_VERSION}." \
    "Install a newer Bash and run this command with that Bash executable." >&2
  exit 2
fi

# Deterministically verify that each requirement a feature spec claims to
# *complete* (its "| FR-### | RQ... | Completes |" mapping rows) is materially
# present in that spec - not just its ID in the trace table. A malformed
# requirement ID inside a Completes cell is a hard error, never a silently
# ignored token: an unparseable claim cannot be allowed to verify OK
# beside well-formed claims.
#
# Read-only: prints a per-requirement verdict to stdout. It never creates or
# edits a branch, spec, plan, tasks, or any file. All failures are actionable
# and exit non-zero. The check is content-based: each completed requirement has
# a curated list of requirement phrases (stable, distinctive wording from the
# requirement); at least one must appear in the spec body. This catches
# transcription drift where a requirement is claimed as complete but never
# represented in the spec.
#
# Every Completes claim is also freshness-checked: the spec must record
# "<ID> sha256:<hex>" where hex is the SHA-256 over the requirement's
# normalized text (trimmed, wrapped lines joined - the same normalized
# text the requirement phrases are validated against). A recorded digest that
# no longer matches the requirement's current wording is STALE; a claimed
# requirement with no recorded digest is UNDIGESTED. Both fail closed: a
# claim that cannot be freshness-checked never passes silently. The
# requirements brief (/speckit-requirements-prepare) emits these digests;
# sha256sum (GNU) or shasum (BSD/macOS) must be available.
#
# Override environment hooks used to localize the check against fixtures:
#   SPECKIT_REQUIREMENTS_FILE  path to REQUIREMENTS.md   (default: repo root)
#   SPECKIT_SPECS_ROOT         directory of specs/*      (default: repo root/specs)
#   SPECKIT_PHRASES_FILE       path to the phrases table (default: the
#                              extension's data/phrases.txt)
#
# Positional arguments: zero or more spec.md files to check. With no arguments
# every spec.md under SPECKIT_SPECS_ROOT is checked. Pass a single spec file
# path to scope the check to one feature.

set -euo pipefail

PROG=$(basename "$0")

err() { printf '%s: error: %s\n' "$PROG" "$1" >&2; }
die() { err "$1"; exit "${2:-1}"; }

trim() {
  local s=$1
  s=${s#"${s%%[![:space:]]*}"}
  s=${s%"${s##*[![:space:]]}"}
  printf '%s' "$s"
}

# sha256_of TEXT: lowercase hex digest, portable across GNU (sha256sum)
# and BSD/macOS (shasum -a 256).
sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    printf '%s' "$1" | sha256sum | cut -d' ' -f1
  else
    printf '%s' "$1" | shasum -a 256 | cut -d' ' -f1
  fi
}

# ---------------------------------------------------------------------------
# Locate source files
# ---------------------------------------------------------------------------
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
find_project_root() {
  local candidate=$1
  while :; do
    if [ -f "$candidate/ROADMAP.md" ] && [ -f "$candidate/REQUIREMENTS.md" ]; then
      printf '%s' "$candidate"
      return 0
    fi
    [ "$candidate" = "/" ] && return 1
    candidate=$(dirname -- "$candidate")
  done
}

resolve_project_root() {
  # Prefer an explicit project dir, then walk up from the script location.
  if [ -n "${SPECIFY_INIT_DIR:-}" ] \
     && [ -f "$SPECIFY_INIT_DIR/ROADMAP.md" ] \
     && [ -f "$SPECIFY_INIT_DIR/REQUIREMENTS.md" ]; then
    printf '%s' "$SPECIFY_INIT_DIR"
    return 0
  fi
  find_project_root "$SCRIPT_DIR"
}

# Resolve the requirements file: an explicit override wins (hermetic runs:
# fixtures, fresh seeds before REQUIREMENTS.md exists must not depend on the
# containing project's state); otherwise discover the project root.
if [ -n "${SPECKIT_REQUIREMENTS_FILE:-}" ]; then
  REQUIREMENTS_FILE=$SPECKIT_REQUIREMENTS_FILE
else
  PROJECT_ROOT=$(resolve_project_root) ||
    die "could not locate project root containing ROADMAP.md and REQUIREMENTS.md (set SPECKIT_REQUIREMENTS_FILE or SPECIFY_INIT_DIR)"
  REQUIREMENTS_FILE=$PROJECT_ROOT/REQUIREMENTS.md
fi

[ -f "$REQUIREMENTS_FILE" ] || die "requirements file not found: $REQUIREMENTS_FILE"

# The discovered project root, when this checkout sits inside one; empty in
# hermetic contexts. Live validation (phrase staleness dies) is when the
# requirements file IS the discovered project's own file - whether it was
# resolved by discovery or explicitly pointed at it.
PROJECT_ROOT=$(resolve_project_root) || PROJECT_ROOT=

# The specs root is needed only for the all-specs default mode (no positional
# arguments); an explicit spec path needs no directory discovery, and a fresh
# project before its first feature has no specs/ tree at all.
if [ "$#" -eq 0 ]; then
  SPECS_ROOT=${SPECKIT_SPECS_ROOT:-${PROJECT_ROOT:+$PROJECT_ROOT/specs}}
  [ -n "$SPECS_ROOT" ] && [ -d "$SPECS_ROOT" ] ||
    die "specs root not found: pass spec.md paths, or run inside a project that has a specs/ tree"
fi

# ---------------------------------------------------------------------------
# Load the curated requirement phrases from the phrases table data file. One line
# per requirement ID: ID|phrase|phrase|... Blank lines and # comments are
# ignored. Every phrase MUST be verbatim (case-insensitive) wording from the
# requirement's own text in REQUIREMENTS.md - validated below so a stale or
# mis-filed phrase (e.g. copying another requirement's wording) is a hard
# error, not a silent false pass. The check passes a claim when the spec body
# contains at least one phrase (matched case-insensitively). Vetted by
# fixtures against a drifted spec and a fully traceable spec, and its
# coverage of REQUIREMENTS.md is asserted by the same suite
# (see extensions/requirements/tests/run-bash-tests.sh).
# ---------------------------------------------------------------------------
PHRASES_FILE=${SPECKIT_PHRASES_FILE:-$SCRIPT_DIR/../../data/phrases.txt}
[ -f "$PHRASES_FILE" ] || die "phrases file not found: $PHRASES_FILE (override with SPECKIT_PHRASES_FILE)"
declare -A PHRASES=()
declare -A PHRASES_SEEN=()
while IFS= read -r _kline || [ -n "$_kline" ]; do
  _kline=$(trim "$_kline")
  [[ -z "$_kline" || "$_kline" == \#* ]] && continue
  [[ "$_kline" == *\|* ]] || die "phrases file line is not 'ID|phrase|...': $_kline"
  _kid=$(trim "${_kline%%|*}")
  if [ -n "${PHRASES_SEEN[$_kid]:-}" ]; then
    die "phrases file has duplicate entry for requirement ID '$_kid'"
  fi
  PHRASES_SEEN[$_kid]=1
  PHRASES[$_kid]=$(trim "${_kline#*|}")
done <"$PHRASES_FILE"
[ "${#PHRASES[@]}" -gt 0 ] || die "phrases file has no entries: $PHRASES_FILE"

# ---------------------------------------------------------------------------
# Parse REQUIREMENTS.md stable bullet IDs -> exact full text. Only indented
# continuation lines belong to a bullet; blank or non-indented lines end it.
# ---------------------------------------------------------------------------
declare -A REQ_TEXT=()
declare -A REQ_SEEN=()
cur_id=""
cur_buf=""

flush_req() {
  [ -n "$cur_id" ] || return 0
  if [ -n "${REQ_SEEN[$cur_id]:-}" ]; then
    die "REQUIREMENTS has duplicate definition for requirement ID '$cur_id'"
  fi
  REQ_SEEN[$cur_id]=1
  REQ_TEXT[$cur_id]=$(trim "$cur_buf")
  cur_id=""
  cur_buf=""
}

while IFS= read -r line || [ -n "$line" ]; do
  if [[ $line =~ ^-[[:space:]]+\*\*([A-Z]+-[0-9]+[a-z]?)\*\*:[[:space:]]?(.*)$ ]]; then
    flush_req
    cur_id=${BASH_REMATCH[1]}
    cur_buf=${BASH_REMATCH[2]}
  elif [ -n "$cur_id" ]; then
    if [[ $line =~ ^[[:space:]]*$ ]]; then
      flush_req
    elif [[ $line =~ ^[[:space:]]+[^[:space:]] ]]; then
      cur_buf="$cur_buf $(trim "$line")"
    else
      flush_req
    fi
  fi
done <"$REQUIREMENTS_FILE"
flush_req

# ---------------------------------------------------------------------------
# Validate every requirement phrase against the requirement's own text: a phrase
# that is not verbatim wording from REQUIREMENTS.md is a stale or mis-filed
# phrase (e.g. QUAL-3 borrowing ART-3's wording), which would otherwise pass
# a spec without the requirement ever being transcribed. Hard error, not a
# silent pass.
# ---------------------------------------------------------------------------
for id in "${!PHRASES[@]}"; do
  if [ -z "${REQ_TEXT[$id]:-}" ]; then
    # A phrase whose ID is absent from the requirements file is stale in live
    # mode (hard error). Against a fixture requirements file (used to
    # localize the claim checks), IDs the fixture does not define are
    # skipped; full validation against the real REQUIREMENTS.md is asserted
    # by the Bash suite, which runs this verifier against it.
    if [ -n "${PROJECT_ROOT:-}" ] \
       && [ "$REQUIREMENTS_FILE" = "$PROJECT_ROOT/REQUIREMENTS.md" ]; then
      die "phrase entry '$id' has no matching requirement in $REQUIREMENTS_FILE (stale phrase?)"
    fi
    continue
  fi
  IFS='|' read -ra _phrases <<<"${PHRASES[$id]}"
  req=$(printf '%s' "${REQ_TEXT[$id]}" | tr '[:upper:]' '[:lower:]')
  for _k in "${_phrases[@]}"; do
    # The requirement text is lowercased; -i makes the phrase comparison
    # case-insensitive both ways, so a requirement phrase that carries the
    # requirement's exact wording in any letter case validates.
    if ! printf '%s' "$req" | grep -Fqi -- "$_k"; then
      die "requirement phrase '$id' -> '$_k' is not verbatim wording of requirement $id in $REQUIREMENTS_FILE (stale or mis-filed phrase)"
    fi
  done
done

# ---------------------------------------------------------------------------
# phrase_hit SPEC_LOWER PHRASE: true when the phrase appears in the lowercased
# spec body as a fixed string (case-insensitive, no regex interpretation).
# ---------------------------------------------------------------------------
phrase_hit() {
  local spec_lower=$1 phrase=$2
  printf '%s' "$spec_lower" | grep -Fqi -- "$phrase"
}

# ---------------------------------------------------------------------------
# verify_spec SPEC_FILE: prints one line per completed requirement and appends
# drifted IDs to DRIFTED. Fails closed when the spec has no Completes rows.
# ---------------------------------------------------------------------------
verify_spec() {
  local spec_file=$1 name resolved line cells id tokens phrases_csv phrase found
  local claimed_count=0 id_l recorded
  local -a spec_drifted=() spec_uncurated=() spec_stale=() spec_undigested=()

  [ -f "$spec_file" ] || die "spec file not found: $spec_file"
  name=$(basename "$(dirname -- "$spec_file")")  # e.g. 001-relation-smoke
  resolved=$(readlink -f "$spec_file") || true
  # Lowercase and collapse all whitespace (including line breaks) to a single
  # space so requirement phrases match across wrapped source lines.
  spec=$(tr '[:upper:]' '[:lower:]' <"$spec_file" | tr -s '[:space:]' ' ')

  while IFS= read -r line || [ -n "$line" ]; do
    line=$(trim "$line")
    [[ $line =~ ^\|[[:space:]]*FR-[0-9]+[[:space:]]*\|(.*)\|[[:space:]]*Completes[[:space:]]*\|$ ]] || continue
    cells=${BASH_REMATCH[1]}
    IFS=',' read -ra tokens <<<"$cells"
    for token in "${tokens[@]}"; do
      id=$(trim "$token")
      # An empty token (a trailing comma) is formatting, not a claim;
      # anything else that does not parse as a requirement ID is a
      # malformed claim and fails closed - a token the verifier cannot
      # parse must never be silently ignored while the well-formed
      # claims around it verify OK.
      [ -n "$id" ] || continue
      if ! [[ $id =~ ^[A-Z]+-[0-9]+[a-z]?$ ]]; then
        err "malformed requirement ID '$id' in a Completes mapping row of $resolved"
        err "(expected ID forms like GREET-1 or TEL-2a); the claim is not skipped"
        return 1
      fi
      claimed_count=$((claimed_count + 1))
      # Freshness: the spec must record "<ID> sha256:<hex>" where hex
      # is the digest of the requirement's normalized text. A digest
      # that no longer matches the current wording is STALE; a claimed
      # requirement with no recorded digest is UNDIGESTED. The pattern
      # is extracted from the whitespace-collapsed spec, so line
      # wrapping cannot hide it.
      id_l=$(printf '%s' "$id" | tr '[:upper:]' '[:lower:]')
      recorded=$(printf '%s' "$spec" \
        | grep -oE "(^|[^a-z0-9])${id_l} sha256:[0-9a-f]{64}" \
        | head -n1 | grep -oE '[0-9a-f]{64}' || true)
      if [ -z "$recorded" ]; then
        printf '  %s %-12s %s\n' "$name" "$id" \
          "UNDIGESTED (no recorded requirement digest in the spec)"
        spec_undigested+=("$id")
      elif [ "$recorded" != "$(sha256_of "${REQ_TEXT[$id]}")" ]; then
        printf '  %s %-12s %s\n' "$name" "$id" \
          "STALE - requirement wording changed since this spec recorded its digest"
        spec_stale+=("$id")
      fi
      phrases_csv=${PHRASES[$id]:-""}
      if [ -z "$phrases_csv" ]; then
        printf '  %s %-12s %s\n' "$name" "$id" "UNCURATED (no requirement phrases for this requirement)"
        spec_uncurated+=("$id")
        continue
      fi
      found=0
      IFS='|' read -ra phrases <<<"$phrases_csv"
      for phrase in "${phrases[@]}"; do
        if phrase_hit "$spec" "$phrase"; then
          printf '  %s %-12s ok   (phrase: %s)\n' "$name" "$id" "$phrase"
          found=1
          break
        fi
      done
      if [ "$found" -eq 0 ]; then
        printf '  %s %-12s DRIFTED - none of { %s } appears in the spec\n' \
          "$name" "$id" "$phrases_csv"
        spec_drifted+=("$id")
      fi
    done
  done <"$spec_file"

  if [ "$claimed_count" -eq 0 ]; then
    err "no '| FR-### | RQ... | Completes |' rows found in $resolved; cannot confirm traceability (fail closed)"
    return 1
  fi
  # Accumulate across specs: the verdict must consider every checked spec,
  # not only the last one.
  if [ "${#spec_drifted[@]}" -gt 0 ]; then
    DRIFTED+=("${spec_drifted[@]}")
  fi
  if [ "${#spec_uncurated[@]}" -gt 0 ]; then
    UNCURATED+=("${spec_uncurated[@]}")
  fi
  if [ "${#spec_stale[@]}" -gt 0 ]; then
    STALE+=("${spec_stale[@]}")
  fi
  if [ "${#spec_undigested[@]}" -gt 0 ]; then
    UNDIGESTED+=("${spec_undigested[@]}")
  fi
  TOTAL_CLAIMED=$((TOTAL_CLAIMED + claimed_count))
  return 0
}

# ---------------------------------------------------------------------------
# Select spec files: positional args, or every spec.md under SPECS_ROOT.
# ---------------------------------------------------------------------------
if [ "$#" -gt 0 ]; then
  SPEC_FILES=("$@")
  for f in "$@"; do
    [ -f "$f" ] || die "spec file not found: $f"
  done
else
  mapfile -t SPEC_FILES < <(find "$SPECS_ROOT" -mindepth 2 -maxdepth 2 -name spec.md | sort)
  if [ "${#SPEC_FILES[@]}" -eq 0 ]; then
    die "no spec.md files found under $SPECS_ROOT"
  fi
fi

# ---------------------------------------------------------------------------
# Run.
# ---------------------------------------------------------------------------
TOTAL_CLAIMED=0
DRIFTED=()
UNCURATED=()
STALE=()
UNDIGESTED=()
for spec_file in "${SPEC_FILES[@]}"; do
  verify_spec "$spec_file" || exit 1
done

echo "Requirement traceability"
echo "========================"
echo "Checked ${#SPEC_FILES[@]} spec(s), ${TOTAL_CLAIMED} claimed-complete requirement(s) against:"
echo "  Requirements: $REQUIREMENTS_FILE"
echo

if [ "${#DRIFTED[@]}" -eq 0 ] && [ "${#UNCURATED[@]}" -eq 0 ] \
   && [ "${#STALE[@]}" -eq 0 ] && [ "${#UNDIGESTED[@]}" -eq 0 ]; then
  echo "OK - every claimed-complete requirement has distinctive content in its spec."
  exit 0
fi

if [ "${#DRIFTED[@]}" -gt 0 ]; then
  echo "DRIFT - requirements claimed as complete but absent from the spec:"
  for id in "${DRIFTED[@]}"; do
    printf '  %s\n' "== ${id} =="
    printf '%s\n' "${REQ_TEXT[$id]:-}" | fold -s -w 78 | sed 's/^/     /'
  done
  echo
  echo "Resolve each finding by transcribing the requirement's own wording into the"
  echo "spec, then run a fresh /speckit-requirements-verify to confirm."
fi

if [ "${#UNCURATED[@]}" -gt 0 ]; then
  echo
  echo "CURATE - claimed requirements with no requirement phrases (maintainer action,"
  echo "not a spec defect):"
  for id in "${UNCURATED[@]}"; do
    printf '  %s\n' "== ${id} =="
  done
  echo
  echo "Add verbatim phrases for each ID to the phrases table"
  echo "($PHRASES_FILE) from that requirement's own REQUIREMENTS.md wording,"
  echo "then re-run; the claim cannot be verified until the phrase exists."
fi

if [ "${#STALE[@]}" -gt 0 ]; then
  echo
  echo "STALE - requirements whose current wording no longer matches the"
  echo "digest this spec recorded:"
  for id in "${STALE[@]}"; do
    printf '  %s\n' "== ${id} =="
    printf '%s\n' "${REQ_TEXT[$id]:-}" | fold -s -w 78 | sed 's/^/     /'
  done
  echo
  echo "Resolve each finding by re-verifying the spec against the requirement's"
  echo "current wording and re-recording its digest (the requirements brief"
  echo "emits the current digests), then run a fresh /speckit-requirements-verify."
fi

if [ "${#UNDIGESTED[@]}" -gt 0 ]; then
  echo
  echo "UNDIGESTED - claimed requirements with no recorded digest (every"
  echo "Completes claim must carry '<ID> sha256:<digest>' in its spec):"
  for id in "${UNDIGESTED[@]}"; do
    printf '  %s\n' "== ${id} =="
  done
  echo
  echo "Record each digest from the requirements brief (rerun"
  echo "/speckit-requirements-prepare for the current digests)."
fi
exit 1
