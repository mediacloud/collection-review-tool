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

echo "postdeploy: attempting Airtable deployment update for ${AIRTABLE_NAME} (${AIRTABLE_ENV})"

if python -m mc_manage.airtable_deployment_update; then
    exit 0
fi

if command -v mc-manage >/dev/null 2>&1; then
    if mc-manage airtable-deployment-update; then
        exit 0
    fi
fi

echo "postdeploy: unable to run mc-manage deployment update command; skipping."
exit 0
