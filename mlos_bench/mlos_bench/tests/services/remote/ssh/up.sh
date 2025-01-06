#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# A script to start the SSH server in a container and copy the SSH keys from it.
# For pytest, the fixture in conftest.py will handle this for us using the
# pytest-docker plugin, but for manual testing, this script can be used.

set -eu
set -x

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"

PROJECT_NAME="mlos_bench-test-manual"

#docker compose -p "$PROJECT_NAME" build
export TIMEOUT=infinity
docker compose -p "$PROJECT_NAME" up --build --remove-orphans
docker compose -p "$PROJECT_NAME" exec ssh-server service ssh start
docker compose -p "$PROJECT_NAME" cp ssh-server:/root/.ssh/id_rsa ./id_rsa
chmod 0600 ./id_rsa
set +x

echo "OK: private key available at '$scriptdir/id_rsa'. Connect to the ssh-server container at the following port:"
docker compose -p "$PROJECT_NAME" port ssh-server ${PORT:-2254} | cut -d: -f2
echo "INFO: And this port for the alt-server container:"
docker compose -p "$PROJECT_NAME" port alt-server ${PORT:-2254} | cut -d: -f2
echo "INFO: And this port for the reboot-server container:"
docker compose -p "$PROJECT_NAME" port reboot-server ${PORT:-2254} | cut -d: -f2
