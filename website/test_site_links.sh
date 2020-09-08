#!/bin/bash
#
# Quick script to help check for dead links in the markdown -> html converted
# site that get's published to microsoft.github.io/MLOS
#
# Note: this assumes that build_site.sh, hugo, etc. have all already been run
# to do the markdown -> html conversion.

# Be strict.
set -eu

# Be verbose.
#set -x

# ensure we're in the right folder
scriptdir=$(readlink -f "$(dirname "$0")")
MLOS_ROOT=$(readlink -f "$scriptdir/..")
cd "$MLOS_ROOT/website"

# Make sure we have the
if ! [ -x /usr/bin/linklint ]; then
    echo "Missing linklint dependency" >&2
    set -x
    sudo apt-get update > /dev/null
    sudo apt-get -y install linklint
    set +x
fi

# Use docker to create a temporary web server for the site.
container_name='mlos-website-link-checker'

echo "INFO: Starting $container_name container to server website content for link checking." >&2

# Make sure there's no container from a previous run hanging around first.
docker rm -f $container_name 2>/dev/null || true
# Start a new one.
docker run -d --name $container_name -v $PWD:/src/MLOS/website -v $PWD/nginx.conf:/etc/nginx/conf.d/mlos.conf -p 8080:8080 nginx:latest

echo "INFO: Performing link checking." >&2

# Now check the site for links.
# For now, ignore anchors checks.
linklint_output=$(linklint -quiet -silent -error -no_anchors -host localhost:8080 -http /MLOS/@)

# Finally, cleanup the container.
if ! docker rm -f $container_name >/dev/null; then
    echo "WARNING: Failed to cleanup $container_name container." >&2
fi

if [ -n "$linklint_output" ]; then
    echo "ERROR: link issues found:" >&2
    echo "$linklint_output"
    exit 1
else
    echo "OK: Link lint checks passed."
fi

exit 0
