#!/usr/bin/env bash
# This extension uses associative arrays and mapfile, both introduced in Bash 4.
if (( BASH_VERSINFO[0] < 4 )); then
  printf '%s\n' \
    "assemble-brief.sh: error: Bash 4 or later is required; found Bash ${BASH_VERSION}." \
    "Install a newer Bash and run this command with that Bash executable." >&2
  exit 2
fi

# Deterministically assemble a self-contained requirements-context brief for a
# single roadmap ID from ROADMAP.md and REQUIREMENTS.md.
#
# Read-only: prints a brief and a ready-to-run core /speckit-specify command to
# stdout. It never creates a branch, spec, checklist, or any file. It resolves
# the existing manual roadmap mapping into the brief. All failures are
# actionable and exit non-zero.
#
# Overrides for testing:
#   SPECKIT_ROADMAP_FILE       path to ROADMAP.md      (default: repo root)
#   SPECKIT_REQUIREMENTS_FILE  path to REQUIREMENTS.md (default: repo root)

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
# and BSD/macOS (shasum -a 256). Used to emit the per-requirement
# digests the verifier freshness-checks against.
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

# Resolve the root only when an override has not already supplied both
# source files: hermetic invocations (fixtures, fresh seeds before
# REQUIREMENTS.md exists) must not depend on the containing project.
if [ -z "${SPECKIT_ROADMAP_FILE:-}" ] || [ -z "${SPECKIT_REQUIREMENTS_FILE:-}" ]; then
  DEFAULT_ROOT=$(resolve_project_root) ||
    die "could not locate project root containing ROADMAP.md and REQUIREMENTS.md (set SPECKIT_ROADMAP_FILE/SPECKIT_REQUIREMENTS_FILE or SPECIFY_INIT_DIR)"
  ROADMAP_FILE=${SPECKIT_ROADMAP_FILE:-$DEFAULT_ROOT/ROADMAP.md}
  REQUIREMENTS_FILE=${SPECKIT_REQUIREMENTS_FILE:-$DEFAULT_ROOT/REQUIREMENTS.md}
else
  ROADMAP_FILE=$SPECKIT_ROADMAP_FILE
  REQUIREMENTS_FILE=$SPECKIT_REQUIREMENTS_FILE
fi

# ---------------------------------------------------------------------------
# Validate input grammar: exactly one roadmap ID (R + positive integer)
# ---------------------------------------------------------------------------
if [ "$#" -eq 0 ]; then
  die "missing roadmap ID; expected exactly one, e.g. R2"
fi
if [ "$#" -gt 1 ]; then
  die "expected exactly one roadmap ID but got $# values ('$*'); pass a single ID such as R2"
fi
ID=$1
if ! printf '%s' "$ID" | grep -Eq '^R[1-9][0-9]*$'; then
  die "malformed roadmap ID '$ID'; expected 'R' followed by a positive integer (e.g. R1, R2)"
fi

[ -f "$ROADMAP_FILE" ] || die "roadmap file not found: $ROADMAP_FILE"
[ -f "$REQUIREMENTS_FILE" ] || die "requirements file not found: $REQUIREMENTS_FILE"

# ---------------------------------------------------------------------------
# Parse ROADMAP.md pipe table
# ---------------------------------------------------------------------------
EXPECT_HEADERS=(ID "Sub-feature" "Intent" "Scope boundary" "Depends on" "Status" "Completes (RQ)" "Advances (RQ)" "Sub-spec")
NCOL=${#EXPECT_HEADERS[@]}

# parse_cells LINE -> populates global array CELLS (0-indexed, trimmed).
# Returns 1 if LINE is not a well-formed pipe-table row.
parse_cells() {
  local line=$1
  line=$(trim "$line")
  [ -n "$line" ] || return 1
  [ "${line:0:1}" = "|" ] || return 1
  [ "${line: -1}" = "|" ] || return 1
  line=${line#|}
  line=${line%|}
  local IFS='|'
  read -ra _raw <<<"$line"
  CELLS=()
  local c
  for c in "${_raw[@]}"; do
    CELLS+=("$(trim "$c")")
  done
  return 0
}

is_separator_row() {
  # true when every cell is a run of dashes/colons (Markdown table separator)
  local c
  for c in "${CELLS[@]}"; do
    [[ $c =~ ^:?-+:?$ ]] || return 1
  done
  return 0
}

declare -A ROW_STATUS=()
HEADER_SEEN=0
MATCH_COUNT=0
SEL_INTENT="" SEL_SCOPE="" SEL_DEPENDS="" SEL_STATUS="" SEL_COMPLETES="" SEL_ADVANCES="" SEL_SUBFEATURE=""

while IFS= read -r line || [ -n "$line" ]; do
  parse_cells "$line" || continue
  # Skip separator rows.
  is_separator_row && continue
  if [ "$HEADER_SEEN" -eq 0 ] && [ "${CELLS[0]}" = "ID" ]; then
    # Validate table schema (fail closed on drift / unsupported shape).
    if [ "${#CELLS[@]}" -ne "$NCOL" ]; then
      die "ROADMAP schema drift: header has ${#CELLS[@]} columns, expected $NCOL"
    fi
    local_i=0
    while [ "$local_i" -lt "$NCOL" ]; do
      if [ "${CELLS[$local_i]}" != "${EXPECT_HEADERS[$local_i]}" ]; then
        die "ROADMAP schema drift: column $((local_i + 1)) is '${CELLS[$local_i]}', expected '${EXPECT_HEADERS[$local_i]}'"
      fi
      local_i=$((local_i + 1))
    done
    HEADER_SEEN=1
    continue
  fi
  [ "$HEADER_SEEN" -eq 1 ] || continue
  # A data row must have the full column count; anything else is unsupported
  # (e.g. a multiline/continued cell). Fail closed rather than misread it.
  if [ "${#CELLS[@]}" -ne "$NCOL" ]; then
    die "ROADMAP schema drift: data row '${CELLS[0]}' has ${#CELLS[@]} columns, expected $NCOL (multiline/continued rows are not supported)"
  fi
  rid=${CELLS[0]}
  # Only consider well-formed roadmap IDs as rows.
  [[ $rid =~ ^R[1-9][0-9]*$ ]] || continue
  if [ -n "${ROW_STATUS[$rid]:-}" ]; then
    die "ROADMAP has duplicate row for ID '$rid'"
  fi
  ROW_STATUS[$rid]=${CELLS[5]}
  if [ "$rid" = "$ID" ]; then
    MATCH_COUNT=$((MATCH_COUNT + 1))
    SEL_SUBFEATURE=${CELLS[1]}
    SEL_INTENT=${CELLS[2]}
    SEL_SCOPE=${CELLS[3]}
    SEL_DEPENDS=${CELLS[4]}
    SEL_STATUS=${CELLS[5]}
    SEL_COMPLETES=${CELLS[6]}
    SEL_ADVANCES=${CELLS[7]}
  fi
done <"$ROADMAP_FILE"

[ "$HEADER_SEEN" -eq 1 ] || die "ROADMAP table header not found in $ROADMAP_FILE"
[ "$MATCH_COUNT" -ge 1 ] || die "no ROADMAP row found for ID '$ID'"

# ---------------------------------------------------------------------------
# Parse requirement-ID lists (comma separated; em dash / empty means none)
# ---------------------------------------------------------------------------
# parse_id_list CELL LABEL -> populates the global PARSED_IDS array with
# validated requirement IDs. Calls die (parent-exiting) on a malformed ID so a
# bad ROADMAP cell aborts the script rather than being swallowed by a command
# substitution subshell. Emits nothing to stdout. The ID grammar allows one
# trailing lowercase letter (e.g. TEL-2a, SCEN-5a, PLATFORM-9a) to match
# REQUIREMENTS.md.
PARSED_IDS=()
parse_id_list() {
  local cell=$1 label=$2 tok
  cell=$(trim "$cell")
  if [ -z "$cell" ] || [ "$cell" = "-" ]; then
    PARSED_IDS=()
    return 0
  fi
  cell=${cell//,/ }
  PARSED_IDS=()
  for tok in $cell; do
    if ! [[ $tok =~ ^[A-Z]+-[0-9]+[a-z]?$ ]]; then
      die "malformed requirement ID '$tok' in ROADMAP $label column of row $ID"
    fi
    PARSED_IDS+=("$tok")
  done
}

parse_id_list "$SEL_COMPLETES" "Completes"
COMPLETES=("${PARSED_IDS[@]}")
parse_id_list "$SEL_ADVANCES" "Advances"
ADVANCES=("${PARSED_IDS[@]}")

# Detect Completes/Advances overlap (an RQ cannot be both for one feature).
declare -A IN_COMPLETES=()
for id in "${COMPLETES[@]}"; do IN_COMPLETES[$id]=1; done
for id in "${ADVANCES[@]}"; do
  if [ -n "${IN_COMPLETES[$id]:-}" ]; then
    die "requirement ID '$id' appears in both Completes and Advances for row $ID (overlap not allowed)"
  fi
done

# Detect duplicates within either list.
detect_dupes() {
  local label=$1; shift
  local -A seen=()
  local id
  for id in "$@"; do
    if [ -n "${seen[$id]:-}" ]; then
      die "requirement ID '$id' is listed more than once in the $label column of row $ID"
    fi
    seen[$id]=1
  done
}
[ "${#COMPLETES[@]}" -gt 0 ] && detect_dupes "Completes" "${COMPLETES[@]}"
[ "${#ADVANCES[@]}" -gt 0 ] && detect_dupes "Advances" "${ADVANCES[@]}"

# ---------------------------------------------------------------------------
# Dependency gate: every listed predecessor must have Status 'done'.
# The selected row's own status does not gate selection.
# ---------------------------------------------------------------------------
DEP_DISPLAY=$(trim "$SEL_DEPENDS")
declare -a DEPS=()
dep_cell=$(trim "$SEL_DEPENDS")
if [ -n "$dep_cell" ] && [ "$dep_cell" != "-" ]; then
  dep_cell=${dep_cell//,/ }
  for tok in $dep_cell; do
    if ! [[ $tok =~ ^R[1-9][0-9]*$ ]]; then
      die "malformed dependency ID '$tok' in ROADMAP 'Depends on' column of row $ID"
    fi
    DEPS+=("$tok")
  done
fi

for dep in "${DEPS[@]}"; do
  dep_status=${ROW_STATUS[$dep]:-}
  if [ -z "$dep_status" ]; then
    die "dependency '$dep' of row $ID is not present in ROADMAP; cannot confirm it is done"
  fi
  if [ "$dep_status" != "done" ]; then
    die "dependency '$dep' of row $ID has status '$dep_status' (must be 'done' before $ID can be prepared)"
  fi
done

# ---------------------------------------------------------------------------
# Parse REQUIREMENTS.md stable bullet IDs -> exact full text.
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
# Ensure every mapped requirement ID exists in REQUIREMENTS.md.
# ---------------------------------------------------------------------------
missing=()
for id in "${COMPLETES[@]}" "${ADVANCES[@]}"; do
  [ -n "${REQ_TEXT[$id]:-}" ] || missing+=("$id")
done
if [ "${#missing[@]}" -gt 0 ]; then
  die "requirement ID(s) mapped by ROADMAP row $ID are absent from REQUIREMENTS.md: ${missing[*]}"
fi

# ---------------------------------------------------------------------------
# Emit the brief.
# ---------------------------------------------------------------------------
rule() { printf '%s\n' "--------------------------------------------------------------------------------"; }

join_csv() {
  local out="" id
  for id in "$@"; do
    if [ -z "$out" ]; then out="$id"; else out="$out, $id"; fi
  done
  printf '%s' "$out"
}

completes_csv=$(join_csv "${COMPLETES[@]}")
advances_csv=$(join_csv "${ADVANCES[@]}")
[ -n "$completes_csv" ] || completes_csv="(none)"
[ -n "$advances_csv" ] || advances_csv="(none)"

if [ "${#DEPS[@]}" -eq 0 ]; then
  dep_evidence="none (no predecessor gates this feature)"
else
  parts=""
  for dep in "${DEPS[@]}"; do
    entry="$dep=${ROW_STATUS[$dep]}"
    if [ -z "$parts" ]; then parts="$entry"; else parts="$parts, $entry"; fi
  done
  dep_evidence="$parts (all satisfied)"
fi

echo "================================================================================"
echo "Requirements context brief - $ID ($SEL_SUBFEATURE)"
echo "================================================================================"
echo
echo "Assembled deterministically from the authoritative, human-maintained sources:"
echo "  Roadmap:      ROADMAP.md  (row $ID)"
echo "  Requirements: REQUIREMENTS.md"
echo
echo "Roadmap status: $SEL_STATUS"
echo "Dependencies:   ${DEP_DISPLAY:--}"
echo "Dependency gate: $dep_evidence"
echo
echo "Intent"
rule
printf '%s\n' "$SEL_INTENT"
echo
echo "Scope boundary"
rule
printf '%s\n' "$SEL_SCOPE"
echo
echo "Requirement mapping (IDs cited from the ROADMAP.md row for $ID)"
rule
echo "Completes: $completes_csv"
echo "Advances:  $advances_csv"
echo
echo "Requirement text - Completes"
echo "(the product fully satisfies these RQ IDs once $ID is done)"
rule
if [ "${#COMPLETES[@]}" -eq 0 ]; then
  echo "(none)"
else
  for id in "${COMPLETES[@]}"; do
    printf -- '- **%s**: %s\n' "$id" "${REQ_TEXT[$id]}"
  done
fi
echo
echo "Requirement text - Advances"
echo "(foundational only; a later feature completes these - never a completion claim)"
rule
if [ "${#ADVANCES[@]}" -eq 0 ]; then
  echo "(none)"
else
  for id in "${ADVANCES[@]}"; do
    printf -- '- **%s**: %s\n' "$id" "${REQ_TEXT[$id]}"
  done
fi
echo
echo "Requirements Coverage seed"
echo "(paste into spec.md; matches extensions/requirements/templates/spec-template.md)"
rule
echo "Roadmap entry: \`ROADMAP.md\` -> **$ID**"
echo
echo "- **Completes**: $completes_csv"
echo "- **Advances**: $advances_csv"
echo "  (foundational only - do NOT record these as done in this feature)"
if [ "${#COMPLETES[@]}" -gt 0 ]; then
  digest_csv=""
  for id in "${COMPLETES[@]}"; do
    entry="${id} sha256:$(sha256_of "${REQ_TEXT[$id]}")"
    if [ -z "$digest_csv" ]; then digest_csv="$entry"; else digest_csv="$digest_csv, $entry"; fi
  done
  echo "- **Requirement digests**: $digest_csv"
fi
echo
echo "Suggested spec Input line:"
echo "**Input**: Parent roadmap: \`ROADMAP.md\` -> entry **$ID**. $SEL_INTENT"
echo
echo "Ready-to-run core command (review before running)"
rule
printf '/speckit-specify %s Scope boundary: %s\n' "$SEL_INTENT" "$SEL_SCOPE"
echo
rule
cat <<EOF
NOTE: This brief was assembled deterministically from ROADMAP.md and
REQUIREMENTS.md. It did NOT create a branch, spec, checklist, or any file, and
resolved the existing manual ROADMAP.md mapping. The mapping remains manual and
authoritative. A human must REVIEW this brief and then run the core
/speckit-specify command above; only that core command creates the feature.
EOF
