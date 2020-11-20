# External CMake Modules

This directory contains `cmake` modules for external project integration.

## Overview

The general usage pattern is to

1. Use [`FetchContent`](https://cmake.org/cmake/help/v3.15/module/FetchContent.html) to obtain the MLOS source tree as a dependency
   for the external project's `cmake` build system and add this directory to their `CMAKE_MODULE_PATH` so that `include(MLOS)` can
   find the `MLOS.cmake` file in this directory.

    Note: This can happen at a common level for an entire external project's `cmake` build system.

    See Also: [`ExternalIntegrationExample/MlosBuildIntegrations.cmake`](../ExternalIntegrationExample/MlosBuildIntegrations.cmake#mlos-github-tree-view)

2. Use the `add_mlos_settings_registry()` function provided there to provide a `cmake` target wrapper for `dotnet build` of various
   `SmartComponent.SettingsRegistry.csproj` files the external project will add.

    See Also: [`ExternalIntegrationExample.SettingsRegistry/CMakeLists.txt`](../ExternalIntegrationExample/ExternalIntegrationExample.SettingsRegistry/CMakeLists.txt#mlos-github-tree-view)

4. Reference those using `add_dependencies()` in the C/C++ components.

    See Also: [`ExternalIntegrationExample/CMakeLists.txt`](../ExternalIntegrationExample/CMakeLists.txt#mlos-github-tree-view)
