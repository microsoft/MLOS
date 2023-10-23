# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# To reduce disk space, we manage installing conda ourselves instead of using
# the miniconda devcontainer image as a base so that we can combine multiple
# hard linked files into a single layer.

ARG DEBIAN_FRONTEND=noninteractive

# To start, we need to install a basic set of packages to support conda.
FROM mcr.microsoft.com/vscode/devcontainers/base:debian AS base
USER root
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
        python3-minimal python3-pip \
        build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Prepare the mlos_deps.yml file in a cross platform way.
# See Also: updateContentCommand in .devcontainer/devcontainer.json
FROM base AS deps-prep
COPY --chown=vscode:vscode . /tmp/conda-tmp/
RUN /tmp/conda-tmp/prep-deps-files.sh \
    && ls -l /tmp/conda-tmp/ && cat /tmp/conda-tmp/combined.requirements.txt /tmp/conda-tmp/mlos_deps.yml

# Build the devcontainer image.
FROM base AS terminal-env
# Add some additional packages for the devcontainer terminal environment.
USER root
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
        bash bash-completion \
        less colordiff \
        curl jq \
        ripgrep \
        vim-nox neovim python3-pynvim \
        make \
        rename \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    echo "# Also tweak C-w to stop at slashes as well instead of just spaces" \
    && echo "C-w: unix-filename-rubout" >> /etc/inputrc \
    && addgroup conda \
    && adduser vscode conda

# Now start installing conda, updating it, configuring it, and setting up the
# mlos environment all in one shot to reduce the number of layers and allow
# hardlinking files within that layer.
FROM terminal-env AS devcontainer

ARG PIP_CACHE_DIR=/var/cache/pip
ENV PIP_CACHE_DIR=/var/cache/pip

ARG CONDA_PKGS_DIRS=/opt/conda/pkgs
ENV CONDA_PKGS_DIRS=/opt/conda/pkgs

USER vscode
COPY --from=deps-prep --chown=vscode:vscode /tmp/conda-tmp/mlos_deps.yml /tmp/conda-tmp/combined.requirements.txt /tmp/conda-tmp/
RUN set -x \
    && curl -Ss https://repo.anaconda.com/pkgs/misc/gpgkeys/anaconda.asc | sudo -n tee /etc/apt/trusted.gpg.d/anaconda.asc \
    && echo "deb [signed-by=/etc/apt/trusted.gpg.d/anaconda.asc] https://repo.anaconda.com/pkgs/misc/debrepo/conda stable main" | sudo -n tee /etc/apt/sources.list.d/conda.list \
    && sudo -n apt-get update \
    && sudo -n apt-get -y install --no-install-recommends \
        conda \
    && sudo -n apt-get clean && sudo -n rm -rf /var/lib/apt/lists/* \
    && echo "# Give the vscode user access to modify the conda envs directly." \
    && sudo -n chgrp -R conda /opt/conda \
    && sudo -n chmod -R g+w /opt/conda \
    && echo "# Set some cache dirs to be owned by the vscode user even as we're currently" \
    && echo "# executing as root to build the container image." \
    && sudo -n mkdir -p ${PIP_CACHE_DIR} \
    && sudo -n chown -R vscode:conda ${PIP_CACHE_DIR} \
    && sudo -n chmod -R u=rwX,g=rwXs,o=rX ${PIP_CACHE_DIR} \
    && sudo -n mkdir -p ${CONDA_PKGS_DIRS}/cache/ \
    && sudo -n chown -R vscode:conda ${CONDA_PKGS_DIRS} \
    && sudo -n chmod -R u=rwX,g=rwXs,o=rX ${CONDA_PKGS_DIRS} \
    && echo "# Upgrade conda and use strict priorities" \
    && echo "# Use the mamba solver (necessary for some quality of life speedups due to" \
    && echo "# required packages to support Windows)" \
    && umask 0002 \
    && /opt/conda/bin/conda init bash \
    && /opt/conda/bin/conda config --set channel_priority strict \
    && /opt/conda/bin/conda info \
    && /opt/conda/bin/conda update -v -y -n base -c defaults --all \
    && /opt/conda/bin/conda list -n base \
    && /opt/conda/bin/conda install -v -y -n base conda-libmamba-solver \
    && /opt/conda/bin/conda config --set solver libmamba \
    && /opt/conda/bin/conda list -n base \
    && echo "# Update the base. This helps save space by making sure the same version" \
    && echo "# python is used for both the base env and mlos env." \
    && /opt/conda/bin/conda update -v -y -n base -c defaults conda python \
    && /opt/conda/bin/conda list -n base \
    && echo "# Install some additional editor packages for the base environment." \
    && /opt/conda/bin/conda run -n base pip install --no-cache-dir -U pynvim \
    && echo "# Install some additional dependencies for the mlos environment." \
    && /opt/conda/bin/conda env create -n mlos -v -f /tmp/conda-tmp/mlos_deps.yml \
    && /opt/conda/bin/conda run -n mlos pip install -U -r /tmp/conda-tmp/combined.requirements.txt \
    && mkdir -p /home/vscode/.conda/envs \
    && ln -s /opt/conda/envs/mlos /home/vscode/.conda/envs/mlos \
    && echo "# Reclaim some disk space" \
    && /opt/conda/bin/conda clean -v -y -a && /opt/conda/bin/conda run -n base pip cache purge
