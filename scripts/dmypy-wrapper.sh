#!/bin/bash

set -eu

#set -x

# Start in the root dir.
scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir/.."

DMYPY_STATUS_FILE='.dmypy.json'
DMYPY_STATUS_ARGS="--status-file $DMYPY_STATUS_FILE"
DMYPY_START_ARGS=''

while [ -z "${1:-}" ]; do
    opt="$1"
    case $opt in
        --*)
            DMYPY_START_ARGS+=" $opt"
            shift
            ;;
        *)
            break
            ;;
    esac
done
if [ -z "$DMYPY_START_ARGS" ]; then
    DMYPY_START_ARGS='--pretty --cache-fine-grained --install-types --non-interactive'
fi

dmypy $DMYPY_STATUS_ARGS status >/dev/null || dmypy $DMYPY_STATUS_ARGS start -- $DMYPY_START_ARGS

# Restart the daemon if the config file has changed.
if [ setup.cfg -nt /proc/$(cat $DMYPY_STATUS_FILE | jq -e -r .pid) ]; then
    dmypy $DMYPY_STATUS_ARGS restart -- $DMYPY_START_ARGS
fi

# Check the files passed as arguments.
dmypy $DMYPY_STATUS_ARGS check $*
