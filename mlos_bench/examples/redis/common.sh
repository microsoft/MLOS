##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

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

check_root() {
    if [ $EUID != 0 ]; then
        echo "ERROR: This script expects to be executed with root privileges." >&2
        exit 1
    fi
}

check_docker() {
    if ! hash docker 2>/dev/null; then
        check_root

        # Taken from https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository
        distro=$(lsb_release -is | tr '[:upper:]' '[:lower:]')

        # Remove any older versions
        apt-get remove docker docker-engine docker.io containerd runc || true

        # Allow apt to use a repo over HTTPS
        apt-get update
        apt-get -y install \
            ca-certificates \
            curl \
            gnupg \
            lsb-release

        # Add Docker's official GPG key
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/$distro/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

        # Set up the repo
        echo \
            "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$distro \
            $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

        # Install latest version of Docker Engine and related
        apt-get update
        apt-get -y install docker-ce docker-ce-cli containerd.io
    fi
}
