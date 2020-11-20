# In this file we add our extensions to the existing build definitions for this example external project.

# First, start by making sure that MLOS is available for this project.
#
# Since it is not available in packaged form yet, we simply grab the sources for now.

# Instruct cmake how to find the Mlos source code.
include(FetchContent)
#set(FETCHCONTENT_QUIET OFF)
FetchContent_Declare(
    mlos
    # Normally we'd fetch directly from the upstream repo,
    #GIT_REPOSITORY  https://github.com/microsoft/MLOS.git
    # however for local testing, we just reference the current checkout.
    GIT_REPOSITORY  file://${CMAKE_CURRENT_LIST_DIR}/../..
    # FIXME: For now, we need to specify a branch name that supports the
    # external project integration logic that we're adding.
    # However, in the future we expect to be able to reference an upstream
    # release version, branch name, or commit hash.
    #GIT_TAG         v0.1.2
    GIT_TAG         external-cmake-project-integration
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

    # Make the MLOS project targets available for other cmake targets to reference as dependencies.
    add_subdirectory("${mlos_SOURCE_DIR}" "${mlos_BINARY_DIR}" EXCLUDE_FROM_ALL)

    # Instruct those other targets how to find the Mlos cmake module.
    set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${mlos_SOURCE_DIR}/external/cmake")
endif()

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
