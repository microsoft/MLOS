# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# See Also:
# - LICENSE.txt in this repository's root directory
# - https://aka.ms/mcr/osslegalnotice

# A Dockerfile for creating a suitable (Linux) build environment for MLOS for
# development and testing on the various versions of Ubuntu we need to support.

# Supported UbuntuVersions: 16.04, 18.04, 20.04
#
# Do a minimal build with:
#   UbuntuVersion=20.04;
#   docker build . --target mlos-build-base-without-extras \
#       --build-arg=UbuntuVersion=$UbuntuVersion \
#       -t mlos-build-ubuntu-$UbuntuVersion \
#       --cache-from ghcr.io/microsoft-cisl/mlos/mlos-build-ubuntu-$UbuntuVersion
#
# Note: to optionally reference a local proxy cache, also add the following argument:
#       --build-arg=http_proxy=http://some-proxy-host:3128
#
# Run with:
#   docker run -it -v $PWD:/src/MLOS -P --name mlos-build mlos-build-ubuntu-$UbuntuVersion
#
# This allows live editing in a native editor (e.g. VSCode or
# VisualStudio) and building using the container's environment.
#
# Alternatively, change the --target option in the command above to
# "mlos-build-base-with-source" to include the current source tree in the image
# and then omit the "-v" option arguments in the "docker run" command.
#
# To restart an existing container:
#   docker start -i mlos-build
#
# Once inside the container the `make` command will handle typical build needs.
# See the markdown files in the documentation/ directory for additional information.

# The default version of Ubuntu to use.
# This is currently set to 16.04 since that is the version that SqlServer
# supports.  See above for ways to override this.
ARG UbuntuVersion=16.04

# Allow requesting an image with additional content useful for interactive
# development by passing --build-arg=MlosBuildBaseArg=with-extras
ARG MlosBuildBaseArg=without-extras

FROM --platform=linux/amd64 ubuntu:${UbuntuVersion} AS mlos-build-base

LABEL org.opencontainers.image.vendor="Microsoft"
LABEL org.opencontainers.image.url="https://github.com/Microsoft/MLOS"
LABEL org.opencontainers.image.usage="https://github.com/Microsoft/MLOS/tree/main/documentation"

ARG DEBIAN_FRONTEND=noninteractive
ARG TZ=UTC
ARG LANG=en_US.UTF-8

# Use root for the setup tasks.
USER root

# Setup the tzdata and locale early on so it doesn't prompt or spit warnings at us.
RUN apt-get update && \
    LANG=C apt-get --no-install-recommends -y install apt-utils && \
    LANG=C apt-get --no-install-recommends -y install locales && \
    locale-gen ${LANG} && update-locale LANG=${LANG} && \
    DEBIAN_FRONTEND=${DEBIAN_FRONTEND} TZ=${TZ} \
        apt-get --no-install-recommends -y install tzdata && \
    DEBIAN_FRONTEND=${DEBIAN_FRONTEND} TZ=${TZ} \
        dpkg-reconfigure tzdata && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*

# Start setting up the container image to include the necessary build tools.
RUN apt-get update && \
    apt-get --no-install-recommends -y install \
        git make build-essential sudo curl wget lsb-release \
        software-properties-common apt-transport-https apt-utils \
        ca-certificates gnupg \
        exuberant-ctags vim-nox bash-completion less && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*

# A few quality of life improvements:
# - Don't beep/bell on tab completion failure.
# - Add the default pip command install location to the search PATH
RUN echo 'set bell-style none' >> /etc/inputrc && \
    echo 'export PATH="$PATH:$HOME/.local/bin"' >> /etc/profile.d/pip-cmds.sh

# Allow members of the sudo group to execute commands without prompting for a password.
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Setup some build output directories with appropriate permissions for non-root
# users to use.
RUN mkdir -p \
    /src/MLOS/out \
    /src/MLOS/target \
    /src/MLOS/temp \
    /src/MLOS/tools && \
    chgrp -R src /src/MLOS && \
    chmod 0775 \
        /src/MLOS/out \
        /src/MLOS/target \
        /src/MLOS/temp \
        /src/MLOS/tools

# Declare a volume that we can bind mount the current MLOS repo into in-place
# instead of the default copy.
VOLUME /src/MLOS

# Mark the output directories as separate volumes so that we can reuse the live
# source tree across different container build targets without conflicting
# cmake or build outputs.
VOLUME /src/MLOS/out
VOLUME /src/MLOS/target
VOLUME /src/MLOS/tools
VOLUME /src/MLOS/temp

WORKDIR /src/MLOS

# Create directory for our scripts to go.
RUN mkdir -p /tmp/MLOS/scripts /tmp/MLOS/tools

# Setup a regular user that we can use for running the container.
#
# Use 1000:1000 as the ids (they're the typical default in most cases so should
# work well with bind mounts).
#
# Rather than make this configurable, which would require rebuilding the image
# in a non-cache friendly way, this script can also be used on a running
# container instance to setup additional users to match local uid/gid if
# desired.  See .github/workflows/main.yml for examples.
COPY ./scripts/setup-container-user.sh /tmp/MLOS/scripts/
RUN /tmp/MLOS/scripts/setup-container-user.sh mlos-docker 1000 1000

# Run as a non-root-user from here on out.
USER mlos-docker

# Add some directories for vscode to bind to avoid having to rebuild extensions every launch
# and to save bash history across runs.
# https://code.visualstudio.com/docs/remote/containers-advanced#_avoiding-extension-reinstalls-on-container-rebuild
# https://code.visualstudio.com/docs/remote/containers-advanced#_persist-bash-history-between-runs
RUN mkdir -p \
    /home/mlos-docker/.histvol \
    /home/mlos-docker/.vscode-server/extensions \
    /home/mlos-docker/.vscode-server-insiders/extensions && \
    touch /home/mlos-docker/.histvol/bash_history && \
    chown -R mlos-docker \
        /home/mlos-docker/.histvol \
        /home/mlos-docker/.vscode-server \
        /home/mlos-docker/.vscode-server-insiders && \
    echo 'shopt -s histappend && export HISTFILE="$HOME/.histvol/bash_history"' >> /home/mlos-docker/.bashrc

# By default execute a bash shell for interactive usage.
# This can also be overridden on the "docker run" command line with
# "make" to execute a build and exit for pipeline usage instead.
CMD ["/bin/bash", "-l"]

# End mlos-build-base stage.

FROM mlos-build-base AS mlos-build-base-with-python

# Use root for the setup tasks.
USER root

# Install python3.7 and its pip dependencies
COPY ./scripts/install.python.sh /tmp/MLOS/scripts/
RUN /bin/bash /tmp/MLOS/scripts/install.python.sh && \
    apt-get update && \
    apt-get --no-install-recommends -y install \
        libfreetype6-dev unixodbc-dev && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*

RUN python3.7 -m pip install pip && \
    python3.7 -m pip install --upgrade pip && \
    python3.7 -m pip install setuptools wheel

COPY ./source/Mlos.Python/requirements.txt /tmp/
RUN python3.7 -m pip install -r /tmp/requirements.txt

# Expose the typical port that we start mlos microservice optimizer on by default.
EXPOSE 50051/tcp
# Also expose the nginx port for website build testing.
EXPOSE 8080/tcp

# Restore the non-root user for default CMD execution.
USER mlos-docker

# End mlos-build-base-with-python stage.

FROM mlos-build-base-with-python AS mlos-build-base-without-extras

# Use root for the setup tasks.
USER root

# Install LLVM using our script.
# Also install libstdc++-10-dev (https://github.com/Microsoft/MLOS/pull/133)
COPY ./scripts/install.llvm-clang.sh /tmp/MLOS/scripts/
RUN apt-get update && \
    apt-get --no-install-recommends -y install \
        gnupg-agent && \
    /bin/bash /tmp/MLOS/scripts/install.llvm-clang.sh && \
    if dpkg --compare-versions `lsb_release -r -s` ge-nl 20.04; then \
        apt-get --no-install-recommends -y install libstdc++-10-dev; \
    fi && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*

# Install some dependencies necessary for dotnet.
# Older versions of Ubuntu need additional libcurl libraries not already pulled
# in by the curl binary.
RUN if [ v`lsb_release -s -r` = 'v16.04' ]; then \
        apt-get update && \
        apt-get --no-install-recommends -y install libcurl3 && \
        apt-get -y clean && rm -rf /var/lib/apt/lists/*; \
    fi
# Note: libxml2 automatically pulls in an appropriate version of the ^libicu[0-9]+$ package.
RUN apt-get update && \
    apt-get --no-install-recommends -y install \
        liblttng-ctl0 liblttng-ust0 libxml2 zlib1g && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*

# Disable some noisy dotnet messages
ENV DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1

# Install dotnet in the system using our script.
COPY ./scripts/install.dotnet.sh /tmp/MLOS/scripts/
RUN /bin/bash /tmp/MLOS/scripts/install.dotnet.sh && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*

# Install cmake in the system using our script.
COPY ./scripts/install.cmake.sh /tmp/MLOS/scripts/
RUN /bin/bash /tmp/MLOS/scripts/install.cmake.sh && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*

# Restore the non-root user for default CMD execution.
USER mlos-docker

# End mlos-build-base-without-extras stage

FROM mlos-build-base-without-extras AS mlos-build-base-with-extras

# Use root for the setup tasks.
USER root

# Whether or not to include extras to make interactive editing inside the
# container using "docker exec" somewhat more reasonable.
# Run the docker build command with an additional "--build-arg=WithExtras=true"
# to install them as well.
RUN apt-get update && \
    apt-get -y install \
        man man-db manpages manpages-dev && \
    /etc/cron.weekly/man-db && \
    apt-get -y clean

# Restore the non-root user for default CMD execution.
USER mlos-docker

# End mlos-build-base-with-extras stage

FROM mlos-build-base-${MlosBuildBaseArg} AS mlos-build-base-with-source

USER mlos-docker

# Copy the current MLOS source tree into /src/MLOS so that it can also be
# executed standalone without a bind mount.
# Note: due to the recursive copy, this step is not very cacheable.
COPY --chown=mlos-docker:mlos-docker ./ /src/MLOS/

# End mlos-build-base-with-source stage
