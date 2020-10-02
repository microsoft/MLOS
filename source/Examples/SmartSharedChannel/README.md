# [SmartSharedChannel Example](./#mlos-github-tree-view)

This [SmartSharedChannel](./#mlos-github-tree-view) example demonstrates a using a microbenchmark of the MLOS shared memory channel to tune the MLOS shared memory channel itself.

Here are some brief instructions on how to try it out:

## Building

> Note: these command examples expect to be run from the top-level of the repository.
>
> To move there, execute the following:
>
> `cd $(git rev-parse --show-toplevel)`

1. [Build or pull the docker image](../../../documentation/01-Prerequisites.md#build-the-docker-image)
2. [Create a docker image instance](../../../documentation/02-Build.md#create-a-new-container-instance)
3. [Build the code](../../../documentation/02-Build.md#cli-make)

   (inside the docker container)

    ```sh
    make -C source/Mlos.Agent.Server
    make -C source/Examples/SmartSharedChannel
    ```

## Executing

```sh
export MLOS_SETTINGS_REGISTRY_PATH=out/dotnet/source/Mlos.UnitTest/Mlos.UnitTest.SettingsRegistry/obj/AnyCPU:out/dotnet/source/Examples/SmartSharedChannel/SmartSharedChannel.SettingsRegistry/obj/AnyCPU

./tools/bin/dotnet out/dotnet/source/Mlos.Agent.Server/obj/AnyCPU/Mlos.Agent.Server.dll --executable out/cmake/Release/source/Examples/SmartSharedChannel/SmartSharedChannel
```
