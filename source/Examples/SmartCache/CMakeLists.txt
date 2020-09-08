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

# FIXME:
# - This doesn't finish, it just hangs.
# - When you pkill dotnet to end it, the test reports success.
#add_test(NAME MlosTestRun_MlosAgentServer_SmartCache
#    COMMAND ${DOTNET} $<TARGET_PROPERTY:Mlos.Agent.Server,DOTNET_OUTPUT_DLL> $<TARGET_FILE:SmartCache>)
#add_dependencies(check ${PROJECT_NAME} Mlos.Agent.Server)
