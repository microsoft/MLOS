# External CMake Modules

This directory contains `cmake` modules for external project integration.

## Overview

The general usage pattern is to

1. Use [`FetchContent`](https://cmake.org/cmake/help/v3.15/module/FetchContent.html) to obtain the MLOS source tree as a dependency
   for the external project's `cmake` build system and add this directory to their `CMAKE_MODULE_PATH` so that `include(MLOS)` can
   find the [`MLOS.cmake`](./MLOS.cmake#mlos-github-tree-view) file in this directory.

    Note: This can happen at a common level for an entire external project's `cmake` build system.

    ```cmake
    # Make MLOS source code available in the external project.
    include(FetchContent)
    FetchContent_Declare(
        mlos
        GIT_REPOSITORY  "https://github.com/microsoft/MLOS"
        GIT_TAG         "main"
        GIT_SHALLOW     OFF
    )
    FetchContent_GetProperties(mlos)
    set(MLOS_CMAKE_BUILD_TYPE Release)
    if(NOT mlos_POPULATED)
        FetchContent_Populate(mlos)
        add_subdirectory("${mlos_SOURCE_DIR}" "${mlos_BINARY_DIR}" EXCLUDE_FROM_ALL)

        # Instruct other targets how to find the Mlos cmake module.
        set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${mlos_SOURCE_DIR}/external/cmake")
    endif()

    # Include the MLOS cmake module (from the path above).
    # (this includes the add_mlos_settings_registry() function used next)
    include(MLOS)

    # Define some common settings used in C# SettingsRegistry and C++ builds.
    set(MlosCodeGenBaseOutDir "${CMAKE_SOURCE_DIR}/Mlos.CodeGen.out")
    include_directories(${MlosCodeGenBaseOutDir})

    set(MlosSettingsRegistryDllDir "${CMAKE_BINARY_DIR}/SettingsRegistryDlls")
    ```

    See Also: [`ExternalIntegrationExample/MlosBuildIntegrations.cmake`](../ExternalIntegrationExample/cmake/MlosBuildIntegrations.cmake#mlos-github-tree-view)

2. Use the `add_mlos_settings_registry()` function provided there to provide a `cmake` target wrapper for `dotnet build` of various
   *`SmartComponent`*`.SettingsRegistry.csproj` files the external project will add.

    ```cmake
    # MySmartComponent.SettingsRegistry/CMakeLists.txt:
    # A wrapper for the MySmartComponent.csproj file in the same directory.

    include(MLOS)

    add_mlos_settings_registry(
        NAME MySmartComponent.SettingsRegistry
        DIRECTORY "${CMAKE_CURRENT_LIST_DIR}"
        CODEGEN_OUTPUT_DIR "${MlosCodeGenBaseOutDir}/MySmartComponent"
        BINPLACE_DIR "${MlosSettingsRegistryDllDir}"
        USE_LOCAL_MLOS_NUGETS
    )
    ```

    See Also: [`ExternalIntegrationExample.SettingsRegistry/CMakeLists.txt`](../ExternalIntegrationExample/ExternalIntegrationExample.SettingsRegistry/CMakeLists.txt#mlos-github-tree-view)

3. Reference those using `add_dependencies()` in the C/C++ components.

    ```cmake
    # MySmartComponent/CMakeLists.txt:

    # ... existing cmake definitions

    target_link_libraries(${PROJECT_NAME} Mlos.Core)

    # SettingsRegistry projects produce C++ codegen artifacts, that this project
    # consumes, so we mark that project as a dependency.
    #
    add_subdirectory(MySmartComponent.SettingsRegistry)
    add_dependencies(${PROJECT_NAME} MySmartComponent.SettingsRegistry)
    ```

    See Also: [`ExternalIntegrationExample/CMakeLists.txt`](../ExternalIntegrationExample/CMakeLists.txt#mlos-github-tree-view)
