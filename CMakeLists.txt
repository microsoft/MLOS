# Note: We intentionally omit VERSION from the remainder of the CMakeLists.txt
# files in order to encourage running cmake only from the top-level of the repo.
cmake_minimum_required(VERSION 3.15)

get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}" ABSOLUTE)
include("${MLOS_ROOT}/build/Mlos.Common.cmake")

# Top level project:
project(MLOS)

# Force the test target that gets generated to run ctest in verbose mode.
set(CMAKE_CTEST_ARGUMENTS "--verbose;${CMAKE_CTEST_ARGUMENTS}")
set(CMAKE_CTEST_ARGUMENTS "--timeout ${DEFAULT_CTEST_TIMEOUT};${CMAKE_CTEST_ARGUMENTS}")

enable_testing()
# Add a custom "check" target that will run all of the tests registered in the
# various other CMakeLists.txt via "ctest", but making sure that the targets
# are build first.
add_custom_target(check
    COMMAND ${CMAKE_CTEST_COMMAND}
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR})

# Start listing our other sub projects.
# See Also: dirs.proj

add_subdirectory(source)
add_subdirectory(test)

# Add some additional helper targets.
include("${MLOS_ROOT}/build/Mlos.Common.targets.cmake")
