#!/bin/sh

set -eu

if [ -z "${AIRTABLE_API_KEY:-}" ] || [ -z "${AIRTABLE_BASE_ID:-}" ]; then
    echo "postdeploy: AIRTABLE_API_KEY or AIRTABLE_BASE_ID missing; skipping deployment update."
    exit 0
fi

if [ -z "${AIRTABLE_ENV:-}" ]; then
    AIRTABLE_ENV=prod
fi

if [ -z "${AIRTABLE_NAME:-}" ]; then
    AIRTABLE_NAME=collection-review
fi

VERSION="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
AIRTABLE_HARDWARE_NORMALIZED="$(printf "%s" "${AIRTABLE_HARDWARE:-unknown}" | tr '[:upper:]' '[:lower:]')"

echo "postdeploy: attempting Airtable deployment update for ${AIRTABLE_NAME} (${AIRTABLE_ENV})"

if MEAG_BASE_ID="$AIRTABLE_BASE_ID" \
    python -m mc-manage.airtable-deployment-update \
        --codebase "collection-review" \
        --env "$AIRTABLE_ENV" \
        --hardware "$AIRTABLE_HARDWARE_NORMALIZED" \
        --name "$AIRTABLE_NAME" \
        --version "$VERSION"; then
    exit 0
fi

echo "postdeploy: unable to run mc-manage deployment update command; skipping."
exit 0
