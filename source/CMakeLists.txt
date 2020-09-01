get_filename_component(MLOS_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
include("${MLOS_ROOT}/build/Mlos.Common.cmake")

# "dotnet build" cmake wrappers provided to allow building C++ project
# SettingProvider code generations and ctest invokation
# Note: We mark them as "EXCLUDE_FROM_ALL" to avoid unnecessary rebuilds when
# invoked from our `make` wrappers (which just call "dotnet build" for all
# .csproj files).
add_subdirectory(Mlos.SettingsSystem.Attributes EXCLUDE_FROM_ALL)
add_subdirectory(Mlos.SettingsSystem.CodeGen EXCLUDE_FROM_ALL)
add_subdirectory(Mlos.NetCore EXCLUDE_FROM_ALL)
add_subdirectory(Mlos.NetCore.UnitTest EXCLUDE_FROM_ALL)
add_subdirectory(Mlos.Model.Services EXCLUDE_FROM_ALL)
add_subdirectory(Mlos.Model.Services.Client EXCLUDE_FROM_ALL)
add_subdirectory(Mlos.Streaming EXCLUDE_FROM_ALL)
add_subdirectory(Mlos.Agent EXCLUDE_FROM_ALL)
add_subdirectory(Mlos.Agent.GrpcClient EXCLUDE_FROM_ALL)
add_subdirectory(Mlos.Agent.GrpcServer EXCLUDE_FROM_ALL)
add_subdirectory(Mlos.Agent.Server EXCLUDE_FROM_ALL)

# Start listing our other C++ sub projects.
# See Also: dirs.proj

add_subdirectory(Mlos.Core)
add_subdirectory(Mlos.UnitTest)
add_subdirectory(Examples)
