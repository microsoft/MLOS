# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

FROM debian:stable-slim AS base

# Add some additional packages for the devcontainer terminal environment.
USER root
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        bash bash-completion \
        less colordiff \
        curl gpg \
        jq \
        ripgrep \
        vim-nox neovim \
        make \
        rename \
        sudo \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && echo "C-w: unix-filename-rubout" >> /etc/inputrc
    # Also tweak C-w to stop at slashes as well instead of just spaces

RUN useradd -m -U -G sudo vscode

RUN echo "Setup miniconda" \
    && curl -Ss https://repo.anaconda.com/pkgs/misc/gpgkeys/anaconda.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/conda.gpg \
    && gpg --keyring /etc/apt/trusted.gpg.d/conda.gpg --no-default-keyring --fingerprint 34161F5BF5EB1D4BFBBB8F0A8AEB4F8B29D82806 \
    && echo "deb [arch=amd64 signed-by=/etc/apt/trusted.gpg.d/conda.gpg] https://repo.anaconda.com/pkgs/misc/debrepo/conda stable main" | sudo tee /etc/apt/sources.list.d/conda.list \
    && apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends conda \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && adduser vscode conda \
    && /opt/conda/bin/conda init --system bash \
    && echo "# Upgrade conda and use strict priorities" \
    && echo "# Use the mamba solver (necessary for some quality of life speedups due to required packages to support Windows)" \
    && umask 0002 \
    && /opt/conda/bin/conda config --set channel_priority strict \
    && /opt/conda/bin/conda info \
    && /opt/conda/bin/conda update -v -y -n base -c defaults --all \
    && /opt/conda/bin/conda list -n base \
    && /opt/conda/bin/conda install -v -y -n base conda-libmamba-solver \
    && /opt/conda/bin/conda config --set solver libmamba \
    && /opt/conda/bin/conda list -n base \
    && /opt/conda/bin/conda clean -v -y -a \
    && /opt/conda/bin/conda run -n base pip cache purge

# Set some cache dirs to be owned by the vscode user even as we're currently
# executing as root to build the container image.
# NOTE: We do *not* mark these as volumes - it doesn't help rebuilding at all.

ARG VSCODE_UID=1000
ARG VSCODE_GID=1000
ARG DOCKER_GID=999

RUN groupmod --non-unique --gid $VSCODE_GID vscode \
    && usermod --non-unique --uid $VSCODE_UID --gid $NODE_GID vscode \
    && chown -R $NODE_UID:$NODE_GID /home/vscode \
    && groupadd --non-unique --gid $DOCKER_GID docker \
    && adduser vscode docker

ARG PIP_CACHE_DIR=/var/cache/pip
ENV PIP_CACHE_DIR=/var/cache/pip
RUN mkdir -p ${PIP_CACHE_DIR} \
    && chown -R vscode:conda ${PIP_CACHE_DIR} \
    && chmod -R u=rwX,g=rwXs,o=rX ${PIP_CACHE_DIR}

ARG CONDA_PKGS_DIRS=/opt/conda/pkgs
ENV CONDA_PKGS_DIRS=/opt/conda/pkgs
RUN mkdir -p ${CONDA_PKGS_DIRS} \
    && chown -R vscode:conda ${CONDA_PKGS_DIRS} \
    && chmod -R u=rwX,g=rwXs,o=rX ${CONDA_PKGS_DIRS}

USER vscode:conda

# No longer relevant since we're using conda-forge in the environment files by default now.
## Update the base. This helps save space by making sure the same version
## python is used for both the base env and mlos env.
#RUN umask 0002 \
#    && /opt/conda/bin/conda update -v -y -n base -c defaults --all \
#    && /opt/conda/bin/conda update -v -y -n base -c defaults conda python \
#    && /opt/conda/bin/conda clean -v -y -a \
#    && /opt/conda/bin/conda run -n base pip cache purge

# Install some additional editor packages for the base environment.
RUN umask 0002 \
    && /opt/conda/bin/conda run -n base pip install --no-cache-dir -U pynvim

# Setup (part of) the mlos environment in the devcontainer.
# NOTEs:
# - The mlos_deps.yml file is prepared by the prep-container-build script(s).
# - The rest happens during first container start once the source is available.
# See Also: updateContentCommand in .devcontainer/devcontainer.json
RUN mkdir -p /opt/conda/pkgs/cache/ && chown -R vscode:conda /opt/conda/pkgs/cache/
RUN /opt/conda/bin/conda init bash \
    && /opt/conda/bin/conda config --set solver libmamba

# Prepare the mlos_deps.yml file in a cross platform way.
FROM debian:stable-slim AS deps-prep
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        python3-minimal python3-setuptools
COPY --chown=vscode:conda . /tmp/conda-tmp/
RUN /tmp/conda-tmp/prep-deps-files.sh \
    && ls -l /tmp/conda-tmp/ # && cat /tmp/conda-tmp/combined.requirements.txt /tmp/conda-tmp/mlos_deps.yml

# Install some additional dependencies for the mlos environment.
# Make sure they have conda group ownership to make the devcontainer more
# reliable useable across vscode uid changes.
FROM base AS devcontainer
USER vscode
COPY --from=deps-prep --chown=vscode:conda /tmp/conda-tmp/mlos_deps.yml /tmp/conda-tmp/combined.requirements.txt /tmp/conda-tmp/
RUN umask 0002 \
    && sg conda -c "/opt/conda/bin/conda env create -n mlos -v -f /tmp/conda-tmp/mlos_deps.yml" \
    && sg conda -c "/opt/conda/bin/conda run -n mlos pip install --no-cache-dir -U -r /tmp/conda-tmp/combined.requirements.txt" \
    && sg conda -c "/opt/conda/bin/conda run -n mlos pip cache purge" \
    && sg conda -c "/opt/conda/bin/conda clean -v -y -a" \
    && mkdir -p /opt/conda/pkgs/cache/ && chown -R vscode:conda /opt/conda/pkgs/cache/
RUN mkdir -p /home/vscode/.conda/envs \
    && ln -s /opt/conda/envs/mlos /home/vscode/.conda/envs/mlos

# Try and prime the devcontainer's ssh known_hosts keys with the github one for scripted calls.
RUN mkdir -p /home/vscode/.ssh \
    && ( \
        grep -q ^github.com /home/vscode/.ssh/known_hosts \
        || ssh-keyscan github.com | tee -a /home/vscode/.ssh/known_hosts \
    )
