#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# A script to stop the containerized SQL DBMS servers.
# For pytest, the fixture in conftest.py will handle this for us using the
# pytest-docker plugin, but for manual testing, this script can be used.

set -eu

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"

PROJECT_NAME="mlos_bench-test-sql-storage-manual"

docker compose -p "$PROJECT_NAME" down
