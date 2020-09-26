# Mlos.Common.targets.cmake
#
# A set of common additional cmake targets to be provided by the top-level CMakeList.txt
# Seperated mostly for readability.

# Optionally generate a ctags database for local editors to use to navigate the code.
# Note: We exclude this from the "all" target and don't give it source file
# dependencies to avoid issues with file addition/removal.
# To invoke this, the target needs to be explictly asked for.
find_program(CTAGS ctags)
if(CTAGS)
    set(CTAGS_OUTPUT "${MLOS_ROOT}/tags")
    add_custom_target(ctags
        COMMENT "Generating ctags db"
        COMMAND ${CTAGS}
                --recurse --exclude=.git --tag-relative=yes
                --languages=+Python --languages=+C++ --languages=+C\#
                --C++-kinds=+p --C\#-kinds=+p
                -h "+.inl" --langmap=C++:+.inl
                --fields=+iaS --fields=+l --extra=+q --fields=+K
                --exclude=tools/ --exclude=target/
                .
        VERBATIM
        BYPRODUCTS "${CTAGS_OUTPUT}"
        WORKING_DIRECTORY "${MLOS_ROOT}")
else()
    add_custom_target(ctags
        COMMENT "Skipping ctags - command not found.")
endif()

# Make sure that if this doesn't exist we invoke the setup-dotnet.sh script.
# See Also: Mlos.NetCore.cmake

# FIXME: Prevent "clean" from removing this output file.

add_custom_command(OUTPUT "${DOTNET}"
    COMMAND "${MLOS_ROOT}/scripts/setup-dotnet.sh"
    WORKING_DIRECTORY "${MLOS_ROOT}"
    COMMENT "Setting up local dotnet")

add_custom_target(DOTNET_TOOL
    DEPENDS "${DOTNET_REAL}"
    DEPENDS "${DOTNET}")
