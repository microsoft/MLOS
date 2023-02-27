FROM python:slim

# Adjust the uid/gid of the container user to match the host user
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd --non-unique --gid $USER_GID vscode \
    && useradd --non-unique --uid $USER_UID --gid $USER_GID --create-home --shell /bin/bash vscode

USER vscode
WORKDIR /src
