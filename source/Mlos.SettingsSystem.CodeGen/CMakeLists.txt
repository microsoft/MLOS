# We provide a CMakeWrapper for this project mostly so that C++ projects that
# need SettingsProvider code generation that pull this in as a dependency can
# build it with out (or at least fewer) race conditions.

project(Mlos.SettingsSystem.CodeGen LANGUAGES NONE)

get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
include("${MLOS_ROOT}/build/Mlos.Common.cmake")
include("${MLOS_ROOT}/build/Mlos.NetCore.cmake")

add_mlos_dotnet_project(NAME ${PROJECT_NAME}
    DIRECTORY ${PROJECT_SOURCE_DIR}
    WITH_BINPLACE)
