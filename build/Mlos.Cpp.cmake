# Mlos.Cpp.cmake
#
# A set of common C++ related cmake rules.

# First search for headers in the current source directory.
# This takes the place of include_directories(.) in most projects.
include_directories(${PROJECT_SOURCE_DIR})

# Next, assume that the C++ projects we're building also need to include either
# Mlos.Core headers and the SettingsProvider code generation output.
include_directories(${MLOS_ROOT}/source/Mlos.Core/)
include_directories(${MLOS_CODEGEN_OUTPUT_ROOT}/)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Make sure to flag all warnings.
add_compile_options(-Wall -Wextra -Wpedantic -Werror)
add_link_options(-Wall -Wextra -Wpedantic -Werror)

# The codegen output currently relies on __declspec(selectany) attributes to
# instruct the linker to ignore extra definitions resulting from including the
# same header in multiple places.
# NOTE: This option is only available with clang, not gcc.
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fdeclspec")

# When compiling for Debug build, make sure that DEBUG is defined for the compiler.
# This is to mimic MSVC behavior so that our #ifdefs can remain the same rather
# than having to switch to using NDEBUG.
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -DDEBUG")

# Always include symbols to make debugging reasonable.
# TODO: For optimized builds, strip them and keep the symbols separately.
add_compile_options(-g)
add_link_options(-g)

# TODO: Search for clang compiler and set the appropriate C/CXX compiler variables.
#if(NOT (CMAKE_CXX_COMPILER_ID MATCHES "Clang"))
#    # TODO: Add local version of clang to use?
#    find_program(CLANGCPP
#        NAMES clang++-10
#        #PATHS ENV PATH
#        )
#    if(CLANGCPP)
#        message(WARNING "Forcing CXX compiler to ${CLANGCPP}")
#        set(CMAKE_CXX_COMPILER ${CLANGPP})
#        set(CMAKE_CXX_COMPILER_ID "Clang")
#    endif()
#endif()

# For now we just abort if Clang is not the compiler selected.
if(NOT (CMAKE_CXX_COMPILER_ID MATCHES "Clang"))
    message(SEND_ERROR
        "MLOS currently only supports clang (not '${CMAKE_CXX_COMPILER_ID}') for compilation.\n"
        "Please re-run (c)make with 'CC=clang-10 CXX=clang++-10' set.\n")
endif()

# TODO: This just finds the program, but doesn't actually enable it as a
# target.  To use clang-tidy, we will need to provide a .clang-format config
# and probably reformat some code again.
find_program(CLANG_TIDY NAMES clang-tidy clang-tidy-6.0)
if(CLANG_TIDY)
    add_custom_target(
        clang-tidy
        COMMAND ${CLANG_TIDY}
        ${SOURCE_FILES}
        --
        -I ${CMAKE_SOURCE_DIR}/include)
endif()

# https://github.com/google/sanitizers/wiki/AddressSanitizer
#
option(ADDRESS_SANITIZER "Enable Clang AddressSanitizer" OFF)
if(ADDRESS_SANITIZER)
    message(STATUS "AddressSanitizer enabled for debug build")
    set(CMAKE_CXX_FLAGS_DEBUG
        "${CMAKE_CXX_FLAGS_DEBUG} -O1 -fno-omit-frame-pointer -fsanitize=address")
endif()

# https://releases.llvm.org/10.0.0/tools/clang/docs/UndefinedBehaviorSanitizer.html
#
option(UNDEFINED_SANITIZER "Enable Clang UndefinedBehaviorSanitizer" OFF)
if(UNDEFINED_SANITIZER)
    message(STATUS "UndefinedBehaviorSanitizer enabled for debug build")
    set(CMAKE_CXX_FLAGS_DEBUG
        "${CMAKE_CXX_FLAGS_DEBUG} -fsanitize=undefined -fsanitize=integer")
endif()
