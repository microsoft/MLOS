cmake_minimum_required(VERSION 3.15)

get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)

if(NOT MLOS_CMAKE_BUILD_TYPE)
    set(MLOS_CMAKE_BUILD_TYPE "${CMAKE_BUILD_TYPE}")
endif()
if(NOT ((${MLOS_CMAKE_BUILD_TYPE} STREQUAL "Release") OR (${MLOS_CMAKE_BUILD_TYPE} STREQUAL "Debug")))
    message(FATAL_ERROR "Unsupported MLOS_CMAKE_BUILD_TYPE: ${MLOS_CMAKE_BUILD_TYPE}.")
endif()

# TODO: Convert these to target_include_directories() using some macros?
# Make sure to include the Mlos project's codegen output directories to the include search path.
include_directories("${MLOS_ROOT}/out/Mlos.CodeGen.out/${MLOS_CMAKE_BUILD_TYPE}")

# add_mlos_settings_registry()
#
# A wrapper function build an MLOS C# SettingsRegistry .csproj using "dotnet build".
#
# See ExternalIntegrationExample.SettingsRegistry/CMakeLists.txt for an example.
#
function(add_mlos_settings_registry)
    set(options USE_LOCAL_MLOS_NUGETS)
    set(oneValueArgs NAME DIRECTORY CODEGEN_OUTPUT_DIR BINPLACE_DIR)
    cmake_parse_arguments(add_mlos_settings_registry "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    if(NOT DEFINED MLOS_ROOT)
        message(FATAL_ERROR "Missing MLOS_ROOT.")
    endif()

    set(NAME ${add_mlos_settings_registry_NAME})
    set(DIRECTORY ${add_mlos_settings_registry_DIRECTORY})
    set(CODEGEN_OUTPUT_DIR ${add_mlos_settings_registry_CODEGEN_OUTPUT_DIR})
    set(BINPLACE_DIR ${add_mlos_settings_registry_BINPLACE_DIR})
    set(USE_LOCAL_MLOS_NUGETS ${add_mlos_settings_registry_USE_LOCAL_MLOS_NUGETS})

    # TODO: Add dependencies for the target.
    # - the *.cs files
    # - the Mlos nuget target

    # In the "dotnet build" command update some properites
    # - BinplaceDir
    # - Codegen Output Dir

    if(CODEGEN_OUTPUT_DIR)
        get_filename_component(CODEGEN_OUTPUT_DIR "${CODEGEN_OUTPUT_DIR}" ABSOLUTE)
        set(CODEGEN_OUTPUT_DIR_ARGS "'/p:MlosSettingsSystemCodeGenOutputDirectory=${CODEGEN_OUTPUT_DIR}'")
        message(SEND_ERROR "CODEGEN_OUTPUT_ARGS ${CODEGEN_OUTPUT_ARGS}")
    else()
        set(CODEGEN_OUTPUT_DIR_ARGS "")
    endif()

    if(BINPLACE_DIR)
        get_filename_component(BINPLACE_DIR "${BINPLACE_DIR}" ABSOLUTE)
        set(BINPLACE_DIR_ARGS "'/p:MlosSettingsRegistryAssemblyOutputDirectory=${BINPLACE_DIR}'")
        message(SEND_ERROR "BINPLACE_DIR_ARGS ${BINPLACE_DIR_ARGS}")
    else()
        set(BINPLACE_DIR_ARGS "")
    endif()

    if(${USE_LOCAL_MLOS_NUGETS})
        set(MlosLocalPkgOutput "${MLOS_ROOT}/target/pkg/${MLOS_CMAKE_BUILD_TYPE}")
        set(NUGET_RESTORE_ARGS "'/p:RestoreSources=${MlosLocalPkgOutput}\;https://api.nuget.org/v3/index.json'")
        set(MlosLocalPkgTargetDeps "Mlos.NetCore.Components.Packages")
    else()
        set(NUGET_RESTORE_ARGS "")
    endif()

    # Parse the csproj files in the directory to determine the *.cs file dependencies.
    execute_process(
        COMMAND "${MLOS_ROOT}/build/CMakeHelpers/ParseCsProjForCsFiles.sh"
        WORKING_DIRECTORY "${DIRECTORY}"
        OUTPUT_VARIABLE CS_SOURCES
        #COMMAND_ECHO STDERR
    )

    # Rather than track the outputs from the "dotnet build" (which could change according to how the build was authored),
    # we'll simply use a build.stamp file in the cmake output dir to mark when the "dotnet build" last succeeded.
    get_filename_component(DIRECTORY "${DIRECTORY}" ABSOLUTE)
    file(RELATIVE_PATH DIRECTORY_RELATIVE_TO_SOURCE_ROOT "${CMAKE_SOURCE_DIR}" "${DIRECTORY}")
    set(OUTDIR "${CMAKE_BINARY_DIR}/${DIRECTORY_RELATIVE_TO_SOURCE_ROOT}")
    set(BUILD_STAMP "${OUTDIR}/build.stamp")

    set(CSPROJ ${NAME}.csproj)

    set(DEPENDENCIES
        ${DIRECTORY}/${CSPROJ}
        ${CS_SOURCES}
        ${MlosLocalPkgOutput} ${MlosLocalPkgTargetDeps})

    add_custom_command(OUTPUT "${BUILD_STAMP}" "${CODEGEN_OUTPUT_DIR}"
        # we compose the dependency graph already above, so we can skip
        # building project references here in order to avoid some parallel
        # dotnet processes accessing the same files.
        COMMAND ${DOTNET} build -m --configuration ${CMAKE_BUILD_TYPE} ${NUGET_RESTORE_ARGS} ${CODEGEN_OUTPUT_DIR_ARGS} ${BINPLACE_DIR_ARGS} "${CSPROJ}"
        # Also, "dotnet build" doesn't update timestamps in a make compatible
        # way, so we also mark the projects as having been built using touch.
        COMMAND ${CMAKE_COMMAND} -E make_directory "${OUTDIR}"
        COMMAND ${CMAKE_COMMAND} -E touch "${BUILD_STAMP}"
        DEPENDS "${DEPENDENCIES}"
        WORKING_DIRECTORY "${DIRECTORY}"
        COMMENT "Building dotnet assembly and MLOS CodeGen for ${NAME}.")

    add_custom_target(${NAME} ALL
        DEPENDS "${BUILD_STAMP}" "${CODEGEN_OUTPUT_DIR}")
endfunction()
