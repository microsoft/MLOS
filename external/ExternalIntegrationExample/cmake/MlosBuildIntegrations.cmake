# In this file we add our extensions to the existing build definitions for this example external project.

# First, start by making sure that MLOS is available for this project.
#
# Since it is not available in packaged form yet, we simply grab the sources for now.

# Normally we'd fetch directly from the upstream repo,
#set(MLOS_GIT_URL "https://github.com/microsoft/MLOS.git")
# and would specify a particular stable version.
#set(MLOS_GIT_TAG v0.1.2)

# However for local (and CI pipeline) testing, we just reference the current checkout.
set(MLOS_GIT_URL "file://${CMAKE_CURRENT_LIST_DIR}/../../..")
set(MLOS_GIT_TAG "HEAD")

# Instruct cmake how to find the Mlos source code.
include(FetchContent)
#set(FETCHCONTENT_QUIET OFF)
FetchContent_Declare(
    # The name of the dependency (used to form variable names later on).  By convention listed in lowercase.
    mlos
    # Where to fetch it from.
    GIT_REPOSITORY  "${MLOS_GIT_URL}"
    # and which version.
    GIT_TAG         "${MLOS_GIT_TAG}"
    # Since we use GitVersionTask for versioning nugets we need a non-shallow fetch.
    GIT_SHALLOW     OFF
)
FetchContent_GetProperties(mlos)
# Allow building the MLOS projects with a different build type than the rest parent project,
# but by default use a Release build.
set(MLOS_CMAKE_BUILD_TYPE Release)
if(NOT mlos_POPULATED)
    # Actually fetch the mlos code (at generation time).
    FetchContent_Populate(mlos)

    # In case we checked out an unnamed version (e.g. in Github Actions CI),
    # give it a local branch name for GitVersionTask to compute from.
    if("${MLOS_GIT_TAG}" STREQUAL "HEAD")
        execute_process(
            COMMAND git checkout --quiet --detach
            WORKING_DIRECTORY "${mlos_SOURCE_DIR}")
        execute_process(
            COMMAND git branch -f local-cmake-checkout
            WORKING_DIRECTORY "${mlos_SOURCE_DIR}")
        execute_process(
            COMMAND git branch --no-track -f local-cmake-checkout origin/HEAD
            WORKING_DIRECTORY "${mlos_SOURCE_DIR}")
        execute_process(
            COMMAND git checkout local-cmake-checkout
            WORKING_DIRECTORY "${mlos_SOURCE_DIR}")

        # Also make the upstream/main available for comparison.
        execute_process(
            COMMAND git remote add upstream https://github.com/microsoft/MLOS
            WORKING_DIRECTORY "${mlos_SOURCE_DIR}")
        execute_process(
            COMMAND git fetch -q upstream
            WORKING_DIRECTORY "${mlos_SOURCE_DIR}")
        execute_process(
            COMMAND git branch -f main upstream/main
            WORKING_DIRECTORY "${mlos_SOURCE_DIR}")
    endif()

    # Make the MLOS project targets available for other cmake targets to reference as dependencies.
    add_subdirectory("${mlos_SOURCE_DIR}" "${mlos_BINARY_DIR}" EXCLUDE_FROM_ALL)

    # Instruct those other targets how to find the Mlos cmake module.
    set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${mlos_SOURCE_DIR}/external/cmake")
endif()

# Include the MLOS cmake module (from the path above).
include(MLOS)

# Now, we instruct all the external project component targets to look in the
# following path for their Mlos codegen outputs.
#
# Note: This should match the path set in the C# build props.
# See Also:
# - ExternalIntegrationExample.SettingsRegistry/ExternalIntegrationExample.SettingsRegistry.csproj
# - ExternalIntegrationExample.SettingsRegistry/build/Common.props
#
# It can also be set in the add_mlos_settings_registry() definition.
# See Also:
# - ExternalIntegrationExample.SettingsRegistry/CMakeLists.txt
#
set(MlosCodeGenBaseOutDir "${CMAKE_SOURCE_DIR}/Mlos.CodeGen.out")
include_directories(${MlosCodeGenBaseOutDir})

# The path to place the Mlos SettingRegistry dlls.
#
# See Also:
# - ExternalIntegrationExample.SettingsRegistry/CMakeLists.txt
#
set(MlosSettingsRegistryDllDir "${CMAKE_BINARY_DIR}/SettingsRegistryDlls")
