project(Mlos.Core)

get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
include("${MLOS_ROOT}/build/Mlos.Common.cmake")
include("${MLOS_ROOT}/build/Mlos.Cpp.cmake")

add_library(${PROJECT_NAME} STATIC
    ArenaAllocator.cpp
    GlobalMemoryRegion.cpp
    InternalMlosContext.cpp
    InterProcessMlosContext.cpp
    Mlos.Core.cpp
    MlosContext.cpp
    NamedEvent.Linux.cpp
    SharedChannel.cpp
    SharedConfigDictionary.cpp
    SharedConfigManager.cpp
    SharedConfigMemoryRegion.cpp
    SharedMemoryMapView.Linux.cpp)

find_package(Threads REQUIRED)
target_link_libraries(${PROJECT_NAME} pthread)

target_link_libraries(${PROJECT_NAME} rt)

# Add dependencies on SettingsRegistry project(s).

# Mlos.NetCore currently also does the Mlos.Core SettingsProvider code generation.
add_dependencies(${PROJECT_NAME} Mlos.NetCore)
