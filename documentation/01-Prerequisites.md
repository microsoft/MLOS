# Prerequisites for building and using MLOS

These are one-time setup instructions that should be executed prior to following the build instructions in [02-Build.md](./02-Build.md)

## Contents

- [Prerequisites for building and using MLOS](#prerequisites-for-building-and-using-mlos)
  - [Contents](#contents)
  - [Clone the repository](#clone-the-repository)
  - [Python quickstart](#python-quickstart)
  - [Linux](#linux)
    - [Linux Distribution Requirements](#linux-distribution-requirements)
    - [Option 1: Linux Docker Build Env](#option-1-linux-docker-build-env)
      - [Install Docker](#install-docker)
      - [Build the Docker Image](#build-the-docker-image)
        - [Pull the upstream docker image](#pull-the-upstream-docker-image)
        - [Local docker image build](#local-docker-image-build)
    - [Option 2: Manual Build Tools Install](#option-2-manual-build-tools-install)
    - [Install Python on Linux](#install-python-on-linux)
      - [Option 1: Docker Python Install](#option-1-docker-python-install)
      - [Option 2: Using Conda](#option-2-using-conda)
  - [Windows](#windows)
    - [Step 1: Install Python](#step-1-install-python)
    - [Step 2: Install Docker on Windows](#step-2-install-docker-on-windows)
    - [Step 3: Install Windows Build Tools](#step-3-install-windows-build-tools)
    - [Step 4: Build the Docker image](#step-4-build-the-docker-image)

MLOS currently supports 64-bit Intel/AMD platforms, though ARM64 support is under development.
It supports Windows and Linux environments. Below we provide instructions for each OS.

## Clone the repository

Make sure you have [git](https://git-scm.com/) installed and clone the repo:

```shell
git clone https://github.com/microsoft/MLOS.git
cd MLOS
```

## Python quickstart

Some of the examples require only the installation of the `mlos` Python library, which is easy to install on any operating system.

It's recommended to use the [Anaconda python distribution](https://www.anaconda.com/products/individual).
or the smaller [miniconda installer](https://docs.conda.io/en/latest/miniconda.html).
After installing either anaconda or miniconda, you can create a new environment with all requirements for the examples using

```shell
conda env create -f MLOS/source/Mlos.Notebooks/environment.yml
```

The environment will be called `mlos_python_environment` and you can activate it as follows:

```shell
conda activate mlos_python_environment
```

Use `pip` to install the Python library:

```shell
pip install MLOS/source/Mlos.Python/
```

After this installation, you can run any of the Python-only example notebooks. To do so you can:

```shell
jupyter-notebook --notebook-dir=MLOS/source/Mlos.Notebooks
```

Jupyter will list a few notebooks. A good place to start is the *BayesianOptimization.ipynb*, which provides an [Introduction to Bayesian Optimization](../source/Mlos.Notebooks/BayesianOptimization.ipynb#mlos-github-tree-view).

## Linux

On Linux, there are a couple of options to install the build tools and the needed Python environment.
The preferred way is via the [Docker images](#option-1-linux-docker-build).
All of them require `git` and, of course, a Linux installation:

### Linux Distribution Requirements

- Ubuntu 16.04 (xenial), 18.04 (bionic), 20.04 (focal)

> Other distros/versions may work, but are untested.

### Option 1: Linux Docker Build Env

#### Install Docker

Docker is used for certain portions of the end-to-end examples and as a convient way to setup the build/dev/test environments.

> If you are starting with the [Python only setup](#install-python-on-linux), you can skip this step for now if you wish.

Please see the official Docker install documenation for distribution specific documentation. The Ubuntu docs are [here](https://docs.docker.com/engine/install/ubuntu/).

#### Build the Docker Image

##### Pull the upstream docker image

```sh
docker pull ghcr.io/microsoft-cisl/mlos/mlos-build-ubuntu-20.04
```

##### Local docker image build

To automatically setup a Linux build environment using `docker`, run the following to build the image locally:

```sh
# Build the docker image:
docker build . --build-arg=UbuntuVersion=20.04 -t mlos-build-ubuntu-20.04 \
    --cache-from ghcr.io/microsoft-cisl/mlos/mlos-build-ubuntu-20.04
```

> Where `20.04` can also be replaced with another [supported `UbuntuVersion`](#linux-distribution-requirements).
>
> Note: in Linux environments, you can also simply execute `make docker-image`
>
> See the [`Makefile`](../Makefile#mlos-github-tree-view) for advanced usage details.

See [02-Build.md](./02-Build.md#docker) for instructions on how to run this image.

### Option 2: Manual Build Tools Install

To manually setup your own Linux build environment:

```sh
# Make sure some basic build tools are available:
sudo apt-get install build-essential
```

```sh
# Make sure some apt related tools are available:
sudo apt-get install \
  apt-transport-https ca-certificates curl gnupg-agent software-properties-common

# Make sure an appropriate version of clang is available:
./scripts/install.llvm-clang.sh
```

```sh
# Make sure some dotnet dependencies are available:
sudo apt-get install liblttng-ctl0 liblttng-ust0 zlib1g libxml2
```

> Note: older distros such as Ubuntu 16.04 may also need the `libcurl3` package installed for `dotnet restore` to work, but is unavailable on (or will break) more recent versions of Ubuntu.
>
> Note: `libxml2` pulls an appropriate version of `libicu`.

```sh
# Install dotnet in the system:
./scripts/install.dotnet.sh
```

```sh
# Install cmake in the system:
./scripts/install.cmake.sh
```

Optional tools:

```sh
sudo apt-get install exuberant-ctags
```

> When available `make ctags` can be invoked to help generate a `tags` database at the root of the source tree to allow easier code navigation in editors that support it.

### Install Python on Linux

#### Option 1: Docker Python Install

If you used the [Docker build image](#docker-build-image) instructions you're done!  All of the required packages should already be installed in the image.

#### Option 2: Using Conda

Follow the [Python Quickstart](#python-quickstart) above.

## Windows

MLOS is easiest to use on Windows 10, Version 1903 (March 2019) or newer.

### Step 1: Install Python

Follow the [Python Quickstart](#python-quickstart) above.

### Step 2: Install Docker on Windows

Portions of MLOS use Docker. Please follow the instructions on the [Docker Website](https://www.docker.com/products/docker-desktop) to install it. Note that on Windows *Home*, you need a fairly recent Windows version to install Docker (Windows 10 1903 or newer).

On Windows 10 v1903 or newer, we recommend you use the [Windows Subsytem for Linux v2](https://docs.microsoft.com/en-us/windows/wsl/install-win10#update-to-wsl-2) to run the containers. On older Windows 10, you can resort to the [Hyper-V support](https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/) of Docker.

### Step 3: Install Windows Build Tools

Download and install Visual Studio 2019 (free) Community Edition:

<https://visualstudio.microsoft.com/vs/community/>

Be sure to include support for .Net Core and C++.

### Step 4: Build the Docker image

The instructions for [building the docker image](#build-the-docker-image) are the same as for Linux.
