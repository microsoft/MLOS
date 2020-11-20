CONFIGURATION ?= Release

all: dotnet-build

clean: dotnet-clean

dotnet-build:
	dotnet build $(MSBUILD_ARGS) -c $(CONFIGURATION) /p:PackMlosDependencies=true

dotnet-build-quick:
	dotnet build $(MSBUILD_ARGS) -c $(CONFIGURATION) --no-restore

dotnet-rebuild-all:
	dotnet build $(MSBUILD_ARGS) -c $(CONFIGURATION) /p:PackMlosDependencies=true /p:CleanMlosPackages=true

dotnet-clean:
	dotnet build $(MSBUILD_ARGS) -c $(CONFIGURATION) --no-restore /t:clean

# A quick wrapper for invoking testing the CMakeLists.txt wrapper.
cmake-build:
	mkdir -p ../build
	cd ../build && cmake ../build
	make -C ../build/ ExternalIntegrationExample.SettingsRegistry
