# Mlos.NetCore.cmake

# add_mlos_dotnet_project()
#
# CMake doesn't currently support generating build files for CSharp language on Linux.
# Instead, we add a custom function to build existing .csproj files with "dotnet build".
#
# Adapted from https://github.com/FFIG/ffig/blob/80332cc972f4dd952e8fc5bc642e574246495808/cmake/dotnet.cmake
#
# To invoke it include the following CMakeLists.txt wrapper in the .csproj directory:
#
#   project(Mlos.SettingsSystem.Attributes LANGUAGES NONE)
#   get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
#   include("${MLOS_ROOT}/build/Mlos.Common.cmake")
#   include("${MLOS_ROOT}/build/Mlos.NetCore.cmake")
#   add_mlos_dotnet_project(NAME ${PROJECT_NAME}
#       DIRECTORY ${PROJECT_SOURCE_DIR})
#
function(add_mlos_dotnet_project)
    set(options MLOS_SETTINGS_REGISTRY)
    set(oneValueArgs NAME DIRECTORY)
    cmake_parse_arguments(add_mlos_dotnet_project "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    if(NOT DEFINED MLOS_ROOT)
        message(FATAL_ERROR "Missing MLOS_ROOT.")
    endif()

    set(MLOS_SETTINGS_REGISTRY ${add_mlos_dotnet_project_MLOS_SETTINGS_REGISTRY})
    set(NAME ${add_mlos_dotnet_project_NAME})
    set(DIRECTORY ${add_mlos_dotnet_project_DIRECTORY})

    get_filename_component(DIRECTORY "${DIRECTORY}" ABSOLUTE)

    file(RELATIVE_PATH DIRECTORY_RELATIVE_TO_MLOS_ROOT "${MLOS_ROOT}" "${DIRECTORY}")

    set(DOTNET_OUTPUT_BASEDIR "${MLOS_ROOT}/out/dotnet")
    if("${CMAKE_BUILD_TYPE}" STREQUAL "Release")
        set(DOTNET_OBJ_DIR "obj")
    elseif("${CMAKE_BUILD_TYPE}" STREQUAL "Debug")
        set(DOTNET_OBJ_DIR "objd")
    else()
        message(SEND_ERROR
            "Unhandled CMAKE_BUILD_TYPE: '${CMAKE_BUILD_TYPE}'")
    endif()

    # We currently only build for AnyCPU with dotnet.
    set(DOTNET_TARGET_PLATFORM "AnyCPU")

    # Note: We don't actually specify a -o output directory for the "dotnet build" command.
    # Instead we rely on our existing .csproj file authoring paths.
    # We compute the same ones simply so we can refer to the outputs.
    set(OUTPUT_PATH ${DOTNET_OUTPUT_BASEDIR}/${DIRECTORY_RELATIVE_TO_MLOS_ROOT}/${DOTNET_OBJ_DIR}/${DOTNET_TARGET_PLATFORM})

    # By convention .csproj files, their output, and their library name
    # all share the same basename.
    set(OUTPUT_DLL ${OUTPUT_PATH}/${NAME}.dll)
    set(OUTPUT_EXE ${BINPLACE_DIR}/${NAME}.dll)
    set(CSPROJ ${NAME}.csproj)

    # Parse the csproj files in the directory to determine the *.cs file dependencies.

    execute_process(
        COMMAND "${MLOS_ROOT}/build/CMakeHelpers/ParseCsProjForCsFiles.sh"
        WORKING_DIRECTORY "${DIRECTORY}"
        OUTPUT_VARIABLE CS_SOURCES
        #COMMAND_ECHO STDERR
    )

    set(DEPENDENCIES
        DOTNET_TOOL
        ${CS_SOURCES}
        ${DIRECTORY}/${CSPROJ})

    add_custom_command(OUTPUT ${OUTPUT_DLL}
        COMMAND ${DOTNET} build -m --configuration ${CMAKE_BUILD_TYPE} ${CSPROJ}
        DEPENDS ${DEPENDENCIES}
        WORKING_DIRECTORY ${DIRECTORY}
        COMMENT "Building dotnet assembly ${NAME}.dll")

    add_custom_target(${NAME} ALL
        DEPENDS ${OUTPUT_DLL})

    # Save the path to the output dll so we can reference it some tests later on.
    set_target_properties(${NAME}
        PROPERTIES DOTNET_OUTPUT_DIR ${OUTPUT_PATH})
    set_target_properties(${NAME}
        PROPERTIES DOTNET_OUTPUT_DLL ${OUTPUT_DLL})
    # If the .csproj specifies a binplace rule, this is the path it should be placed in.
    set_target_properties(${NAME}
        PROPERTIES DOTNET_OUTPUT_EXE ${OUTPUT_EXE})

    if(${MLOS_SETTINGS_REGISTRY})
        add_dependencies(${NAME} Mlos.SettingsSystem.Attributes)
        add_dependencies(${NAME} Mlos.SettingsSystem.CodeGen)
    endif()

    # Parse the csproj files in the directory to determine the *.csproj project
    # dependencies and turn them into target dependencies.

    execute_process(
        COMMAND "${MLOS_ROOT}/build/CMakeHelpers/ParseCsProjForCsProjs.sh"
        WORKING_DIRECTORY "${DIRECTORY}"
        OUTPUT_VARIABLE CS_PROJS
        #COMMAND_ECHO STDERR
    )

    if(CS_PROJS)
        add_dependencies(${NAME} ${CS_PROJS})
    endif()
endfunction()
