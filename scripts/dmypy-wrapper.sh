#!/bin/bash

set -eu

#set -x

# Start in the root dir.
scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir/.."

# Make sure there's only a single dmypy running.
if [ $(pgrep -fla bin/dmypy[^-] | wc -l) -gt 1 ]; then
    pkill -f bin/dmypy[^-]
fi

dmypy status >/dev/null || dmypy start >/dev/null

# Restart the daemon if the config file has changed.
if [ setup.cfg -nt /proc/$(pgrep -f bin/dmypy[^-]) ]; then
    dmypy restart >/dev/null
fi

# Check the files passed as arguments.
# FIXME: would have to remove some args to use with vscode.
dmypy check $*
