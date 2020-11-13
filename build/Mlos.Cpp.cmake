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

# The codegen output currently relies on asking the compiler to select one of
# our equivalent but duplicative definitions that results from including the
# same header in multiple places.
# For clang, make use of the original __declspec(selectany) attributes that msvc
# uses.
# For gcc, we use __attribute__((weak)) to achieve the same.
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fdeclspec")
endif()

# When compiling for Debug build, make sure that DEBUG is defined for the compiler.
# This is to mimic MSVC behavior so that our #ifdefs can remain the same rather
# than having to switch to using NDEBUG.
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -DDEBUG")

# Always include symbols to make debugging reasonable.
# TODO: For optimized builds, strip them and keep the symbols separately.
add_compile_options(-g)
add_link_options(-g)

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
