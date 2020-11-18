cmake_minimum_required(VERSION 3.15)

# Here we assume some existing external build system setup, using cmake:

project(ExternalIntegrationExample)

add_executable(${PROJECT_NAME}
    ExternalIntegrationExample.cpp
)

# TODO: Now, we start adding MLOS integrations.
include(./MlosBuildIntegrations.cmake)

# TODO: Move this to a function:
target_link_libraries(${PROJECT_NAME} Mlos.Core)
