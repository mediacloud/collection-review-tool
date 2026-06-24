#!/bin/sh

# Common configuration and helpers for UNDP Collections Review Dokku deployments.
# Patterned after mediacloud/web-search dokku-scripts/common.sh.

# Phil: IMO unduly mangled from my web-search and rss-fetcher versions
# please copy from one of those, or maybe it's time to have a repo
# with a single/common version of the scripts??

check_not_root() {
    if [ "$(id -u)" -eq 0 ]; then
        echo "$0: do not run as root" 1>&2
        exit 1
    fi
}

# Base app name for all instances
APP_BASE=undp-collections-review

# Git remote name used for Dokku
DOKKU_GIT_REMOTE=dokku

# Dokku SSH host (for git pushes).
# Default assumes you are running these scripts *on the Dokku host itself*,
# so we talk to dokku@localhost. You can override, e.g.:
#   FQDN=my-dokku-host ./dokku-scripts/push.sh
FQDN=${FQDN:-localhost}

# INSTANCE is provided by the caller (prod, staging, or username)
# Phil: conform to convention used w/ other apps:
#	instance prefix first in app name
case "$INSTANCE" in
prod)
    APP="$APP_BASE"
    ALLOWED_HOSTS="${APP_BASE}.mediacloud.org"
    ;;
'')
    echo "common.sh: INSTANCE is not set" 1>&2
    exit 1
    ;;
*)
    APP="${INSTANCE}-$APP_BASE"
    ALLOWED_HOSTS="${APP_BASE}-${INSTANCE}.mediacloud.org"
    ;;
esac

# Postgres service name (per app)
PG_SVC="${APP}"
