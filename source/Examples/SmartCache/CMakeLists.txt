project(SmartCache)

get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../.." ABSOLUTE)
include("${MLOS_ROOT}/build/Mlos.Common.cmake")
include("${MLOS_ROOT}/build/Mlos.Cpp.cmake")

add_executable(${PROJECT_NAME}
    Main.cpp
    Workloads.cpp)

target_link_libraries(${PROJECT_NAME} Mlos.Core)

# Add dependencies on SettingsRegistry project(s).

# Mlos.NetCore currently also does the Mlos.Core SettingsProvider code generation.
add_dependencies(${PROJECT_NAME} Mlos.NetCore)

add_subdirectory(SmartCache.SettingsRegistry)
add_dependencies(${PROJECT_NAME} SmartCache.SettingsRegistry)
