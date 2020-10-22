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

. "$MLOS_ROOT/scripts/util.sh"

if ! [ -e public/python_api/index.html ]; then
    echo "ERROR: The sphinx API docs have not yet been generated.  Please run 'make sphinx-site' first." >&2
    exit 1
fi

if ! [ -e public/index.html ]; then
    echo "ERROR: The public site has not yet been generated.  Please run 'make hugo-site' first." >&2
    exit 1
fi

# Make sure we have the
if ! [ -x /usr/bin/linklint ]; then
    echo "Missing linklint dependency" >&2
    set -x
    sudo apt-get update > /dev/null
    sudo apt-get -y install linklint
    set +x
fi

container_name='mlos-website-link-checker'
if ! areInDockerContainer && [ -x /usr/bin/docker ]; then
    echo "INFO: Starting $container_name container to serve website content for link checking." >&2

    # Make sure there's no container from a previous run hanging around first.
    docker rm -f $container_name 2>/dev/null || true
    # Start a new one.
    docker run -d --name $container_name -v $PWD:/src/MLOS/website -v $PWD/nginx.conf:/etc/nginx/conf.d/mlos.conf -p 8080:8080 nginx:latest
else
    echo "INFO: already inside docker.  Starting nginx for website content link checking." >&2

    # Already in a docker container - install nginx for local testing.
    if ! [ -x /usr/sbin/nginx ]; then
        set -x
        sudo apt-get update > /dev/null
        sudo apt-get -y install nginx
        set +x
    fi
    if ! [ -L /etc/nginx/conf.d/mlos.conf ]; then
        set -x
        sudo rm -f /etc/nginx/conf.d/mlos.conf
        sudo ln -s $PWD/nginx.conf /etc/nginx/conf.d/mlos.conf
        set +x
    fi
    set -x
    sudo service nginx start >/dev/null
    sudo service nginx reload >/dev/null
    set +x
fi

echo "INFO: Performing link checking." >&2

# Now check the site for links.
# For now, ignore anchors checks.
linklint_output=$(linklint -quiet -silent -error -no_anchors -host localhost:8080 -http /MLOS/@)

# Finally, cleanup the container.
if ! areInDockerContainer; then
    if ! docker rm -f $container_name >/dev/null; then
        echo "WARNING: Failed to cleanup $container_name container." >&2
    fi
else
    set -x
    sudo service nginx stop >/dev/null &
    set +x
fi

if [ -n "$linklint_output" ]; then
    echo "ERROR: link issues found:" >&2
    echo "$linklint_output"
    exit 1
else
    echo "OK: Basic link lint checks passed."
fi

# Now do anchor link checking.

# To do this we need to tweak the site slightly for linklint's benefit.

# Some special treatment for the base level index file, mostly to keep linklint
# happy about checking anchors.
# Without this it seems to get confused about /#foo anchors.
sed -i.bak -r 's|<a href="#|<a href="/MLOS/#|g' public/index.html

# Make / and /MLOS synonmous for the local checks.
if [ -L public/MLOS ]; then
    rm -f public/MLOS
elif [ -e public/MLOS ]; then
    echo "ERROR: public/MLOS already exists and si not a symlink." >&2
    exit 1
fi
ln -s . public/MLOS

linklint_output=$(linklint -quiet -silent -error -root public -local /@)

# Cleanup after ourselves.
rm -f public/index.html.bak
rm -f public/MLOS

if [ -n "$linklint_output" ]; then
    echo "ERROR: local anchor link issues found:" >&2
    echo "$linklint_output"
    exit 1
else
    echo "OK: Local anchor link lint checks passed."
fi

exit 0
