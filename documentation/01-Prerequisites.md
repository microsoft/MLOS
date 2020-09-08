# Prerequisites for building and using MLOS

These are one-time setup instructions that should be executed prior to following the build instructions in [02-Build.md](./02-Build.md)

## Contents

- [Prerequisites for building and using MLOS](#prerequisites-for-building-and-using-mlos)
  - [Contents](#contents)
  - [Linux](#linux)
    - [Linux Distribution Requirements](#linux-distribution-requirements)
    - [Clone the repository](#clone-the-repository)
    - [Option 1: Linux Docker Build Env](#option-1-linux-docker-build-env)
      - [Install Docker](#install-docker)
      - [Build the Docker Image](#build-the-docker-image)
    - [Option 2: Manual Build Tools Install](#option-2-manual-build-tools-install)
    - [Install Python on Linux](#install-python-on-linux)
      - [Option 1: Docker Python Install](#option-1-docker-python-install)
      - [Option 2: Using Conda](#option-2-using-conda)
      - [Option 3: Manual Python Install](#option-3-manual-python-install)
  - [Windows](#windows)
    - [Step 1: Clone the repository](#step-1-clone-the-repository)
    - [Step 2: Install Python](#step-2-install-python)
    - [Step 3: Install Docker on Windows](#step-3-install-docker-on-windows)
    - [Step 4: Install Windows Build Tools](#step-4-install-windows-build-tools)

MLOS currently supports 64-bit Intel/AMD platforms, though ARM64 support is under development.
It supports Windows and Linux environments. Below we provide instructions for each OS.

## Linux

On Linux, there are a couple of options to install the build tools and the needed Python environment.
The preferred way is via the [Docker images](#option-1-linux-docker-build).
All of them require `git` and, of course, a Linux installation:

### Linux Distribution Requirements

- Ubuntu 16.04 (xenial), 18.04 (bionic), 20.04 (focal)

> Other distros/versions may work, but are untested.

### Clone the repository

Make sure you have `git` available:

```sh
apt-get -y install git
```

Clone the repository:

```sh
git clone https://github.com/microsoft/MLOS.git
```

### Option 1: Linux Docker Build Env

#### Install Docker

Docker is used for certain portions of the end-to-end examples and as a convient way to setup the build/dev/test environments.

> If you are starting with the Python only setup, you can skip this step for now if you wish.

Please see the official Docker install documenation for distribution specific documentation. The Ubuntu docs are [here](https://docs.docker.com/engine/install/ubuntu/).

#### Build the Docker Image

To automatically setup a Linux build environment using `docker`, run the following to build the image locally:

```sh
# Select your target Ubuntu version:
UbuntuVersion=20.04
# Build the docker image:
docker build --build-arg=UbuntuVersion=$UbuntuVersion -t mlos/build:ubuntu-$UbuntuVersion .
```

> Where `UbuntuVersion` can also be set to another supported version of Ubuntu.

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
> Note: `libxml2` pulls an appropriate version of `libicu`.
> Note: most other dependencies like `dotnet` and `cmake` are automatically fetched to the `tools/` directory using helpers in `scripts/` and invoked by the `Makefile` and `cmake` tools.

Optional tools:

```sh
sudo apt-get install exuberant-ctags
```

> When available `make ctags` can be invoked to help generate a `tags` database at the root of the source tree to allow easier code navigation in editors that support it.

### Install Python on Linux

#### Option 1: Docker Python Install

If you used the [Docker build image](#docker-build-image) instructions you're done!  All of the required packages should already be installed in the image.

#### Option 2: Using Conda

TODO

#### Option 3: Manual Python Install

1. Install Python 3.7

    ```sh
    # We need to add a special apt repository for Python 3.7 support:
    sudo apt-get -y install \
        software-properties-common apt-transport-https
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get -y install python3.7
    ```

2. Install MLOS Python dependencies:

    ```sh
    # Also add some dependencies needed by some of the pip modules
    sudo apt-get -y install python3-pip python3.7-dev \
        build-essential libfreetype-dev unixodbc-dev
    ```

    ```sh
    python3.7 -m pip install --upgrade pip
    python3.7 -m pip install setuptools

    python3.7 -m pip install \
        -r source/Mlos.Python/requirements.txt
    ```

## Windows

MLOS is easiest to use on Windows 10, Version 1903 (March 2019) or newer.

### Step 1: Clone the repository

[Install git](https://git-scm.com/) and clone the repo:

```shell
git clone https://github.com/microsoft/MLOS.git
```

### Step 2: Install Python

TODO

### Step 3: Install Docker on Windows

Portions of MLOS use Docker. Please follow the instructions on the [Docker Website](https://www.docker.com/products/docker-desktop) to install it. Note that on Windows *Home*, you need a fairly recent Windows version to install Docker (Windows 10 1903 or newer).

On Windows 10 v1903 or newer, we recommend you use the [Windows Subsytem for Linux v2](https://docs.microsoft.com/en-us/windows/wsl/install-win10#update-to-wsl-2) to run the containers. On older Windows 10, you can resort to the [Hyper-V support](https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/) of Docker.

### Step 4: Install Windows Build Tools

Download and install Visual Studio 2019 (free) Community Edition:

<https://visualstudio.microsoft.com/vs/community/>

Be sure to include support for .Net Core and C++.
