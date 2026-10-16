#!/usr/bin/env bash
# This script uses associative arrays, introduced in Bash 4.
if (( BASH_VERSINFO[0] < 4 )); then
  printf '%s\n' \
    "extract-phrases.sh: error: Bash 4 or later is required; found Bash ${BASH_VERSION}." \
    "Install a newer Bash and run this command with that Bash executable." >&2
  exit 2
fi

# Extract candidate requirement phrases from REQUIREMENTS.md for
# requirement-content traceability.
#
# Deterministic and read-only by default (prints to stdout). With -o/--output,
# writes candidate phrases (preceded by a header comment) to the target
# phrases.txt file. Every generated phrase is validated as a case-insensitive
# verbatim substring of the requirement text before it is emitted, so the table
# always passes the verifier's load-time check. Candidates are not guaranteed
# to be *distinctive*: a generic phrase (for example "list pets") still
# verifies a claim without proving the requirement was transcribed, so review
# the draft and prefer wording unique to each requirement.
#
# Usage:
#   extract-phrases.sh [REQUIREMENTS_FILE] [-o OUTPUT_FILE]
#
# Overrides:
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

clean_phrase() {
  local p=$1 stripped
  p=$(trim "$p")
  while [ -n "$p" ]; do
    stripped=${p%[.,;:]}
    if [ "$stripped" = "$p" ]; then break; fi
    p=$stripped
  done
  trim "$p"
}

# ---------------------------------------------------------------------------
# Locate REQUIREMENTS.md
# ---------------------------------------------------------------------------
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)

find_project_root() {
  local candidate=$1
  while :; do
    if [ -f "$candidate/REQUIREMENTS.md" ]; then
      printf '%s' "$candidate"
      return 0
    fi
    [ "$candidate" = "/" ] && return 1
    candidate=$(dirname -- "$candidate")
  done
}

REQ_FILE=""
OUTPUT_FILE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    -o|--output)
      [ "$#" -ge 2 ] || die "missing argument for $1"
      OUTPUT_FILE=$2
      shift 2
      ;;
    *)
      if [ -z "$REQ_FILE" ]; then
        REQ_FILE=$1
        shift
      else
        die "unexpected argument: $1"
      fi
      ;;
  esac
done

if [ -z "$REQ_FILE" ]; then
  if [ -n "${SPECKIT_REQUIREMENTS_FILE:-}" ]; then
    REQ_FILE=$SPECKIT_REQUIREMENTS_FILE
  else
    PROJECT_ROOT=$(find_project_root "$PWD") || PROJECT_ROOT=$(find_project_root "$SCRIPT_DIR") ||
      die "could not locate REQUIREMENTS.md (pass as argument or set SPECKIT_REQUIREMENTS_FILE)"
    REQ_FILE=$PROJECT_ROOT/REQUIREMENTS.md
  fi
fi

[ -f "$REQ_FILE" ] || die "requirements file not found: $REQ_FILE"

# Refuse to overwrite the requirements source with generated phrases: an
# in-place run (-o pointing at the same file) would destroy REQUIREMENTS.md.
if [ -n "$OUTPUT_FILE" ] && [ -f "$OUTPUT_FILE" ] && [ "$OUTPUT_FILE" -ef "$REQ_FILE" ]; then
  die "refusing to overwrite the requirements file with generated phrases: $OUTPUT_FILE"
fi

# ---------------------------------------------------------------------------
# Parse REQUIREMENTS.md stable bullet IDs -> exact full text.
# ---------------------------------------------------------------------------
declare -A REQ_TEXT=()
declare -A REQ_SEEN=()
declare -a REQ_ORDER=()
cur_id=""
cur_buf=""

flush_req() {
  [ -n "$cur_id" ] || return 0
  if [[ -n "${REQ_SEEN[$cur_id]:-}" ]]; then
    die "REQUIREMENTS has duplicate definition for requirement ID '$cur_id'"
  fi
  REQ_SEEN[$cur_id]=1
  REQ_ORDER+=("$cur_id")
  REQ_TEXT[$cur_id]=$(trim "$cur_buf")
  cur_id=""
  cur_buf=""
}

bullet_re="^-[[:space:]]+\*\*([A-Z]+-[0-9]+[a-z]?)\*\*:[[:space:]]?(.*)$"

while IFS= read -r line || [ -n "$line" ]; do
  if [[ $line =~ $bullet_re ]]; then
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
done <"$REQ_FILE"
flush_req

[ "${#REQ_ORDER[@]}" -gt 0 ] || die "no requirements found in $REQ_FILE"

# ---------------------------------------------------------------------------
# Extract verbatim candidate phrases per requirement
# ---------------------------------------------------------------------------
must_re="(MUST[[:space:]]+allow|MUST[[:space:]]+NOT|MUST)[[:space:]]+(.*)"
split_comma_re="^([^,;]+)[,;][[:space:]]+(.*)$"
split_and_re="^(.*)[[:space:]]+and[[:space:]]+(.*)$"

OUT_LINES=()

for id in "${REQ_ORDER[@]}"; do
  text=${REQ_TEXT[$id]}
  phrase1=""
  phrase2=""

  if [[ $text =~ $must_re ]]; then
    clause=${BASH_REMATCH[2]}
    if [[ $clause =~ $split_comma_re ]]; then
      phrase1=$(clean_phrase "${BASH_REMATCH[1]}")
      phrase2=$(clean_phrase "${BASH_REMATCH[2]}")
    elif [[ $clause =~ $split_and_re ]]; then
      phrase1=$(clean_phrase "${BASH_REMATCH[1]}")
      phrase2=$(clean_phrase "${BASH_REMATCH[2]}")
    else
      phrase1=$(clean_phrase "$clause")
    fi
  fi

  wcount=0
  if [ -n "$phrase1" ]; then
    wcount=$(wc -w <<<"$phrase1")
  fi
  if [ "$wcount" -lt 2 ]; then
    phrase1=$(clean_phrase "$text")
  fi

  text_lower=$(tr '[:upper:]' '[:lower:]' <<<"$text")
  line_out="$id"

  if [ -n "$phrase1" ]; then
    p1_lower=$(tr '[:upper:]' '[:lower:]' <<<"$phrase1")
    if [[ $text_lower == *"$p1_lower"* ]]; then
      case "$phrase1" in
        *"|"*) die "extracted phrase for requirement '$id' contains '|', which would corrupt the phrases table: $phrase1" ;;
      esac
      line_out="$line_out|$phrase1"
    fi
  fi

  if [ -n "$phrase2" ]; then
    p2_lower=$(tr '[:upper:]' '[:lower:]' <<<"$phrase2")
    wcount2=$(wc -w <<<"$phrase2")
    if [ "$wcount2" -ge 2 ] && [[ $text_lower == *"$p2_lower"* ]]; then
      case "$phrase2" in
        *"|"*) die "extracted phrase for requirement '$id' contains '|', which would corrupt the phrases table: $phrase2" ;;
      esac
      line_out="$line_out|$phrase2"
    fi
  fi

  if [[ "$line_out" != *"|"* ]]; then
    die "no candidate phrase extracted for requirement '$id' (empty requirement text?)"
  fi
  OUT_LINES+=("$line_out")
done

if [ -n "$OUTPUT_FILE" ]; then
  mkdir -p "$(dirname -- "$OUTPUT_FILE")"
  {
    printf '# Requirement phrases generated by extract-phrases.sh.\n'
    printf '# Format: <ID>|<phrase>|... (each phrase verbatim wording from REQUIREMENTS.md)\n'
    printf '%s\n' "${OUT_LINES[@]}"
  } >"$OUTPUT_FILE"
  echo "Wrote ${#OUT_LINES[@]} requirement phrase lines to $OUTPUT_FILE"
else
  printf '%s\n' "${OUT_LINES[@]}"
fi
