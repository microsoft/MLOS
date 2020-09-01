# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# A set of helper functions to use in other scripts.

# Uses "sort -V" from recent coreutils to check if the installed version ($2)
# is at least as large as the needed version ($1).
hasVersInstalled() {
    if [ $# -eq 0 ] || [ $# -gt 2 ]; then
        echo 'hasVersInstalled: Invalid number of arguments.' >&2
        exit 2
    elif [ $# -eq 1 ]; then
        #echo 'Invalid syntax or no version installed.' >&2
        # Assume there's just no version installed to make calling easier.
        return 1
    fi

    neededVers="$1"
    installedVers="$2"
    greaterVers=`echo -e "$neededVers\n$installedVers" | sort -V | tail -n1`
    [  "$greaterVers" = "$installedVers" ]
}
