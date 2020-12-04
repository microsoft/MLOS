# This is a CMakeLists for the dotnet meta-project that handles nuget packaging.
# We use this to allow other CMakeLists (e.g. from external projects referencing
# MLOS via FetchContent) a dependency to reference so they can obtain local
# packages.

project(Mlos.NetCore.Components.Packages LANGUAGES NONE)

get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
include("${MLOS_ROOT}/build/Mlos.Common.cmake")

# Note: for this particular project, we don't use the build/Mlos.NetCore.cmake
# and instead provide our own custom targets.

# Parse the csproj files in the directory to determine the *.csproj project
# dependencies and turn them into target dependencies.
execute_process(
    COMMAND "${MLOS_ROOT}/build/CMakeHelpers/ParseCsProjForCsProjs.sh"
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    OUTPUT_VARIABLE CS_PROJS
    #COMMAND_ECHO STDERR
)

set(PROJ "${PROJECT_SOURCE_DIR}/${PROJECT_NAME}.proj")
set(PKG_OUTPUT_DIR "${MLOS_ROOT}/target/pkg/${CMAKE_BUILD_TYPE}")

set(DEPENDENCIES
    ${PROJ}
    ${CS_PROJS}
)

file(RELATIVE_PATH RelativeProjectSourcePath "${MLOS_ROOT}" "${PROJECT_SOURCE_DIR}")
set(OUTDIR "${MLOS_ROOT}/out/dotnet/${RelativeProjectSourcePath}")
set(ProjectBuildStampFile "${OUTDIR}/build.stamp")

add_custom_command(OUTPUT "${ProjectBuildStampFile}" "${PKG_OUTPUT_DIR}"
    COMMAND dotnet build -c ${CMAKE_BUILD_TYPE} "${PROJ}"
    COMMAND ${CMAKE_COMMAND} -E make_directory "${OUTDIR}"
    COMMAND ${CMAKE_COMMAND} -E touch "${ProjectBuildStampFile}"
    DEPENDS "${DEPENDENCIES}"
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    COMMENT "Creating MLOS Nuget Packages")

add_custom_target(${PROJECT_NAME} ALL
    DEPENDS "${ProjectBuildStampFile}" "${PKG_OUTPUT_DIR}")
