# This is a sub component of the ExternalIntegrationExample.cpp
# As such, some additional setup work to fetch and prepare the MLOS upstream
# source repo for use is expected to have been done already.
# See Also: MlosBuildIntegrations.cmake

include(MLOS)

# Use an MLOS cmake module provided function to create a small wrapper target
# around the dotnet build for the SettingsRegistry csproj file.
#
add_mlos_settings_registry(
    # The name of the .csproj for this MLOS SettingsRegistry:
    NAME ExternalIntegrationExample.SettingsRegistry
    # Where to find it:
    DIRECTORY "${CMAKE_CURRENT_LIST_DIR}"
    # Optionally override some settings in the .csproj file.
    #
    # This is equivalent to "dotnet build /p:MlosSettingsSystemCodeGenOutputDirectory=/basepath-to-all-codegen-output/specific-component"
    CODEGEN_OUTPUT_DIR "${MlosCodeGenBaseOutDir}/ExternalIntegrationExample"
    # This is equivalent to "dotnet build /p:MlosSettingsRegistryAssemblyOutputDirectory=/path-to-all-settings-registry-dll-outputs"
    BINPLACE_DIR "${MlosSettingsRegistryDllDir}"
    # Optionally build, pack, and restore the nugets from the local Mlos repo checkout.
    # (since we aren't yet publishing these nugets, this is currently required)
    USE_LOCAL_MLOS_NUGETS
)
