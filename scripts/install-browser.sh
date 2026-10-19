#!/usr/bin/env bash
# Install the browser used by the Phase 2 acceptance test.
#
# This is deliberately not part of the base image: phases 01-04 do not need
# a browser, and installing Chrome costs time and image size. The workshop
# action `install-browser` runs this script on demand:
#
#   workshop run --uid 0 -- install-browser
#
# The action runs as root. The final check runs Chrome as the workshop user,
# which is the account the acceptance test uses.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "error: run as root: workshop run --uid 0 -- install-browser" >&2
    exit 1
fi

export DEBIAN_FRONTEND=noninteractive

if ! command -v google-chrome >/dev/null 2>&1; then
    echo "Installing Google Chrome (roughly 700 MB in the container)"
    apt-get update
    apt-get install --assume-yes --no-install-recommends wget ca-certificates

    case "$(dpkg --print-architecture)" in
        amd64)
            chrome_url=https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
            ;;
        arm64)
            chrome_url=https://dl.google.com/linux/direct/google-chrome-stable_current_arm64.deb
            ;;
        *)
            echo "error: unsupported architecture: $(dpkg --print-architecture)" >&2
            exit 1
            ;;
    esac

    chrome_deb=$(mktemp --suffix=.deb)
    trap 'rm -f "${chrome_deb}"' EXIT
    wget --quiet --output-document="${chrome_deb}" "${chrome_url}"
    apt-get install --assume-yes --no-install-recommends "${chrome_deb}"
    rm -f "${chrome_deb}"
    trap - EXIT
fi

google-chrome --version

runuser -u workshop -- env HOME=/home/workshop \
    google-chrome \
    --headless=new \
    --no-sandbox \
    --disable-gpu \
    --disable-dev-shm-usage \
    --no-first-run \
    --no-default-browser-check \
    --dump-dom about:blank >/dev/null

echo "PASS: Chrome is installed and launches headless as user workshop"
