#!/bin/sh

# Deploy code by pushing current branch to Dokku app instance
# Patterned after mediacloud/web-search dokku-scripts/push.sh

SCRIPT_DIR=$(dirname "$0")

usage() {
    cat 1>&2 <<-EOF
$0: push current branch to dokku instance (depending on branch)
options:
 --force-push
      add --force to git push commands
 --help or -h
      this message.
 --unpushed or -u
      allow deployment even if current branch not pushed to upstream.
EOF
}

PUSH_FLAGS=
# MCWEB_UNPUSHED inherited from environment
for ARG in "$@"; do
    case "$ARG" in
    --force-push) PUSH_FLAGS=--force ;; # force push code to dokku repo
    --unpushed|-u) MCWEB_UNPUSHED=1 ;;  # allow unpushed repo for development
    --help|-h)
        usage
        exit 0
        ;;
    *)
        echo "$0: unknown argument $ARG" 1>&2
        usage
        exit 1
        ;;
    esac
done

# works when su'ed to another user or invoked via ssh
UNAME=$(whoami)

BRANCH=$(git branch --show-current)

if [ -z "$BRANCH" ]; then
    echo "$0: could not determine current branch" 1>&2
    exit 1
fi

# Update instance.sh if you change how instances are named!
case "$BRANCH" in
prod|staging)
    INSTANCE=$BRANCH
    ;;
*)
    INSTANCE=$UNAME
    ;;
esac

export INSTANCE
. "$SCRIPT_DIR/common.sh"

check_not_root

# Ensure dokku app exists
if ! dokku apps:exists "$APP" >/dev/null 2>&1; then
    echo "$0: dokku app $APP does not exist." 1>&2
    echo "Run '$SCRIPT_DIR/instance.sh create $INSTANCE' first." 1>&2
    exit 1
fi

# Make sure branch is pushed and in sync with upstream (unless overridden)
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null)
if [ -z "$UPSTREAM" ]; then
    if [ -z "$MCWEB_UNPUSHED" ]; then
        echo "$0: branch $BRANCH has no upstream; push to GitHub first or use --unpushed." 1>&2
        exit 1
    fi
else
    AHEAD=$(git rev-list --count "${UPSTREAM}..$BRANCH" 2>/dev/null)
    if [ "${AHEAD:-0}" -gt 0 ] && [ -z "$MCWEB_UNPUSHED" ]; then
        echo "$0: branch $BRANCH has unpushed commits; push to upstream or use --unpushed." 1>&2
        exit 1
    fi
fi

# Set deploy branch inside Dokku to main (idempotent)
dokku git:set "$APP" deploy-branch main >/dev/null 2>&1 || true

echo "Deploying branch $BRANCH to dokku app $APP (instance=$INSTANCE) on $FQDN"

set -e

git push $PUSH_FLAGS "$DOKKU_GIT_REMOTE" "$BRANCH:main"

echo "Deployment to $APP complete."

