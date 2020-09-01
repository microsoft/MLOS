# This project also does the SettingsProvider code generation for Mlos.Core.
# TODO? Split that out to it's own Mlos.Core.SettingsRegistry project?

project(Mlos.NetCore LANGUAGES NONE)

get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
include("${MLOS_ROOT}/build/Mlos.Common.cmake")
include("${MLOS_ROOT}/build/Mlos.NetCore.cmake")

add_mlos_dotnet_project(NAME ${PROJECT_NAME}
    DIRECTORY ${PROJECT_SOURCE_DIR}
    MLOS_SETTINGS_REGISTRY)
