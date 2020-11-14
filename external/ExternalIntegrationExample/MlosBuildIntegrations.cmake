# In this file we add our extensions to the existing build definitions for this example external project.

# First, start by making sure that MLOS is available for this project.
#
# Since it is not available in packaged form yet, we simply grab the sources for now.

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
    GIT_TAG         codegen-nuget-for-external-project-integration
    # TODO: Can we do this and still get reasonable nuget versions out?
    GIT_SHALLOW     ON
)
FetchContent_GetProperties(mlos)
# Allow building the MLOS projects with a different build type than the rest parent project.
set(MLOS_CMAKE_BUILD_TYPE Release)
if(NOT mlos_POPULATED)
    FetchContent_Populate(mlos)
    add_subdirectory("${mlos_SOURCE_DIR}" "${mlos_BINARY_DIR}" EXCLUDE_FROM_ALL)
endif()

# Add the Mlos project's codegen output directories to our
# TODO: make this use target_include_directories?
include_directories("${mlos_SOURCE_DIR}/out/Mlos.CodeGen.out/${MLOS_CMAKE_BUILD_TYPE}")

# We instruct it look in the following path for Mlos codegen outputs.
# Note: This should match the path set in the C# build props.
# See Also:
# - ExternalIntegrationExample.SettingsRegistry/ExternalIntegrationExample.SettingsRegistry.csproj
# - ExternalIntegrationExample.SettingsRegistry/build/Common.props
include_directories(./Mlos.Codegen.out)
