cmake_minimum_required(VERSION 3.15)

# Here we assume some existing external build system setup, using cmake:

project(ExternalIntegrationExample)

# Set some general compile options.
include(./cmake/Common.cmake)

# This is a simple existing project definition.
#
add_executable(${PROJECT_NAME}
    ExternalIntegrationExample.cpp
)

# Now, we start adding MLOS integrations.

# First, include some cross component/target cmake rules for
# fetching the MLOS source code and registering its cmake targets.
#
include(./cmake/MlosBuildIntegrations.cmake)

target_link_libraries(${PROJECT_NAME} Mlos.Core)

# SettingsRegistry projects produce C++ codegen artifacts, that this project
# consumes, so we mark that project as a dependency.
#
add_subdirectory(ExternalIntegrationExample.SettingsRegistry)
add_dependencies(${PROJECT_NAME} ExternalIntegrationExample.SettingsRegistry)
