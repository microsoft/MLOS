# Prerequisites for building and using MLOS

These are one-time setup instructions that should be executed prior to following the build instructions in [02-Build.md](./02-Build.md)

## Contents

- [Prerequisites for building and using MLOS](#prerequisites-for-building-and-using-mlos)
  - [Contents](#contents)
  - [Linux](#linux)
    - [Requirements](#linux-requirements)
    - [Clone the repository](#clone-the-repository)
    - [Linux build tools](#linux-build-tools)
      - [Linux Build Manually](#linux-build-manually)
      - [Docker](#docker)
    - [Linux Python Install](#linux-python-install)
    - [Linux Docker Install](#linux-docker-install)
  - [Windows](#Windows)
    - [Windows Requirements](#windows-requirements)
    - [Clone the repository](#clone-the-repository)
    - [Windows build tools](#windows-build-tools)
      - [Using a local script](#using-a-local-script)
      - [Using Chocolatey](#using-chocolatey)
      - [Windows Build Manually](#win-build-manually)
    - [Windows Pythoon Install](#windows-python-install)
    - [Windows Docker Install](#windows-docker-install)

MLOS currently supports 64-bit Intel/AMD platforms, though ARM64 support is under development.
It supports Windows and Linux environments. Below we provide instructions for each OS.

## Linux

### Linux Requirements

  - Ubuntu 16.04 (xenial), 18.04 (bionic), 20.04 (focal)

  > Other distros/versions may work, but are untested.


### Linux build tools

#### Linux Build Manually
To manually setup your own Linux build environment:

```sh
# Make sure some basic build tools are available:
sudo apt-get install git make build-essential
```

```sh
# Make sure some apt related tools are available:
sudo apt-get install \
  apt-transport-https ca-certificates curl gnupg-agent software-properties-common

# Make sure an appropriate version of clang is available:
./script/install.llvm-clang.sh
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

#### Docker

To automatically setup a Linux build environment using `docker`, run the following:

```sh
# Select your target Ubuntu version:
UbuntuVersion=20.04
# Build the docker image:
docker build --build-arg=UbuntuVersion=$UbuntuVersion -t mlos/build:ubuntu-$UbuntuVersion .
```

> Where `UbuntuVersion` can also be set to another supported version of Ubuntu.

> Tip: you can also pass `--build-arg=http_proxy=http:/some-proxy-caching-host:3128` to help direct `apt` and `pip` to fetch the necessary packages via local caches.

See [02-Build.md](./02-Build.md#docker) for instructions on how to run this image.


### Clone the repository

Cross platform

```shell
git clone https://github.com/microsoft/MLOS.git
```

> See <https://git-scm.com/book/en/v2/Getting-Started-Installing> for help installing `git`.


### Linux Python Install

1. Install Python 3.7

    ```sh
    # We need to add a special apt repository for Python 3.7 support:
    sudo apt-get -y install software-properties-common apt-transport-https
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

    python3.7 -m pip install -r source/Mlos.Python/requirements.txt
    ```


### Linux Docker Install

Please see the official Docker install documenation for distribution specific documentation:

- Ubuntu: <https://docs.docker.com/engine/install/ubuntu/>

  As a short guide (copied from the link above):

  ```sh
  sudo apt-get remove docker docker-engine docker.io containerd runc
  sudo apt-get update

  sudo apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common

  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

  sudo add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) \
    stable"

  sudo apt-get update
  sudo apt-get install docker-ce docker-ce-cli containerd.io

  apt-get install docker-ce
  ```

## Windows

> Note: Most Windows shell commands here expect `powershell` (or [`pwsh`](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell-core-on-windows)).

### Windows Requirements

  > Portions of MLOS use Docker, which requires a Linux VM.  So support for *one* of the following is required:
  - [WSL2](https://docs.microsoft.com/en-us/windows/wsl/install-win10#update-to-wsl-2) (e.g. Windows 10 build >= 2004, including Pro, Enterprise, *and* Home), *or*
  - [Hyper-V support](https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/) (only Windows 10 Pro/Enterprise, *not* ~~Home~~)

  > Note: WSL2 is advised for ease of setup, integrations with Docker, and more flexible resource utilizations benefits.

  See the [Install Docker](#install-docker) section for more details.

- Linux
  - Ubuntu 16.04 (xenial), 18.04 (bionic), 20.04 (focal)

  > Other distros/versions may work, but are untested.


### Windows build tools

There are several build tools install paths to choose from on Windows.

> Note: For most of these commands we first need a `powershell` with Administrator privileges:

1. Start a powershell environment with Administrator privileges:

    ```shell
    powershell -NoProfile -Command "Start-Process powershell -Verb RunAs"
    ```

    > If you find that when you start a new shell environment it can't find some of the tools installed later on, the new `PATH` environment variable might not be updated.  Try to restart your machine.

2. Allow local powershell scripts to be executed:

    ```powershell
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    ```

    > This is necessary for our build environment initialization script `scripts/init.windows.ps1` as well.

#### Using a local script

1. Launch the script we provide in the MLOS repo to install/update Visual Studio 2019 Community Edition with the necessary components:

    ```powershell
    .\scripts\install-vs2019.ps1
    ```

    ```text
    Waiting for installer process vs_community to end ...
    Waiting for installer process vs_community to end ...
    ...
    Done
    ```

    > Note: This will install the free Community edition by default. Use the `-Sku` option if you prefer to install the `Enterprise` version instead.

#### Using Chocolatey

[Chocolatey](https://chocolatey.org) is a package manager for Windows to help support scripted and reproducable installation of tools.

0. Install chocolatey:

    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    ```

    ```text
    Getting latest version of the Chocolatey package for download.
    ...
    Chocolatey (choco.exe) is now ready.
    You can call choco from anywhere, command line or powershell by typing choco.
    Run choco /? for a list of functions.
    You may need to shut down and restart powershell and/or consoles
    first prior to using choco.
    ...
    ```

    See Also: <https://chocolatey.org/install>

1. Install build tools:

    ```shell
    choco install -y git
    choco install -y dotnetcore-runtime.install --params="Skip32Bit"
    choco install -y dotnetcore dotnetcore-sdk
    choco install -y visualstudio2019buildtools visualstudio2019-workload-netcorebuildtools visualstudio2019-workload-vctools
    ```

2. Install an editor
  (*optional*)

    ```shell
    choco install -y vscode
    choco install -y vscode-cpptools vscode-csharp vscode-cake
    ```

    or

    ```shell
    choco install -y visualstudio2019community
    ```

#### Windows Build Manually

Download and install Visual Studio 2019 (free) Community Edition:

<https://visualstudio.microsoft.com/vs/community/>

Be sure to include support for .Net Core, C++, CMake



### Clone the repository

Cross platform

```shell
git clone https://github.com/microsoft/MLOS.git
```

> See <https://git-scm.com/book/en/v2/Getting-Started-Installing> for help installing `git`.





### Windows Python Install

#### Using Chocolatey

0. See above for instructions on installing Chocolatey.

1. Install Python

    ```shell
    choco install -y python --version=3.7.8
    ```

2. Install MLOS Python dependencies:

    ```shell
    pip install -r source\Mlos.Python\requirements.txt
    ```


### Windows Docker Install

As mentioned above, Docker on Windows first requires a Linux VM.

> As such, if your Windows development environment is itself a VM, you'll need one that supports *nested virtualization*.\
> <https://docs.microsoft.com/en-us/azure/virtual-machines/acu>

- The easiest route is through [WSL2](https://docs.microsoft.com/en-us/windows/wsl/install-win10):

  1. Enable WSL2 on Windows 10 build 2004 or later:

      ```shell
      dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

      dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
      ```

      ```powershell
      Invoke-WebRequest -Uri https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi -OutFile wsl_update_x64.msi -UseBasicParsing
      Invoke-Item wsl_update_x64.msi
      ```

      > Note: You may need to restart at this point.

      ```shell
      wsl --set-default-version 2
      ```

  2. [Install a Linux distro for WSL2](https://docs.microsoft.com/en-us/windows/wsl/install-manual) (e.g. [Ubuntu 20.04](https://www.microsoft.com/en-us/p/ubuntu-2004-lts/9n6svws3rx71?rtc=1&activetab=pivot:overviewtab)):

      ```powershell
      Invoke-WebRequest -Uri https://aka.ms/wslubuntu2004 -OutFile Ubuntu-20.04.appx -UseBasicParsing

      Add-AppxPackage ./Ubuntu-20.04.appx
      ```

      > Finish the installation by launching the "*Ubuntu 20.04*" distribution from the Start menu to setup your Linux account in the WSL distribution.

  3. Install Docker

      - Chocolatey

        ```shell
        choco install docker-desktop docker-cli
        ```

      - Manually

        <https://docs.docker.com/docker-for-windows/install/>

     Configure Docker Desktop to use WSL2

  At this point `docker` commands should work naturally from any shell environment and proxied through to the WSL2 Linux distribution configured in Docker Desktop.

- Alternatively, you can enable Hyper-V and use [`docker-machine`](https://docs.docker.com/machine/reference/create/) to create a VM suitable for running Docker containers:

  > Note: This isn't supported on Windows Home edition.

  1. Enable Hyper-V

      ```powershell
      Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
      ```

  2. Install `docker-machine`:

      - Manually:

        <https://docs.docker.com/machine/install-machine/>

      - Or, via Chocolatey:

        ```shell
        choco install docker-machine
        ```

  3. Build a VM for running Docker containers:

      ```shell
      docker-machine create --driver hyperv --hyperv-virtual-switch "NameOfYourDockerVSwitch" docker-dev-vm
      ```

  4. Invoke a shell environment to use it:

      ```shell
      docker-machine env --shell powershell docker-dev-vm | Invoke-Expression
      ```

      From within this shell environment, `docker` cli commands should be proxied through to your `docker-dev-vm` prepared by `docker-machine`.



--------------



## Install build tools


