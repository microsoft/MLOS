REDIS_IMAGE='redis:7.0'
REDIS_PORT='6379'
REDIS_SERVER_NAME='redis-server'
REDIS_CLIENT_NAME='redis-client'

if [ -z "${REDIS_SERVER_HOST:-}" ]; then
    # If not provided, assume that the client and server containers are run on the same host.
    # NOTE: In setup-app.sh we expose the server port on the host so we can connect to the host from the client.
    if grep WSL2 /proc/version 2>/dev/null; then
        # In the case of WSL2, the docker containers run in a different VM than the typical CLI,
        # so we have to connect to the host machine instead
        # (which we infer from the WSL2 VM's gateway address).
        REDIS_SERVER_HOST=$(ip route show | grep '^default via ' | awk '{ print $3 }')
    else
        REDIS_SERVER_HOST=$(hostname -f)
    fi
fi
