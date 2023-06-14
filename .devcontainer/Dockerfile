# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

FROM mcr.microsoft.com/devcontainers/miniconda:3 AS base

# Add some additional packages for the devcontainer terminal environment.
USER root
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        bash bash-completion \
        less colordiff \
        curl jq \
        ripgrep \
        vim-nox neovim python3-pynvim \
        make \
        rename \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && echo "C-w: unix-filename-rubout" >> /etc/inputrc
    # Also tweak C-w to stop at slashes as well instead of just spaces

# Set some cache dirs to be owned by the vscode user even as we're currently
# executing as root to build the container image.
# NOTE: We do *not* mark these as volumes - it doesn't help rebuilding at all.

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

USER vscode

# Use the mamba solver (necessary for some quality of life speedups due to
# required packages to support Windows)
RUN umask 0002 \
    && /opt/conda/bin/conda install -v -y -n base conda-libmamba-solver \
    && /opt/conda/bin/conda config --set solver libmamba

# Update the base. This helps save space by making sure the same version
# python is used for both the base env and mlos env.
RUN umask 0002 \
    && /opt/conda/bin/conda update -v -y -n base -c defaults --all \
    && /opt/conda/bin/conda clean -v -y -a

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
FROM mcr.microsoft.com/devcontainers/miniconda:3 AS deps-prep
COPY --chown=vscode:conda . /tmp/conda-tmp/
RUN /tmp/conda-tmp/prep-deps-files.sh \
    && ls -l /tmp/conda-tmp/ # && cat /tmp/conda-tmp/combined.requirements.txt /tmp/conda-tmp/mlos_deps.yml

# Install some additional dependencies for the mlos environment.
FROM base AS devcontainer
COPY --from=deps-prep --chown=vscode:conda /tmp/conda-tmp/mlos_deps.yml /tmp/conda-tmp/combined.requirements.txt /tmp/conda-tmp/
RUN umask 0002 \
    && /opt/conda/bin/conda env create -n mlos -v -f /tmp/conda-tmp/mlos_deps.yml \
    && /opt/conda/bin/conda run -n mlos pip install -U -r /tmp/conda-tmp/combined.requirements.txt \
    && /opt/conda/bin/conda clean -v -y -a \
    && mkdir -p /opt/conda/pkgs/cache/ && chown -R vscode:conda /opt/conda/pkgs/cache/
RUN mkdir -p /home/vscode/.conda/envs \
    && ln -s /opt/conda/envs/mlos /home/vscode/.conda/envs/mlos
