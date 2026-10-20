#!/bin/bash

set -e -u -o pipefail

PROJECT_ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)

# The petstore working tree is inside the repository, so the project mount
# makes it host-backed and visible in the IDE.
mkdir --parents "${PROJECT_ROOT}/petstore"

# NB: the workshop name is the definition file's name (.workshop/<name>.yaml);
# it keys the tool's image cache, so it is per-project. Derived from the
# single definition present; set WORKSHOP_NAME to override (for example,
# in a tree with more than one definition).
if [ -z "${WORKSHOP_NAME:-}" ]; then
    shopt -s nullglob
    definitions=(.workshop/*.yaml)
    shopt -u nullglob
    if [ "${#definitions[@]}" -eq 1 ]; then
        WORKSHOP_NAME=$(basename "${definitions[0]}" .yaml)
    elif [ "${#definitions[@]}" -eq 0 ]; then
        echo "error: no .workshop/*.yaml definition found in $(pwd); set WORKSHOP_NAME" >&2
        exit 1
    else
        echo "error: multiple .workshop/*.yaml definitions found; set WORKSHOP_NAME" >&2
        exit 1
    fi
fi

if ! workshop info "${WORKSHOP_NAME}" >&/dev/null; then
    echo "Launching new workshop ${WORKSHOP_NAME}"
    workshop launch "${WORKSHOP_NAME}"
fi
workshop refresh "${WORKSHOP_NAME}" >/dev/null

echo "Workshop ready (connect with 'workshop shell')"
echo "Work in /project/petstore (host: ${PROJECT_ROOT}/petstore)"
