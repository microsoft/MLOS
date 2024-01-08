#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# This script is used to update the git tags, version numbers, etc. in a number of files.
# See Also: .bumpversion.cfg (which gets rewritten by the tool, and strips comments, so we keep a separate config file for it)

set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir/.."

set -x
# Example usage: "./update-version.sh --dry-run patch" to bump v0.0.4 -> v0.0.5, for instance.
# Or:            "./update-version 0.2.0", to set the version to 0.2.0 explicitly, for instance.
conda run -n ${CONDA_ENV_NAME:-mlos} bumpversion --verbose $*
