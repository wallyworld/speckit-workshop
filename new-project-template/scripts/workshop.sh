#!/bin/bash

set -e -u -o pipefail

# The workshop name is the definition file's name (.workshop/<name>.yaml);
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

# Agent configuration and credentials are deliberately not mounted from the
# host. Each agent SDK declares persistent mount plugs for its own config, and
# Workshop allocates their host directories automatically. Mounting a host
# agent config directory would expose the host's skills, credentials, and
# settings to every process in the workshop.

if ! workshop info "${WORKSHOP_NAME}" >&/dev/null; then
    echo "Launching new workshop ${WORKSHOP_NAME}"
    workshop launch "${WORKSHOP_NAME}"
fi
workshop refresh "${WORKSHOP_NAME}" >/dev/null

echo "Workshop ready (connect with 'workshop shell')"
