# Mlos.Common.cmake
#
# A set of common rules to include in CMakeLists.txt

# TODO: Verify what our actual version depenedency is.
cmake_minimum_required(VERSION 3.15)

if(WIN32)
    message(FATAL_ERROR
        "CMake is not currently supported on Windows for MLOS.  Please use 'msbuild' instead.")
endif()

# Expect projects to include this set of rules using something like the following:
#   get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
#   include("${MLOS_ROOT}/build/Mlos.Common.cmake")
if(NOT DEFINED MLOS_ROOT)
    message(FATAL_ERROR
        "CMakeLists.txt error: MLOS_ROOT is not defined.")
endif()

# Set a default build type if none was specified.
# (used in the codegen output determination)
set(default_build_type "Release")
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  message(STATUS "Setting build type to '${default_build_type}' since none was specified.")
  set(CMAKE_BUILD_TYPE "${default_build_type}" CACHE
      STRING "Choose the type of build." FORCE)
  # Set the possible values of build type for cmake-gui
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS
    "Debug" "Release") # "MinSizeRel" "RelWithDebInfo")
endif()

if(NOT (${CMAKE_SOURCE_DIR} STREQUAL ${MLOS_ROOT}))
    message(FATAL_ERROR
        "Please run 'cmake' from '${MLOS_ROOT}'.")
endif()

# Prevent in-source builds as well as the default build/ directory
# - it conflicts with our MSBuild config location.
if((${CMAKE_SOURCE_DIR} STREQUAL ${CMAKE_BINARY_DIR}) OR (${CMAKE_BINARY_DIR} STREQUAL "build"))
    message(FATAL_ERROR
        "In-source builds not allowed. Please run\n"
        "# make\n"
        "or\n"
        "# rm -f CMakeCache.txt && cmake -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} -S ${MLOS_ROOT} -B ${MLOS_ROOT}/out/cmake/${CMAKE_BUILD_TYPE}\n"
        "to place CMake build outputs in the out/cmake/${CMAKE_BUILD_TYPE}/ directory.\n")
endif()
set(CMAKE_BINARY_DIR "${MLOS_ROOT}/out/cmake/${CMAKE_BUILD_TYPE}")

# Set a binplace dir to match the msbuild rules.
# We will use this in our install() definition rules.
# See Also: Mlos.Binplace.props
set(BINPLACE_DIR "${MLOS_ROOT}/target/bin/${CMAKE_BUILD_TYPE}/${CMAKE_SYSTEM_PROCESSOR}")

# We currently only build for AnyCPU with dotnet.
set(DOTNET_TARGET_PLATFORM "AnyCPU")
# Set the corresponding binplace root dir.
# See Also: Mlos.NetCore.cmake
set(DOTNET_BINPLACE_ROOT "${MLOS_ROOT}/target/bin/${CMAKE_BUILD_TYPE}/${DOTNET_TARGET_PLATFORM}")
# Currently settings registry project output dlls are expected to be placed in the same root.
# To be searched by the Mlos.Agent.Server via --settings-registry-path argument.
# See Also: Mlos.Cpp.UnitTest.cmake
set(MLOS_SETTINGS_REGISTRY_BINPLACE_ROOT "${DOTNET_BINPLACE_ROOT}")

# The base output for SettingsSystem codegen output.
# See Also: Mlos.SettingsSystem.CodeGen.targets
set(MLOS_CODEGEN_OUTPUT_ROOT "${MLOS_ROOT}/out/Mlos.CodeGen.out/${CMAKE_BUILD_TYPE}")

# By default only let any ctest processes last for limited number of seconds.
# To override on a per test basis, use add_test_properties()
set(DEFAULT_CTEST_TIMEOUT 120)

# See Also: Mlos.NetCore.cmake, Mlos.Common.targets.cmake
find_program(DOTNET NAMES dotnet)
if(NOT DOTNET)
    find_program(DOTNET NAMES dotnet
        HINTS "${MLOS_ROOT}/tools/bin")
endif()
if(NOT DOTNET)
    message(WARNING
        "Unable to find dotnet.  Perhaps you need to run ${MLOS_ROOT}/scripts/install.dotnet.sh")
endif()

find_program(PYTHON3
    NAMES python3.7 python3)
if(NOT PYTHON3)
    message(WARNING
        "Unable to find and appropriate version of python.  Perhaps you need to run ${MLOS_ROOT}/scripts/install.python.sh")
endif()
