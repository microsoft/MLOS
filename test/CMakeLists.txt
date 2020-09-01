# Start listing our other sub projects.
# See Also: dirs.proj

get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
include("${MLOS_ROOT}/build/Mlos.Common.cmake")

add_subdirectory(Mlos.TestRun)
