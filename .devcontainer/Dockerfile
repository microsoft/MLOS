# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

FROM mcr.microsoft.com/vscode/devcontainers/base AS base

# Add some additional packages for the devcontainer terminal environment.
USER root
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        bash bash-completion \
        less colordiff \
        curl gpg ca-certificates \
        jq \
        ripgrep \
        vim-nox neovim python3-pynvim \
        make \
        rename \
        sudo \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && echo "C-w: unix-filename-rubout" >> /etc/inputrc
    # Also tweak C-w to stop at slashes as well instead of just spaces

# Prepare the mlos_deps.yml file in a cross platform way.
FROM mcr.microsoft.com/vscode/devcontainers/base AS deps-prep
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        python3-minimal python3-venv
COPY --chown=vscode . /tmp/conda-tmp/
RUN /tmp/conda-tmp/prep-deps-files.sh \
    && ls -l /tmp/conda-tmp/ # && cat /tmp/conda-tmp/combined.requirements.txt /tmp/conda-tmp/mlos_deps.yml

FROM base AS conda

# Set some cache dirs to be owned by the vscode user even as we're currently
# executing as root to build the container image.
# NOTE: We do *not* mark these as volumes - it doesn't help rebuilding at all.

RUN addgroup conda \
    && adduser vscode conda

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

# Try and prime the devcontainer's ssh known_hosts keys with the github one for scripted calls.
RUN mkdir -p /home/vscode/.ssh \
    && ( \
        grep -q ^github.com /home/vscode/.ssh/known_hosts \
        || ssh-keyscan github.com | tee -a /home/vscode/.ssh/known_hosts \
    )

COPY --from=deps-prep --chown=vscode:conda /tmp/conda-tmp/.pre-commit-config.yaml /tmp/conda-tmp/mlos_deps.yml /tmp/conda-tmp/combined.requirements.txt /tmp/conda-tmp/

# Combine the installation of miniconda and the mlos dependencies into a single step in order to save space.
# This allows the mlos env to reference the base env's packages without duplication across layers.
RUN echo "Setup miniconda" \
    && curl -Ss --url https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-$(uname -m).sh -o /tmp/miniconda3.sh \
    && sudo sh /tmp/miniconda3.sh -b -u -p /opt/conda \
    && rm -rf /tmp/miniconda3.sh \
    && echo "# Adjust the conda installation to be user/group writable." \
    && sudo /opt/conda/bin/conda init --system \
    && sudo chgrp -R conda /opt/conda \
    && sudo chmod -R g+wX /opt/conda \
    && find /opt/conda -type d -print0 | xargs -0 sudo chmod -c g+s \
    && umask 0002 \
    && echo "# Use conda-forge first to get the latest versions of packages " \
    && echo "# and reduce duplication with mlos env (which also uses conda-forge first)." \
    && echo "# Upgrade conda and use strict priorities" \
    && echo "# Use the mamba solver (necessary for some quality of life speedups due to required packages to support Windows)" \
    && /opt/conda/bin/conda init \
    && /opt/conda/bin/conda config --set channel_priority strict \
    && /opt/conda/bin/conda info \
    && /opt/conda/bin/conda config --show \
    && /opt/conda/bin/conda tos accept --override-channels --channel defaults \
    && /opt/conda/bin/conda update -v -y -n base -c conda-forge -c defaults --all \
    && /opt/conda/bin/conda list -n base \
    && /opt/conda/bin/conda install -v -y -n base -c conda-forge -c defaults conda-libmamba-solver \
    && /opt/conda/bin/conda config --system --set solver libmamba \
    && echo "# Install some additional editor packages for the base environment." \
    && /opt/conda/bin/conda run -n base pip install --no-cache-dir -U pynvim \
    && echo "# Clean up conda cache to save some space." \
    && /opt/conda/bin/conda list -n base \
    && /opt/conda/bin/conda clean -v -y -a \
    && /opt/conda/bin/conda run -n base pip cache purge \
    && echo "# Install some additional dependencies for the mlos environment." \
    && echo "# Make sure they have conda group ownership to make the devcontainer more" \
    && echo "# reliable useable across vscode uid changes." \
    && sg conda -c "/opt/conda/bin/conda env create -n mlos -v -f /tmp/conda-tmp/mlos_deps.yml" \
    && sg conda -c "/opt/conda/bin/conda run -n mlos pip install --no-cache-dir -U -r /tmp/conda-tmp/combined.requirements.txt" \
    && sg conda -c "git -C /tmp/conda-tmp init" \
    && sg conda -c "/opt/conda/bin/conda run --cwd /tmp/conda-tmp -n mlos pre-commit install-hooks -c .pre-commit-config.yaml" \
    && sg conda -c "/opt/conda/bin/conda run -n mlos pip cache purge" \
    && sg conda -c "/opt/conda/bin/conda clean -v -y -a" \
    && mkdir -p /opt/conda/pkgs/cache/ && chown -R vscode:conda /opt/conda/pkgs/cache/ \
    && mkdir -p /home/vscode/.conda/envs \
    && ln -s /opt/conda/envs/mlos /home/vscode/.conda/envs/mlos

#ENV PATH=/opt/conda/bin:$PATH
ENV PATH=/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
