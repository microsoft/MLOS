# A CMakeList `dotnet build` wrapper so that we can run unit tests via cmake as well.

project(Mlos.Agent.Server LANGUAGES NONE)

get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
include("${MLOS_ROOT}/build/Mlos.Common.cmake")
include("${MLOS_ROOT}/build/Mlos.NetCore.cmake")

add_mlos_dotnet_project(NAME ${PROJECT_NAME}
    DIRECTORY ${PROJECT_SOURCE_DIR}
    WITH_BINPLACE)

add_dependencies(${PROJECT_NAME} Mlos.NetCore)
