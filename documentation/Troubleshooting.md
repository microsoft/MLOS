# Troubleshooting Tips

Here are some common tips for troubleshooting various issues.

## Contents

- [Troubleshooting Tips](#troubleshooting-tips)
  - [Contents](#contents)
  - [Editor Integrations](#editor-integrations)
    - [VSCode in WSL](#vscode-in-wsl)
      - ["Missing .Net SDK" message when executing `code .` in WSL](#missing-net-sdk-message-when-executing-code--in-wsl)

## Editor Integrations

### VSCode in WSL

#### "Missing .Net SDK" message when executing `code .` in WSL

The [Omnisharp](https://github.com/OmniSharp/omnisharp-vscode/wiki/Troubleshooting:-'The-.NET-Core-SDK-cannot-be-located.'-errors) plugin for VSCode may have trouble finding the `dotnet` setup locally for the MLOS repo in `tools/`, even if you source the `scripts/init.linux.sh` script to setup your `PATH` environment.

To workaround this issue, you can [install `dotnet` system wide for your WSL2 distro](https://docs.microsoft.com/en-us/dotnet/core/install/linux).

Here are the instructions for Ubuntu 20.04:\
<https://docs.microsoft.com/en-us/dotnet/core/install/linux-ubuntu#2004->
