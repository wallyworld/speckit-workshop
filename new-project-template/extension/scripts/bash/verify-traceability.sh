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
# Every Completes claim is also freshness-checked: the requirement-digests
# field must record "<ID> sha256:<hex>" where hex is the SHA-256 over the
# requirement's normalized text (trimmed, wrapped lines joined - the same
# normalized text the requirement phrases are validated against). A
# recorded digest that no longer matches the requirement's current wording
# is STALE; a claimed requirement with no recorded digest is UNDIGESTED; a
# digest that is not exactly one 64-hex token - duplicates, non-hex
# characters, punctuation suffixes - is MALFORMED. All fail closed: a
# claim that cannot be freshness-checked never passes silently, and only
# the digests field is read, never prose. The requirements brief
# (from the requirements prepare command) emits these digests; sha256sum
# (GNU) or shasum (BSD/macOS) must be available.
#
# Override environment hooks used to localize the check against fixtures:
#   SPECKIT_REQUIREMENTS_FILE  path to REQUIREMENTS.md   (default: repo root)
#   SPECKIT_SPECS_ROOT         directory of specs/*      (default: repo root/specs)
#   SPECKIT_PHRASES_FILE       path to the phrases table (default: the
#                              requirement-phrases.txt beside the
#                              requirements file)
#
# Positional arguments: zero or more spec.md files to check. With no arguments
# every spec.md under SPECKIT_SPECS_ROOT is checked. Pass a single spec file
# path to scope the check to one feature.

set -euo pipefail

PROG=$(basename "$0")

err() { printf '%s: error: %s\n' "$PROG" "$1" >&2; }
die() { err "$1"; exit "${2:-1}"; }

# canonical_path PATH: absolute physical path, portable (GNU readlink -f
# is unavailable on macOS, and a failing readlink would compare empty
# against empty and silently turn a fixture run into a live one). The
# parent directory must exist - true for every caller here, whose files
# were already checked - and the final component need not.
canonical_path() {
  local _p=$1 _d
  _d=$(dirname -- "$_p")
  if (cd -- "$_d" >/dev/null 2>&1); then
    printf '%s/%s\n' "$(cd -- "$_d" && pwd -P)" "$(basename -- "$_p")"
  else
    printf '%s\n' "$_p"
  fi
}

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
# The phrases table is a project artifact beside REQUIREMENTS.md, outside
# the extension source tree. Resolve it from the requirements file's
# directory so an overridden requirements file never borrows the host
# checkout's table.
_requirements_dir=$(cd -- "$(dirname -- "$REQUIREMENTS_FILE")" && pwd -P)
_default_phrases="$_requirements_dir/requirement-phrases.txt"
PHRASES_FILE=${SPECKIT_PHRASES_FILE:-$_default_phrases}
[ -f "$PHRASES_FILE" ] || die "phrases file not found: $PHRASES_FILE (override with SPECKIT_PHRASES_FILE)"
declare -A PHRASES=()
declare -A PHRASES_SEEN=()
while IFS= read -r _kline || [ -n "$_kline" ]; do
  _kline=$(trim "$_kline")
  [[ -z "$_kline" || "$_kline" == \#* ]] && continue
  [[ "$_kline" == *\|* ]] || die "phrases file line is not 'ID|phrase|...': $_kline"
  _kid=$(trim "${_kline%%|*}")
  [ -n "$_kid" ] \
    || die "phrases file line has an empty requirement ID field: $_kline"
  if [ -n "${PHRASES_SEEN[$_kid]:-}" ]; then
    die "phrases file has duplicate entry for requirement ID '$_kid'"
  fi
  # An empty phrase field matches every spec text (grep of the empty
  # string) and lets a Completes claim pass with no required content;
  # an entry with no fields at all is the same vacuity one field later.
  # Every field must carry non-whitespace text. Separator shapes are
  # rejected before the split: read drops a trailing empty field, so a
  # leading, adjacent, or trailing '|' would otherwise slip an empty
  # phrase past the field loop.
  _phrase_fields=${_kline#*|}
  if [[ "$_phrase_fields" == '|'* || "$_phrase_fields" == *'|' || "$_phrase_fields" == *'||'* ]]; then
    die "phrases file entry for requirement ID '$_kid' has an empty phrase field"
  fi
  _kfields=()
  IFS='|' read -ra _kfields <<<"$_phrase_fields"
  [ "${#_kfields[@]}" -gt 0 ] \
    || die "phrases file entry for requirement ID '$_kid' has no phrase fields"
  for _kf in "${_kfields[@]}"; do
    _kf=$(trim "$_kf")
    [ -n "$_kf" ] \
      || die "phrases file entry for requirement ID '$_kid' has an empty phrase field"
  done
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
    # The live-requirements check compares canonical paths: a caller
    # may pass the live file as a relative path (SPECKIT_REQUIREMENTS_
    # FILE=REQUIREMENTS.md from the project root), and the string
    # comparison would then miss it and treat a stale phrase-table
    # entry as a fixture-only exception instead of failing.
    # canonical_path never fails: an existing requirements file always
    # resolves, and a project root that cannot be resolved falls back
    # to its own path, which never equals a resolved requirements file.
    if [ -n "${PROJECT_ROOT:-}" ] \
       && [ "$(canonical_path "$REQUIREMENTS_FILE")" = "$(canonical_path "$PROJECT_ROOT/REQUIREMENTS.md")" ]; then
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
  local claimed_count=0 id_l recorded digests_field digests_field_count leftovers
  local -a spec_drifted=() spec_uncurated=() spec_stale=() spec_undigested=()
  local -a spec_unknown=() spec_malformed=() dtokens=()

  [ -f "$spec_file" ] || die "spec file not found: $spec_file"
  name=$(basename "$(dirname -- "$spec_file")")  # e.g. 001-relation-smoke
  resolved=$(canonical_path "$spec_file")
  # Lowercase and collapse all whitespace (including line breaks) to a single
  # space so requirement phrases match across wrapped source lines.
  spec=$(tr '[:upper:]' '[:lower:]' <"$spec_file" | tr -s '[:space:]' ' ')
  # The requirement-digests field: the only surface a Completes ID's
  # digest is ever read from. Exactly one field is accepted - a second
  # field is a stale or conflicting record riding a valid one and
  # fails closed, never first-wins. Every entry in it must parse as
  # "<ID> sha256:<token>": prose or stray text inside the field is
  # rejected, never silently ignored. Bounded by the next bullet
  # field, table row, or heading in the collapsed text, so a digest
  # mentioned in prose, a comment, or an earlier sentence never
  # satisfies freshness for a stale or absent field entry, and
  # duplicates inside the field are visible instead of
  # first-match-wins.
  # grep exits 1 on no match; under set -o pipefail the unguarded
  # pipeline would abort the assignment. The guard treats exactly
  # grep's no-match status as a zero count and lets any other failure
  # (a broken pipe, a bad flag) propagate - never masked, never
  # fail-open. The count still counts every occurrence, duplicates
  # included.
  digests_field_count=$(printf '%s' "$spec" \
    | { grep -oF -- "- **requirement digests**: " || [ "$?" -eq 1 ]; } \
    | wc -l)
  if [ "$digests_field_count" -gt 1 ]; then
    err "$resolved carries $digests_field_count requirement-digests fields; exactly one is required - conflicting digest records fail closed"
    return 1
  fi
  digests_field=$(printf '%s' "$spec" | awk '
    {
      m = "- **requirement digests**: "
      i = index($0, m)
      if (i == 0) { print ""; exit }
      r = substr($0, i + length(m))
      c = 0
      if (index(r, " - **") > 0) c = index(r, " - **")
      if (index(r, " | ") > 0 && (c == 0 || index(r, " | ") < c)) c = index(r, " | ")
      if (match(r, " #[#]* ") > 0 && (c == 0 || RSTART < c)) c = RSTART
      if (c > 0) r = substr(r, 1, c - 1)
      print r
    }')
  # Unparsed content: strip every well-formed entry and require that
  # nothing but separators remains. Prose, stray words, or an entry
  # that does not parse as "<ID> sha256:<token>" (an empty token
  # included) fail the whole spec closed.
  if [ -n "$digests_field" ]; then
    leftovers=$(printf '%s' "$digests_field" \
      | sed -E 's/[a-z]+-[0-9]+[a-z]? sha256:[^ ,]+//g' | tr -d ' ,')
    if [ -n "$leftovers" ]; then
      err "requirement-digests field of $resolved carries unparsed content (every entry must be '<ID> sha256:<token>'): ${leftovers:0:70}"
      return 1
    fi
  fi

  while IFS= read -r line || [ -n "$line" ]; do
    line=$(trim "$line")
    [[ $line =~ ^\|[[:space:]]*FR-[0-9]+[a-z]?[[:space:]]*\|(.*)\|[[:space:]]*Completes[[:space:]]*\|$ ]] || continue
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
      # A well-formed ID the requirements source does not define fails
      # closed as UNKNOWN - never an unbound-lookup crash under set -u -
      # and skips the digest and phrase checks, which are meaningless
      # without the requirement text.
      if [ -z "${REQ_TEXT[$id]+x}" ]; then
        printf '  %s %-12s %s\n' "$name" "$id" \
          "UNKNOWN (completes an ID the requirements source does not define)"
        spec_unknown+=("$id")
        continue
      fi
      # Freshness: the Completes ID's digest is recorded in the
      # requirement-digests field as exactly one "sha256:<64 hex>"
      # token. No token there is UNDIGESTED; more than one is
      # MALFORMED (a duplicate or conflicting entry, never
      # first-match-wins); a token that is not exactly 64 hex
      # characters - non-hex letters, punctuation suffixes riding a
      # correct prefix, wrong lengths - is MALFORMED and never
      # freshness-validated on its prefix. Only a well-formed token
      # is compared against the requirement's current wording (a
      # mismatch is STALE). The field is bounded at extraction, so
      # digests outside it never reach this check.
      id_l=$(printf '%s' "$id" | tr '[:upper:]' '[:lower:]')
      dtokens=()
      mapfile -t dtokens < <(printf '%s\n' "$digests_field" \
        | grep -oE "(^|[^a-z0-9])${id_l} sha256:[^ ,]*" || true)
      if [ "${#dtokens[@]}" -eq 0 ]; then
        printf '  %s %-12s %s\n' "$name" "$id" \
          "UNDIGESTED (no digest recorded in the requirement-digests field)"
        spec_undigested+=("$id")
      elif [ "${#dtokens[@]}" -gt 1 ]; then
        printf '  %s %-12s %s\n' "$name" "$id" \
          "MALFORMED (digest recorded more than once in the requirement-digests field)"
        spec_malformed+=("$id")
      else
        recorded=${dtokens[0]##*sha256:}
        if [[ ! "$recorded" =~ ^[0-9a-f]{64}$ ]]; then
          printf '  %s %-12s %s\n' "$name" "$id" \
            "MALFORMED (recorded digest is not exactly 64 hex characters; fail closed)"
          spec_malformed+=("$id")
        elif [ "$recorded" != "$(sha256_of "${REQ_TEXT[$id]}")" ]; then
          printf '  %s %-12s %s\n' "$name" "$id" \
            "STALE - requirement wording changed since this spec recorded its digest"
          spec_stale+=("$id")
        fi
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
  if [ "${#spec_unknown[@]}" -gt 0 ]; then
    UNKNOWN+=("${spec_unknown[@]}")
  fi
  if [ "${#spec_malformed[@]}" -gt 0 ]; then
    MALFORMED+=("${spec_malformed[@]}")
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
UNKNOWN=()
MALFORMED=()
for spec_file in "${SPEC_FILES[@]}"; do
  verify_spec "$spec_file" || exit 1
done

echo "Requirement traceability"
echo "========================"
echo "Checked ${#SPEC_FILES[@]} spec(s), ${TOTAL_CLAIMED} claimed-complete requirement(s) against:"
echo "  Requirements: $REQUIREMENTS_FILE"
echo

if [ "${#DRIFTED[@]}" -eq 0 ] && [ "${#UNCURATED[@]}" -eq 0 ] \
   && [ "${#STALE[@]}" -eq 0 ] && [ "${#UNDIGESTED[@]}" -eq 0 ] \
   && [ "${#UNKNOWN[@]}" -eq 0 ] && [ "${#MALFORMED[@]}" -eq 0 ]; then
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
  echo "spec, then run a fresh requirements verify pass to confirm."
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
  echo "emits the current digests), then run a fresh requirements verify pass."
fi

if [ "${#UNDIGESTED[@]}" -gt 0 ]; then
  echo
  echo "UNDIGESTED - claimed requirements with no digest recorded in the"
  echo "requirement-digests field (every Completes claim must carry"
  echo "'<ID> sha256:<digest>' there):"
  for id in "${UNDIGESTED[@]}"; do
    printf '  %s\n' "== ${id} =="
  done
  echo
  echo "Record each digest from the requirements brief (rerun the"
  echo "requirements prepare command for the current digests)."
fi

if [ "${#UNKNOWN[@]}" -gt 0 ]; then
  echo
  echo "UNKNOWN - Completes claims for requirement IDs the requirements"
  echo "source does not define:"
  for id in "${UNKNOWN[@]}"; do
    printf '  %s\n' "== ${id} =="
  done
  echo
  echo "Resolve each finding by fixing the ID (or defining the requirement)"
  echo "and re-recording its digest, then run a fresh requirements"
  echo "verify pass."
fi

if [ "${#MALFORMED[@]}" -gt 0 ]; then
  echo
  echo "MALFORMED - recorded digests that are not exactly 64 hex"
  echo "characters (a correct 64-hex prefix with extra trailing"
  echo "alphanumerics never passes freshness):"
  for id in "${MALFORMED[@]}"; do
    printf '  %s\n' "== ${id} =="
  done
  echo
  echo "Re-record each digest verbatim from the requirements brief (rerun"
  echo "the requirements prepare command); the digest must be the full"
  echo "sha256: line with no extra characters."
fi
exit 1
