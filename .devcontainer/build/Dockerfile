# Start with npm
FROM node:latest

# Install some basic dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        apt-transport-https ca-certificates curl gnupg2 software-properties-common \
        lsb-release less jq

# Install docker CLI
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - \
    && add-apt-repository "deb https://download.docker.com/linux/`lsb_release -si | tr A-Z a-z` `lsb_release -sc | tr A-Z a-z` stable" \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin

# Install the devcontainer CLI
RUN npm install -g @devcontainers/cli

# Adjust the uid/gid of the node user to match the host user
ARG NODE_UID=1000
ARG NODE_GID=1000
ARG DOCKER_GID=999
RUN groupmod --gid $NODE_GID node \
    && usermod --uid $NODE_UID --gid $NODE_GID node \
    && chown -R $NODE_UID:$NODE_GID /home/node \
    && groupadd --non-unique --gid $DOCKER_GID docker \
    && adduser node docker

USER node
WORKDIR /src

CMD "/bin/bash"
