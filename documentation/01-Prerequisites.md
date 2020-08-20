# Prerequisites for building and using MLOS

These are one-time setup instructions that should be executed prior to following the build instructions in [02-Build.md](./02-Build.md)

## Contents

- [Requirements](#requirements)
- [Clone the repository](#clone-the-repository)
- [Install build tools](#install-build-tools)
  - [Linux](#linux-build-tools)
  - [Windows](#windows-build-tools)
- [Install Python Dependencies](#install-python-dependencies)
  - [Linux](#linux-python-install)
  - [Windows](#windows-python-install)
- [Install Docker](#install-docker)
  - [Linux](#linux-docker-install)
  - [Windows](#windows-docker-install)

> Note: Most Windows shell commands here expect `powershell` (or [`pwsh`](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell-core-on-windows)).

## Requirements

MLOS currently only supports 64-bit Intel/AMD platforms, though ARM64 support is under development.

It supports Windows and Linux environments.

- Windows

  > Portions of MLOS require Docker, which requires a Linux VM.  So support for *one* of the following is required:
  - [WSL2](https://docs.microsoft.com/en-us/windows/wsl/install-win10#update-to-wsl-2) (e.g. Windows 10 build >= 2004, including Pro, Enterprise, *and* Home), *or*
  - [Hyper-V support](https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/) (only Windows 10 Pro/Enterprise, *not* ~~Home~~)

  > Note: WSL2 is advised for ease of setup, integrations with Docker, and more flexible resource utilizations benefits.

- Linux
  - Ubuntu 18.04 (bionic), 20.04 (focal)
  - Debian 9 (stretch), 10 (buster)

## Clone the repository

Cross platform

```shell
git clone https://github.com/microsoft/MLOS.git
```

> See <https://git-scm.com/book/en/v2/Getting-Started-Installing> for help installing `git`.

## Install build tools

### Linux build tools

 TODO

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

#### Manually

Download and install Visual Studio 2019 (free) Community Edition:

<https://visualstudio.microsoft.com/vs/community/>

Be sure to include support for .Net Core, C++, CMake

## Install Python Dependencies

### Linux Python Install

1. Install Python 3.x

    ```sh
    apt -y install python3 python3-pip
    ```

2. Install MLOS Python dependencies:

    ```sh
    # Also add some dependencies needed by some of the pip modules
    apt -y install build-essential libfreetype-dev unixodbc-dev
    ```

    ```sh
    pip3 install -r source/Mlos.Python/requirements.txt
    ```

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

## Install Docker

### Linux Docker Install

TODO

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
