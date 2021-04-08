# Make sure that the nuget.org source is available.
# Needed to work around a Github Actions runner change.
#
if (!(dotnet nuget list source --format Short | Select-String ' https://api.nuget.org/v3/index.json$' -Quiet)) {
    Write-Warning "Adding missing nuget.org sources."
    dotnet nuget add source https://api.nuget.org/v3/index.json -n nuget.org --configfile $env:APPDATA\NuGet\NuGet.Config
}
