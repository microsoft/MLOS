project(Mlos.TestRun)

# Simply depends on the custom "check" target definied in the top-level CMakeLists.txt
# in order to make sure that all tests are built and run.
# Provided as an analogue to the "msbuild Mlos.TestRun.proj" pattern.

add_custom_target(${PROJECT_NAME}
    DEPENDS check)
