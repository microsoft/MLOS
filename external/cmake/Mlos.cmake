cmake_minimum_required(VERSION 3.15)

# TODO: add target for making sure that the Mlos.NetCore.Components.Packages have been built out of the Mlos source tree
#   - that should probably happen in the Mlos.NetCore.Components.Packages/CMakeLists.txt file directly
#   - mark it as EXCLUDE_FROM_ALL though

# TODO: function/macro for building SettingsRegistry targets
    # - use the existing helper script to include the sources found in the project file, plus the project file itself
    # - add a dependency on special Mlos pkgs target
    # - run "dotnet build" with the special /p:RestoreSources property set to the mlos build dir packages path
    # - upon success output a build stamp as the output (instead of trying to track where the .dll goes)
    # - allow specifying the binplace directory via the function

# TODO: function/macro to add additional settings/dependencies to C++ project

