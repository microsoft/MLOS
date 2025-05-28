#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

# A script to start the containerized SQL DBMS servers.
# For pytest, the fixture in conftest.py will handle this for us using the
# pytest-docker plugin, but for manual testing, this script can be used.

set -eu
set -x

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"

PROJECT_NAME="mlos_bench-test-sql-storage-manual"
CONTAINER_COUNT=2

docker compose -p "$PROJECT_NAME" up --build --remove-orphans -d
set +x

function get_project_health() {
    docker compose -p "$PROJECT_NAME" ps --format '{{.Name}} {{.State}} {{.Health}}'
}

project_health=$(get_project_health)
while ! echo "$project_health" | grep -c ' running healthy$' | grep -q -x $CONTAINER_COUNT; do
    echo "Waiting for $CONTAINER_COUNT containers to report healthy ..."
    echo "$project_health"
    sleep 1
    project_health=$(get_project_health)
done

mysql_port=$(docker compose -p "$PROJECT_NAME" port mysql-mlos-bench-server ${PORT:-3306} | cut -d: -f2)
echo "Connect to the mysql server container at the following port: $mysql_port"
postgres_port=$(docker compose -p "$PROJECT_NAME" port postgres-mlos-bench-server ${PORT:-5432} | cut -d: -f2)
echo "Connect to the postgres server container at the following port: $postgres_port"
