#!/bin/bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# A simple helper script to setup a local container user with an appropriate
# set of uid/gids to match the host so that bind mounts work naturally.
# Placed outside of the Dockerfile so that it can be reused in CI runs which
# may have a different UID/GID.

set -eu

if [ $EUID -ne 0 ]; then
    echo 'ERROR: This script must be run with root privileges.' >&2
    exit 1
fi

username="${1:-}"
uid="${2:-}"
gid="${3:-}"

function usage()
{
    msg="${1:-}"
    if [ -n "$msg" ]; then
        echo "$msg" >&2
    fi
    echo "usage: $0 <username> <uid> <gid>"
    exit 1
}

if ! echo "$username" | egrep -q '^[a-zA-Z0-9_-]+$'; then
    usage "Missing or invalid username: '$username'"
fi

if ! echo "$uid" | egrep -q '^[0-9]+$'; then
    usage "Missing or invalid uid: '$uid'"
fi

if ! echo "$gid" | egrep -q '^[0-9]+$'; then
    usage "Missing or invalid gid: '$gid'"
fi

# First make sure the gid exists.
if getent group $gid; then
    echo "WARNING: gid $gid already exists.  Refusing to re-create." >&2
else
    addgroup --gid $gid $username
fi

if getent passwd $uid; then
    echo "WARNING: uid $uid already exists. Refusing to re-create." >&2

    # Check to see if we need to add it to the desired gid.
    current_gid=$(getent passwd $uid | cut -d: -f4)
    current_uid_username=$(getent passwd $uid | cut -d: -f1)
    current_gid_groupname=$(getent group $gid | cut -d: -f1)
    if [ "$gid" != "$current_gid" ]; then
        echo "WARNING: $uid has a different primary gid ($current_gid) than desired ($gid)." >&2
        addgroup $current_uid_username $current_gid_groupname
    fi
else
    adduser --disabled-password --gecos '' --uid $uid --gid $gid $username
fi
current_uid_username=$(getent passwd $uid | cut -d: -f1)

# Add a group to use for the local container outputs.
adduser $current_uid_username src

# Add the user to the sudo group.
# (by the name associated with the uid in case the uid already existed)
adduser $current_uid_username sudo

# Try to prime the pip install dir so that the default ~/.profile rules take
# affect and add it to the PATH.
user_home=$(getent passwd $uid | cut -d: -f6 | grep '^/home' || true)
if [ -n "$user_home" ]; then
    sudo -u $current_uid_username mkdir -p "$user_home/.local/bin" || true
fi
