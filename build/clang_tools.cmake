find_program(CLANG_TIDY NAMES clang-tidy clang-tidy-6.0)
if (CLANG_TIDY)
    add_custom_target(
            clang-tidy
            COMMAND ${CLANG_TIDY}
            ${SOURCE_FILES}
            --
            -I ${CMAKE_SOURCE_DIR}/include
    )
endif()

# https://github.com/google/sanitizers/wiki/AddressSanitizer
#
option(ADDRESS_SANITIZER "Enable Clang AddressSanitizer" OFF)
if (ADDRESS_SANITIZER)
    message(STATUS "AddressSanitizer enabled for debug build")
    set(CMAKE_CXX_FLAGS_DEBUG
            "${CMAKE_CXX_FLAGS_DEBUG} -O1 -fno-omit-frame-pointer -fsanitize=address")
endif()

# https://releases.llvm.org/10.0.0/tools/clang/docs/UndefinedBehaviorSanitizer.html
#
option(UNDEFINED_SANITIZER "Enable Clang UndefinedBehaviorSanitizer" OFF)
if (UNDEFINED_SANITIZER)
    message(STATUS "UndefinedBehaviorSanitizer enabled for debug build")
    set(CMAKE_CXX_FLAGS_DEBUG
            "${CMAKE_CXX_FLAGS_DEBUG} -fsanitize=undefined -fsanitize=integer")
endif()
