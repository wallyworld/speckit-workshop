#!/bin/bash

set -e -u -o pipefail

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

# Maps "<sdk>:<mount name>" to the host directory it should be backed by.
# The tilde is left unexpanded on purpose; expand_home handles it when used.
declare -A MOUNTS=(
    [copilot:copilot-config]='~/.copilot'
    [opencode:opencode-config]='~/.config/opencode'
    [opencode:opencode-data]='~/.local/share/opencode'
)

expand_home() {
    printf '%s' "${1/#\~/${HOME}}"
}

# Succeed when the mount already points at the wanted host directory,
# whether workshop reports it with a literal ~ or an expanded path.
mount_is_current() {
    local sdk=${1%%:*} mount=${1#*:} wanted=$2 current
    current=$(yq ".sdks.\"${sdk}\".mounts.\"${mount}\".\"host-source\"" <<<"${INFO}")
    [[ ${current} == "${wanted}" || ${current} == "$(expand_home "${wanted}")" ]]
}

if ! workshop info "${WORKSHOP_NAME}" >&/dev/null; then
    echo "Launching new workshop ${WORKSHOP_NAME}"
    workshop launch "${WORKSHOP_NAME}"
fi
workshop refresh "${WORKSHOP_NAME}" >/dev/null

if ! command -v yq >&/dev/null; then
    echo "Installing yq snap on host"
    sudo snap install yq
fi

# Query the workshop once and check every mount against that snapshot.
INFO=$(workshop info "${WORKSHOP_NAME}")

stale=()
for key in "${!MOUNTS[@]}"; do
    if ! mount_is_current "${key}" "${MOUNTS[${key}]}"; then
        stale+=("${key}")
    fi
done

# The slow stop/start cycle happens once, and only if something is stale.
if ((${#stale[@]} > 0)); then
    echo "Mounting host configuration directories"
    workshop stop "${WORKSHOP_NAME}"
    for key in "${stale[@]}"; do
        echo "Mounting ${key} from host"
        host_path=$(expand_home "${MOUNTS[${key}]}")
        mkdir --parents "${host_path}"
        workshop remount "${WORKSHOP_NAME}/${key}" "${host_path}"
    done
    workshop start "${WORKSHOP_NAME}"
fi

echo "Workshop ready (connect with 'workshop shell')"
