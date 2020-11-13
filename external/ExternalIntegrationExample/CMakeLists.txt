cmake_minimum_required(VERSION 3.15)

project(ExternalIntegrationExample)

add_executable(${PROJECT_NAME}
    ExternalIntegrationExample.cpp
)

include_directories(./Mlos.Codegen.out/Release/)

# TODO: Add Mlos integrations.
