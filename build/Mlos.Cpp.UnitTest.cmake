# Mlos.Cpp.UnitTest.cmake
#
# A set of cmake rules for C++ unit tests.

# Fetch and build Google Test library dependency.

include(FetchContent)
#set(FETCHCONTENT_QUIET OFF)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY  https://github.com/google/googletest.git
    GIT_TAG         release-1.10.0
    GIT_SHALLOW     ON
)

FetchContent_GetProperties(googletest)
if(NOT googletest_POPULATED)
    FetchContent_Populate(googletest)
    add_subdirectory(${googletest_SOURCE_DIR} ${googletest_BINARY_DIR} EXCLUDE_FROM_ALL)
endif()


# Add some test fixtures to use for setup/tear down of other Mlos unit tests.

# Note: Fixtures only run once per ctest invokation.
# That's fine for the pre-check, but the cleanup step, so we moved that into
# the test command itself for now.

# These "tests" are really just to help define fixtures to be depended on by
# other tests for setup/tear down checks.
add_test(NAME CheckForMlosSharedMemories
    COMMAND ${MLOS_ROOT}/build/CMakeHelpers/CheckForMlosSharedMemories.sh)
#add_test(NAME RemoveMlosSharedMemories
#    COMMAND ${MLOS_ROOT}/build/CMakeHelpers/RemoveMlosSharedMemories.sh)
# These properties add the pre/post actions for the "MlosSharedMemoriesChecks" fixture.
set_tests_properties(CheckForMlosSharedMemories PROPERTIES
    FIXTURES_SETUP MlosSharedMemoriesChecks)
#set_tests_properties(RemoveMlosSharedMemories PROPERTIES
#    FIXTURES_CLEANUP MlosSharedMemoriesChecks)
# Now other test can add "MlosSharedMemoriesChecks" to their
# "FIXTURES_REQUIRED" property to invoke these scripts before/after themselves.
add_test(NAME LocalPipInstallMlos
    COMMAND ${PYTHON3} -m pip install ${MLOS_ROOT}/source/Mlos.Python)
add_test(NAME StartMlosOptimizerService
    COMMAND ${MLOS_ROOT}/build/CMakeHelpers/BackgroundProcessHelper.sh
        start /tmp/mlos_optimizer_microservice.pid /tmp/mlos_optimizer_microservice.log
        ${PYTHON3} ${MLOS_ROOT}/source/Mlos.Python/mlos/start_optimizer_microservice.py launch --port 54321)
add_test(NAME StopMlosOptimizerService
    COMMAND ${MLOS_ROOT}/build/CMakeHelpers/BackgroundProcessHelper.sh
        stop /tmp/mlos_optimizer_microservice.pid /tmp/mlos_optimizer_microservice.log)
set_tests_properties(StartMlosOptimizerService PROPERTIES
    DEPENDS LocalPipInstallMlos
    FIXTURES_SETUP MlosOptimizerService)
set_tests_properties(StopMlosOptimizerService PROPERTIES
    FIXTURES_CLEANUP MlosOptimizerService)

# Mark all setup/tear down activities involving the shared memory regions as
# mutually exclusive (no parallel runs).
set_tests_properties(
    CheckForMlosSharedMemories
    #RemoveMlosSharedMemories
    PROPERTIES RESOURCE_LOCK MlosSharedMemories)

# add_mlos_agent_server_exe_test_run()
#
# Provide a function for handling some of the boilerplate to setup a test run
# of an executable using the Mlos.Agent.Server
#
#   add_mlos_agent_server_exe_test_run(
#       NAME MlosTestRun_Mlos.Agent.Server_${PROJECT_NAME}
#       EXECUTABLE_TARGET ${PROJECT_NAME}
#       TIMEOUT 240
#       SETTINGS_REGISTRY_PATH "${MLOS_SETTINGS_REGISTRY_BINPLACE_ROOT}")
#
function(add_mlos_agent_server_exe_test_run)
    set(options WITH_OPTIMIZER)
    set(oneValueArgs NAME EXECUTABLE_TARGET TIMEOUT SETTINGS_REGISTRY_PATH)
    cmake_parse_arguments(add_mlos_agent_server_exe_test_run "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    set(WITH_OPTIMIZER ${add_mlos_agent_server_exe_test_run_WITH_OPTIMIZER})
    set(TEST_NAME ${add_mlos_agent_server_exe_test_run_NAME})
    set(TEST_EXECUTABLE_TARGET ${add_mlos_agent_server_exe_test_run_EXECUTABLE_TARGET})

    if(NOT DEFINED add_mlos_agent_server_exe_test_run_TIMEOUT)
        set(TEST_TIMEOUT ${DEFAULT_CTEST_TIMEOUT})
    else()
        set(TEST_TIMEOUT ${add_mlos_agent_server_exe_test_run_TIMEOUT})
    endif()

    if(NOT DEFINED add_mlos_agent_server_exe_test_run_SETTINGS_REGISTRY_PATH)
        set(SETTINGS_REGISTRY_PATH ${MLOS_SETTINGS_REGISTRY_BINPLACE_ROOT})
    else()
        set(SETTINGS_REGISTRY_PATH ${add_mlos_agent_server_exe_test_run_SETTINGS_REGISTRY_PATH})
    endif()

    if(${WITH_OPTIMIZER})
        set(OPTIMIZER_ARGS --optimizer-uri http://localhost:54321)
    else()
        set(OPTIMIZER_ARGS "")
    endif()

    # Basically we want to run:
    # $ dotnet Mlos.Agent.Server.dll --executable /some/test/exe
    # However, we need to
    # - Make sure there aren't other things using the shared mem regions in
    #   /dev/shm/ that we're about to create (e.g. from a previous failed test
    #   or something else that's running).
    #   (and also clean them up after we're done)
    # - Make sure that the Agent can find the SettingsRegistry DLLs that the
    #   /some/test/exe needs to use.
    add_test(NAME ${TEST_NAME}
        COMMAND ${MLOS_ROOT}/build/CMakeHelpers/RunTestsAndSharedMemChecks.sh
            ${DOTNET} $<TARGET_PROPERTY:Mlos.Agent.Server,DOTNET_OUTPUT_DLL>
            --executable $<TARGET_FILE:${TEST_EXECUTABLE_TARGET}>
            --settings-registry-path "${SETTINGS_REGISTRY_PATH}"
            ${OPTIMIZER_ARGS})
    set_tests_properties(${TEST_NAME} PROPERTIES
        TIMEOUT ${TEST_TIMEOUT}
        # Make sure to check for existing shared registry memories before hand.
        FIXTURES_REQUIRED MlosSharedMemoriesChecks
        # This test conflicts with any other test using the MlosSharedMemories
        # (no parallel test runs).
        RESOURCE_LOCK MlosSharedMemories)
    if(${WITH_OPTIMIZER})
        set_tests_properties(${TEST_NAME} PROPERTIES
            FIXTURES_REQUIRED MlosOptimizerService)
    endif()
    # Include these targets in cmake's "check" target so we can build/test in one shot.
    add_dependencies(check ${TEST_EXECUTABLE_TARGET} Mlos.Agent.Server)
    add_dependencies(${TEST_EXECUTABLE_TARGET} Mlos.Agent.Server)
endfunction()
