# This is a CMakeLists for the dotnet meta-project that handles nuget packaging.
# We use this to allow other CMakeLists (e.g. from external projects referencing
# MLOS via FetchContent) a dependency to reference so they can obtain local
# packages.

project(Mlos.NetCore.Components.Packages LANGUAGES NONE)

get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
include("${MLOS_ROOT}/build/Mlos.Common.cmake")

# Note: for this particular project, we don't use the build/Mlos.NetCore.cmake
# and instead provide our own custom targets.

file(RELATIVE_PATH RelativeProjectSourcePath "${MLOS_ROOT}" "${CMAKE_CURRENT_LIST_DIR}")
set(ProjectBuildStampFile "${CMAKE_BINARY_DIR}/${RelativeProjectSourcePath}/build.stamp")
# TODO: Gather the dependencies using the helper script
add_custom_command(OUTPUT "${ProjectBuildStampFile}"
    COMMAND dotnet build -c ${CMAKE_BUILD_TYPE}
    COMMAND ${CMAKE_COMMAND} -E touch "${ProjectBuildStampFile}"
    WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
    COMMENT "Creating MLOS Nuget Packages")

add_custom_target(${PROJECT_NAME} ALL
    DEPENDS "${ProjectBuildStampFile}")
