#!/bin/bash
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# A simple script to help manage backgrounding another command.
# usage: BackgroundProcessHelper.sh <start|stop> <pidfile> [command]

# Be strict
set -eu

function showUsage
{
    msg=${1:-}
    if [ -n "$msg" ]; then
        echo "ERROR: $msg" >&2
    fi

    echo "$0 <start|stop> <pidfile> <logfile> [command args]" >&2
    exit 1
}

# Parse the args:
if [ $# -lt 3 ]; then
    showUsage
fi

action=${1:-}; shift
pidfile=${1:-}; shift
logfile=${1:-}; shift

if [ -z "$pidfile" ]; then
    showUsage 'Missing pidfile argument.'
fi

if [ -z "$logfile" ]; then
    showUsage 'Missing logfile argument.'
fi

if [ "$action" == 'start' ]; then
    if [ -z "${1:-}" ]; then
        showUsage "Missing command argument(s): '$*'"
    fi

    if [ -e "$pidfile" ]; then
        echo "ERROR: Refusing to reuse an existing pidfile: '$pidfile'" >&2
        exit 1
    fi

    if [ -e "$logfile" ]; then
        echo "ERROR: Refusing to reuse an existing logfile: '$logfile'" >&2
        exit 1
    fi

    # Start the process in the background with the remaining args.
    echo "# $*" >&2
    $* < /dev/null > $logfile 2>&1 &
    # Save the pid of the background process to the pidfile.
    backgroundPid=$!
    echo $backgroundPid > $pidfile
    sleep 1
    if ! kill -0 $backgroundPid; then
        echo "ERROR: Background process $backgroundPid is not alive." >&2
        exit 1
    fi
    exit 0
elif [ "$action" == 'stop' ]; then
    if ! [ -e "$pidfile" ]; then
        echo "ERROR: pidfile '$pidfile' is missing." >&2
        exit 1
    fi

    backgroundPid=$(cat "$pidfile" | head -n1)
    if ! echo "$backgroundPid" | egrep -q '^[0-9]+$'; then
        echo "ERROR: invalid pidfile contents: '$backgroundPid'" >&2
        exit 1
    fi
    echo "Stopping PID $backgroundPid"
    kill $backgroundPid || echo "WARNING: Failed to kill $backgroundPid"
    rm "$pidfile" || echo "WARNING: Failed to remove pidfile '$pidfile'"
    echo "Logfile '$logfile' contents:"
    cat "$logfile" || true
    rm "$logfile" || echo "WARNING: Failed to remove logfile '$logfile'"
    exit 0
else
    showUsage "Invalid action argument: '$action'"
fi
