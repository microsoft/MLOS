# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# Start with npm
FROM node:lts-slim

# Install some basic dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    apt-transport-https ca-certificates curl gnupg2 software-properties-common \
    less jq \
    build-essential g++ libx11-dev libxkbfile-dev libsecret-1-dev python-is-python3 python3-minimal

# Install docker CLI
# https://docs.docker.com/engine/install/debian/
RUN install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | tee /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin docker-compose-plugin

# Install the devcontainer CLI
RUN npm install -g @devcontainers/cli

# Also add the cspell tool to image.
RUN npm install -g cspell

# Also add the markdown-link-check tool to image.
RUN npm install -g markdown-link-check

# Adjust the uid/gid of the node user to match the host user
ARG NODE_UID=1000
ARG NODE_GID=1000
ARG DOCKER_GID=999
RUN groupmod --non-unique --gid $NODE_GID node \
    && usermod --non-unique --uid $NODE_UID --gid $NODE_GID node \
    && chown -R $NODE_UID:$NODE_GID /home/node \
    && groupadd --non-unique --gid $DOCKER_GID docker \
    && adduser node docker

USER node
WORKDIR /src

CMD "/bin/bash"
